import ezdxf
from typing import Dict, List, Any, Tuple, Set
import math
from collections import defaultdict, deque
import networkx as nx
from shapely.geometry import Polygon
from tkinter import filedialog
import matplotlib.pyplot as plt
import random

class LoopDetector:
 
    def extract_edges_from_dxf(self, decimal_precision=4):
        doc = self.current_doc
        msp = doc.modelspace()
        edges = []

        def rounded_point(x, y):
            return (round(x, decimal_precision), round(y, decimal_precision))

        for e in msp:
            if e.dxftype() == "LINE":
                start = rounded_point(e.dxf.start.x, e.dxf.start.y)
                end = rounded_point(e.dxf.end.x, e.dxf.end.y)
                edges.append((start, end))

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
                    edges.append((arc_points[i], arc_points[i + 1]))

        return edges

    def build_graph(self, edges):
        G = nx.Graph()
        for start, end in edges:
            G.add_edge(start, end)
        return G

    def extract_loops(self, G):
        cycles = nx.cycle_basis(G)
        polygons = []
        for cycle in cycles:
            if len(cycle) >= 3:
                polygon = Polygon(cycle)
                if polygon.is_valid and abs(polygon.area) > 5:  # ⬅️ Ignore tiny loops
                    polygons.append(polygon)
        return polygons

    def classify_profile(self, polygons):
        return "Solid" if len(polygons) == 1 else "Hollow"

    def plot_loops(self, polygons):
        fig, ax = plt.subplots()
        loop_info = []
        colors = ['green', 'blue', 'magenta', 'cyan', 'orange']

        sorted_polygons = sorted(polygons, key=lambda p: abs(p.area), reverse=True)

        for idx, poly in enumerate(sorted_polygons):
            x, y = poly.exterior.xy
            color = 'red' if idx == 0 else random.choice(colors)
            ax.plot(x, y, color=color, linewidth=2)
            loop_info.append(f"Loop {idx + 1}: Area = {abs(poly.area):.2f} mm²")

        profile_type = self.classify_profile(polygons)
        ax.set_title(f"Profile Type: {profile_type}\n" + "\n".join(loop_info), fontsize=10)
        ax.set_aspect('equal')
        ax.set_facecolor('black')
        plt.show()

    def run_visualizer(self):
        edges = self.extract_edges_from_dxf()
        G = self.build_graph(edges)
        polygons = self.extract_loops(G)
        if polygons:
            self.plot_loops(polygons)
            return len(polygons)
        else:
            return 0
    
    def classify_profile(self, polygons):
        return "Solid" if len(polygons) == 1 else "Hollow"

    def __init__(self):
        """Initialize the loop detector."""
        self.tolerance = 0.001
        self.current_doc = None
        self.entities = []
        self.graph = None
        
    def set_document(self, doc: ezdxf.document.Drawing):
        """
        Set the DXF document to analyze.
        
        Args:
            doc: The ezdxf document
        """
        self.current_doc = doc
        if doc:
            msp = doc.modelspace()
            self.entities = list(msp)
            self._build_connectivity_graph()
    
    def detect_loops(self) -> Dict[str, Any]:
        """
        Detect all loops in the DXF file.
        
        Returns:
            Dictionary containing detected loops and analysis
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        loops = self._find_all_loops()
        
        # Analyze the loops
        loop_analysis = {
            'total_loops': len(loops),
            'loops': [],
            'statistics': self._analyze_loops(loops)
        }
        
        for i, loop in enumerate(loops):
            loop_info = {
                'id': i + 1,
                'entities': len(loop),
                'entity_types': self._get_loop_entity_types(loop),
                'perimeter': self._calculate_loop_perimeter(loop),
                'area': self._calculate_loop_area(loop),
                'is_clockwise': self._is_clockwise(loop),
                'bounding_box': self._get_loop_bounding_box(loop)
            }
            loop_analysis['loops'].append(loop_info)
        
        return loop_analysis
    
    def find_largest_loop(self) -> Dict[str, Any]:
        """
        Find the largest loop by area.
        
        Returns:
            Dictionary containing information about the largest loop
        """
        loops = self._find_all_loops()
        
        if not loops:
            return {'error': 'No loops found'}
        
        largest_loop = None
        largest_area = 0
        
        for loop in loops:
            area = self._calculate_loop_area(loop)
            if area > largest_area:
                largest_area = area
                largest_loop = loop
        
        if largest_loop:
            return {
                'entities': len(largest_loop),
                'area': largest_area,
                'perimeter': self._calculate_loop_perimeter(largest_loop),
                'entity_types': self._get_loop_entity_types(largest_loop),
                'loop_entities': largest_loop
            }
        
        return {'error': 'No valid loops found'}
    
    def find_nested_loops(self) -> Dict[str, Any]:
        """
        Find nested loops (loops inside other loops).
        
        Returns:
            Dictionary containing nested loop information
        """
        loops = self._find_all_loops()
        
        if len(loops) < 2:
            return {'nested_loops': [], 'total_nested': 0}
        
        nested_relationships = []
        
        for i, outer_loop in enumerate(loops):
            for j, inner_loop in enumerate(loops):
                if i != j and self._is_loop_inside_loop(inner_loop, outer_loop):
                    nested_relationships.append({
                        'outer_loop_id': i,
                        'inner_loop_id': j,
                        'outer_area': self._calculate_loop_area(outer_loop),
                        'inner_area': self._calculate_loop_area(inner_loop)
                    })
        
        return {
            'nested_loops': nested_relationships,
            'total_nested': len(nested_relationships)
        }
    
    def _build_connectivity_graph(self):
        """Build a connectivity graph from DXF entities."""
        self.graph = defaultdict(list)
        
        # Extract endpoints from entities
        endpoints = {}  # entity -> (start_point, end_point)
        
        for entity in self.entities:
            if entity.dxftype() == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                endpoints[entity] = (start, end)
            
            elif entity.dxftype() == 'ARC':
                start = self._get_arc_start_point(entity)
                end = self._get_arc_end_point(entity)
                endpoints[entity] = (start, end)
            
            elif entity.dxftype() == 'CIRCLE':
                # Circles are self-connected (form a loop by themselves)
                center = (entity.dxf.center.x, entity.dxf.center.y)
                endpoints[entity] = (center, center)
        
        # Build connectivity graph
        entities_list = list(endpoints.keys())
        for i, entity1 in enumerate(entities_list):
            for entity2 in entities_list[i+1:]:
                if self._entities_connected(endpoints[entity1], endpoints[entity2]):
                    self.graph[entity1].append(entity2)
                    self.graph[entity2].append(entity1)
    
    def _entities_connected(self, endpoints1: Tuple, endpoints2: Tuple) -> bool:
        """Check if two entities are connected at their endpoints."""
        start1, end1 = endpoints1
        start2, end2 = endpoints2
        
        # Check all possible connections
        connections = [
            self._points_close(start1, start2),
            self._points_close(start1, end2),
            self._points_close(end1, start2),
            self._points_close(end1, end2)
        ]
        
        return any(connections)
    
    def _points_close(self, p1: Tuple[float, float], p2: Tuple[float, float]) -> bool:
        """Check if two points are close within tolerance."""
        distance = math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
        return distance < self.tolerance
    
    def _find_all_loops(self) -> List[List]:
        """Find all loops using depth-first search."""
        if not self.graph:
            return []
        
        visited_edges = set()
        loops = []
        
        for start_entity in self.graph:
            for neighbor in self.graph[start_entity]:
                edge = tuple(sorted([id(start_entity), id(neighbor)]))
                if edge not in visited_edges:
                    visited_edges.add(edge)
                    
                    # Try to find a loop starting from this edge
                    loop = self._find_loop_from_edge(start_entity, neighbor, visited_edges)
                    if loop and len(loop) >= 3:  # Minimum loop size
                        loops.append(loop)
        
        return loops
    
    def _find_loop_from_edge(self, start_entity, current_entity, visited_edges: Set) -> List:
        """Find a loop starting from a specific edge using DFS."""
        path = [start_entity, current_entity]
        visited_in_path = {start_entity, current_entity}
        
        def dfs(entity):
            for neighbor in self.graph[entity]:
                if neighbor == start_entity and len(path) >= 3:
                    # Found a loop back to start
                    return path + [neighbor]
                
                if neighbor not in visited_in_path:
                    edge = tuple(sorted([id(entity), id(neighbor)]))
                    if edge not in visited_edges:
                        visited_edges.add(edge)
                        path.append(neighbor)
                        visited_in_path.add(neighbor)
                        
                        result = dfs(neighbor)
                        if result:
                            return result
                        
                        # Backtrack
                        path.pop()
                        visited_in_path.remove(neighbor)
                        visited_edges.remove(edge)
            
            return None
        
        return dfs(current_entity)
    
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
    
    def _analyze_loops(self, loops: List[List]) -> Dict[str, Any]:
        """Analyze the detected loops and provide statistics."""
        if not loops:
            return {}
        
        areas = [self._calculate_loop_area(loop) for loop in loops]
        perimeters = [self._calculate_loop_perimeter(loop) for loop in loops]
        entity_counts = [len(loop) for loop in loops]
        
        return {
            'total_area': sum(areas),
            'average_area': sum(areas) / len(areas),
            'largest_area': max(areas),
            'smallest_area': min(areas),
            'average_perimeter': sum(perimeters) / len(perimeters),
            'average_entities_per_loop': sum(entity_counts) / len(entity_counts),
            'most_complex_loop': max(entity_counts),
            'simplest_loop': min(entity_counts)
        }
    
    def _get_loop_entity_types(self, loop: List) -> Dict[str, int]:
        """Get the types of entities in a loop."""
        entity_types = defaultdict(int)
        for entity in loop[:-1]:  # Exclude the duplicate start entity
            entity_types[entity.dxftype()] += 1
        return dict(entity_types)
    
    def _calculate_loop_perimeter(self, loop: List) -> float:
        """Calculate the perimeter of a loop."""
        perimeter = 0.0
        
        for entity in loop[:-1]:  # Exclude the duplicate start entity
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                perimeter += length
            
            elif entity.dxftype() == 'ARC':
                radius = entity.dxf.radius
                start_angle = math.radians(entity.dxf.start_angle)
                end_angle = math.radians(entity.dxf.end_angle)
                angle_diff = end_angle - start_angle
                if angle_diff < 0:
                    angle_diff += 2 * math.pi
                arc_length = radius * angle_diff
                perimeter += arc_length
            
            elif entity.dxftype() == 'CIRCLE':
                radius = entity.dxf.radius
                circumference = 2 * math.pi * radius
                perimeter += circumference
        
        return perimeter
    
    def _calculate_loop_area(self, loop: List) -> float:
        """Calculate the area of a loop using the shoelace formula."""
        # This is a simplified implementation
        # For complex loops with arcs and circles, more sophisticated methods are needed
        
        points = []
        for entity in loop[:-1]:  # Exclude the duplicate start entity
            if entity.dxftype() == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                points.extend([start, end])
            elif entity.dxftype() == 'CIRCLE':
                radius = entity.dxf.radius
                return math.pi * radius**2
        
        if len(points) < 3:
            return 0.0
        
        # Remove duplicate consecutive points
        unique_points = [points[0]]
        for point in points[1:]:
            if not self._points_close(point, unique_points[-1]):
                unique_points.append(point)
        
        if len(unique_points) < 3:
            return 0.0
        
        # Shoelace formula
        area = 0.0
        n = len(unique_points)
        for i in range(n):
            j = (i + 1) % n
            area += unique_points[i][0] * unique_points[j][1]
            area -= unique_points[j][0] * unique_points[i][1]
        
        return abs(area) / 2.0
    
    def _is_clockwise(self, loop: List) -> bool:
        """Determine if a loop is oriented clockwise."""
        # Calculate signed area
        points = []
        for entity in loop[:-1]:
            if entity.dxftype() == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                points.append(start)
        
        if len(points) < 3:
            return False
        
        signed_area = 0.0
        n = len(points)
        for i in range(n):
            j = (i + 1) % n
            signed_area += (points[j][0] - points[i][0]) * (points[j][1] + points[i][1])
        
        return signed_area > 0
    
    def _get_loop_bounding_box(self, loop: List) -> Dict[str, float]:
        """Get the bounding box of a loop."""
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for entity in loop[:-1]:
            if entity.dxftype() == 'LINE':
                points = [(entity.dxf.start.x, entity.dxf.start.y),
                         (entity.dxf.end.x, entity.dxf.end.y)]
                for x, y in points:
                    min_x = min(min_x, x)
                    max_x = max(max_x, x)
                    min_y = min(min_y, y)
                    max_y = max(max_y, y)
            
            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                center = entity.dxf.center
                radius = entity.dxf.radius
                min_x = min(min_x, center.x - radius)
                max_x = max(max_x, center.x + radius)
                min_y = min(min_y, center.y - radius)
                max_y = max(max_y, center.y + radius)
        
        return {
            'min_x': min_x,
            'min_y': min_y,
            'max_x': max_x,
            'max_y': max_y,
            'width': max_x - min_x,
            'height': max_y - min_y
        }
    
    def _is_loop_inside_loop(self, inner_loop: List, outer_loop: List) -> bool:
        """Check if one loop is inside another loop."""
        # Simplified implementation using bounding box check
        inner_bbox = self._get_loop_bounding_box(inner_loop)
        outer_bbox = self._get_loop_bounding_box(outer_loop)
        
        return (inner_bbox['min_x'] >= outer_bbox['min_x'] and
                inner_bbox['max_x'] <= outer_bbox['max_x'] and
                inner_bbox['min_y'] >= outer_bbox['min_y'] and
                inner_bbox['max_y'] <= outer_bbox['max_y'])
    
    def set_tolerance(self, tolerance: float):
        """Set the tolerance for point matching."""
        self.tolerance = max(tolerance, 0.0001)
    
    def get_tolerance(self) -> float:
        """Get the current tolerance."""
        return self.tolerance 