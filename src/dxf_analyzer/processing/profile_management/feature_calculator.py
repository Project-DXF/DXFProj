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
import networkx as nx
from shapely.geometry import LineString, Point, Polygon


class AdvancedFeatureCalculator:
    """Calculates advanced features for DXF profile analysis."""
    
    def __init__(self):
        """Initialize the feature calculator."""
        self.current_doc = None
        self.outer_loop = None
        self.inner_loops = []
        self.all_loops = []
        self.mandrel_paths = {}
        
    def set_document(self, doc: ezdxf.document.Drawing):
        """Set the DXF document to analyze."""
        self.current_doc = doc
        self._detect_loops()
    
    def _detect_loops(self):
        if not self.current_doc:
            return
        msp = self.current_doc.modelspace()
        all_entities = list(msp)
        entity_types = {}
        for e in all_entities:
            entity_type = e.dxftype()
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        print(f"Entity type distribution: {entity_types}")
        entities = [e for e in all_entities if e.dxftype() in ['LINE', 'ARC', 'CIRCLE', 'POLYLINE', 'LWPOLYLINE', 'ELLIPSE', 'SPLINE']]
        print(f"Found {len(entities)} entities for loop detection out of {len(all_entities)} total")
        loops_with_entities = []
        for entity in entities:
            points = []
            try:
                if entity.dxftype() == 'CIRCLE':
                    center = entity.dxf.center
                    radius = entity.dxf.radius
                    for i in range(36):
                        angle = i * 2 * math.pi / 36
                        x = center.x + radius * math.cos(angle)
                        y = center.y + radius * math.sin(angle)
                        points.append((x, y))
                    loops_with_entities.append({'points': points, 'entities': [entity]})
                elif entity.dxftype() == 'LWPOLYLINE':
                    if entity.is_closed:
                        pts = [(float(p[0]), float(p[1])) for p in entity.get_points()]
                        loops_with_entities.append({'points': pts, 'entities': [entity]})
                elif entity.dxftype() == 'POLYLINE':
                    if entity.is_closed:
                        pts = [(float(v.dxf.location.x), float(v.dxf.location.y)) for v in entity.vertices()]
                        loops_with_entities.append({'points': pts, 'entities': [entity]})
                elif entity.dxftype() == 'ELLIPSE':
                    center = entity.dxf.center
                    major_axis = entity.dxf.major_axis
                    ratio = entity.dxf.ratio
                    for i in range(36):
                        angle = i * 2 * math.pi / 36
                        x = center.x + major_axis.x * math.cos(angle)
                        y = center.y + major_axis.y * math.sin(angle) * ratio
                        points.append((x, y))
                    loops_with_entities.append({'points': points, 'entities': [entity]})
                elif entity.dxftype() == 'SPLINE':
                    if entity.is_closed:
                        pts = [(float(cp.x), float(cp.y)) for cp in entity.control_points]
                        loops_with_entities.append({'points': pts, 'entities': [entity]})
            except Exception as e:
                print(f"Error processing entity {entity.dxftype()} for path extraction: {e}")
                continue
        if not loops_with_entities:
            print("No closed polylines/circles/ellipses/splines found, trying graph-based loop detection for LINE/ARC...")
            loops_with_entities = self._find_loops_from_lines_arcs(entities)
        print(f"Extracted {len(loops_with_entities)} loops with their entities")
        if loops_with_entities:
            loops_with_entities.sort(key=lambda item: self._calculate_polygon_area(item['points']), reverse=True)
            self.all_loops = [item['points'] for item in loops_with_entities]
            self.outer_loop = self.all_loops[0] if self.all_loops else None
            self.inner_loops = self.all_loops[1:] if len(self.all_loops) > 1 else []
            self.mandrel_paths.clear()
            inner_loop_entities = [item['entities'] for item in loops_with_entities[1:]]
            for i, entities_list in enumerate(inner_loop_entities, 1):
                self.mandrel_paths[f'mandrel_{i}'] = entities_list
            print(f"Outer loop has {len(self.outer_loop)} points, {len(self.inner_loops)} inner loops")
        else:
            print("No loops detected, will try fallback method")
    
    def _find_loops_from_lines_arcs(self, entities):
        edges = []
        entity_points = {}
        decimal_precision = 4
        def rounded_point(x, y):
            return (round(x, decimal_precision), round(y, decimal_precision))
        for e in entities:
            if e.dxftype() == "LINE":
                start = rounded_point(e.dxf.start.x, e.dxf.start.y)
                end = rounded_point(e.dxf.end.x, e.dxf.end.y)
                edges.append((start, end, e))
                entity_points[e] = [start, end]
            elif e.dxftype() == "ARC":
                center = e.dxf.center
                radius = e.dxf.radius
                start_angle = math.radians(e.dxf.start_angle)
                end_angle = math.radians(e.dxf.end_angle)
                if end_angle < start_angle:
                    end_angle += 2 * math.pi
                arc_points = []
                for angle in range(0, 101):
                    theta = start_angle + (end_angle - start_angle) * (angle / 100)
                    x = center.x + radius * math.cos(theta)
                    y = center.y + radius * math.sin(theta)
                    arc_points.append(rounded_point(x, y))
                for i in range(len(arc_points) - 1):
                    edges.append((arc_points[i], arc_points[i + 1], e))
                entity_points[e] = arc_points
        G = nx.Graph()
        for start, end, e in edges:
            G.add_edge(start, end, entity=e)
        cycles = nx.cycle_basis(G)
        loops_with_entities = []
        for cycle in cycles:
            if len(cycle) >= 3:
                polygon = Polygon(cycle)
                if polygon.is_valid and abs(polygon.area) > 5:  # Ignore tiny loops
                    loop_entities = []
                    loop_points = []
                    used = set()
                    for i in range(len(cycle)):
                        pt1 = cycle[i]
                        pt2 = cycle[(i + 1) % len(cycle)]
                        for e in entities:
                            if e in used:
                                continue
                            pts = entity_points.get(e, [])
                            if pt1 in pts and pt2 in pts:
                                loop_entities.append(e)
                                used.add(e)
                                break
                        loop_points.append(pt1)
                    loops_with_entities.append({'points': loop_points, 'entities': loop_entities})
        return loops_with_entities

    def _extract_closed_paths_with_entities(self, entities) -> List[Dict[str, Any]]:
        print("Warning: _extract_closed_paths_with_entities is deprecated.")
        return []

    def _extract_closed_paths(self, entities) -> List[List[Tuple[float, float]]]:
        print("Warning: _extract_closed_paths is deprecated.")
        return []
    
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
        if not self.inner_loops or not self.outer_loop or len(self.outer_loop) < 3:
            return {
                'max_wall_thickness': 0,
                'min_wall_thickness': 0,
                'avg_wall_thickness': 0,
                'wall_thickness_variability': 0
            }

        inner_polygons = [Polygon(inner) for inner in self.inner_loops if len(inner) >= 3]
        if not inner_polygons:
            return {
                'max_wall_thickness': 0,
                'min_wall_thickness': 0,
                'avg_wall_thickness': 0,
                'wall_thickness_variability': 0
            }

        outer = self.outer_loop
        n_samples = min(200, len(outer))  
        step = max(1, len(outer) // n_samples)
        thicknesses = []
        for i in range(0, len(outer), step):
            p0 = np.array(outer[i])
            p_prev = np.array(outer[i - 1])
            p_next = np.array(outer[(i + 1) % len(outer)])
            tangent = p_next - p_prev
            tangent_norm = np.linalg.norm(tangent)
            if tangent_norm == 0:
                continue
            tangent = tangent / tangent_norm
            normal = np.array([-tangent[1], tangent[0]])
            centroid = np.mean(np.array(outer), axis=0)
            test_point = p0 + normal * 1.0
            dist1 = np.linalg.norm((test_point - centroid))
            test_point2 = p0 - normal * 1.0
            dist2 = np.linalg.norm((test_point2 - centroid))
            if dist2 < dist1:
                normal = -normal
            ray_end = p0 + normal * 1e4
            ray = LineString([tuple(p0), tuple(ray_end)])
            min_dist = None
            for poly in inner_polygons:
                inter = ray.intersection(poly.boundary)
                if inter.is_empty:
                    continue
                if inter.geom_type == 'Point':
                    pts = [inter]
                elif inter.geom_type == 'MultiPoint':
                    pts = list(inter.geoms)
                elif inter.geom_type == 'LineString':
                    pts = [Point(c) for c in inter.coords]
                else:
                    continue
                for pt in pts:
                    v = np.array([pt.x, pt.y]) - p0
                    if np.dot(v, normal) > 1e-6:
                        d = np.linalg.norm(v)
                        if min_dist is None or d < min_dist:
                            min_dist = d
            if min_dist is not None:
                thicknesses.append(min_dist)
        if thicknesses:
            return {
                'max_wall_thickness': float(np.max(thicknesses)),
                'min_wall_thickness': float(np.min(thicknesses)),
                'avg_wall_thickness': float(np.mean(thicknesses)),
                'wall_thickness_variability': float(np.std(thicknesses))
            }
        else:
            return {
                'max_wall_thickness': 0,
                'min_wall_thickness': 0,
                'avg_wall_thickness': 0,
                'wall_thickness_variability': 0
            }
    
    def _calculate_moments_of_inertia(self) -> Dict[str, Any]:
        points = np.array(self.outer_loop)
        centroid = self._calculate_centroid(self.outer_loop)
        
        points_centered = points - centroid
        
        Ix = np.sum(points_centered[:, 1] ** 2)
        Iy = np.sum(points_centered[:, 0] ** 2)
        Ixy = np.sum(points_centered[:, 0] * points_centered[:, 1])
        
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
        
        for i, mandrel in enumerate(self.inner_loops, 1): 
            key = f'mandrel_{i}'
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
            
            mandrel_features[key] = {
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