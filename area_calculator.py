#!/usr/bin/env python3
"""
Floor Plan Area Calculator
Combines multiple approaches for accurate area calculation
"""

import cv2
import numpy as np
from shapely.geometry import Polygon
import pytesseract
import re

class FloorPlanAreaCalculator:
    """
    Calculate room areas from floor plans using various methods
    """

    def __init__(self):
        self.scale_factor = None  # pixels per meter

    def detect_scale(self, image):
        """
        Detect scale from floor plan using OCR
        Looks for patterns like "1:100", "1cm=1m", "Scale 1/100"
        """
        # OCR to find scale text
        text = pytesseract.image_to_string(image)

        # Pattern matching for scale
        patterns = [
            r'1:(\d+)',           # 1:100
            r'1/(\d+)',           # 1/100
            r'Scale.*?1:(\d+)',   # Scale 1:100
            r'(\d+)cm\s*=\s*(\d+)m'  # 1cm = 1m
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                scale_ratio = int(match.group(1))
                # Assuming 96 DPI standard
                self.scale_factor = 96 / (scale_ratio / 100)
                print(f"✓ Scale detected: 1:{scale_ratio}")
                return self.scale_factor

        print("⚠ Scale not found, using default DPI")
        return None

    def segment_rooms_opencv(self, image):
        """
        Segment rooms using classical computer vision
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Threshold to get room regions
        _, binary = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)

        rooms = []
        for cnt in contours:
            area_pixels = cv2.contourArea(cnt)
            if area_pixels > 1000:  # Filter small noise
                rooms.append({
                    'contour': cnt,
                    'area_pixels': area_pixels
                })

        return rooms

    def calculate_area(self, contour, scale_factor=None):
        """
        Calculate area from contour
        """
        area_pixels = cv2.contourArea(contour)

        if scale_factor:
            # Convert to square meters
            area_sqm = area_pixels / (scale_factor ** 2)
            return area_pixels, area_sqm

        return area_pixels, None

    def extract_room_labels_ocr(self, image, contours):
        """
        Extract room labels using OCR
        """
        results = []

        for i, cnt in enumerate(contours):
            # Get bounding box
            x, y, w, h = cv2.boundingRect(cnt)

            # Extract ROI
            roi = image[y:y+h, x:x+w]

            # OCR on ROI
            text = pytesseract.image_to_string(roi, config='--psm 7')
            text = text.strip()

            # Extract dimensions if present (e.g., "3.5m x 4.2m")
            dim_pattern = r'(\d+\.?\d*)\s*[mx]\s*(\d+\.?\d*)'
            match = re.search(dim_pattern, text, re.IGNORECASE)

            room_info = {
                'id': i,
                'label': text,
                'bounds': (x, y, w, h)
            }

            if match:
                width = float(match.group(1))
                height = float(match.group(2))
                room_info['dimensions'] = (width, height)
                room_info['area_from_text'] = width * height

            results.append(room_info)

        return results

    def process_floor_plan(self, image_path, output_path=None):
        """
        Complete pipeline: detect scale, segment rooms, calculate areas
        """
        print("="*60)
        print("Floor Plan Area Calculator")
        print("="*60)

        # Load image
        image = cv2.imread(image_path)
        print(f"✓ Loaded image: {image.shape}")

        # Detect scale
        scale = self.detect_scale(image)

        # Segment rooms
        print("\n[1] Segmenting rooms...")
        rooms = self.segment_rooms_opencv(image)
        print(f"✓ Found {len(rooms)} rooms")

        # Extract labels
        print("\n[2] Extracting room labels...")
        contours = [r['contour'] for r in rooms]
        labels = self.extract_room_labels_ocr(image, contours)

        # Calculate areas
        print("\n[3] Calculating areas...")
        total_area = 0
        results = []

        for i, room in enumerate(rooms):
            area_px, area_sqm = self.calculate_area(room['contour'], scale)

            label = labels[i]['label'] if i < len(labels) else f"Room {i+1}"

            result = {
                'name': label,
                'area_pixels': area_px,
                'area_sqm': area_sqm,
                'area_sqft': area_sqm * 10.764 if area_sqm else None
            }

            results.append(result)

            if area_sqm:
                total_area += area_sqm
                print(f"  {label}: {area_sqm:.2f} m² ({area_sqm*10.764:.2f} ft²)")
            else:
                print(f"  {label}: {area_px:.0f} pixels (scale unknown)")

        if total_area > 0:
            print(f"\n✓ Total Area: {total_area:.2f} m² ({total_area*10.764:.2f} ft²)")

        # Visualize
        if output_path:
            self.visualize_results(image, rooms, labels, output_path)

        return results

    def visualize_results(self, image, rooms, labels, output_path):
        """
        Draw room boundaries and labels on image
        """
        output = image.copy()

        for i, room in enumerate(rooms):
            # Draw contour
            cv2.drawContours(output, [room['contour']], -1, (0, 255, 0), 2)

            # Add label
            if i < len(labels):
                x, y, w, h = labels[i]['bounds']
                cv2.putText(output, f"{i+1}", (x+10, y+30),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imwrite(output_path, output)
        print(f"\n✓ Visualization saved to: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Calculate room areas from floor plan')
    parser.add_argument('image', help='Input floor plan image')
    parser.add_argument('--output', '-o', help='Output visualization image')
    parser.add_argument('--json', help='Export results to JSON file')

    args = parser.parse_args()

    calculator = FloorPlanAreaCalculator()
    results = calculator.process_floor_plan(args.image, args.output)

    if args.json:
        import json
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"✓ Results exported to: {args.json}")


if __name__ == '__main__':
    main()
