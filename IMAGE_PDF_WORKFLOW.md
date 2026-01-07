# Working with Images and PDFs in SymPointV2

## ⚠️ Important: SymPointV2 Requirements

**SymPointV2 does NOT work directly with images or PDFs.**

It requires:
- ✅ **SVG files** (vector graphics)
- ✅ Converted to **JSON format** with point cloud data

## 📊 Format Comparison

| Format | Works with SymPointV2? | Why? |
|--------|----------------------|------|
| **SVG** | ✅ Yes (after JSON conversion) | Vector format with paths/shapes |
| **PNG/JPG** | ❌ No | Raster format (pixels) |
| **PDF** | ❌ No (needs conversion) | Can contain vectors but needs extraction |
| **DWG/DXF** | ⚠️ Possible (convert to SVG first) | CAD format |
| **TIFF** | ❌ No | Raster format |

---

## 🔄 Workflow: Image → SymPointV2

### Method 1: Using Potrace (Simple, Fast)

```bash
# Install dependencies
apt-get install potrace imagemagick

# Convert your floor plan
python convert_to_svg.py floorplan.png --method potrace

# Parse to JSON
python parse_svg_v5.py --input floorplan.svg --output floorplan_s2.json

# Run SymPointV2
python tools/inference.py configs/svg/svg_pointT.yaml checkpoints/best.pth \
    --datadir . --out results/
```

### Method 2: Using Inkscape (Better Quality)

```bash
# Install Inkscape
apt-get install inkscape

# Convert with better tracing
python convert_to_svg.py floorplan.png --method inkscape

# Continue with parsing...
```

### Method 3: PDF Floor Plans

```bash
# Install pdf2svg
apt-get install pdf2svg

# Convert PDF (page 1)
python convert_to_svg.py floorplan.pdf --method pdf2svg --page 1

# If PDF has multiple pages
for i in {1..5}; do
    python convert_to_svg.py floorplan.pdf --method pdf2svg --page $i -o page_$i.svg
done
```

---

## 🎯 Alternative: Models That Work Directly with Images

If you want to skip SVG conversion, use these models instead:

### 1. **CubiCasa5k** (Works with Images!)
```bash
# Directly process PNG/JPG floor plans
git clone https://github.com/CubiCasa/CubiCasa5k
cd CubiCasa5k
python predict.py --input floorplan.png
```

**Output**: Room segmentation masks

### 2. **YOLO for Floor Plans** (Fast Image Detection)
```bash
# Train or use pretrained YOLO
from ultralytics import YOLO
model = YOLO('yolov8n.pt')
results = model.predict('floorplan.jpg')
```

**Output**: Bounding boxes for symbols

### 3. **Mask R-CNN / Detectron2** (Image-based Instance Segmentation)
```bash
# Works directly on images
import detectron2
# ... configure model ...
outputs = predictor(image)
```

**Output**: Instance masks

---

## 🔍 Quality Considerations

### Image → SVG Conversion Issues:

**Problems:**
- ❌ Loss of precision in vectorization
- ❌ Text becomes paths (not readable)
- ❌ Complex details may be simplified
- ❌ Dimension annotations lost

**Best Input for Conversion:**
- ✅ High resolution (300+ DPI)
- ✅ Clean, binary (black & white)
- ✅ No watermarks or backgrounds
- ✅ Clear lines without compression artifacts

### When NOT to Use SymPointV2:

If your floor plans are:
1. **Scanned paper drawings** → Use image-based models (CubiCasa5k)
2. **Low-quality images** → Preprocess first or use robust image models
3. **Photos of plans** → Rectify and enhance, then use image models
4. **PDFs with embedded text** → Extract text separately, use hybrid approach

---

## 📝 Complete Workflow Example

### Starting with a PNG Floor Plan:

```bash
# 1. Prepare your image
convert floorplan.png -threshold 50% -resize 200% floorplan_clean.png

# 2. Convert to SVG
python convert_to_svg.py floorplan_clean.png -o floorplan.svg

# 3. Check SVG quality (open in browser or Inkscape)
firefox floorplan.svg  # or
inkscape floorplan.svg

# 4. If quality is good, parse to JSON
python parse_svg_v5.py --input floorplan.svg

# 5. Run SymPointV2
python tools/inference.py \
    configs/svg/svg_pointT.yaml \
    checkpoints/best.pth \
    --datadir . \
    --out results/
```

---

## 🎨 What About Your ArchiCAD Question?

**ArchiCAD** is CAD software, not a model. But:

### ArchiCAD → SymPointV2:
```bash
# In ArchiCAD:
# 1. File → Save As → SVG
# 2. Export with these settings:
#    - Include: All visible elements
#    - Resolution: Vector
#    - No rasterization

# 3. Use the SVG with SymPointV2
python parse_svg_v5.py --input archicad_export.svg
```

### ArchiCAD → Direct Analysis:
```bash
# Export as image from ArchiCAD
# Then use CubiCasa5k or other image-based models
```

---

## 💡 Recommended Approach

**For Best Results:**

1. **If you have native CAD files (DWG, DXF, ArchiCAD):**
   - Export as SVG directly from CAD software
   - Use SymPointV2 ✅

2. **If you have only images/PDFs:**
   - Option A: Convert to SVG (quality loss) → SymPointV2
   - Option B: Use image-based models (CubiCasa5k, YOLO) ✅ Recommended

3. **For production system:**
   - Accept both formats
   - Route SVG → SymPointV2
   - Route Images → CubiCasa5k or custom image model

---

## 🔧 Troubleshooting

**SVG conversion produces poor results?**
```bash
# Try different threshold
convert floorplan.png -threshold 30% cleaned.png
python convert_to_svg.py cleaned.png

# Or use Inkscape's advanced tracing
inkscape --verb=EditSelectAll \
         --verb=SelectionTrace \
         --verb=FileSave \
         --verb=FileQuit \
         floorplan.png
```

**Parse SVG fails?**
```bash
# Check SVG structure
grep -c "<path" floorplan.svg
grep -c "<line" floorplan.svg

# Simplify SVG
inkscape --export-plain-svg=simple.svg floorplan.svg
```

---

## Summary

| Starting Format | Best Approach | Model to Use |
|----------------|---------------|--------------|
| **SVG** (native) | Direct use | SymPointV2 ✅ |
| **CAD** (DWG/DXF) | Export to SVG | SymPointV2 ✅ |
| **PDF** (vector) | Extract to SVG | SymPointV2 ⚠️ |
| **Image** (PNG/JPG) | Use as-is | CubiCasa5k ✅ |
| **Scanned** plans | Preprocess | Image model ✅ |

**Bottom Line**: SymPointV2 is excellent for **vector-based** floor plans. For **raster images**, consider image-based alternatives.
