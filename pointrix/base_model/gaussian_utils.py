import torch
from pytorch_msssim import ms_ssim
from pointrix.utils.losses import l1_loss

from tqdm import tqdm

# FIXME: this is a hack to build lpips loss and lpips metric
from lpips import LPIPS
lpips_net = LPIPS(net="vgg").to("cuda")
lpips_norm_fn = lambda x: x[None, ...] * 2 - 1
lpips_norm_b_fn = lambda x: x * 2 - 1
lpips_fn = lambda x, y: lpips_net(lpips_norm_fn(x), lpips_norm_fn(y)).mean()
lpips_b_fn = lambda x, y: lpips_net(lpips_norm_b_fn(x), lpips_norm_b_fn(y)).mean()

def inverse_sigmoid(x):
    return torch.log(x/(1-x))

def build_rotation(r):
    norm = torch.sqrt(r[:,0]*r[:,0] + r[:,1]*r[:,1] + r[:,2]*r[:,2] + r[:,3]*r[:,3])

    q = r / norm[:, None]

    R = torch.zeros((q.size(0), 3, 3), device='cuda')

    r = q[:, 0]
    x = q[:, 1]
    y = q[:, 2]
    z = q[:, 3]

    R[:, 0, 0] = 1 - 2 * (y*y + z*z)
    R[:, 0, 1] = 2 * (x*y - r*z)
    R[:, 0, 2] = 2 * (x*z + r*y)
    R[:, 1, 0] = 2 * (x*y + r*z)
    R[:, 1, 1] = 1 - 2 * (x*x + z*z)
    R[:, 1, 2] = 2 * (y*z - r*x)
    R[:, 2, 0] = 2 * (x*z - r*y)
    R[:, 2, 1] = 2 * (y*z + r*x)
    R[:, 2, 2] = 1 - 2 * (x*x + y*y)
    return R

def build_covariance_from_scaling_rotation(scaling, scaling_modifier, rotation):
    
    s = scaling_modifier * scaling
    
    L = torch.zeros((s.shape[0], 3, 3), dtype=torch.float)
    
    R = build_rotation(rotation)
    
    L[:,0,0] = s[:,0]
    L[:,1,1] = s[:,1]
    L[:,2,2] = s[:,2]

    L = R @ L
    # L = build_scaling_rotation(scaling_modifier * scaling, rotation)
    L = L @ L.transpose(1, 2)
    
    uncertainty = torch.zeros((L.shape[0], 6), dtype=torch.float)

    uncertainty[:, 0] = L[:, 0, 0]
    uncertainty[:, 1] = L[:, 0, 1]
    uncertainty[:, 2] = L[:, 0, 2]
    uncertainty[:, 3] = L[:, 1, 1]
    uncertainty[:, 4] = L[:, 1, 2]
    uncertainty[:, 5] = L[:, 2, 2]
    
    return uncertainty


def psnr(img1, img2):
    mse = (((img1 - img2)) ** 2).view(img1.shape[0], -1).mean(1, keepdim=True)
    return 20 * torch.log10(1.0 / torch.sqrt(mse))

# TODO: rewite this function, it is ugly
def validation_process(render_func, dataset, global_step=0, logger=None):
    l1_test = 0.0
    psnr_test = 0.0
    ssims_test = 0.0
    lpips_test = 0.0
    progress_bar = tqdm(
        range(0, len(dataset)), 
        desc="Validation progress", 
        leave=False,
    )
    for data in dataset:
        render_results = render_func(data)
        image = torch.clamp(render_results["render"], 0.0, 1.0)
        gt_image = torch.clamp(data["image"].to("cuda"), 0.0, 1.0)
        opacity = render_results["opacity"]
        depth = render_results["depth"]
        depth_normal = (depth - depth.min()) / (depth.max() - depth.min())

        if logger:
            image_name = data["image_name"]
            iteration = global_step
            logger.add_images("test" + f"_view_{image_name}/render", image[None], global_step=iteration)
            logger.add_images("test" + f"_view_{image_name}/ground_truth", gt_image[None], global_step=iteration)
            logger.add_images("test" + f"_view_{image_name}/opacity", opacity[None], global_step=iteration)
            logger.add_images("test" + f"_view_{image_name}/depth", depth_normal[None], global_step=iteration)
            
        l1_test += l1_loss(image, gt_image).mean().double()
        psnr_test += psnr(image, gt_image).mean().double()
        ssims_test += ms_ssim(
            image[None], gt_image[None], data_range=1, size_average=True
        )   
        lpips_test += lpips_fn(image, gt_image).item()
        progress_bar.update(1)
    progress_bar.close()
    l1_test /= len(dataset)
    psnr_test /= len(dataset)
    ssims_test /= len(dataset)
    lpips_test /= len(dataset)    
    print(f"\n[ITER {iteration}] Evaluating test: L1 {l1_test:.5f} PSNR {psnr_test:.5f} SSIMS {ssims_test:.5f} LPIPS {lpips_test:.5f}")
    if logger:
        iteration = global_step
        logger.add_scalar(
            "test" + '/loss_viewpoint - l1_loss', 
            l1_test, 
            iteration
        )
        logger.add_scalar(
            "test" + '/loss_viewpoint - psnr', 
            psnr_test, 
            iteration
        )
        logger.add_scalar(
            "test" + '/loss_viewpoint - ssims', 
            ssims_test, 
            iteration
        )
        logger.add_scalar(
            "test" + '/loss_viewpoint - lpips', 
            lpips_test, 
            iteration
        )
        
# TODO: rewite this function, it is ugly
def render_batch(render_func, batch):
    renders = []
    viewspace_points = []
    visibilitys = []
    radiis = []
    gt_images = []
    
    for b_i in batch:
        render_results = render_func(b_i)
        
        renders.append(render_results["render"])
        viewspace_points.append(render_results["viewspace_points"])
        visibilitys.append(render_results["visibility_filter"].unsqueeze(0))
        radiis.append(render_results["radii"].unsqueeze(0))
        gt_images.append(b_i["image"].cuda())
        
    radii = torch.cat(radiis,0).max(dim=0).values
    visibility = torch.cat(visibilitys).any(dim=0)
    images = torch.stack(renders)
    gt_images = torch.stack(gt_images)    
    
    return images, gt_images, radii, visibility, viewspace_points