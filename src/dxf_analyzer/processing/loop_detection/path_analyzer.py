"""
Path Analyzer for DXF Files

Analyzes paths and connectivity patterns in DXF files.
"""

import ezdxf
from typing import Dict, List, Any, Tuple, Set
import math
from collections import defaultdict


class PathAnalyzer:
    """Analyzes paths and connectivity in DXF files."""
    
    def __init__(self):
        """Initialize the path analyzer."""
        self.tolerance = 0.001
        self.current_doc = None
        self.entities = []
        
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
    
    def analyze_connectivity(self) -> Dict[str, Any]:
        """
        Analyze the connectivity of entities in the DXF file.
        
        Returns:
            Dictionary containing connectivity analysis
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        # Build connectivity graph
        graph = self._build_connectivity_graph()
        
        # Analyze connected components
        components = self._find_connected_components(graph)
        
        # Analyze endpoints
        endpoints_analysis = self._analyze_endpoints()
        
        # Find open paths
        open_paths = self._find_open_paths(graph)
        
        return {
            'total_entities': len(self.entities),
            'connected_components': len(components),
            'largest_component_size': max(len(comp) for comp in components) if components else 0,
            'isolated_entities': len([comp for comp in components if len(comp) == 1]),
            'open_paths': len(open_paths),
            'endpoints': endpoints_analysis,
            'connectivity_ratio': self._calculate_connectivity_ratio(graph)
        }
    
    def find_open_paths(self) -> List[Dict[str, Any]]:
        """
        Find all open paths (non-closed sequences of connected entities).
        
        Returns:
            List of open path information
        """
        graph = self._build_connectivity_graph()
        open_paths = []
        
        # Find entities with degree 1 (endpoints)
        endpoints = [entity for entity, neighbors in graph.items() if len(neighbors) == 1]
        
        visited = set()
        
        for endpoint in endpoints:
            if endpoint not in visited:
                path = self._trace_path_from_endpoint(endpoint, graph, visited)
                if len(path) > 1:
                    path_info = {
                        'entities': len(path),
                        'length': self._calculate_path_length(path),
                        'start_point': self._get_entity_endpoint(path[0], True),
                        'end_point': self._get_entity_endpoint(path[-1], False),
                        'entity_types': self._get_path_entity_types(path)
                    }
                    open_paths.append(path_info)
        
        return open_paths
    
    def find_branching_points(self) -> List[Dict[str, Any]]:
        """
        Find branching points (entities connected to more than 2 others).
        
        Returns:
            List of branching point information
        """
        graph = self._build_connectivity_graph()
        branching_points = []
        
        for entity, neighbors in graph.items():
            if len(neighbors) > 2:
                # This is a branching point
                branch_info = {
                    'entity_type': entity.dxftype(),
                    'connections': len(neighbors),
                    'connected_entity_types': [neighbor.dxftype() for neighbor in neighbors],
                    'position': self._get_entity_center(entity)
                }
                branching_points.append(branch_info)
        
        return branching_points
    
    def analyze_path_complexity(self) -> Dict[str, Any]:
        """
        Analyze the complexity of paths in the DXF file.
        
        Returns:
            Dictionary containing path complexity metrics
        """
        graph = self._build_connectivity_graph()
        components = self._find_connected_components(graph)
        
        complexity_metrics = {
            'total_components': len(components),
            'component_sizes': [len(comp) for comp in components],
            'branching_points': len(self.find_branching_points()),
            'open_paths': len(self.find_open_paths()),
            'complexity_score': 0
        }
        
        # Calculate complexity score
        score = 0
        score += len(components) * 10  # More components = more complex
        score += complexity_metrics['branching_points'] * 20  # Branching adds complexity
        score += complexity_metrics['open_paths'] * 5  # Open paths add some complexity
        
        # Add complexity based on entity types
        entity_type_weights = {
            'LINE': 1,
            'ARC': 3,
            'CIRCLE': 2,
            'SPLINE': 5,
            'POLYLINE': 4,
            'LWPOLYLINE': 4
        }
        
        for entity in self.entities:
            score += entity_type_weights.get(entity.dxftype(), 1)
        
        complexity_metrics['complexity_score'] = score
        complexity_metrics['complexity_level'] = self._classify_complexity(score)
        
        return complexity_metrics
    
    def _build_connectivity_graph(self) -> Dict:
        """Build a connectivity graph from DXF entities."""
        graph = defaultdict(list)
        
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
                # Circles are self-connected
                center = (entity.dxf.center.x, entity.dxf.center.y)
                endpoints[entity] = (center, center)
        
        # Build connectivity graph
        entities_list = list(endpoints.keys())
        for i, entity1 in enumerate(entities_list):
            for entity2 in entities_list[i+1:]:
                if self._entities_connected(endpoints[entity1], endpoints[entity2]):
                    graph[entity1].append(entity2)
                    graph[entity2].append(entity1)
        
        return graph
    
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
    
    def _find_connected_components(self, graph: Dict) -> List[List]:
        """Find all connected components in the graph."""
        visited = set()
        components = []
        
        for entity in graph:
            if entity not in visited:
                component = []
                self._dfs_component(entity, graph, visited, component)
                components.append(component)
        
        return components
    
    def _dfs_component(self, entity, graph: Dict, visited: Set, component: List):
        """Depth-first search to find connected component."""
        visited.add(entity)
        component.append(entity)
        
        for neighbor in graph[entity]:
            if neighbor not in visited:
                self._dfs_component(neighbor, graph, visited, component)
    
    def _analyze_endpoints(self) -> Dict[str, Any]:
        """Analyze endpoints in the DXF file."""
        endpoints = []
        
        for entity in self.entities:
            if entity.dxftype() == 'LINE':
                start = (entity.dxf.start.x, entity.dxf.start.y)
                end = (entity.dxf.end.x, entity.dxf.end.y)
                endpoints.extend([start, end])
            
            elif entity.dxftype() == 'ARC':
                start = self._get_arc_start_point(entity)
                end = self._get_arc_end_point(entity)
                endpoints.extend([start, end])
        
        # Count unique endpoints
        unique_endpoints = []
        for point in endpoints:
            is_unique = True
            for unique_point in unique_endpoints:
                if self._points_close(point, unique_point):
                    is_unique = False
                    break
            if is_unique:
                unique_endpoints.append(point)
        
        # Count endpoint degrees (how many entities connect to each endpoint)
        endpoint_degrees = defaultdict(int)
        for point in endpoints:
            for unique_point in unique_endpoints:
                if self._points_close(point, unique_point):
                    endpoint_degrees[unique_point] += 1
                    break
        
        return {
            'total_endpoints': len(endpoints),
            'unique_endpoints': len(unique_endpoints),
            'isolated_endpoints': len([deg for deg in endpoint_degrees.values() if deg == 1]),
            'connected_endpoints': len([deg for deg in endpoint_degrees.values() if deg > 1]),
            'max_connections_at_point': max(endpoint_degrees.values()) if endpoint_degrees else 0
        }
    
    def _find_open_paths(self, graph: Dict) -> List[List]:
        """Find open paths in the graph."""
        # Find entities with degree 1 (endpoints)
        endpoints = [entity for entity, neighbors in graph.items() if len(neighbors) == 1]
        
        open_paths = []
        visited = set()
        
        for endpoint in endpoints:
            if endpoint not in visited:
                path = self._trace_path_from_endpoint(endpoint, graph, visited)
                if len(path) > 1:
                    open_paths.append(path)
        
        return open_paths
    
    def _trace_path_from_endpoint(self, start_entity, graph: Dict, visited: Set) -> List:
        """Trace a path from an endpoint entity."""
        path = [start_entity]
        visited.add(start_entity)
        current = start_entity
        
        while True:
            # Find unvisited neighbors
            unvisited_neighbors = [n for n in graph[current] if n not in visited]
            
            if not unvisited_neighbors:
                break
            
            # If there's only one unvisited neighbor, continue the path
            if len(unvisited_neighbors) == 1:
                next_entity = unvisited_neighbors[0]
                path.append(next_entity)
                visited.add(next_entity)
                current = next_entity
            else:
                # Multiple unvisited neighbors - this is a branching point
                break
        
        return path
    
    def _calculate_connectivity_ratio(self, graph: Dict) -> float:
        """Calculate the connectivity ratio of the graph."""
        if not graph:
            return 0.0
        
        total_possible_connections = len(graph) * (len(graph) - 1) / 2
        actual_connections = sum(len(neighbors) for neighbors in graph.values()) / 2
        
        return actual_connections / total_possible_connections if total_possible_connections > 0 else 0.0
    
    def _calculate_path_length(self, path: List) -> float:
        """Calculate the total length of a path."""
        total_length = 0.0
        
        for entity in path:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                total_length += length
            
            elif entity.dxftype() == 'ARC':
                radius = entity.dxf.radius
                start_angle = math.radians(entity.dxf.start_angle)
                end_angle = math.radians(entity.dxf.end_angle)
                angle_diff = end_angle - start_angle
                if angle_diff < 0:
                    angle_diff += 2 * math.pi
                arc_length = radius * angle_diff
                total_length += arc_length
            
            elif entity.dxftype() == 'CIRCLE':
                radius = entity.dxf.radius
                circumference = 2 * math.pi * radius
                total_length += circumference
        
        return total_length
    
    def _get_entity_endpoint(self, entity, is_start: bool) -> Tuple[float, float]:
        """Get the start or end point of an entity."""
        if entity.dxftype() == 'LINE':
            if is_start:
                return (entity.dxf.start.x, entity.dxf.start.y)
            else:
                return (entity.dxf.end.x, entity.dxf.end.y)
        
        elif entity.dxftype() == 'ARC':
            if is_start:
                return self._get_arc_start_point(entity)
            else:
                return self._get_arc_end_point(entity)
        
        elif entity.dxftype() == 'CIRCLE':
            center = (entity.dxf.center.x, entity.dxf.center.y)
            return center
        
        return (0.0, 0.0)
    
    def _get_path_entity_types(self, path: List) -> Dict[str, int]:
        """Get the types of entities in a path."""
        entity_types = defaultdict(int)
        for entity in path:
            entity_types[entity.dxftype()] += 1
        return dict(entity_types)
    
    def _get_entity_center(self, entity) -> Tuple[float, float]:
        """Get the center point of an entity."""
        if entity.dxftype() == 'LINE':
            start = entity.dxf.start
            end = entity.dxf.end
            return ((start.x + end.x) / 2, (start.y + end.y) / 2)
        
        elif entity.dxftype() in ['CIRCLE', 'ARC']:
            center = entity.dxf.center
            return (center.x, center.y)
        
        return (0.0, 0.0)
    
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
    
    def _classify_complexity(self, score: int) -> str:
        """Classify complexity level based on score."""
        if score < 100:
            return 'Simple'
        elif score < 300:
            return 'Moderate'
        elif score < 600:
            return 'Complex'
        else:
            return 'Very Complex'
    
    def set_tolerance(self, tolerance: float):
        """Set the tolerance for point matching."""
        self.tolerance = max(tolerance, 0.0001)
    
    def get_tolerance(self) -> float:
        """Get the current tolerance."""
        return self.tolerance 