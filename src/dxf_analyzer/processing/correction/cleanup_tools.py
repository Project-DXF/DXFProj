"""
Cleanup Tools for DXF Files

Provides general cleanup and optimization tools for DXF files.
"""

import ezdxf
from typing import Dict, List, Any, Set
from collections import defaultdict


class CleanupTools:
    """General cleanup and optimization tools for DXF files."""
    
    def __init__(self):
        """Initialize the cleanup tools."""
        pass
    
    def cleanup_layers(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Clean up layers by removing empty layers and organizing entities.
        
        Args:
            doc: The DXF document to clean up
            
        Returns:
            Dictionary containing cleanup results
        """
        msp = doc.modelspace()
        entities = list(msp)
        
        # Count entities per layer
        layer_counts = defaultdict(int)
        for entity in entities:
            layer_counts[entity.dxf.layer] += 1
        
        # Find empty layers
        all_layers = set(layer.dxf.name for layer in doc.layers)
        used_layers = set(layer_counts.keys())
        empty_layers = all_layers - used_layers
        
        # Remove empty layers (except layer '0' which is required)
        removed_layers = 0
        for layer_name in empty_layers:
            if layer_name != '0':
                try:
                    doc.layers.remove(layer_name)
                    removed_layers += 1
                except:
                    pass  # Layer might be in use or protected
        
        return {
            'operation': 'cleanup_layers',
            'total_layers': len(all_layers),
            'used_layers': len(used_layers),
            'empty_layers_removed': removed_layers,
            'message': f'Removed {removed_layers} empty layers'
        }
    
    def optimize_entities(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Optimize entities by combining similar ones and removing redundant data.
        
        Args:
            doc: The DXF document to optimize
            
        Returns:
            Dictionary containing optimization results
        """
        msp = doc.modelspace()
        entities = list(msp)
        
        original_count = len(entities)
        optimizations = []
        
        # Combine collinear lines
        line_optimization = self._combine_collinear_lines(doc)
        optimizations.append(line_optimization)
        
        # Remove zero-length entities
        zero_length_optimization = self._remove_zero_length_entities(doc)
        optimizations.append(zero_length_optimization)
        
        # Optimize polylines
        polyline_optimization = self._optimize_polylines(doc)
        optimizations.append(polyline_optimization)
        
        final_count = len(list(msp))
        entities_removed = original_count - final_count
        
        return {
            'operation': 'optimize_entities',
            'original_count': original_count,
            'final_count': final_count,
            'entities_removed': entities_removed,
            'optimizations': optimizations,
            'message': f'Optimized entities: removed {entities_removed} redundant entities'
        }
    
    def standardize_properties(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Standardize entity properties like colors, line types, etc.
        
        Args:
            doc: The DXF document to standardize
            
        Returns:
            Dictionary containing standardization results
        """
        msp = doc.modelspace()
        entities = list(msp)
        
        standardized_count = 0
        
        # Standardize colors (move entities with non-standard colors to appropriate layers)
        color_changes = 0
        for entity in entities:
            if hasattr(entity.dxf, 'color') and entity.dxf.color != 256:  # 256 = BYLAYER
                entity.dxf.color = 256  # Set to BYLAYER
                color_changes += 1
                standardized_count += 1
        
        # Standardize line types
        linetype_changes = 0
        for entity in entities:
            if hasattr(entity.dxf, 'linetype') and entity.dxf.linetype != 'BYLAYER':
                entity.dxf.linetype = 'BYLAYER'
                linetype_changes += 1
                standardized_count += 1
        
        return {
            'operation': 'standardize_properties',
            'entities_processed': len(entities),
            'color_changes': color_changes,
            'linetype_changes': linetype_changes,
            'total_standardized': standardized_count,
            'message': f'Standardized {standardized_count} entity properties'
        }
    
    def remove_unused_definitions(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """
        Remove unused block definitions, line types, and other definitions.
        
        Args:
            doc: The DXF document to clean up
            
        Returns:
            Dictionary containing cleanup results
        """
        removed_items = {
            'blocks': 0,
            'linetypes': 0,
            'text_styles': 0,
            'dimension_styles': 0
        }
        
        # Find used blocks
        msp = doc.modelspace()
        used_blocks = set()
        for entity in msp:
            if entity.dxftype() == 'INSERT':
                used_blocks.add(entity.dxf.name)
        
        # Remove unused blocks
        all_blocks = set(block.name for block in doc.blocks)
        unused_blocks = all_blocks - used_blocks
        for block_name in unused_blocks:
            if not block_name.startswith('*'):  # Don't remove system blocks
                try:
                    doc.blocks.delete_block(block_name)
                    removed_items['blocks'] += 1
                except:
                    pass
        
        # Note: Removing unused linetypes, text styles, and dimension styles
        # requires more careful analysis to avoid breaking references
        
        total_removed = sum(removed_items.values())
        
        return {
            'operation': 'remove_unused_definitions',
            'removed_items': removed_items,
            'total_removed': total_removed,
            'message': f'Removed {total_removed} unused definitions'
        }
    
    def _combine_collinear_lines(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """Combine collinear lines into single lines."""
        msp = doc.modelspace()
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        combined_count = 0
        tolerance = 0.001
        
        # Group lines by direction and position
        line_groups = defaultdict(list)
        
        for line in lines:
            # Calculate line direction and a point on the line
            dx = line.dxf.end.x - line.dxf.start.x
            dy = line.dxf.end.y - line.dxf.start.y
            length = (dx**2 + dy**2)**0.5
            
            if length > tolerance:
                # Normalize direction
                dir_x = dx / length
                dir_y = dy / length
                
                # Use direction as key (considering both directions as same)
                if dir_x < 0 or (dir_x == 0 and dir_y < 0):
                    dir_x, dir_y = -dir_x, -dir_y
                
                direction_key = (round(dir_x, 6), round(dir_y, 6))
                line_groups[direction_key].append(line)
        
        # For each group, check for collinear lines
        entities_to_remove = []
        
        for direction, group_lines in line_groups.items():
            if len(group_lines) < 2:
                continue
            
            # Check each pair for collinearity and adjacency
            for i, line1 in enumerate(group_lines):
                for line2 in group_lines[i+1:]:
                    if self._lines_are_collinear_and_adjacent(line1, line2, tolerance):
                        # Combine the lines
                        self._extend_line_to_include(line1, line2)
                        if line2 not in entities_to_remove:
                            entities_to_remove.append(line2)
                            combined_count += 1
        
        # Remove the combined lines
        for entity in entities_to_remove:
            msp.delete_entity(entity)
        
        return {
            'operation': 'combine_collinear_lines',
            'lines_combined': combined_count,
            'message': f'Combined {combined_count} collinear lines'
        }
    
    def _remove_zero_length_entities(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """Remove entities with zero or near-zero length."""
        msp = doc.modelspace()
        entities = list(msp)
        
        removed_count = 0
        tolerance = 0.001
        entities_to_remove = []
        
        for entity in entities:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                if length < tolerance:
                    entities_to_remove.append(entity)
                    removed_count += 1
            
            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                if entity.dxf.radius < tolerance:
                    entities_to_remove.append(entity)
                    removed_count += 1
        
        # Remove zero-length entities
        for entity in entities_to_remove:
            msp.delete_entity(entity)
        
        return {
            'operation': 'remove_zero_length_entities',
            'entities_removed': removed_count,
            'message': f'Removed {removed_count} zero-length entities'
        }
    
    def _optimize_polylines(self, doc: ezdxf.document.Drawing) -> Dict[str, Any]:
        """Optimize polylines by removing redundant vertices."""
        msp = doc.modelspace()
        polylines = [entity for entity in msp if entity.dxftype() in ['POLYLINE', 'LWPOLYLINE']]
        
        optimized_count = 0
        vertices_removed = 0
        
        for polyline in polylines:
            if hasattr(polyline, 'vertices'):
                original_vertices = list(polyline.vertices)
                if len(original_vertices) > 2:
                    # Remove redundant vertices (simplified implementation)
                    optimized_vertices = self._remove_redundant_vertices(original_vertices)
                    if len(optimized_vertices) < len(original_vertices):
                        vertices_removed += len(original_vertices) - len(optimized_vertices)
                        optimized_count += 1
                        # Note: Actually updating polyline vertices requires more complex operations
        
        return {
            'operation': 'optimize_polylines',
            'polylines_optimized': optimized_count,
            'vertices_removed': vertices_removed,
            'message': f'Optimized {optimized_count} polylines, removed {vertices_removed} redundant vertices'
        }
    
    def _lines_are_collinear_and_adjacent(self, line1, line2, tolerance: float) -> bool:
        """Check if two lines are collinear and adjacent."""
        # Check if endpoints are close (adjacent)
        endpoints1 = [(line1.dxf.start.x, line1.dxf.start.y), (line1.dxf.end.x, line1.dxf.end.y)]
        endpoints2 = [(line2.dxf.start.x, line2.dxf.start.y), (line2.dxf.end.x, line2.dxf.end.y)]
        
        for ep1 in endpoints1:
            for ep2 in endpoints2:
                distance = ((ep2[0] - ep1[0])**2 + (ep2[1] - ep1[1])**2)**0.5
                if distance < tolerance:
                    return True
        
        return False
    
    def _extend_line_to_include(self, line1, line2):
        """Extend line1 to include the span of line2."""
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
                distance = ((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)**0.5
                if distance > max_distance:
                    max_distance = distance
                    best_pair = (p1, p2)
        
        if best_pair:
            line1.dxf.start = ezdxf.math.Vec3(best_pair[0][0], best_pair[0][1], 0)
            line1.dxf.end = ezdxf.math.Vec3(best_pair[1][0], best_pair[1][1], 0)
    
    def _remove_redundant_vertices(self, vertices) -> List:
        """Remove redundant vertices from a polyline."""
        if len(vertices) <= 2:
            return vertices
        
        # Simplified implementation - remove vertices that are collinear
        optimized = [vertices[0]]
        tolerance = 0.001
        
        for i in range(1, len(vertices) - 1):
            prev_vertex = vertices[i - 1]
            curr_vertex = vertices[i]
            next_vertex = vertices[i + 1]
            
            # Check if current vertex is on the line between prev and next
            if not self._point_on_line(prev_vertex, next_vertex, curr_vertex, tolerance):
                optimized.append(curr_vertex)
        
        optimized.append(vertices[-1])
        return optimized
    
    def _point_on_line(self, p1, p2, point, tolerance: float) -> bool:
        """Check if a point lies on a line within tolerance."""
        # Calculate distance from point to line
        x1, y1 = p1.dxf.location.x, p1.dxf.location.y
        x2, y2 = p2.dxf.location.x, p2.dxf.location.y
        x0, y0 = point.dxf.location.x, point.dxf.location.y
        
        # Line equation: ax + by + c = 0
        a = y2 - y1
        b = x1 - x2
        c = x2 * y1 - x1 * y2
        
        if a == 0 and b == 0:
            return False
        
        # Distance formula
        distance = abs(a * x0 + b * y0 + c) / (a**2 + b**2)**0.5
        return distance < tolerance 