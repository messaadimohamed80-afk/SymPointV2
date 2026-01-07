#!/bin/bash
# SymPointV2 RunPod Setup Script
# This script automates the setup process on RunPod

set -e  # Exit on error

echo "=========================================="
echo "SymPointV2 RunPod Setup"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running on GPU instance
if ! command -v nvidia-smi &> /dev/null; then
    echo -e "${RED}Error: nvidia-smi not found. Please run on a GPU instance.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ GPU detected${NC}"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

# Check CUDA
if [ -z "$CUDA_HOME" ]; then
    echo -e "${YELLOW}Setting CUDA_HOME...${NC}"
    export CUDA_HOME=/usr/local/cuda
    export PATH=$CUDA_HOME/bin:$PATH
    export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH

    # Add to bashrc for persistence
    echo 'export CUDA_HOME=/usr/local/cuda' >> ~/.bashrc
    echo 'export PATH=$CUDA_HOME/bin:$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=$CUDA_HOME/lib64:$LD_LIBRARY_PATH' >> ~/.bashrc
fi

echo -e "${GREEN}✓ CUDA_HOME set to: $CUDA_HOME${NC}"

# Install system dependencies
echo -e "${YELLOW}Installing system dependencies...${NC}"
apt-get update -qq
apt-get install -y -qq git wget build-essential > /dev/null 2>&1
echo -e "${GREEN}✓ System dependencies installed${NC}"

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"

# Check PyTorch
if python3 -c "import torch" 2>/dev/null; then
    TORCH_VERSION=$(python3 -c "import torch; print(torch.__version__)")
    echo -e "${GREEN}✓ PyTorch $TORCH_VERSION already installed${NC}"
else
    echo -e "${YELLOW}Installing PyTorch with CUDA support...${NC}"
    pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118 -q
    echo -e "${GREEN}✓ PyTorch installed${NC}"
fi

# Install other dependencies
echo -e "${YELLOW}Installing other dependencies...${NC}"
pip3 install -q gdown munch tensorboard tensorboardx pyyaml scipy svgpathtools
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Verify CUDA availability
echo -e "${YELLOW}Verifying CUDA availability...${NC}"
python3 << EOF
import torch
assert torch.cuda.is_available(), "CUDA is not available!"
print(f"✓ CUDA available: {torch.cuda.get_device_name(0)}")
print(f"✓ PyTorch version: {torch.__version__}")
print(f"✓ CUDA version: {torch.version.cuda}")
EOF

# Compile PointOps
echo -e "${YELLOW}Compiling PointOps CUDA module...${NC}"
cd modules/pointops
python3 setup.py install > /dev/null 2>&1
cd ../..
echo -e "${GREEN}✓ PointOps compiled successfully${NC}"

# Verify PointOps
python3 << EOF
try:
    import pointops_cuda
    print("✓ PointOps CUDA module loaded successfully!")
except ImportError:
    print("⚠ Warning: PointOps CUDA module not found, but model may still work")
EOF

# Run basic model test
echo -e "${YELLOW}Running model structure test...${NC}"
python3 test_model_basic.py

# Create necessary directories
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p checkpoints
mkdir -p results
mkdir -p dataset/test/test/svg_gt
mkdir -p dataset/train/train/svg_gt
mkdir -p dataset/val/val/svg_gt
echo -e "${GREEN}✓ Directories created${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Download model weights:"
echo "   gdown https://drive.google.com/uc?id=1ZeWtgZJKD_yWmFNWwBOMN9_4-x-ZXUuS"
echo "   mv *.pth checkpoints/best.pth"
echo ""
echo "2. Prepare your data in dataset/ directory"
echo ""
echo "3. Run inference:"
echo "   python tools/inference.py configs/svg/svg_pointT.yaml checkpoints/best.pth --datadir dataset/test/test/svg_gt"
echo ""
echo "4. Or run test on validation set:"
echo "   python tools/test.py configs/svg/svg_pointT.yaml checkpoints/best.pth"
echo ""
echo "For more details, see RUNPOD_SETUP.md"
