#!/usr/bin/env python3
"""
Image/PDF to SVG Converter for SymPointV2
This script helps convert raster floor plans to vector format
"""

import os
import subprocess
from pathlib import Path

def convert_image_to_svg_potrace(image_path, output_svg):
    """
    Convert raster image to SVG using Potrace

    Installation:
        apt-get install potrace imagemagick
    """
    print(f"Converting {image_path} to SVG...")

    # Convert to PBM first (Potrace requirement)
    pbm_path = output_svg.replace('.svg', '.pbm')

    # Convert to black & white PBM
    cmd1 = f"convert {image_path} -threshold 50% -negate {pbm_path}"
    subprocess.run(cmd1, shell=True, check=True)

    # Convert PBM to SVG using Potrace
    cmd2 = f"potrace {pbm_path} -s -o {output_svg}"
    subprocess.run(cmd2, shell=True, check=True)

    # Cleanup
    os.remove(pbm_path)
    print(f"✓ SVG created: {output_svg}")

def convert_pdf_to_svg(pdf_path, output_svg, page=1):
    """
    Convert PDF to SVG

    Installation:
        apt-get install pdf2svg
    """
    print(f"Converting PDF page {page} to SVG...")
    cmd = f"pdf2svg {pdf_path} {output_svg} {page}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"✓ SVG created: {output_svg}")

def convert_image_to_svg_inkscape(image_path, output_svg):
    """
    Convert using Inkscape (better quality)

    Installation:
        apt-get install inkscape
    """
    print(f"Converting {image_path} to SVG with Inkscape...")
    cmd = f"inkscape --trace-to={output_svg} {image_path}"
    subprocess.run(cmd, shell=True, check=True)
    print(f"✓ SVG created: {output_svg}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert images/PDFs to SVG for SymPointV2')
    parser.add_argument('input', help='Input image or PDF file')
    parser.add_argument('--output', '-o', help='Output SVG file')
    parser.add_argument('--method', choices=['potrace', 'inkscape', 'pdf2svg'],
                       default='potrace', help='Conversion method')
    parser.add_argument('--page', type=int, default=1, help='PDF page number')

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_svg = args.output
    else:
        output_svg = Path(args.input).stem + '.svg'

    # Convert based on method
    input_ext = Path(args.input).suffix.lower()

    if input_ext == '.pdf' and args.method == 'pdf2svg':
        convert_pdf_to_svg(args.input, output_svg, args.page)
    elif args.method == 'potrace':
        convert_image_to_svg_potrace(args.input, output_svg)
    elif args.method == 'inkscape':
        convert_image_to_svg_inkscape(args.input, output_svg)
    else:
        print(f"Unsupported combination: {input_ext} with {args.method}")
        return

    print("\n" + "="*60)
    print("Next steps:")
    print(f"1. Parse SVG: python parse_svg_v5.py --input {output_svg}")
    print("2. Run inference with SymPointV2")
    print("="*60)

if __name__ == '__main__':
    main()
