import torch
import torch.nn as nn
from pointrix.utils.config import parse_structured

from .base_optimizer import BaseOptimizer, OPTIMIZER_REGISTRY
from .gs_optimizer import GaussianSplattingOptimizer
from .optimizers import Optimizers
from .scheduler import ExponLRScheduler, SCHEDULER_REGISTRY


__all__ = ["BaseOptimizer", "GaussianSplattingOptimizer"]


def getattr_recursive(m, attr):
    for name in attr.split("."):
        m = getattr(m, name)
    return m

def get_parameters(model, name):
    module = getattr_recursive(model, name)
    if isinstance(module, nn.Module):
        return module.parameters()
    elif isinstance(module, nn.Parameter):
        return module
    return []

def parse_optimizer(configs, model, **kwargs):
    """
    Parse the optimizer.

    Parameters
    ----------
    config : dict
        The configuration dictionary.
    model : BaseModel
        The model.
    """
    param_groups = model.get_param_groups()
    optimizer_dict = {}
    for name, config in configs.items():
        if hasattr(config, "params"):
            params = [
                {"params": param_groups[name], "name": name, **args}
                for name, args in config.params.items()
            ]
        else:
            params = model.parameters()
            
        if config.name in ["FusedAdam"]:
            import apex

            optim = getattr(apex.optimizers, config.name)(params, **config.args)
        else:
            optim = getattr(torch.optim, config.name)(params, **config.args)

        optimizer_type = config.type
        optimizer = OPTIMIZER_REGISTRY.get(optimizer_type)
        optimizer_dict[name] = optimizer(optim, model.point_cloud, config.structure, **kwargs)
    
    return Optimizers(optimizer_dict)

def parse_scheduler(config, lr_scale=1.0):
    scheduler = SCHEDULER_REGISTRY.get(config.name)
    return scheduler(config, lr_scale)