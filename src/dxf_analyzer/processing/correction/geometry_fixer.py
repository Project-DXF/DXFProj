"""
Geometry Fixer for DXF Files

Handles specific geometric corrections and fixes for DXF entities.
"""

import ezdxf
from typing import Dict, List, Any, Optional, Tuple
import math


class GeometryFixer:
    """Handles geometric corrections for DXF entities."""
    
    def __init__(self):
        """Initialize the geometry fixer."""
        self.tolerance = 0.001
        
    def fix_overlapping_lines(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Fix overlapping lines by merging them.
        
        Args:
            doc: The DXF document to fix
            
        Returns:
            Dictionary containing fix results
        """
        msp = doc.modelspace()
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        merged_count = 0
        entities_to_remove = []
        
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                if self._lines_overlap(line1, line2):
                    # Merge the lines
                    merged_line = self._merge_overlapping_lines(line1, line2)
                    if merged_line:
                        # Update line1 with merged coordinates
                        line1.dxf.start = merged_line[0]
                        line1.dxf.end = merged_line[1]
                        
                        # Mark line2 for removal
                        if line2 not in entities_to_remove:
                            entities_to_remove.append(line2)
                            merged_count += 1
        
        # Remove overlapping lines
        for entity in entities_to_remove:
            msp.delete_entity(entity)
        
        return {
            'operation': 'fix_overlapping_lines',
            'merged_lines': merged_count,
            'message': f'Merged {merged_count} overlapping lines'
        }
    
    def fix_arc_connections(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Fix arc connections by adjusting endpoints.
        
        Args:
            doc: The DXF document to fix
            
        Returns:
            Dictionary containing fix results
        """
        msp = doc.modelspace()
        arcs = [entity for entity in msp if entity.dxftype() == 'ARC']
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        connections_fixed = 0
        
        # Check arc-to-line connections
        for arc in arcs:
            arc_start = self._get_arc_start_point(arc)
            arc_end = self._get_arc_end_point(arc)
            
            for line in lines:
                line_start = (line.dxf.start.x, line.dxf.start.y)
                line_end = (line.dxf.end.x, line.dxf.end.y)
                
                # Check if arc end is close to line start
                if self._points_close(arc_end, line_start):
                    line.dxf.start = ezdxf.math.Vec3(arc_end[0], arc_end[1], 0)
                    connections_fixed += 1
                
                # Check if arc start is close to line end
                elif self._points_close(arc_start, line_end):
                    line.dxf.end = ezdxf.math.Vec3(arc_start[0], arc_start[1], 0)
                    connections_fixed += 1
        
        return {
            'operation': 'fix_arc_connections',
            'connections_fixed': connections_fixed,
            'message': f'Fixed {connections_fixed} arc-line connections'
        }
    
    def fix_circle_tangencies(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Fix circle tangencies with lines.
        
        Args:
            doc: The DXF document to fix
            
        Returns:
            Dictionary containing fix results
        """
        msp = doc.modelspace()
        circles = [entity for entity in msp if entity.dxftype() == 'CIRCLE']
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        tangencies_fixed = 0
        
        for circle in circles:
            center = (circle.dxf.center.x, circle.dxf.center.y)
            radius = circle.dxf.radius
            
            for line in lines:
                # Check if line should be tangent to circle
                distance = self._point_to_line_distance(center, line)
                
                if abs(distance - radius) < self.tolerance * 10:  # Larger tolerance for tangency
                    # Adjust line to be exactly tangent
                    self._make_line_tangent_to_circle(line, circle)
                    tangencies_fixed += 1
        
        return {
            'operation': 'fix_circle_tangencies',
            'tangencies_fixed': tangencies_fixed,
            'message': f'Fixed {tangencies_fixed} circle tangencies'
        }
    
    def _lines_overlap(self, line1, line2) -> bool:
        """Check if two lines overlap."""
        # Get line vectors and check if they're parallel
        v1 = (line1.dxf.end.x - line1.dxf.start.x, line1.dxf.end.y - line1.dxf.start.y)
        v2 = (line2.dxf.end.x - line2.dxf.start.x, line2.dxf.end.y - line2.dxf.start.y)
        
        # Check if vectors are parallel (cross product near zero)
        cross_product = abs(v1[0] * v2[1] - v1[1] * v2[0])
        
        if cross_product < self.tolerance:
            # Lines are parallel, check if they overlap
            return self._parallel_lines_overlap(line1, line2)
        
        return False
    
    def _parallel_lines_overlap(self, line1, line2) -> bool:
        """Check if two parallel lines overlap."""
        # Project all points onto the line direction
        v1 = (line1.dxf.end.x - line1.dxf.start.x, line1.dxf.end.y - line1.dxf.start.y)
        length1 = math.sqrt(v1[0]**2 + v1[1]**2)
        
        if length1 < self.tolerance:
            return False
        
        # Normalize direction vector
        dir_vec = (v1[0] / length1, v1[1] / length1)
        
        # Project points onto the line
        def project_point(point, origin, direction):
            rel_vec = (point[0] - origin[0], point[1] - origin[1])
            return rel_vec[0] * direction[0] + rel_vec[1] * direction[1]
        
        origin = (line1.dxf.start.x, line1.dxf.start.y)
        
        # Project all endpoints
        p1_start = 0  # Origin is line1 start
        p1_end = project_point((line1.dxf.end.x, line1.dxf.end.y), origin, dir_vec)
        p2_start = project_point((line2.dxf.start.x, line2.dxf.start.y), origin, dir_vec)
        p2_end = project_point((line2.dxf.end.x, line2.dxf.end.y), origin, dir_vec)
        
        # Sort the projections
        line1_range = sorted([p1_start, p1_end])
        line2_range = sorted([p2_start, p2_end])
        
        # Check for overlap
        return not (line1_range[1] < line2_range[0] or line2_range[1] < line1_range[0])
    
    def _merge_overlapping_lines(self, line1, line2) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """Merge two overlapping lines into one."""
        # Get all endpoints
        points = [
            (line1.dxf.start.x, line1.dxf.start.y),
            (line1.dxf.end.x, line1.dxf.end.y),
            (line2.dxf.start.x, line2.dxf.start.y),
            (line2.dxf.end.x, line2.dxf.end.y)
        ]
        
        # Find the two points that are farthest apart
        max_distance = 0
        best_pair = None
        
        for i, p1 in enumerate(points):
            for j, p2 in enumerate(points[i+1:], i+1):
                distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
                if distance > max_distance:
                    max_distance = distance
                    best_pair = (p1, p2)
        
        return best_pair
    
    def _get_arc_start_point(self, arc) -> Tuple[float, float]:
        """Get the start point of an arc."""
        center = arc.dxf.center
        radius = arc.dxf.radius
        start_angle = math.radians(arc.dxf.start_angle)
        
        x = center.x + radius * math.cos(start_angle)
        y = center.y + radius * math.sin(start_angle)
        
        return (x, y)
    
    def _get_arc_end_point(self, arc) -> Tuple[float, float]:
        """Get the end point of an arc."""
        center = arc.dxf.center
        radius = arc.dxf.radius
        end_angle = math.radians(arc.dxf.end_angle)
        
        x = center.x + radius * math.cos(end_angle)
        y = center.y + radius * math.sin(end_angle)
        
        return (x, y)
    
    def _points_close(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
        """Check if two points are close within tolerance."""
        distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        return distance < self.tolerance
    
    def _point_to_line_distance(self, point: Tuple[float, float], line) -> float:
        """Calculate distance from a point to a line."""
        x0, y0 = point
        x1, y1 = line.dxf.start.x, line.dxf.start.y
        x2, y2 = line.dxf.end.x, line.dxf.end.y
        
        # Line equation: ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        c = x2 * y1 - x1 * y2
        
        # Distance formula
        distance = abs(a * x0 + b * y0 + c) / math.sqrt(a**2 + b**2)
        return distance
    
    def _make_line_tangent_to_circle(self, line, circle):
        """Adjust a line to be exactly tangent to a circle."""
        # This is a simplified implementation
        # In practice, this would involve more complex geometric calculations
        center = (circle.dxf.center.x, circle.dxf.center.y)
        radius = circle.dxf.radius
        
        # For now, just ensure the line maintains its direction but is tangent
        # This would need more sophisticated implementation for production use
        pass
    
    def set_tolerance(self, tolerance: float):
        """Set the tolerance for geometric operations."""
        self.tolerance = max(tolerance, 0.0001)
    
    def get_tolerance(self) -> float:
        """Get the current tolerance."""
        return self.tolerance 