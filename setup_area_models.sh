#!/bin/bash
# Setup script for area calculation models from GitHub

set -e

echo "=========================================="
echo "Area Calculation Models Setup"
echo "=========================================="

# Create models directory
mkdir -p ../area_models
cd ../area_models

# 1. CubiCasa5k
echo -e "\n[1/3] Cloning CubiCasa5k..."
if [ ! -d "CubiCasa5k" ]; then
    git clone https://github.com/CubiCasa/CubiCasa5k.git
    cd CubiCasa5k
    pip install -r requirements.txt
    echo "✓ CubiCasa5k installed"
    cd ..
else
    echo "✓ CubiCasa5k already exists"
fi

# 2. Segment Anything (SAM)
echo -e "\n[2/3] Installing Segment Anything..."
pip install -q git+https://github.com/facebookresearch/segment-anything.git
pip install -q opencv-python

# Download SAM checkpoint
if [ ! -f "sam_vit_h_4b8939.pth" ]; then
    echo "Downloading SAM checkpoint (2.4GB)..."
    wget -q https://dl.fbaipublicfiles.com/segment_anything/sam_vit_h_4b8939.pth
    echo "✓ SAM checkpoint downloaded"
else
    echo "✓ SAM checkpoint already exists"
fi

# 3. DeepFloorplan
echo -e "\n[3/3] Cloning DeepFloorplan..."
if [ ! -d "DeepFloorplan" ]; then
    git clone https://github.com/zlzeng/DeepFloorplan.git
    cd DeepFloorplan
    pip install -r requirements.txt 2>/dev/null || echo "⚠ Some dependencies may need manual install"
    echo "✓ DeepFloorplan installed"
    cd ..
else
    echo "✓ DeepFloorplan already exists"
fi

echo -e "\n=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Models installed in: $(pwd)"
echo ""
echo "Quick start examples:"
echo ""
echo "1. CubiCasa5k:"
echo "   cd CubiCasa5k"
echo "   python floortrans/loaders/house.py --image ../floorplan.png"
echo ""
echo "2. SAM:"
echo "   python ../SymPointV2/examples/sam_area.py --image floorplan.png"
echo ""
echo "3. DeepFloorplan:"
echo "   cd DeepFloorplan"
echo "   python main.py --image ../floorplan.png"
echo ""
