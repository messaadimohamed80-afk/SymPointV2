#!/usr/bin/env python3
"""
Example: Using SAM (Segment Anything) for area calculation
GitHub: https://github.com/facebookresearch/segment-anything
"""

import cv2
import numpy as np
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True, help='Floor plan image')
    parser.add_argument('--checkpoint', default='sam_vit_h_4b8939.pth')
    parser.add_argument('--scale', type=float, default=0.01,
                       help='Scale factor: pixels to meters (default: 0.01)')
    args = parser.parse_args()

    try:
        from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
    except ImportError:
        print("Error: segment-anything not installed")
        print("Install with: pip install git+https://github.com/facebookresearch/segment-anything.git")
        return

    print("="*60)
    print("SAM Area Calculator")
    print("="*60)

    # Load image
    print(f"\n[1] Loading image: {args.image}")
    image = cv2.imread(args.image)
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    print(f"✓ Image shape: {image.shape}")

    # Load SAM model
    print(f"\n[2] Loading SAM model...")
    sam = sam_model_registry["vit_h"](checkpoint=args.checkpoint)
    mask_generator = SamAutomaticMaskGenerator(sam)
    print("✓ Model loaded")

    # Generate masks
    print(f"\n[3] Generating room masks...")
    masks = mask_generator.generate(image_rgb)
    print(f"✓ Found {len(masks)} regions")

    # Calculate areas
    print(f"\n[4] Calculating areas...")
    total_area = 0

    for i, mask in enumerate(masks):
        area_pixels = mask['area']
        area_sqm = area_pixels * (args.scale ** 2)

        if area_sqm > 1.0:  # Filter small regions
            print(f"  Region {i+1}: {area_sqm:.2f} m² ({area_sqm*10.764:.2f} ft²)")
            total_area += area_sqm

    print(f"\n✓ Total area: {total_area:.2f} m² ({total_area*10.764:.2f} ft²)")

    # Visualize
    output_path = args.image.replace('.', '_annotated.')
    visualize_masks(image, masks, output_path)
    print(f"\n✓ Visualization saved: {output_path}")

def visualize_masks(image, masks, output_path):
    """Draw masks on image"""
    output = image.copy()

    for i, mask in enumerate(masks):
        # Create colored mask
        color = np.random.randint(0, 255, 3).tolist()
        mask_bool = mask['segmentation']
        output[mask_bool] = output[mask_bool] * 0.5 + np.array(color) * 0.5

    cv2.imwrite(output_path, output)

if __name__ == '__main__':
    main()
