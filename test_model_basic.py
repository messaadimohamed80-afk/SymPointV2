#!/usr/bin/env python3
"""
Basic model test without CUDA requirements.
This test verifies that the model structure is correct and can be imported.
"""

import sys
import torch
import yaml
from munch import Munch

print("=" * 80)
print("Basic Model Structure Test")
print("=" * 80)

# Test 1: Import basic modules
print("\n[Test 1] Testing basic imports...")
try:
    from svgnet.model.svgnet import SVGNet
    print("✓ SVGNet imported successfully")
except Exception as e:
    print(f"✗ Failed to import SVGNet: {e}")
    sys.exit(1)

try:
    from svgnet.model.criterion import SetCriterion
    from svgnet.model.matcher import HungarianMatcher
    print("✓ Criterion and Matcher imported successfully")
except Exception as e:
    print(f"✗ Failed to import Criterion/Matcher: {e}")
    sys.exit(1)

# Test 2: Load config
print("\n[Test 2] Loading configuration...")
try:
    cfg_path = "configs/svg/svg_pointT.yaml"
    with open(cfg_path, "r") as f:
        cfg_txt = f.read()
    cfg = Munch.fromDict(yaml.safe_load(cfg_txt))
    print(f"✓ Config loaded successfully")
    print(f"  - Semantic classes: {cfg.model.semantic_classes}")
    print(f"  - Hidden dim: {cfg.model.hidden_dim}")
    print(f"  - Num queries: {cfg.model.num_queries}")
except Exception as e:
    print(f"✗ Failed to load config: {e}")
    sys.exit(1)

# Test 3: Create matcher and criterion
print("\n[Test 3] Creating matcher and criterion...")
try:
    matcher = HungarianMatcher(**cfg.matcher)
    print("✓ HungarianMatcher created successfully")

    weight_dict = {
        "loss_ce": cfg.matcher.cost_class,
        "loss_mask": cfg.matcher.cost_mask,
        "loss_dice": cfg.matcher.cost_dice,
    }
    criterion = SetCriterion(matcher, weight_dict, cfg.criterion)
    print("✓ SetCriterion created successfully")
except Exception as e:
    print(f"✗ Failed to create matcher/criterion: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Create model (this will fail if pointops is required, but we'll see the error)
print("\n[Test 4] Creating model instance...")
try:
    model = SVGNet(cfg.model, criterion=criterion)
    print("✓ SVGNet model created successfully")
    print(f"  - Model type: {type(model).__name__}")

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"  - Total parameters: {total_params / 1e6:.2f}M")
    print(f"  - Trainable parameters: {trainable_params / 1e6:.2f}M")
except Exception as e:
    print(f"✗ Failed to create model: {e}")
    import traceback
    traceback.print_exc()
    # Don't exit, continue with other tests

# Test 5: Check model structure
print("\n[Test 5] Checking model structure...")
try:
    model = SVGNet(cfg.model, criterion=criterion)
    print("✓ Model components:")
    if hasattr(model, 'backbone'):
        print(f"  - Backbone: {type(model.backbone).__name__}")
    if hasattr(model, 'decoder'):
        print(f"  - Decoder: {type(model.decoder).__name__}")
    if hasattr(model, 'criterion'):
        print(f"  - Criterion: {type(model.criterion).__name__}")
    print(f"  - Num classes: {model.num_classes}")
except Exception as e:
    print(f"✗ Failed to check model structure: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Summary")
print("=" * 80)
print("Basic model structure test completed!")
print("Note: Full testing requires CUDA and compiled pointops module.")
print("=" * 80)
