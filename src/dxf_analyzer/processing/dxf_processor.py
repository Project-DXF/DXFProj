"""
DXF file processing and analysis module.
"""

import ezdxf
from typing import Dict, List, Any, Optional
from pathlib import Path


class DXFProcessor:
    """Main class for processing DXF files and extracting information."""
    
    def __init__(self):
        """Initialize the DXF processor."""
        self.current_doc = None
        self.current_file = None
        
    def load_file(self, file_path: str) -> bool:
        """
        Load a DXF file for processing.
        
        Args:
            file_path: Path to the DXF file
            
        Returns:
            True if file loaded successfully, False otherwise
        """
        try:
            self.current_file = Path(file_path)
            self.current_doc = ezdxf.readfile(file_path)
            return True
        except Exception as e:
            print(f"Error loading DXF file: {e}")
            return False
            
    def get_entities(self) -> List[Any]:
        """
        Get all entities from the current DXF file.
        
        Returns:
            List of DXF entities
        """
        if not self.current_doc:
            return []
            
        msp = self.current_doc.modelspace()
        return list(msp)
        
    def get_entity_info(self) -> Dict[str, Any]:
        """
        Extract basic information about entities in the DXF file.
        
        Returns:
            Dictionary containing entity information
        """
        if not self.current_doc:
            return {}
            
        entities = self.get_entities()
        entity_counts = {}
        layers = set()
        
        for entity in entities:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            layers.add(entity.dxf.layer)
            
        return {
            'total_entities': len(entities),
            'entity_counts': entity_counts,
            'layers': list(layers),
            'file_info': {
                'name': self.current_file.name if self.current_file else None,
                'size': self.current_file.stat().st_size if self.current_file else None
            }
        }
        
    def get_dimensions(self) -> Dict[str, float]:
        """
        Calculate the dimensions of the drawing.
        
        Returns:
            Dictionary containing width, height, and bounding box info
        """
        if not self.current_doc:
            return {}
            
        try:
            msp = self.current_doc.modelspace()
            extents = msp.get_extents()
            
            if extents:
                return {
                    'width': extents.max.x - extents.min.x,
                    'height': extents.max.y - extents.min.y,
                    'min_x': extents.min.x,
                    'min_y': extents.min.y,
                    'max_x': extents.max.x,
                    'max_y': extents.max.y
                }
        except Exception as e:
            print(f"Error calculating dimensions: {e}")
            
        return {}
        
    def extract_profile_features(self) -> Dict[str, Any]:
        """
        Extract profile-specific features from the DXF file.
        
        Returns:
            Dictionary containing extracted features
        """
        # This is a placeholder for more advanced feature extraction
        # that would be implemented based on specific requirements
        
        info = self.get_entity_info()
        dimensions = self.get_dimensions()
        
        return {
            'basic_info': info,
            'dimensions': dimensions,
            'features': {
                'has_lines': 'LINE' in info.get('entity_counts', {}),
                'has_arcs': 'ARC' in info.get('entity_counts', {}),
                'has_circles': 'CIRCLE' in info.get('entity_counts', {}),
                'complexity_score': len(info.get('entity_counts', {}))
            }
        } 