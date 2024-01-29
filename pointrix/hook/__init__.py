from .hook import HOOK_REGISTRY
from .log_hook import LogHook
from .checkpoint_hook import CheckPointHook
from .lr_scheduler_hook import LRSchedulerHook

def parse_hooks(cfg):
    if len(cfg) == 0:
        return None
    hooks = []
    for hook in cfg:
        hook_name = cfg[hook]['name']
        hook = HOOK_REGISTRY.get(hook_name)
        assert hook is not None, "Hook is not registered: {}".format(
            hook_name
        )
        hooks.append(hook())
    return hooks