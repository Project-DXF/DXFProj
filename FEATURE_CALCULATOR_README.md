# Advanced Feature Calculator for DXF Profile Analysis

This document describes the new advanced feature calculator that implements all the calculations mentioned in the `calculations.txt` file.

## Overview

The `AdvancedFeatureCalculator` class provides comprehensive analysis of DXF profiles, calculating over 40 different features and parameters that are essential for profile analysis and manufacturing optimization.

## Features Calculated

### 1. Basic Profile Properties
- **Number of loops**: Total count of closed paths in the profile
- **Profile type**: Classification as solid (1 loop) or hollow (multiple loops)
- **Profile area**: Net area (outer area minus inner areas)
- **Hollow ratio**: Ratio of inner area to total area
- **Perimeter**: Outer and total perimeter measurements
- **Bounding box**: Width, height, and area of the bounding rectangle
- **Number of mandrels**: Count of internal loops

### 2. Extrusion Ratios
- **ER for P22, P40, P55**: Extrusion ratios for different container sizes
- **Optimal holes**: Calculated number of holes to maintain ER between 40-60

### 3. Geometric Properties
- **Compactness**: C = P²/(4πA) - measure of shape regularity
- **Solidity**: Area/Convex Hull Area - measure of shape concavity
- **Aspect ratio**: Height to width ratio
- **Circumscribing circle diameter (CCD)**: Diameter of smallest circle containing the shape
- **Min/Max radius**: Distance from centroid to closest/farthest points

### 4. Wall Thickness Analysis
- **Max/Min/Average wall thickness**: Thickness measurements for hollow profiles
- **Wall thickness variability**: Standard deviation of thickness measurements

### 5. Moments of Inertia
- **Ix, Iy**: Second moments of area about x and y axes
- **Polar moment of inertia**: Ip = Ix + Iy
- **Product of inertia**: Ixy

### 6. Fourier Descriptors
- **First 10 normalized Fourier descriptors**: Shape signature for comparison

### 7. Distance and Similarity Metrics
- **Euclidean distance**: Distance from reference shape
- **Cosine similarity**: Similarity measure for shape comparison

### 8. Mass Vectors by Quadrant
- **Distribution of mass**: Percentage of shape in each quadrant

### 9. Complexity Factors
- **C1**: Ps/As (Perimeter to area ratio)
- **C2**: Ps/Ws (Perimeter to weight ratio)
- **C3**: CCD/Tm (Form factor)
- **C4**: Groover's complexity definition
- **C5**: Qamar's complexity definition

### 10. Mandrel Analysis
For each internal loop (up to 4):
- Area, perimeter, compactness, solidity
- Aspect ratio
- Distance from center of gravity to centroid
- Thickness standard deviations in all directions

## UI Improvements

### New Tree-Based Parameter Display
The old disabled text boxes have been replaced with a modern tree widget that:
- **Organizes parameters by category** for better readability
- **Shows units** for each measurement
- **Supports hierarchical display** with expandable categories
- **Provides proper formatting** for different value types
- **Includes search and filtering capabilities**

### Enhanced User Experience
- **Real-time calculation** when the Process button is clicked
- **Progress indication** during complex calculations
- **Error handling** with informative messages
- **Theme-aware styling** that adapts to light/dark modes

## Usage

### In the Application
1. Load a DXF file using the "Upload DXF" button
2. Click the "Process" button to calculate all features
3. View results in the organized tree structure
4. Expand/collapse categories as needed
5. Save the profile with all calculated parameters

### Programmatic Usage
```python
from src.dxf_analyzer.processing.profile_management.feature_calculator import AdvancedFeatureCalculator
import ezdxf

# Load DXF document
doc = ezdxf.readfile('profile.dxf')

# Initialize calculator
calculator = AdvancedFeatureCalculator()
calculator.set_document(doc)

# Calculate all features
features = calculator.calculate_all_features()

# Access specific features
print(f"Profile area: {features['profile_area']}")
print(f"Complexity C1: {features['complexity_factor_c1']}")
```

## Dependencies

The feature calculator requires the following packages:
- `ezdxf>=1.4.1` - DXF file handling
- `numpy>=2.2.5` - Numerical computations
- `scipy>=1.15.3` - Scientific computing

Optional dependencies for enhanced functionality:
- `opencv-python>=4.5.0` - For advanced image processing features
- `shapely>=2.0.0` - For enhanced geometric operations

## Testing

Run the test script to verify the implementation:
```bash
python test_feature_calculator.py
```

This will create a simple test profile and calculate all features to ensure the system is working correctly.

## Technical Notes

### Loop Detection
The current implementation uses a simplified loop detection algorithm. For production use, consider implementing more sophisticated algorithms for:
- Complex nested loops
- Self-intersecting paths
- Broken or incomplete paths

### Performance Considerations
- Large DXF files may take longer to process
- Complex shapes with many vertices will increase calculation time
- Consider implementing caching for repeated calculations

### Accuracy
- Calculations use double precision floating-point arithmetic
- Polygon approximations are used for complex curves
- Results are formatted to appropriate precision levels

## Future Enhancements

1. **Advanced Loop Detection**: Implement topology-based loop detection
2. **Parallel Processing**: Use multiprocessing for large files
3. **Caching**: Store calculated results to avoid recomputation
4. **Export Options**: Export results to CSV, JSON, or PDF
5. **Visualization**: Add graphical representation of calculated features
6. **Comparison Tools**: Compare multiple profiles side-by-side

## Support

For issues or questions regarding the feature calculator:
1. Check the test script output for basic functionality
2. Verify all dependencies are installed correctly
3. Ensure DXF files are valid and contain closed paths
4. Review the console output for detailed error messages 