import ezdxf
from scipy.spatial import KDTree
import numpy as np
from ezdxf.entities import DXFEntity
from typing import List, Tuple, Optional, Set
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EndpointInfo:
    """Store endpoint information with entity reference."""
    point: Tuple[float, float]
    entity: DXFEntity
    is_start: bool
    index: int

class DXFCorrector:
    """Enhanced DXF document corrector with improved gap detection and connection."""
    
    def __init__(self, tolerance: float = 0.001, precision: int = 15):
        """
        Initialize the DXF corrector.
        
        Args:
            tolerance: Default tolerance for geometric operations
            precision: Decimal precision for coordinate rounding
        """
        self.current_doc: Optional[ezdxf.document.Drawing] = None
        self.corrections_applied: List[str] = []
        self.tolerance = tolerance
        self.precision = precision
        self._original_entities: Set[DXFEntity] = set()
        
    def load_document(self, doc: ezdxf.document.Drawing) -> None:
        """
        Load a DXF document for correction.
        
        Args:
            doc: The ezdxf document to correct
        """
        if not doc:
            raise ValueError("Document cannot be None")
            
        self.current_doc = doc
        self.corrections_applied.clear()
        self._original_entities = set(doc.modelspace())
        logger.info(f"Loaded DXF document with {len(self._original_entities)} entities")
        
    def _round_point(self, x: float, y: float) -> Tuple[float, float]:
        """Round coordinates to specified precision."""
        return round(x, self.precision), round(y, self.precision)
    
    def _calculate_arc_endpoints(self, center: Tuple[float, float], radius: float, 
                               start_angle: float, end_angle: float) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Calculate start and end points of an arc."""
        center_x, center_y = center
        
        start_x = center_x + radius * np.cos(np.radians(start_angle))
        start_y = center_y + radius * np.sin(np.radians(start_angle))
        end_x = center_x + radius * np.cos(np.radians(end_angle))
        end_y = center_y + radius * np.sin(np.radians(end_angle))
        
        return (self._round_point(start_x, start_y), 
                self._round_point(end_x, end_y))
    
    def _extract_endpoints(self) -> List[EndpointInfo]:
        """
        Extract all endpoints from supported entities.
        
        Returns:
            List of endpoint information
        """
        if not self.current_doc:
            raise ValueError("No document loaded")
            
        endpoints = []
        
        for idx, entity in enumerate(self.current_doc.modelspace()):
            if entity.dxftype() == "LINE":
                start_point = self._round_point(entity.dxf.start.x, entity.dxf.start.y)
                end_point = self._round_point(entity.dxf.end.x, entity.dxf.end.y)
                
                endpoints.append(EndpointInfo(start_point, entity, True, idx))
                endpoints.append(EndpointInfo(end_point, entity, False, idx))
                
            elif entity.dxftype() == "ARC":
                center = self._round_point(entity.dxf.center.x, entity.dxf.center.y)
                radius = round(entity.dxf.radius, self.precision)
                start_angle = round(entity.dxf.start_angle, self.precision)
                end_angle = round(entity.dxf.end_angle, self.precision)
                
                start_point, end_point = self._calculate_arc_endpoints(
                    center, radius, start_angle, end_angle
                )
                
                endpoints.append(EndpointInfo(start_point, entity, True, idx))
                endpoints.append(EndpointInfo(end_point, entity, False, idx))
                
            elif entity.dxftype() == "POLYLINE":
                vertices = list(entity.vertices)
                if vertices:
                    start_point = self._round_point(vertices[0].dxf.location.x, vertices[0].dxf.location.y)
                    end_point = self._round_point(vertices[-1].dxf.location.x, vertices[-1].dxf.location.y)
                    
                    endpoints.append(EndpointInfo(start_point, entity, True, idx))
                    endpoints.append(EndpointInfo(end_point, entity, False, idx))
        
        logger.info(f"Extracted {len(endpoints)} endpoints from {len(self.current_doc.modelspace())} entities")
        return endpoints
    
    def _find_duplicate_points(self, endpoints: List[EndpointInfo]) -> Set[int]:
        """
        Find endpoints that are duplicates (same location).
        
        Args:
            endpoints: List of endpoint information
            
        Returns:
            Set of indices that are duplicates
        """
        point_map = {}
        duplicates = set()
        
        for i, endpoint in enumerate(endpoints):
            point = endpoint.point
            if point in point_map:
                duplicates.add(i)
                duplicates.add(point_map[point])
            else:
                point_map[point] = i
                
        return duplicates
    
    def connect_gaps_with_lines(self, max_distance: float = 0.01, 
                              avoid_duplicates: bool = True) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Find closest unmatched endpoints within max_distance and connect them.
        
        Args:
            max_distance: Maximum distance to connect gaps
            avoid_duplicates: Skip connections between duplicate points
            
        Returns:
            List of new line connections as (start_point, end_point) tuples
        """
        if not self.current_doc:
            raise ValueError("No document loaded")
            
        endpoints = self._extract_endpoints()
        if len(endpoints) < 2:
            logger.warning("Not enough endpoints to connect gaps")
            return []
        
        duplicates = self._find_duplicate_points(endpoints) if avoid_duplicates else set()
        
        points_array = np.array([ep.point for ep in endpoints])
        tree = KDTree(points_array)
        
        matched = set()
        new_lines = []
        
        for i, endpoint in enumerate(endpoints):
            if i in matched or i in duplicates:
                continue
                
            indices = tree.query_ball_point(endpoint.point, max_distance)
            
            best_match = None
            best_distance = float('inf')
            
            for j in indices:
                if (j != i and j not in matched and j not in duplicates and 
                    endpoints[j].entity != endpoint.entity):  # Avoid connecting same entity
                    
                    distance = np.linalg.norm(np.array(endpoint.point) - np.array(endpoints[j].point))
                    if 0 < distance < best_distance:
                        best_match = j
                        best_distance = distance
            
            if best_match is not None:
                connection = (endpoint.point, endpoints[best_match].point)
                new_lines.append(connection)
                matched.add(i)
                matched.add(best_match)
                
                self.current_doc.modelspace().add_line(
                    start=endpoint.point, 
                    end=endpoints[best_match].point
                )
                
                logger.info(f"Connected gap: {endpoint.point} -> {endpoints[best_match].point} "
                           f"(Distance: {best_distance:.6f})")
        
        correction_msg = f"Added {len(new_lines)} bridging lines (max distance: {max_distance})"
        self.corrections_applied.append(correction_msg)
        logger.info(f"✅ {correction_msg}")
        
        return new_lines
    
    def remove_duplicate_entities(self) -> int:
        """
        Remove duplicate entities based on geometric properties.
        
        Returns:
            Number of duplicates removed
        """
        if not self.current_doc:
            raise ValueError("No document loaded")
            
        entities = list(self.current_doc.modelspace())
        to_remove = set()
        
        for i, entity1 in enumerate(entities):
            if entity1 in to_remove:
                continue
                
            for j, entity2 in enumerate(entities[i+1:], i+1):
                if entity2 in to_remove:
                    continue
                    
                if self._are_entities_duplicate(entity1, entity2):
                    to_remove.add(entity2)
        
        for entity in to_remove:
            self.current_doc.modelspace().delete_entity(entity)
            
        removed_count = len(to_remove)
        if removed_count > 0:
            correction_msg = f"Removed {removed_count} duplicate entities"
            self.corrections_applied.append(correction_msg)
            logger.info(f"✅ {correction_msg}")
            
        return removed_count
    
    def _are_entities_duplicate(self, entity1: DXFEntity, entity2: DXFEntity) -> bool:
        """Check if two entities are duplicates based on their properties."""
        if entity1.dxftype() != entity2.dxftype():
            return False
            
        if entity1.dxftype() == "LINE":
            start1 = self._round_point(entity1.dxf.start.x, entity1.dxf.start.y)
            end1 = self._round_point(entity1.dxf.end.x, entity1.dxf.end.y)
            start2 = self._round_point(entity2.dxf.start.x, entity2.dxf.start.y)
            end2 = self._round_point(entity2.dxf.end.x, entity2.dxf.end.y)
            
            return ((start1 == start2 and end1 == end2) or 
                   (start1 == end2 and end1 == start2))
                   
        elif entity1.dxftype() == "ARC":
            center1 = self._round_point(entity1.dxf.center.x, entity1.dxf.center.y)
            center2 = self._round_point(entity2.dxf.center.x, entity2.dxf.center.y)
            
            return (center1 == center2 and 
                   round(entity1.dxf.radius, self.precision) == round(entity2.dxf.radius, self.precision) and
                   round(entity1.dxf.start_angle, self.precision) == round(entity2.dxf.start_angle, self.precision) and
                   round(entity1.dxf.end_angle, self.precision) == round(entity2.dxf.end_angle, self.precision))
        
        return False
    
    def get_correction_summary(self) -> str:
        """Get a summary of all corrections applied."""
        if not self.corrections_applied:
            return "No corrections applied."
            
        return "Corrections applied:\n" + "\n".join(f"• {correction}" for correction in self.corrections_applied)
    
    def validate_document(self) -> List[str]:
        """
        Validate the document and return list of potential issues.
        
        Returns:
            List of validation warnings/issues
        """
        if not self.current_doc:
            return ["No document loaded"]
            
        issues = []
        entities = list(self.current_doc.modelspace())
        
        if not entities:
            issues.append("Document contains no entities")
            
        for entity in entities:
            if entity.dxftype() == "LINE":
                length = np.linalg.norm(np.array([entity.dxf.end.x - entity.dxf.start.x, 
                                                entity.dxf.end.y - entity.dxf.start.y]))
                if length < self.tolerance:
                    issues.append(f"Very short line detected (length: {length:.6f})")
        
        return issues
