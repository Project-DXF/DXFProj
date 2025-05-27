"""
Advanced Feature Calculator for DXF Profile Analysis

Implements all the calculations mentioned in calculations.txt including:
- Basic profile properties (area, perimeter, loops)
- Extrusion ratios for different containers
- Geometric properties (compactness, solidity, aspect ratio)
- Wall thickness analysis
- Moments of inertia
- Fourier descriptors
- Complexity factors
- Mandrel analysis
"""

import math
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import ezdxf
from scipy.spatial.distance import euclidean, cosine
from scipy.fft import fft
import pandas as pd
from datetime import datetime
import os


class AdvancedFeatureCalculator:
    """Calculates advanced features for DXF profile analysis."""
    
    def __init__(self):
        """Initialize the feature calculator."""
        self.current_doc = None
        self.outer_loop = None
        self.inner_loops = []
        self.all_loops = []
        
    def set_document(self, doc: ezdxf.document.Drawing):
        """Set the DXF document to analyze."""
        self.current_doc = doc
        self._detect_loops()
    
    def _detect_loops(self):
        """Detect outer and inner loops in the DXF."""
        if not self.current_doc:
            return
        
        # This is a simplified loop detection - in practice, you'd use more sophisticated algorithms
        msp = self.current_doc.modelspace()
        all_entities = list(msp)
        
        # Print entity type distribution for debugging
        entity_types = {}
        for e in all_entities:
            entity_type = e.dxftype()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        print(f"Entity type distribution: {entity_types}")
        
        # Filter entities that can form loops
        entities = [e for e in all_entities if e.dxftype() in ['LINE', 'ARC', 'CIRCLE', 'POLYLINE', 'LWPOLYLINE', 'ELLIPSE', 'SPLINE']]
        
        print(f"Found {len(entities)} entities for loop detection out of {len(all_entities)} total")
        
        # Extract closed paths from entities
        self.all_loops = self._extract_closed_paths(entities)
        
        print(f"Extracted {len(self.all_loops)} loops")
        
        if self.all_loops:
            # Sort by area - largest is outer loop
            self.all_loops.sort(key=lambda loop: self._calculate_polygon_area(loop), reverse=True)
            self.outer_loop = self.all_loops[0] if self.all_loops else None
            self.inner_loops = self.all_loops[1:] if len(self.all_loops) > 1 else []
            print(f"Outer loop has {len(self.outer_loop)} points, {len(self.inner_loops)} inner loops")
        else:
            print("No loops detected, will try fallback method")
    
    def _extract_closed_paths(self, entities) -> List[List[Tuple[float, float]]]:
        """Extract closed paths from entities."""
        # Simplified implementation - in practice, you'd need more sophisticated path detection
        paths = []
        
        for entity in entities:
            try:
                if entity.dxftype() == 'CIRCLE':
                    # Create circle as polygon
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    points = []
                    for i in range(36):  # 36 points for circle
                        angle = i * 2 * math.pi / 36
                        x = center.x + radius * math.cos(angle)
                        y = center.y + radius * math.sin(angle)
                        points.append((x, y))
                    paths.append(points)
                    print(f"Added circle with {len(points)} points")
                
                elif entity.dxftype() == 'LWPOLYLINE':
                    # For LWPOLYLINE, try multiple methods
                    points = []
                    
                    # Method 1: Try iterating over entity
                    try:
                        for point in entity:
                            if hasattr(point, '__len__') and len(point) >= 2:
                                points.append((float(point[0]), float(point[1])))
                    except:
                        pass
                    
                    # Method 2: Try get_points()
                    if not points:
                        try:
                            for p in entity.get_points():
                                points.append((float(p[0]), float(p[1])))
                        except:
                            pass
                    
                    # Method 3: Try accessing vertices directly
                    if not points:
                        try:
                            if hasattr(entity, 'vertices'):
                                for vertex in entity.vertices:
                                    if hasattr(vertex, 'location'):
                                        points.append((float(vertex.location.x), float(vertex.location.y)))
                                    elif hasattr(vertex, '__len__') and len(vertex) >= 2:
                                        points.append((float(vertex[0]), float(vertex[1])))
                        except:
                            pass
                    
                    if len(points) > 2:
                        paths.append(points)
                        print(f"Added LWPOLYLINE with {len(points)} points")
                
                elif entity.dxftype() == 'POLYLINE':
                    # For POLYLINE, get vertices using the vertices() method
                    points = []
                    try:
                        for vertex in entity.vertices():
                            points.append((float(vertex.dxf.location.x), float(vertex.dxf.location.y)))
                    except:
                        pass
                    
                    if len(points) > 2:
                        paths.append(points)
                        print(f"Added POLYLINE with {len(points)} points")
                
                elif entity.dxftype() == 'ELLIPSE':
                    # Create ellipse as polygon
                    try:
                        center = entity.dxf.center
                        major_axis = entity.dxf.major_axis
                        ratio = entity.dxf.ratio
                        
                        points = []
                        for i in range(36):
                            angle = i * 2 * math.pi / 36
                            # Simplified ellipse approximation
                            x = center.x + major_axis.x * math.cos(angle)
                            y = center.y + major_axis.y * math.sin(angle) * ratio
                            points.append((x, y))
                        
                        paths.append(points)
                        print(f"Added ELLIPSE with {len(points)} points")
                    except:
                        pass
                
                elif entity.dxftype() == 'SPLINE':
                    # For splines, try to get control points or sample points
                    try:
                        points = []
                        if hasattr(entity, 'control_points'):
                            for cp in entity.control_points:
                                points.append((float(cp.x), float(cp.y)))
                        
                        if len(points) > 2:
                            paths.append(points)
                            print(f"Added SPLINE with {len(points)} points")
                    except:
                        pass
                
                elif entity.dxftype() == 'LINE':
                    # For individual lines, we'll collect them and try to connect later
                    try:
                        start = entity.dxf.start
                        end = entity.dxf.end
                        # Store as a 2-point path for now
                        points = [(float(start.x), float(start.y)), (float(end.x), float(end.y))]
                        # Only add if it's a significant line (not a tiny segment)
                        length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                        if length > 0.001:  # Minimum length threshold
                            paths.append(points)
                            print(f"Added LINE with length {length:.3f}")
                    except Exception as e:
                        print(f"Error processing LINE: {e}")
                
                elif entity.dxftype() == 'ARC':
                    # Convert arc to polyline
                    try:
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        start_angle = math.radians(entity.dxf.start_angle)
                        end_angle = math.radians(entity.dxf.end_angle)
                        
                        # Normalize angles
                        if end_angle < start_angle:
                            end_angle += 2 * math.pi
                        
                        # Create points along the arc
                        points = []
                        num_segments = max(8, int((end_angle - start_angle) * 18 / math.pi))  # At least 8 segments
                        
                        for i in range(num_segments + 1):
                            angle = start_angle + (end_angle - start_angle) * i / num_segments
                            x = center.x + radius * math.cos(angle)
                            y = center.y + radius * math.sin(angle)
                            points.append((float(x), float(y)))
                        
                        if len(points) > 1:
                            paths.append(points)
                            print(f"Added ARC with {len(points)} points, radius {radius:.3f}")
                    except Exception as e:
                        print(f"Error processing ARC: {e}")
                
            except Exception as e:
                print(f"Error processing entity {entity.dxftype()}: {e}")
                continue
        
        print(f"Total paths extracted: {len(paths)}")
        
        # Try to connect individual segments into closed loops
        if paths:
            connected_loops = self._connect_segments_to_loops(paths)
            print(f"Connected {len(connected_loops)} loops from segments")
            return connected_loops
        
        return paths
    
    def _connect_segments_to_loops(self, segments: List[List[Tuple[float, float]]]) -> List[List[Tuple[float, float]]]:
        """Try to connect individual segments into closed loops."""
        if not segments:
            return []
        
        # Separate already-closed paths from individual segments
        closed_paths = []
        individual_segments = []
        
        for segment in segments:
            if len(segment) > 2:
                # Check if it's already a closed path
                start = segment[0]
                end = segment[-1]
                distance = math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2)
                if distance < 0.1:  # Close enough to be considered closed
                    closed_paths.append(segment)
                else:
                    individual_segments.append(segment)
            else:
                individual_segments.append(segment)
        
        print(f"Found {len(closed_paths)} already closed paths, {len(individual_segments)} individual segments")
        
        # Try to connect individual segments
        tolerance = 1.0  # Connection tolerance
        connected_loops = []
        used_segments = set()
        
        for i, start_segment in enumerate(individual_segments):
            if i in used_segments:
                continue
            
            # Start a new potential loop
            current_loop = list(start_segment)
            used_segments.add(i)
            
            # Try to find connecting segments
            max_iterations = len(individual_segments)
            iterations = 0
            
            while iterations < max_iterations:
                iterations += 1
                found_connection = False
                current_end = current_loop[-1]
                
                # Look for a segment that starts near our current end
                for j, candidate in enumerate(individual_segments):
                    if j in used_segments:
                        continue
                    
                    candidate_start = candidate[0]
                    candidate_end = candidate[-1]
                    
                    # Check if candidate starts near our end
                    dist_to_start = math.sqrt((current_end[0] - candidate_start[0])**2 + 
                                            (current_end[1] - candidate_start[1])**2)
                    
                    # Check if candidate ends near our end (reverse connection)
                    dist_to_end = math.sqrt((current_end[0] - candidate_end[0])**2 + 
                                          (current_end[1] - candidate_end[1])**2)
                    
                    if dist_to_start < tolerance:
                        # Connect forward
                        current_loop.extend(candidate[1:])  # Skip first point to avoid duplication
                        used_segments.add(j)
                        found_connection = True
                        break
                    elif dist_to_end < tolerance:
                        # Connect reverse
                        reversed_candidate = list(reversed(candidate))
                        current_loop.extend(reversed_candidate[1:])  # Skip first point
                        used_segments.add(j)
                        found_connection = True
                        break
                
                if not found_connection:
                    break
            
            # Check if we have a closed loop
            if len(current_loop) > 3:
                start_point = current_loop[0]
                end_point = current_loop[-1]
                closing_distance = math.sqrt((end_point[0] - start_point[0])**2 + 
                                           (end_point[1] - start_point[1])**2)
                
                if closing_distance < tolerance * 2:  # Allow slightly larger tolerance for closing
                    # Close the loop
                    current_loop.append(start_point)
                    connected_loops.append(current_loop)
                    print(f"Connected loop with {len(current_loop)} points, closing distance: {closing_distance:.3f}")
        
        # Combine closed paths and connected loops
        all_loops = closed_paths + connected_loops
        
        # Sort by area (largest first)
        if all_loops:
            all_loops.sort(key=lambda loop: self._calculate_polygon_area(loop), reverse=True)
        
        return all_loops
    
    def _create_fallback_loop(self):
        """Create a fallback loop from the bounding box of all entities."""
        if not self.current_doc:
            return
        
        try:
            msp = self.current_doc.modelspace()
            
            # Calculate bounding box manually from all entities
            min_x = min_y = float('inf')
            max_x = max_y = float('-inf')
            
            for entity in msp:
                try:
                    if entity.dxftype() == 'CIRCLE':
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        min_x = min(min_x, center.x - radius)
                        max_x = max(max_x, center.x + radius)
                        min_y = min(min_y, center.y - radius)
                        max_y = max(max_y, center.y + radius)
                    
                    elif entity.dxftype() == 'LINE':
                        start = entity.dxf.start
                        end = entity.dxf.end
                        min_x = min(min_x, start.x, end.x)
                        max_x = max(max_x, start.x, end.x)
                        min_y = min(min_y, start.y, end.y)
                        max_y = max(max_y, start.y, end.y)
                    
                    elif entity.dxftype() == 'ARC':
                        center = entity.dxf.center
                        radius = entity.dxf.radius
                        # Simplified - use full circle bounds
                        min_x = min(min_x, center.x - radius)
                        max_x = max(max_x, center.x + radius)
                        min_y = min(min_y, center.y - radius)
                        max_y = max(max_y, center.y + radius)
                    
                    elif hasattr(entity, 'dxf') and hasattr(entity.dxf, 'insert'):
                        # For entities with insert points
                        point = entity.dxf.insert
                        min_x = min(min_x, point.x)
                        max_x = max(max_x, point.x)
                        min_y = min(min_y, point.y)
                        max_y = max(max_y, point.y)
                
                except Exception as e:
                    print(f"Error processing entity {entity.dxftype()} for bounds: {e}")
                    continue
            
            if min_x != float('inf') and max_x != float('-inf'):
                print(f"Creating fallback loop with bounds: ({min_x}, {min_y}) to ({max_x}, {max_y})")
                
                self.outer_loop = [
                    (min_x, min_y),
                    (max_x, min_y),
                    (max_x, max_y),
                    (min_x, max_y),
                    (min_x, min_y)  # Close the loop
                ]
                self.all_loops = [self.outer_loop]
                self.inner_loops = []
            else:
                print("Could not determine bounds for fallback loop")
                
        except Exception as e:
            print(f"Error creating fallback loop: {e}")
    
    def _calculate_basic_fallback_features(self) -> Dict[str, Any]:
        """Calculate basic fallback features when full calculation fails."""
        if not self.current_doc:
            return {}
        
        try:
            msp = self.current_doc.modelspace()
            entities = list(msp)
            extents = msp.get_extents()
            
            features = {
                'number_of_loops': 0,
                'profile_type': 'Unknown',
                'profile_area': 0,
                'outer_area': 0,
                'inner_area': 0,
                'hollow_ratio': 0,
                'outer_perimeter': 0,
                'total_perimeter': 0,
                'number_of_mandrels': 0,
                'entity_count': len(entities)
            }
            
            if extents:
                width = extents.max.x - extents.min.x
                height = extents.max.y - extents.min.y
                features.update({
                    'bounding_box_width': width,
                    'bounding_box_height': height,
                    'bounding_box_area': width * height,
                    'max_width': width,
                    'max_height': height,
                    'aspect_ratio': height / width if width > 0 else 0
                })
            
            return features
        except Exception as e:
            print(f"Error calculating fallback features: {e}")
            return {'error': 'Failed to calculate any features'}
    
    def calculate_all_features(self) -> Dict[str, Any]:
        """Calculate all features mentioned in calculations.txt."""
        if not self.current_doc:
            return {}
        
        # Re-detect loops to ensure we have data
        self._detect_loops()
        
        # If still no outer loop, try to create a simple bounding box
        if not self.outer_loop:
            self._create_fallback_loop()
        
        if not self.outer_loop:
            return {}
        
        features = {}
        
        try:
            # Basic profile properties
            features.update(self._calculate_basic_properties())
            
            # Extrusion ratios
            features.update(self._calculate_extrusion_ratios())
            
            # Geometric properties
            features.update(self._calculate_geometric_properties())
            
            # Wall thickness analysis
            features.update(self._calculate_wall_thickness())
            
            # Moments of inertia
            features.update(self._calculate_moments_of_inertia())
            
            # Fourier descriptors
            features.update(self._calculate_fourier_descriptors())
            
            # Distance and similarity metrics
            features.update(self._calculate_distance_metrics())
            
            # Mass vectors by quadrant
            features.update(self._calculate_mass_vectors())
            
            # Complexity factors
            features.update(self._calculate_complexity_factors())
            
            # Mandrel analysis
            features.update(self._calculate_mandrel_features())
            
        except Exception as e:
            print(f"Error calculating features: {e}")
            # Return at least basic features if available
            if not features:
                features = self._calculate_basic_fallback_features()
        
        return features
    
    def _calculate_basic_properties(self) -> Dict[str, Any]:
        """Calculate basic profile properties."""
        properties = {}
        
        # Number of loops
        properties['number_of_loops'] = len(self.all_loops)
        
        # Profile type
        if len(self.inner_loops) == 0:
            properties['profile_type'] = 'Solid (1 loop)'
        else:
            properties['profile_type'] = f'Hollow (outer loop + {len(self.inner_loops)} inner loops)'
        
        # Areas
        outer_area = self._calculate_polygon_area(self.outer_loop)
        inner_area = sum(self._calculate_polygon_area(loop) for loop in self.inner_loops)
        profile_area = outer_area - inner_area
        
        properties['outer_area'] = outer_area
        properties['inner_area'] = inner_area
        properties['profile_area'] = profile_area
        
        # Hollow ratio
        properties['hollow_ratio'] = inner_area / outer_area if outer_area > 0 else 0
        
        # Perimeter
        properties['outer_perimeter'] = self._calculate_polygon_perimeter(self.outer_loop)
        properties['total_perimeter'] = properties['outer_perimeter'] + sum(
            self._calculate_polygon_perimeter(loop) for loop in self.inner_loops
        )
        
        # Bounding box
        bbox = self._calculate_bounding_box(self.outer_loop)
        properties['bounding_box_width'] = bbox['width']
        properties['bounding_box_height'] = bbox['height']
        properties['bounding_box_area'] = bbox['width'] * bbox['height']
        properties['max_width'] = bbox['width']
        properties['max_height'] = bbox['height']
        
        # Number of mandrels (internal loops)
        properties['number_of_mandrels'] = len(self.inner_loops)
        
        return properties
    
    def _calculate_extrusion_ratios(self) -> Dict[str, Any]:
        """Calculate extrusion ratios for different containers."""
        profile_area = self._calculate_polygon_area(self.outer_loop) - sum(
            self._calculate_polygon_area(loop) for loop in self.inner_loops
        )
        
        # Container areas
        container_p22 = math.pi * (105 ** 2)  # A = π * 105²
        container_p40 = math.pi * (145 ** 2)  # A = π * 145²
        container_p55 = math.pi * (145 ** 2)  # A = π * 145²
        
        ratios = {}
        
        if profile_area > 0:
            ratios['er_p22'] = container_p22 / profile_area
            ratios['er_p40'] = container_p40 / profile_area
            ratios['er_p55'] = container_p55 / profile_area
            
            # Calculate optimal number of holes for each container
            ratios['holes_p22'] = self._calculate_optimal_holes(ratios['er_p22'])
            ratios['holes_p40'] = self._calculate_optimal_holes(ratios['er_p40'])
            ratios['holes_p55'] = self._calculate_optimal_holes(ratios['er_p55'])
        else:
            ratios.update({
                'er_p22': 0, 'er_p40': 0, 'er_p55': 0,
                'holes_p22': 0, 'holes_p40': 0, 'holes_p55': 0
            })
        
        return ratios
    
    def _calculate_optimal_holes(self, er: float) -> int:
        """Calculate optimal number of holes to keep ER between 40-60."""
        hole_options = [1, 2, 4, 6, 8]
        target_er_min, target_er_max = 40, 60
        
        for holes in hole_options:
            adjusted_er = er / holes
            if target_er_min <= adjusted_er <= target_er_max:
                return holes
        
        # If no exact match, find closest
        best_holes = 1
        best_diff = float('inf')
        
        for holes in hole_options:
            adjusted_er = er / holes
            if adjusted_er < target_er_min:
                diff = target_er_min - adjusted_er
            elif adjusted_er > target_er_max:
                diff = adjusted_er - target_er_max
            else:
                return holes
            
            if diff < best_diff:
                best_diff = diff
                best_holes = holes
        
        return best_holes
    
    def _calculate_geometric_properties(self) -> Dict[str, Any]:
        """Calculate geometric properties like compactness, solidity, aspect ratio."""
        properties = {}
        
        # Aspect ratio
        bbox = self._calculate_bounding_box(self.outer_loop)
        properties['aspect_ratio'] = bbox['height'] / bbox['width'] if bbox['width'] > 0 else 0
        
        # Compactness: C = P² / (4πA)
        area = self._calculate_polygon_area(self.outer_loop)
        perimeter = self._calculate_polygon_perimeter(self.outer_loop)
        properties['compactness'] = (perimeter ** 2) / (4 * math.pi * area) if area > 0 else 0
        
        # Solidity: Area / Convex Hull Area
        convex_hull_area = self._calculate_convex_hull_area(self.outer_loop)
        properties['solidity'] = area / convex_hull_area if convex_hull_area > 0 else 0
        
        # Circumscribing circle diameter (CCD)
        properties['ccd'] = self._calculate_circumscribing_circle_diameter(self.outer_loop)
        
        # Min and max radius of outer contour
        centroid = self._calculate_centroid(self.outer_loop)
        distances = [math.sqrt((p[0] - centroid[0])**2 + (p[1] - centroid[1])**2) for p in self.outer_loop]
        properties['min_radius_outer'] = min(distances) if distances else 0
        properties['max_radius_outer'] = max(distances) if distances else 0
        
        return properties
    
    def _calculate_wall_thickness(self) -> Dict[str, Any]:
        """Calculate wall thickness properties."""
        if not self.inner_loops:
            return {
                'max_wall_thickness': 0,
                'min_wall_thickness': 0,
                'avg_wall_thickness': 0,
                'wall_thickness_variability': 0
            }
        
        # Simplified wall thickness calculation
        # In practice, you'd need more sophisticated algorithms
        thicknesses = []
        
        # Sample points around the outer loop and find distances to inner loops
        for i in range(0, len(self.outer_loop), max(1, len(self.outer_loop) // 100)):
            point = self.outer_loop[i]
            min_dist = float('inf')
            
            for inner_loop in self.inner_loops:
                for inner_point in inner_loop:
                    dist = math.sqrt((point[0] - inner_point[0])**2 + (point[1] - inner_point[1])**2)
                    min_dist = min(min_dist, dist)
            
            if min_dist != float('inf'):
                thicknesses.append(min_dist)
        
        if thicknesses:
            return {
                'max_wall_thickness': max(thicknesses),
                'min_wall_thickness': min(thicknesses),
                'avg_wall_thickness': sum(thicknesses) / len(thicknesses),
                'wall_thickness_variability': np.std(thicknesses)
            }
        else:
            return {
                'max_wall_thickness': 0,
                'min_wall_thickness': 0,
                'avg_wall_thickness': 0,
                'wall_thickness_variability': 0
            }
    
    def _calculate_moments_of_inertia(self) -> Dict[str, Any]:
        """Calculate moments of inertia."""
        # Simplified calculation using polygon approximation
        points = np.array(self.outer_loop)
        centroid = self._calculate_centroid(self.outer_loop)
        
        # Translate to centroid
        points_centered = points - centroid
        
        # Calculate second moments
        Ix = np.sum(points_centered[:, 1] ** 2)
        Iy = np.sum(points_centered[:, 0] ** 2)
        Ixy = np.sum(points_centered[:, 0] * points_centered[:, 1])
        
        # Polar moment of inertia
        Ip = Ix + Iy
        
        return {
            'moment_of_inertia_x': Ix,
            'moment_of_inertia_y': Iy,
            'polar_moment_of_inertia': Ip,
            'product_of_inertia': Ixy
        }
    
    def _calculate_fourier_descriptors(self) -> Dict[str, Any]:
        """Calculate first 10 normalized Fourier descriptors."""
        # Convert polygon to complex representation
        points = np.array(self.outer_loop)
        complex_points = points[:, 0] + 1j * points[:, 1]
        
        # Calculate FFT
        fft_result = fft(complex_points)
        
        # Normalize (make invariant to translation, rotation, scaling, and starting point)
        if len(fft_result) > 1:
            # Remove DC component (translation invariance)
            fft_normalized = fft_result[1:] / fft_result[1]
            
            # Take first 10 descriptors
            descriptors = np.abs(fft_normalized[:10])
            
            return {f'fourier_descriptor_{i+1}': float(desc) for i, desc in enumerate(descriptors)}
        else:
            return {f'fourier_descriptor_{i+1}': 0.0 for i in range(10)}
    
    def _calculate_distance_metrics(self) -> Dict[str, Any]:
        """Calculate Euclidean distance and cosine similarity."""
        # For demonstration, calculate against a reference circle
        num_points = 36
        reference_circle = [(math.cos(i * 2 * math.pi / num_points), math.sin(i * 2 * math.pi / num_points)) for i in range(num_points)]
        
        # Resample outer loop to same number of points
        resampled_loop = self._resample_polygon(self.outer_loop, num_points)
        
        # Ensure both arrays have the same length
        if len(resampled_loop) != len(reference_circle):
            # Pad or truncate to match
            if len(resampled_loop) < len(reference_circle):
                # Repeat last point to fill
                while len(resampled_loop) < len(reference_circle):
                    resampled_loop.append(resampled_loop[-1])
            else:
                # Truncate to match
                resampled_loop = resampled_loop[:len(reference_circle)]
        
        # Flatten for distance calculation
        loop_flat = np.array(resampled_loop).flatten()
        ref_flat = np.array(reference_circle).flatten()
        
        # Verify shapes match
        if loop_flat.shape != ref_flat.shape:
            # Fallback: use simple distance calculation
            euclidean_dist = 0.0
            cosine_sim = 0.0
        else:
            euclidean_dist = euclidean(loop_flat, ref_flat)
            cosine_sim = 1 - cosine(loop_flat, ref_flat)
        
        return {
            'euclidean_distance': euclidean_dist,
            'cosine_similarity': cosine_sim
        }
    
    def _calculate_mass_vectors(self) -> Dict[str, Any]:
        """Calculate mass vectors by quadrant."""
        centroid = self._calculate_centroid(self.outer_loop)
        
        quadrants = {'top_left': 0, 'top_right': 0, 'bottom_left': 0, 'bottom_right': 0}
        
        for point in self.outer_loop:
            x, y = point[0] - centroid[0], point[1] - centroid[1]
            
            if x <= 0 and y >= 0:
                quadrants['top_left'] += 1
            elif x > 0 and y >= 0:
                quadrants['top_right'] += 1
            elif x <= 0 and y < 0:
                quadrants['bottom_left'] += 1
            else:
                quadrants['bottom_right'] += 1
        
        total_points = len(self.outer_loop)
        return {
            'mass_vector_top_left': quadrants['top_left'] / total_points,
            'mass_vector_top_right': quadrants['top_right'] / total_points,
            'mass_vector_bottom_left': quadrants['bottom_left'] / total_points,
            'mass_vector_bottom_right': quadrants['bottom_right'] / total_points
        }
    
    def _calculate_complexity_factors(self) -> Dict[str, Any]:
        """Calculate complexity factors C1-C5."""
        area = self._calculate_polygon_area(self.outer_loop)
        total_perimeter = self._calculate_polygon_perimeter(self.outer_loop) + sum(
            self._calculate_polygon_perimeter(loop) for loop in self.inner_loops
        )
        
        # C1: Ps/As
        c1 = total_perimeter / area if area > 0 else 0
        
        # C2: Ps/Ws (assuming unit weight per length)
        weight_per_length = 1.0  # Placeholder
        c2 = total_perimeter / weight_per_length
        
        # C3: CCD/Tm (Form Factor)
        ccd = self._calculate_circumscribing_circle_diameter(self.outer_loop)
        min_thickness = self._calculate_wall_thickness().get('min_wall_thickness', 1)
        c3 = ccd / min_thickness if min_thickness > 0 else 0
        
        # C4: Groover's Definition
        p0 = 2 * math.sqrt(math.pi * area)  # Perimeter of equivalent circle
        c4 = 0.98 + 0.02 * (total_perimeter / p0) ** 2.25 if p0 > 0 else 0
        
        # C5: Qamar's Definition
        c5 = 0.95 + 0.05 * (total_perimeter / p0) ** 1.5 if p0 > 0 else 0
        
        return {
            'complexity_factor_c1': c1,
            'complexity_factor_c2': c2,
            'complexity_factor_c3': c3,
            'complexity_factor_c4': c4,
            'complexity_factor_c5': c5
        }
    
    def _calculate_mandrel_features(self) -> Dict[str, Any]:
        """Calculate features for each mandrel (inner loop)."""
        mandrel_features = {}
        
        for i, mandrel in enumerate(self.inner_loops[:4], 1):  # Up to 4 mandrels
            area = self._calculate_polygon_area(mandrel)
            perimeter = self._calculate_polygon_perimeter(mandrel)
            
            # Compactness
            compactness = (perimeter ** 2) / (4 * math.pi * area) if area > 0 else 0
            
            # Solidity
            convex_hull_area = self._calculate_convex_hull_area(mandrel)
            solidity = area / convex_hull_area if convex_hull_area > 0 else 0
            
            # Aspect ratio
            bbox = self._calculate_bounding_box(mandrel)
            aspect_ratio = bbox['height'] / bbox['width'] if bbox['width'] > 0 else 0
            
            # Distance from COG to centroid
            outer_centroid = self._calculate_centroid(self.outer_loop)
            mandrel_centroid = self._calculate_centroid(mandrel)
            distance_to_cog = math.sqrt(
                (mandrel_centroid[0] - outer_centroid[0]) ** 2 +
                (mandrel_centroid[1] - outer_centroid[1]) ** 2
            )
            
            # Thickness standard deviations (simplified)
            thickness_std = self._calculate_mandrel_thickness_std(mandrel)
            
            mandrel_features[f'mandrel_{i}'] = {
                'area': area,
                'perimeter': perimeter,
                'compactness': compactness,
                'solidity': solidity,
                'aspect_ratio': aspect_ratio,
                'distance_from_cog_to_centroid': distance_to_cog,
                'thickness_std_plus_x': thickness_std.get('plus_x', 0),
                'thickness_std_plus_y': thickness_std.get('plus_y', 0),
                'thickness_std_minus_x': thickness_std.get('minus_x', 0),
                'thickness_std_minus_y': thickness_std.get('minus_y', 0)
            }
        
        return mandrel_features
    
    def _calculate_mandrel_thickness_std(self, mandrel: List[Tuple[float, float]]) -> Dict[str, float]:
        """Calculate thickness standard deviation in different directions for a mandrel."""
        # Simplified implementation
        centroid = self._calculate_centroid(mandrel)
        
        # Sample thicknesses in different directions
        directions = {
            'plus_x': [],
            'plus_y': [],
            'minus_x': [],
            'minus_y': []
        }
        
        for point in mandrel:
            x_diff = point[0] - centroid[0]
            y_diff = point[1] - centroid[1]
            distance = math.sqrt(x_diff ** 2 + y_diff ** 2)
            
            if x_diff > 0:
                directions['plus_x'].append(distance)
            else:
                directions['minus_x'].append(distance)
            
            if y_diff > 0:
                directions['plus_y'].append(distance)
            else:
                directions['minus_y'].append(distance)
        
        return {
            direction: np.std(values) if values else 0
            for direction, values in directions.items()
        }
    
    # Helper methods
    def _calculate_polygon_area(self, points: List[Tuple[float, float]]) -> float:
        """Calculate area of polygon using shoelace formula."""
        if len(points) < 3:
            return 0
        
        area = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        return abs(area) / 2
    
    def _calculate_polygon_perimeter(self, points: List[Tuple[float, float]]) -> float:
        """Calculate perimeter of polygon."""
        if len(points) < 2:
            return 0
        
        perimeter = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            dx = points[j][0] - points[i][0]
            dy = points[j][1] - points[i][1]
            perimeter += math.sqrt(dx ** 2 + dy ** 2)
        return perimeter
    
    def _calculate_bounding_box(self, points: List[Tuple[float, float]]) -> Dict[str, float]:
        """Calculate bounding box of polygon."""
        if not points:
            return {'width': 0, 'height': 0, 'min_x': 0, 'max_x': 0, 'min_y': 0, 'max_y': 0}
        
        x_coords = [p[0] for p in points]
        y_coords = [p[1] for p in points]
        
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        return {
            'width': max_x - min_x,
            'height': max_y - min_y,
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y
        }
    
    def _calculate_centroid(self, points: List[Tuple[float, float]]) -> Tuple[float, float]:
        """Calculate centroid of polygon."""
        if not points:
            return (0, 0)
        
        area = self._calculate_polygon_area(points)
        if area == 0:
            # Fallback to arithmetic mean
            x = sum(p[0] for p in points) / len(points)
            y = sum(p[1] for p in points) / len(points)
            return (x, y)
        
        cx = cy = 0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            cross = points[i][0] * points[j][1] - points[j][0] * points[i][1]
            cx += (points[i][0] + points[j][0]) * cross
            cy += (points[i][1] + points[j][1]) * cross
        
        cx /= (6 * area)
        cy /= (6 * area)
        return (cx, cy)
    
    def _calculate_convex_hull_area(self, points: List[Tuple[float, float]]) -> float:
        """Calculate area of convex hull using Graham scan algorithm."""
        if len(points) < 3:
            return 0
        
        try:
            # Use scipy's ConvexHull if available
            from scipy.spatial import ConvexHull
            hull = ConvexHull(points)
            return hull.volume  # In 2D, volume is area
        except ImportError:
            # Fallback: use simple convex hull implementation
            hull_points = self._simple_convex_hull(points)
            return self._calculate_polygon_area(hull_points)
        except:
            # Final fallback: assume convex hull area is same as polygon area
            return self._calculate_polygon_area(points)
    
    def _calculate_circumscribing_circle_diameter(self, points: List[Tuple[float, float]]) -> float:
        """Calculate diameter of circumscribing circle."""
        if not points:
            return 0
        
        # Find the maximum distance between any two points
        max_dist = 0
        for i in range(len(points)):
            for j in range(i + 1, len(points)):
                dist = math.sqrt((points[i][0] - points[j][0]) ** 2 + (points[i][1] - points[j][1]) ** 2)
                max_dist = max(max_dist, dist)
        
        return max_dist
    
    def _resample_polygon(self, points: List[Tuple[float, float]], num_points: int) -> List[Tuple[float, float]]:
        """Resample polygon to have a specific number of points."""
        if not points:
            return []
        
        if len(points) == num_points:
            return points
        
        if len(points) < num_points:
            # If we have fewer points, interpolate or repeat
            resampled = list(points)
            while len(resampled) < num_points:
                resampled.append(points[-1])  # Repeat last point
            return resampled[:num_points]
        
        # Simple resampling by taking every nth point
        step = len(points) / num_points
        resampled = []
        for i in range(num_points):
            idx = int(i * step) % len(points)
            resampled.append(points[idx])
        
        return resampled
    
    def _simple_convex_hull(self, points: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """Simple convex hull implementation using Graham scan."""
        if len(points) < 3:
            return points
        
        # Find the bottom-most point (and leftmost in case of tie)
        start = min(points, key=lambda p: (p[1], p[0]))
        
        # Sort points by polar angle with respect to start point
        def polar_angle(p):
            dx = p[0] - start[0]
            dy = p[1] - start[1]
            return math.atan2(dy, dx)
        
        sorted_points = sorted([p for p in points if p != start], key=polar_angle)
        
        # Graham scan
        hull = [start]
        
        for point in sorted_points:
            # Remove points that make clockwise turn
            while len(hull) > 1 and self._cross_product(hull[-2], hull[-1], point) <= 0:
                hull.pop()
            hull.append(point)
        
        return hull
    
    def _cross_product(self, o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
        """Calculate cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])
    
    def export_to_excel(self, features: Dict[str, Any], output_path: str, metadata: Dict[str, Any]) -> bool:
        """
        Export calculated features to an Excel file.
        
        Args:
            features: Dictionary of calculated features
            output_path: Path to save the Excel file
            metadata: Dictionary containing metadata like filename, timestamp, etc.
            
        Returns:
            bool: True if export was successful, False otherwise
        """
        try:
            # Create a DataFrame for the features
            features_df = pd.DataFrame.from_dict(features, orient='index', columns=['Value'])
            features_df.index.name = 'Parameter'
            
            # Create a DataFrame for metadata
            metadata_df = pd.DataFrame.from_dict(metadata, orient='index', columns=['Value'])
            metadata_df.index.name = 'Metadata'
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Write features to first sheet
                features_df.to_excel(writer, sheet_name='Calculated Parameters')
                
                # Write metadata to second sheet
                metadata_df.to_excel(writer, sheet_name='Metadata')
                
                # Auto-adjust column widths
                for sheet_name in writer.sheets:
                    worksheet = writer.sheets[sheet_name]
                    for column in worksheet.columns:
                        max_length = 0
                        column = [cell for cell in column]
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except:
                                pass
                        adjusted_width = (max_length + 2)
                        worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
            
            return True
            
        except Exception as e:
            print(f"Error exporting to Excel: {e}")
            return False 