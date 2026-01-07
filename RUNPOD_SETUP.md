# Running SymPointV2 on RunPod

This guide will help you set up and run SymPointV2 on RunPod with GPU support.

## 1. Create RunPod Instance

1. Go to [RunPod.io](https://www.runpod.io/)
2. Select a GPU pod (recommended: RTX 3090, RTX 4090, or A6000)
3. Choose a PyTorch template or Ubuntu + CUDA template
4. Start your pod

## 2. Initial Setup on RunPod

Once your pod is running, connect via SSH or Jupyter terminal:

```bash
# Update system
apt-get update
apt-get install -y git wget

# Clone the repository
git clone https://github.com/messaadimohamed80-afk/SymPointV2.git
cd SymPointV2
git checkout claude/fix-test-model-0bB0H  # Use the fixed branch
```

## 3. Install Dependencies

```bash
# Install PyTorch with CUDA support (if not already installed)
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip3 install gdown munch tensorboard tensorboardx pyyaml scipy svgpathtools

# Verify CUDA is available
python3 -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'CUDA version: {torch.version.cuda}')"
```

## 4. Compile PointOps Module (Critical!)

This module requires CUDA and must be compiled on the GPU machine:

```bash
# Set CUDA_HOME if not already set
export CUDA_HOME=/usr/local/cuda

# Compile pointops
cd modules/pointops
python3 setup.py install
cd ../..

# Verify installation
python3 -c "import pointops_cuda; print('PointOps CUDA module loaded successfully!')"
```

## 5. Download Model Weights

```bash
# Create directory for weights
mkdir -p checkpoints

# Download the pretrained model
# Option 1: Using gdown (if you have the Google Drive link)
pip3 install gdown
gdown https://drive.google.com/uc?id=1ZeWtgZJKD_yWmFNWwBOMN9_4-x-ZXUuS
mv *.pth checkpoints/best.pth

# Option 2: Download manually and upload via RunPod file manager
```

## 6. Prepare Your Data

The model expects SVG data in JSON format:

```bash
# Example data structure
dataset/
├── train/
│   └── svg_gt/
│       ├── file1_s2.json
│       ├── file2_s2.json
│       └── ...
├── val/
│   └── svg_gt/
└── test/
    └── svg_gt/
```

If you have SVG floor plans, preprocess them:

```bash
python parse_svg_v5.py --split test --data_dir ./dataset/test/test/svg_gt/
```

## 7. Run Inference

### Option A: Test on validation set

```bash
# Single GPU
python tools/test.py \
    configs/svg/svg_pointT.yaml \
    checkpoints/best.pth \
    --out results/

# Multi-GPU (if available)
bash tools/test_dist.sh
```

### Option B: Inference on custom data

```bash
python tools/inference.py \
    configs/svg/svg_pointT.yaml \
    checkpoints/best.pth \
    --datadir path/to/your/json/files \
    --out results/
```

## 8. Verify Installation

Run the basic test to ensure everything is working:

```bash
python3 test_model_basic.py
```

You should see all tests pass with ✓ marks.

## 9. Training (Optional)

If you want to train from scratch:

```bash
# Single GPU
python tools/train.py configs/svg/svg_pointT.yaml

# Multi-GPU
bash tools/train_dist.sh
```

## Troubleshooting

### Issue: CUDA Out of Memory

```bash
# Reduce batch size in config
# Edit configs/svg/svg_pointT.yaml
# Change: batch_size: 2 -> batch_size: 1
```

### Issue: PointOps compilation fails

```bash
# Ensure CUDA_HOME is set correctly
echo $CUDA_HOME
which nvcc

# If not found, set it:
export CUDA_HOME=/usr/local/cuda
export PATH=$CUDA_HOME/bin:$PATH
export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH
```

### Issue: Model loading error

```bash
# Check PyTorch version compatibility
python3 -c "import torch; print(torch.__version__)"

# Model was saved with newer PyTorch, might need to load with weights_only=False
```

## Performance Tips

1. **Use FP16 training**: Set `fp16: True` in config for faster training
2. **Adjust batch size**: Based on your GPU memory
3. **Use gradient checkpointing**: If memory is tight
4. **Monitor GPU usage**: `watch -n 1 nvidia-smi`

## Expected Performance

With the pretrained model on test set:
- **Semantic Segmentation**: ~85% mIoU
- **Instance Segmentation**: ~75% sPQ
- **Inference Speed**: ~0.1-0.5s per floor plan (depending on complexity)

## Saving Results

Results will be saved to the specified output directory:
- Semantic predictions
- Instance masks
- Visualization outputs

## Additional Resources

- Original Paper: [SymPoint Revolutionized (arXiv:2407.01928)](https://arxiv.org/abs/2407.01928)
- Model Weights: [Google Drive Link](https://drive.google.com/file/d/1ZeWtgZJKD_yWmFNWwBOMN9_4-x-ZXUuS/view?usp=drive_link)
- Issues: Report problems on the GitHub repository

---

**Note**: This setup assumes you're working with SVG floor plan data. If you have raster images (PNG/JPG), you'll need to vectorize them to SVG format first.
