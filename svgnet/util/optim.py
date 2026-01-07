import torch.optim
from typing import Any, Dict, List, Set
import copy
import itertools
from munch import Munch

# Replacement for detectron2's maybe_add_gradient_clipping
def maybe_add_gradient_clipping(cfg, optimizer):
    """
    Add gradient clipping to an optimizer if configured.
    This is a simplified version to replace detectron2's implementation.
    """
    if not cfg.SOLVER.CLIP_GRADIENTS.ENABLED:
        return optimizer

    clip_type = cfg.SOLVER.CLIP_GRADIENTS.CLIP_TYPE
    clip_value = cfg.SOLVER.CLIP_GRADIENTS.CLIP_VALUE
    norm_type = cfg.SOLVER.CLIP_GRADIENTS.NORM_TYPE

    if clip_type == "value":
        class GradientClippingOptimizer(type(optimizer)):
            def step(self, closure=None):
                all_params = itertools.chain(*[x["params"] for x in self.param_groups])
                torch.nn.utils.clip_grad_value_(all_params, clip_value)
                super().step(closure=closure)
        return GradientClippingOptimizer.__new__(GradientClippingOptimizer, optimizer.param_groups)
    elif clip_type == "norm":
        class GradientClippingOptimizer(type(optimizer)):
            def step(self, closure=None):
                all_params = itertools.chain(*[x["params"] for x in self.param_groups])
                torch.nn.utils.clip_grad_norm_(all_params, clip_value, norm_type=norm_type)
                super().step(closure=closure)
        return GradientClippingOptimizer.__new__(GradientClippingOptimizer, optimizer.param_groups)
    else:
        return optimizer


def build_optimizer(model, optim_cfg):
    assert "type" in optim_cfg
    _optim_cfg = optim_cfg.copy()
    optim_type = _optim_cfg.pop("type")
    optim = getattr(torch.optim, optim_type)

    return optim(filter(lambda p: p.requires_grad, model.parameters()), **_optim_cfg)

def build_new_optimizer(model,args):
    weight_decay_norm = args.weight_decay
    weight_decay_embed = args.weight_decay_embed
    defaults = {}
    defaults["lr"] = args.lr
    defaults["weight_decay"] = args.weight_decay
    norm_module_types = (
            torch.nn.BatchNorm1d,
            torch.nn.BatchNorm2d,
            torch.nn.BatchNorm3d,
            torch.nn.SyncBatchNorm,
            # NaiveSyncBatchNorm inherits from BatchNorm2d
            torch.nn.GroupNorm,
            torch.nn.InstanceNorm1d,
            torch.nn.InstanceNorm2d,
            torch.nn.InstanceNorm3d,
            torch.nn.LayerNorm,
            torch.nn.LocalResponseNorm,
        )
    params: List[Dict[str, Any]] = []
    memo: Set[torch.nn.parameter.Parameter] = set()
    for module_name, module in model.named_modules():
        for module_param_name, value in module.named_parameters(recurse=False):
            if not value.requires_grad: continue
            if value in memo: continue
            memo.add(value)
            hyperparams = copy.copy(defaults)
            if "decoder" in module_name:
                hyperparams["lr"] = hyperparams["lr"] * args.decoder_multiplier
            if (
                "relative_position_bias_table" in module_param_name
                or "absolute_pos_embed" in module_param_name
            ):
                print(module_param_name)
                hyperparams["weight_decay"] = 0.0
            if isinstance(module, norm_module_types):
                hyperparams["weight_decay"] = weight_decay_norm
            if isinstance(module, torch.nn.Embedding):
                hyperparams["weight_decay"] = weight_decay_embed
            params.append({"params": [value], **hyperparams})
            
    def maybe_add_full_model_gradient_clipping(args,optim):
        # detectron2 doesn't have full model gradient clipping now
        clip_norm_val = args.clip_gradients_value
        enable = (
            args.clip_gradients_enabled
            and args.clip_gradients_type == "full_model"
            and clip_norm_val > 0.0
        )
        class FullModelGradientClippingOptimizer(optim):
            def step(self, closure=None):
                all_params = itertools.chain(*[x["params"] for x in self.param_groups])
                torch.nn.utils.clip_grad_norm_(all_params, clip_norm_val)
                super().step(closure=closure)
        return FullModelGradientClippingOptimizer if enable else optim
    
    optimizer_type = args.type
    if optimizer_type == "SGD":
        optimizer = maybe_add_full_model_gradient_clipping(args,torch.optim.SGD)(
            params, args.lr, momentum=args.momentum
        )
    elif optimizer_type == "AdamW":
        optimizer = maybe_add_full_model_gradient_clipping(args,torch.optim.AdamW)(
            params, args.lr
        )
    else:
        raise NotImplementedError(f"no optimizer type {optimizer_type}")

    # Use Munch instead of detectron2's CfgNode
    args.SOLVER = Munch()
    args.SOLVER.CLIP_GRADIENTS = Munch()
    args.SOLVER.CLIP_GRADIENTS.ENABLED  = args.clip_gradients_enabled
    args.SOLVER.CLIP_GRADIENTS.CLIP_TYPE  = args.clip_gradients_type
    args.SOLVER.CLIP_GRADIENTS.CLIP_VALUE  = args.clip_gradients_value
    args.SOLVER.CLIP_GRADIENTS.NORM_TYPE  = args.clip_gradients_norm_type

    if not args.clip_gradients_type == "full_model":
        optimizer = maybe_add_gradient_clipping(args, optimizer)
    return optimizer