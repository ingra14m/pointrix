import torch
import torch.nn as nn
import torch.nn.functional as F

from pointrix.model.base_model import BaseModel, MODEL_REGISTRY

def get_embedder(multires, i=1):
    if i == -1:
        return nn.Identity(), 3

    embed_kwargs = {
        'include_input': True,
        'input_dims': i,
        'max_freq_log2': multires - 1,
        'num_freqs': multires,
        'log_sampling': True,
        'periodic_fns': [torch.sin, torch.cos],
    }

    embedder_obj = Embedder(**embed_kwargs)
    embed = lambda x, eo=embedder_obj: eo.embed(x)
    return embed, embedder_obj.out_dim

class Embedder:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.create_embedding_fn()

    def create_embedding_fn(self):
        embed_fns = []
        d = self.kwargs['input_dims']
        out_dim = 0
        if self.kwargs['include_input']:
            embed_fns.append(lambda x: x)
            out_dim += d

        max_freq = self.kwargs['max_freq_log2']
        N_freqs = self.kwargs['num_freqs']

        if self.kwargs['log_sampling']:
            freq_bands = 2. ** torch.linspace(0., max_freq, steps=N_freqs)
        else:
            freq_bands = torch.linspace(2. ** 0., 2. ** max_freq, steps=N_freqs)

        for freq in freq_bands:
            for p_fn in self.kwargs['periodic_fns']:
                embed_fns.append(lambda x, p_fn=p_fn, freq=freq: p_fn(x * freq))
                out_dim += d

        self.embed_fns = embed_fns
        self.out_dim = out_dim

    def embed(self, inputs):
        return torch.cat([fn(inputs) for fn in self.embed_fns], -1)

class DeformNetwork(nn.Module):
    def __init__(self, D=8, W=256, input_ch=3, output_ch=59, t_multires=6, multires=10,
                 is_blender=False):  # t_multires 6 for D-NeRF; 10 for HyperNeRF
        super(DeformNetwork, self).__init__()
        self.D = D
        self.W = W
        self.input_ch = input_ch
        self.output_ch = output_ch
        self.t_multires = 6 if is_blender else 10
        self.skips = [D // 2]

        self.embed_time_fn, time_input_ch = get_embedder(t_multires, 1)
        self.embed_fn, xyz_input_ch = get_embedder(multires, 3)
        self.input_ch = xyz_input_ch + time_input_ch

        if is_blender:
            # Better for D-NeRF Dataset
            self.time_out = 30

            self.timenet = nn.Sequential(
                nn.Linear(time_input_ch, 256), nn.ReLU(inplace=True),
                nn.Linear(256, self.time_out))

            self.linear = nn.ModuleList(
                [nn.Linear(xyz_input_ch + self.time_out, W)] + [
                    nn.Linear(W, W) if i not in self.skips else nn.Linear(W + xyz_input_ch + self.time_out, W)
                    for i in range(D - 1)]
            )

        else:
            self.linear = nn.ModuleList(
                [nn.Linear(self.input_ch, W)] + [
                    nn.Linear(W, W) if i not in self.skips else nn.Linear(W + self.input_ch, W)
                    for i in range(D - 1)]
            )

        self.is_blender = is_blender

        self.gaussian_warp = nn.Linear(W, 3)
        # self.branch_w = nn.Linear(W, 3)
        # self.branch_v = nn.Linear(W, 3)
        self.gaussian_rotation = nn.Linear(W, 4)
        self.gaussian_scaling = nn.Linear(W, 3)

    def forward(self, x, t):
        t_emb = self.embed_time_fn(t)
        if self.is_blender:
            t_emb = self.timenet(t_emb)  # better for D-NeRF Dataset
        x_emb = self.embed_fn(x)
        h = torch.cat([x_emb, t_emb], dim=-1)
        for i, l in enumerate(self.linear):
            h = self.linear[i](h)
            h = F.relu(h)
            if i in self.skips:
                h = torch.cat([x_emb, t_emb, h], -1)
        d_xyz = self.gaussian_warp(h)
        scaling = self.gaussian_scaling(h)
        rotation = self.gaussian_rotation(h)

        return d_xyz, rotation, scaling

@MODEL_REGISTRY.register()
class DeformGaussian(BaseModel):
    def __init__(self, cfg, datapipeline, device="cuda"):
        super().__init__(cfg, datapipeline, device)
        self.deform = DeformNetwork(is_blender=False).to(self.device)
    
    def forward(self, batch):
        camera_fid = torch.Tensor([batch[0]['camera'].fid]).float().to(self.device)
        position = self.point_cloud.get_position
        time_input = camera_fid.unsqueeze(0).expand(position.shape[0], -1)
        d_xyz, d_rotation, d_scaling = self.deform(position, time_input)

        render_dict = {
            "position": self.point_cloud.position + d_xyz,
            "opacity": self.point_cloud.get_opacity,
            "scaling": self.point_cloud.get_scaling + d_scaling,
            "rotation": self.point_cloud.get_rotation + d_rotation,
            "shs": self.point_cloud.get_shs,
        }
        
        return render_dict
    
    def get_param_groups(self):
        """
        Get the parameter groups for optimizer

        Returns
        -------
        dict
            The parameter groups for optimizer
        """
        param_group = {}
        param_group[self.point_cloud.prefix_name +
                    'position'] = self.point_cloud.position
        param_group[self.point_cloud.prefix_name +
                    'opacity'] = self.point_cloud.opacity
        param_group[self.point_cloud.prefix_name +
                    'features'] = self.point_cloud.features
        param_group[self.point_cloud.prefix_name +
                    'features_rest'] = self.point_cloud.features_rest
        param_group[self.point_cloud.prefix_name +
                    'scaling'] = self.point_cloud.scaling
        param_group[self.point_cloud.prefix_name +
                    'rotation'] = self.point_cloud.rotation

        param_group['deform'] = self.deform.parameters()
        return param_group