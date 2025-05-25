"""
Feature Extractor for DXF Files

Extracts advanced features and characteristics from DXF files
for analysis and processing workflows.
"""

import ezdxf
from typing import Dict, List, Any, Optional, Tuple
import math
from collections import defaultdict


class FeatureExtractor:
    """Extracts features and characteristics from DXF files."""
    
    def __init__(self):
        """Initialize the feature extractor."""
        self.current_doc = None
        self.entities = []
        
    def set_document(self, doc: ezdxf.document.Drawing):
        """
        Set the DXF document to extract features from.
        
        Args:
            doc: The ezdxf document
        """
        self.current_doc = doc
        if doc:
            msp = doc.modelspace()
            self.entities = list(msp)
    
    def extract_geometric_features(self) -> Dict[str, Any]:
        """
        Extract geometric features from the DXF file.
        
        Returns:
            Dictionary containing geometric features
        """
        if not self.current_doc:
            return {}
        
        features = {
            'lines': self._extract_line_features(),
            'arcs': self._extract_arc_features(),
            'circles': self._extract_circle_features(),
            'polylines': self._extract_polyline_features(),
            'splines': self._extract_spline_features()
        }
        
        # Calculate overall geometric properties
        features['overall'] = self._calculate_overall_properties()
        
        return features
    
    def _extract_line_features(self) -> Dict[str, Any]:
        """Extract features from line entities."""
        lines = [e for e in self.entities if e.dxftype() == 'LINE']
        
        if not lines:
            return {'count': 0}
        
        lengths = []
        angles = []
        
        for line in lines:
            start = line.dxf.start
            end = line.dxf.end
            
            # Calculate length
            length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
            lengths.append(length)
            
            # Calculate angle
            angle = math.atan2(end.y - start.y, end.x - start.x)
            angles.append(math.degrees(angle))
        
        return {
            'count': len(lines),
            'total_length': sum(lengths),
            'average_length': sum(lengths) / len(lengths),
            'min_length': min(lengths),
            'max_length': max(lengths),
            'angles': angles,
            'horizontal_lines': len([a for a in angles if abs(a) < 5 or abs(a - 180) < 5]),
            'vertical_lines': len([a for a in angles if abs(a - 90) < 5 or abs(a + 90) < 5])
        }
    
    def _extract_arc_features(self) -> Dict[str, Any]:
        """Extract features from arc entities."""
        arcs = [e for e in self.entities if e.dxftype() == 'ARC']
        
        if not arcs:
            return {'count': 0}
        
        radii = []
        arc_lengths = []
        
        for arc in arcs:
            radius = arc.dxf.radius
            radii.append(radius)
            
            # Calculate arc length
            start_angle = math.radians(arc.dxf.start_angle)
            end_angle = math.radians(arc.dxf.end_angle)
            angle_diff = end_angle - start_angle
            if angle_diff < 0:
                angle_diff += 2 * math.pi
            
            arc_length = radius * angle_diff
            arc_lengths.append(arc_length)
        
        return {
            'count': len(arcs),
            'radii': radii,
            'average_radius': sum(radii) / len(radii),
            'min_radius': min(radii),
            'max_radius': max(radii),
            'total_arc_length': sum(arc_lengths),
            'average_arc_length': sum(arc_lengths) / len(arc_lengths)
        }
    
    def _extract_circle_features(self) -> Dict[str, Any]:
        """Extract features from circle entities."""
        circles = [e for e in self.entities if e.dxftype() == 'CIRCLE']
        
        if not circles:
            return {'count': 0}
        
        radii = [circle.dxf.radius for circle in circles]
        areas = [math.pi * r**2 for r in radii]
        circumferences = [2 * math.pi * r for r in radii]
        
        return {
            'count': len(circles),
            'radii': radii,
            'average_radius': sum(radii) / len(radii),
            'min_radius': min(radii),
            'max_radius': max(radii),
            'total_area': sum(areas),
            'total_circumference': sum(circumferences)
        }
    
    def _extract_polyline_features(self) -> Dict[str, Any]:
        """Extract features from polyline entities."""
        polylines = [e for e in self.entities if e.dxftype() in ['POLYLINE', 'LWPOLYLINE']]
        
        if not polylines:
            return {'count': 0}
        
        vertex_counts = []
        total_lengths = []
        
        for polyline in polylines:
            if hasattr(polyline, 'vertices'):
                vertices = list(polyline.vertices)
                vertex_counts.append(len(vertices))
                
                # Calculate total length
                total_length = 0
                for i in range(len(vertices) - 1):
                    v1 = vertices[i].dxf.location
                    v2 = vertices[i + 1].dxf.location
                    length = math.sqrt((v2.x - v1.x)**2 + (v2.y - v1.y)**2)
                    total_length += length
                
                total_lengths.append(total_length)
        
        return {
            'count': len(polylines),
            'vertex_counts': vertex_counts,
            'average_vertices': sum(vertex_counts) / len(vertex_counts) if vertex_counts else 0,
            'total_lengths': total_lengths,
            'average_length': sum(total_lengths) / len(total_lengths) if total_lengths else 0
        }
    
    def _extract_spline_features(self) -> Dict[str, Any]:
        """Extract features from spline entities."""
        splines = [e for e in self.entities if e.dxftype() == 'SPLINE']
        
        if not splines:
            return {'count': 0}
        
        degrees = []
        control_point_counts = []
        
        for spline in splines:
            if hasattr(spline.dxf, 'degree'):
                degrees.append(spline.dxf.degree)
            
            if hasattr(spline, 'control_points'):
                control_point_counts.append(len(list(spline.control_points)))
        
        return {
            'count': len(splines),
            'degrees': degrees,
            'average_degree': sum(degrees) / len(degrees) if degrees else 0,
            'control_point_counts': control_point_counts,
            'average_control_points': sum(control_point_counts) / len(control_point_counts) if control_point_counts else 0
        }
    
    def _calculate_overall_properties(self) -> Dict[str, Any]:
        """Calculate overall geometric properties."""
        if not self.current_doc:
            return {}
        
        try:
            msp = self.current_doc.modelspace()
            extents = msp.get_extents()
            
            if extents:
                width = extents.max.x - extents.min.x
                height = extents.max.y - extents.min.y
                area = width * height
                aspect_ratio = width / height if height > 0 else 0
                
                return {
                    'bounding_box': {
                        'min_x': extents.min.x,
                        'min_y': extents.min.y,
                        'max_x': extents.max.x,
                        'max_y': extents.max.y,
                        'width': width,
                        'height': height,
                        'area': area,
                        'aspect_ratio': aspect_ratio
                    },
                    'center': {
                        'x': (extents.min.x + extents.max.x) / 2,
                        'y': (extents.min.y + extents.max.y) / 2
                    }
                }
        except Exception as e:
            print(f"Error calculating overall properties: {e}")
        
        return {}
    
    def extract_layer_features(self) -> Dict[str, Any]:
        """
        Extract features related to layers.
        
        Returns:
            Dictionary containing layer information
        """
        if not self.current_doc:
            return {}
        
        layer_entities = defaultdict(list)
        layer_counts = defaultdict(int)
        
        for entity in self.entities:
            layer = entity.dxf.layer
            layer_entities[layer].append(entity)
            layer_counts[layer] += 1
        
        return {
            'layer_count': len(layer_entities),
            'layers': list(layer_entities.keys()),
            'entity_counts_by_layer': dict(layer_counts),
            'most_used_layer': max(layer_counts, key=layer_counts.get) if layer_counts else None
        }
    
    def extract_complexity_metrics(self) -> Dict[str, Any]:
        """
        Extract complexity metrics from the DXF file.
        
        Returns:
            Dictionary containing complexity metrics
        """
        if not self.current_doc:
            return {}
        
        entity_types = defaultdict(int)
        for entity in self.entities:
            entity_types[entity.dxftype()] += 1
        
        # Calculate complexity score
        complexity_weights = {
            'LINE': 1,
            'ARC': 2,
            'CIRCLE': 2,
            'POLYLINE': 3,
            'LWPOLYLINE': 3,
            'SPLINE': 5,
            'ELLIPSE': 4,
            'HATCH': 6,
            'DIMENSION': 3,
            'TEXT': 2,
            'MTEXT': 3
        }
        
        complexity_score = sum(
            entity_types[entity_type] * complexity_weights.get(entity_type, 1)
            for entity_type in entity_types
        )
        
        return {
            'total_entities': len(self.entities),
            'unique_entity_types': len(entity_types),
            'entity_type_distribution': dict(entity_types),
            'complexity_score': complexity_score,
            'complexity_level': self._classify_complexity(complexity_score)
        }
    
    def _classify_complexity(self, score: int) -> str:
        """Classify complexity level based on score."""
        if score < 50:
            return 'Simple'
        elif score < 200:
            return 'Moderate'
        elif score < 500:
            return 'Complex'
        else:
            return 'Very Complex' 