"""
DXF Corrector

Main class for correcting DXF files, including fixing incomplete lines,
connecting segments, and other geometric corrections.
"""

import ezdxf
from typing import Dict, List, Any, Optional, Tuple
import math


class DXFCorrector:
    """Main class for correcting DXF files."""
    
    def __init__(self):
        """Initialize the DXF corrector."""
        self.current_doc = None
        self.corrections_applied = []
        self.tolerance = 0.001  # Default tolerance for geometric operations
        
    def load_document(self, doc: ezdxf.document.Drawing):
        """
        Load a DXF document for correction.
        
        Args:
            doc: The ezdxf document to correct
        """
        self.current_doc = doc
        self.corrections_applied = []
    
    def correct_dxf(self) -> Dict[str, Any]:
        """
        Apply all available corrections to the DXF file.
        
        Returns:
            Dictionary containing correction results
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        results = {
            'corrections_applied': [],
            'entities_modified': 0,
            'entities_added': 0,
            'entities_removed': 0
        }
        
        # Apply various corrections
        incomplete_lines_result = self.fix_incomplete_lines()
        results['corrections_applied'].append(incomplete_lines_result)
        results['entities_modified'] += incomplete_lines_result.get('entities_modified', 0)
        results['entities_added'] += incomplete_lines_result.get('entities_added', 0)
        
        duplicate_removal_result = self.remove_duplicates()
        results['corrections_applied'].append(duplicate_removal_result)
        results['entities_removed'] += duplicate_removal_result.get('entities_removed', 0)
        
        small_entities_result = self.remove_small_entities()
        results['corrections_applied'].append(small_entities_result)
        results['entities_removed'] += small_entities_result.get('entities_removed', 0)
        
        gap_filling_result = self.fill_small_gaps()
        results['corrections_applied'].append(gap_filling_result)
        results['entities_added'] += gap_filling_result.get('entities_added', 0)
        
        self.corrections_applied = results['corrections_applied']
        return results
    
    def fix_incomplete_lines(self) -> Dict[str, Any]:
        """
        Fix incomplete lines by connecting nearby endpoints.
        
        Returns:
            Dictionary containing the results of the operation
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        msp = self.current_doc.modelspace()
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        if not lines:
            return {
                'operation': 'fix_incomplete_lines',
                'message': 'No lines found to fix',
                'entities_modified': 0,
                'entities_added': 0
            }
        
        # Extract line segments for processing
        segments = []
        for line in lines:
            start = (line.dxf.start.x, line.dxf.start.y)
            end = (line.dxf.end.x, line.dxf.end.y)
            segments.append((start, end))
        
        # Connect segments using basic algorithm
        try:
            connected_segments = self._connect_segments(segments)
            
            # Remove original lines
            for line in lines:
                msp.delete_entity(line)
            
            # Add connected lines
            entities_added = 0
            for segment in connected_segments:
                start, end = segment
                msp.add_line(start, end)
                entities_added += 1
            
            return {
                'operation': 'fix_incomplete_lines',
                'message': f'Connected {len(segments)} segments into {len(connected_segments)} lines',
                'original_count': len(segments),
                'final_count': len(connected_segments),
                'entities_modified': len(lines),
                'entities_added': entities_added
            }
            
        except Exception as e:
            return {
                'operation': 'fix_incomplete_lines',
                'error': f'Failed to fix incomplete lines: {str(e)}',
                'entities_modified': 0,
                'entities_added': 0
            }
    
    def _connect_segments(self, segments):
        """Basic segment connection algorithm."""
        if not segments:
            return []
        
        connected = []
        remaining = segments.copy()
        
        while remaining:
            current = remaining.pop(0)
            connected.append(current)
            
            # Try to connect with remaining segments
            changed = True
            while changed:
                changed = False
                for i, segment in enumerate(remaining):
                    if self._can_connect(current, segment):
                        # Connect the segments
                        current = self._merge_segments(current, segment)
                        remaining.pop(i)
                        changed = True
                        break
            
            # Update the last connected segment
            if connected:
                connected[-1] = current
        
        return connected
    
    def _can_connect(self, seg1, seg2):
        """Check if two segments can be connected."""
        tolerance = self.tolerance
        
        # Check if endpoints are close enough
        endpoints1 = [seg1[0], seg1[1]]
        endpoints2 = [seg2[0], seg2[1]]
        
        for ep1 in endpoints1:
            for ep2 in endpoints2:
                dist = math.sqrt((ep1[0] - ep2[0])**2 + (ep1[1] - ep2[1])**2)
                if dist <= tolerance:
                    return True
        return False
    
    def _merge_segments(self, seg1, seg2):
        """Merge two segments into one."""
        # Find the connection point and create a merged segment
        tolerance = self.tolerance
        
        endpoints1 = [seg1[0], seg1[1]]
        endpoints2 = [seg2[0], seg2[1]]
        
        # Find which endpoints connect
        for i, ep1 in enumerate(endpoints1):
            for j, ep2 in enumerate(endpoints2):
                dist = math.sqrt((ep1[0] - ep2[0])**2 + (ep1[1] - ep2[1])**2)
                if dist <= tolerance:
                    # Connect the segments
                    other_ep1 = endpoints1[1-i]
                    other_ep2 = endpoints2[1-j]
                    return (other_ep1, other_ep2)
        
        # If no connection found, return original segment
        return seg1
    
    def remove_duplicates(self) -> Dict[str, Any]:
        """
        Remove duplicate entities from the DXF file.
        
        Returns:
            Dictionary containing the results of the operation
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        msp = self.current_doc.modelspace()
        entities = list(msp)
        
        duplicates_removed = 0
        entities_to_remove = []
        
        # Check for duplicate lines
        lines = [e for e in entities if e.dxftype() == 'LINE']
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                if self._lines_are_duplicate(line1, line2):
                    if line2 not in entities_to_remove:
                        entities_to_remove.append(line2)
                        duplicates_removed += 1
        
        # Remove duplicates
        for entity in entities_to_remove:
            msp.delete_entity(entity)
        
        return {
            'operation': 'remove_duplicates',
            'message': f'Removed {duplicates_removed} duplicate entities',
            'entities_removed': duplicates_removed
        }
    
    def remove_small_entities(self) -> Dict[str, Any]:
        """
        Remove very small entities that might be artifacts.
        
        Returns:
            Dictionary containing the results of the operation
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        msp = self.current_doc.modelspace()
        entities = list(msp)
        
        small_threshold = 0.01  # Adjust based on drawing scale
        entities_removed = 0
        entities_to_remove = []
        
        for entity in entities:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = math.sqrt((end.x - start.x)**2 + (end.y - start.y)**2)
                if length < small_threshold:
                    entities_to_remove.append(entity)
                    entities_removed += 1
            
            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                if entity.dxf.radius < small_threshold:
                    entities_to_remove.append(entity)
                    entities_removed += 1
        
        # Remove small entities
        for entity in entities_to_remove:
            msp.delete_entity(entity)
        
        return {
            'operation': 'remove_small_entities',
            'message': f'Removed {entities_removed} small entities (threshold: {small_threshold})',
            'entities_removed': entities_removed,
            'threshold': small_threshold
        }
    
    def fill_small_gaps(self) -> Dict[str, Any]:
        """
        Fill small gaps between line endpoints.
        
        Returns:
            Dictionary containing the results of the operation
        """
        if not self.current_doc:
            return {'error': 'No document loaded'}
        
        msp = self.current_doc.modelspace()
        lines = [entity for entity in msp if entity.dxftype() == 'LINE']
        
        gap_threshold = 0.1  # Maximum gap to fill
        entities_added = 0
        
        # Find gaps between line endpoints
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                gap_line = self._find_gap_between_lines(line1, line2, gap_threshold)
                if gap_line:
                    start, end = gap_line
                    msp.add_line(start, end)
                    entities_added += 1
        
        return {
            'operation': 'fill_small_gaps',
            'message': f'Filled {entities_added} small gaps (threshold: {gap_threshold})',
            'entities_added': entities_added,
            'threshold': gap_threshold
        }
    
    def _lines_are_duplicate(self, line1, line2) -> bool:
        """Check if two lines are duplicates."""
        tolerance = self.tolerance
        
        # Check if start and end points match (in either direction)
        start1, end1 = line1.dxf.start, line1.dxf.end
        start2, end2 = line2.dxf.start, line2.dxf.end
        
        # Same direction
        same_direction = (
            abs(start1.x - start2.x) < tolerance and
            abs(start1.y - start2.y) < tolerance and
            abs(end1.x - end2.x) < tolerance and
            abs(end1.y - end2.y) < tolerance
        )
        
        # Opposite direction
        opposite_direction = (
            abs(start1.x - end2.x) < tolerance and
            abs(start1.y - end2.y) < tolerance and
            abs(end1.x - start2.x) < tolerance and
            abs(end1.y - start2.y) < tolerance
        )
        
        return same_direction or opposite_direction
    
    def _find_gap_between_lines(self, line1, line2, max_gap: float) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Find if there's a small gap between two lines that can be filled.
        
        Returns:
            Tuple of (start_point, end_point) for the gap line, or None if no gap
        """
        tolerance = self.tolerance
        
        # Get endpoints
        start1, end1 = line1.dxf.start, line1.dxf.end
        start2, end2 = line2.dxf.start, line2.dxf.end
        
        # Check all possible gap combinations
        gaps = [
            ((end1.x, end1.y), (start2.x, start2.y)),
            ((end1.x, end1.y), (end2.x, end2.y)),
            ((start1.x, start1.y), (start2.x, start2.y)),
            ((start1.x, start1.y), (end2.x, end2.y))
        ]
        
        for gap_start, gap_end in gaps:
            gap_length = math.sqrt((gap_end[0] - gap_start[0])**2 + (gap_end[1] - gap_start[1])**2)
            
            # Check if gap is within threshold and not too small
            if tolerance < gap_length <= max_gap:
                return (gap_start, gap_end)
        
        return None 