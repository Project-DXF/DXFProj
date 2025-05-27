#!/usr/bin/env python3
"""
Test script for the Advanced Feature Calculator

This script tests the feature calculator with a simple DXF file
to verify that all calculations are working correctly.
"""

import sys
import os
import math

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    import ezdxf
    from src.dxf_analyzer.processing.profile_management.feature_calculator import AdvancedFeatureCalculator
    
    def create_test_dxf():
        """Create a simple test DXF file with a rectangle and a circle."""
        doc = ezdxf.new('R2010')
        msp = doc.modelspace()
        
        # Create a rectangle (outer loop)
        rect_points = [(0, 0), (100, 0), (100, 50), (0, 50), (0, 0)]
        msp.add_lwpolyline(rect_points, close=True)
        
        # Create a circle inside (inner loop)
        msp.add_circle(center=(50, 25), radius=10)
        
        return doc
    
    def test_feature_calculator():
        """Test the feature calculator with a simple DXF."""
        print("Testing Advanced Feature Calculator...")
        
        # Create test DXF
        doc = create_test_dxf()
        
        # Initialize calculator
        calculator = AdvancedFeatureCalculator()
        calculator.set_document(doc)
        
        # Calculate features
        features = calculator.calculate_all_features()
        
        print(f"\nCalculated {len(features)} features:")
        print("-" * 50)
        
        # Print basic properties
        if 'number_of_loops' in features:
            print(f"Number of loops: {features['number_of_loops']}")
        if 'profile_type' in features:
            print(f"Profile type: {features['profile_type']}")
        if 'profile_area' in features:
            print(f"Profile area: {features['profile_area']:.2f} mm²")
        if 'outer_perimeter' in features:
            print(f"Outer perimeter: {features['outer_perimeter']:.2f} mm")
        
        # Print dimensions
        if 'bounding_box_width' in features:
            print(f"Width: {features['bounding_box_width']:.2f} mm")
        if 'bounding_box_height' in features:
            print(f"Height: {features['bounding_box_height']:.2f} mm")
        if 'aspect_ratio' in features:
            print(f"Aspect ratio: {features['aspect_ratio']:.2f}")
        
        # Print extrusion ratios
        if 'er_p22' in features:
            print(f"ER P22: {features['er_p22']:.2f}")
        if 'holes_p22' in features:
            print(f"Optimal holes P22: {features['holes_p22']}")
        
        # Print complexity factors
        if 'complexity_factor_c1' in features:
            print(f"Complexity C1: {features['complexity_factor_c1']:.4f}")
        
        print("\nTest completed successfully!")
        return True
    
    if __name__ == "__main__":
        try:
            test_feature_calculator()
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

except ImportError as e:
    print(f"Import error: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install ezdxf numpy scipy")
    sys.exit(1) 