import cv2
import numpy as np
import scipy.signal
import torch
import torchvision.transforms as T
from PIL import Image

def visualize_depth_numpy(depth, minmax=None, cmap=cv2.COLORMAP_JET):
    """
    depth: (H, W)
    """

    x = np.nan_to_num(depth)  # change nan to 0
    if minmax is None:
        mi = np.min(x[x > 0])  # get minimum positive depth (ignore background)
        ma = np.max(x)
    else:
        mi, ma = minmax

    x = (x - mi) / (ma - mi + 1e-8)  # normalize to 0~1
    x = (255 * x).astype(np.uint8)
    x_ = cv2.applyColorMap(x, cmap)
    return x_, [mi, ma]


def visualize_depth(depth, minmax=None, cmap=cv2.COLORMAP_JET):
    """
    depth: (H, W)
    """
    if type(depth) is not np.ndarray:
        depth = depth.cpu().numpy()

    x = np.nan_to_num(depth)  # change nan to 0
    if minmax is None:
        mi = np.min(x[x > 0])  # get minimum positive depth (ignore background)
        ma = np.max(x)
    else:
        mi, ma = minmax

    x = (x - mi) / (ma - mi + 1e-8)  # normalize to 0~1
    x = (255 * x).astype(np.uint8)
    x_ = Image.fromarray(cv2.applyColorMap(x, cmap))
    x_ = T.ToTensor()(x_)  # (3, H, W)
    return x_, [mi, ma]