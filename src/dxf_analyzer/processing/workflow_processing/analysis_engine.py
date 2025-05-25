"""
Analysis Engine for DXF Processing

Provides comprehensive analysis capabilities for DXF files,
combining multiple analysis techniques and generating reports.
"""

import ezdxf
from typing import Dict, List, Any, Optional
from .dxf_processor import DXFProcessor
from .feature_extractor import FeatureExtractor


class AnalysisEngine:
    """Comprehensive analysis engine for DXF files."""
    
    def __init__(self):
        """Initialize the analysis engine."""
        self.processor = DXFProcessor()
        self.feature_extractor = FeatureExtractor()
        self.current_analysis = None
        
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a DXF file.
        
        Args:
            file_path: Path to the DXF file
            
        Returns:
            Dictionary containing complete analysis results
        """
        # Load the file
        if not self.processor.load_file(file_path):
            return {'error': 'Failed to load DXF file'}
        
        # Set up feature extractor
        self.feature_extractor.set_document(self.processor.current_doc)
        
        # Perform various analyses
        analysis_results = {
            'file_info': self._analyze_file_info(),
            'basic_info': self.processor.get_entity_info(),
            'dimensions': self.processor.get_dimensions(),
            'geometric_features': self.feature_extractor.extract_geometric_features(),
            'layer_analysis': self.feature_extractor.extract_layer_features(),
            'complexity_metrics': self.feature_extractor.extract_complexity_metrics(),
            'quality_assessment': self._assess_quality(),
            'recommendations': self._generate_recommendations()
        }
        
        self.current_analysis = analysis_results
        return analysis_results
    
    def _analyze_file_info(self) -> Dict[str, Any]:
        """Analyze basic file information."""
        if not self.processor.current_file:
            return {}
        
        file_path = self.processor.current_file
        file_size = file_path.stat().st_size
        
        return {
            'filename': file_path.name,
            'file_size_bytes': file_size,
            'file_size_mb': round(file_size / (1024 * 1024), 2),
            'dxf_version': self.processor.current_doc.dxfversion if self.processor.current_doc else None,
            'units': self._detect_units()
        }
    
    def _detect_units(self) -> str:
        """Detect the units used in the DXF file."""
        if not self.processor.current_doc:
            return 'Unknown'
        
        try:
            # Try to get units from header variables
            units_code = self.processor.current_doc.header.get('$INSUNITS', 0)
            
            units_map = {
                0: 'Unitless',
                1: 'Inches',
                2: 'Feet',
                3: 'Miles',
                4: 'Millimeters',
                5: 'Centimeters',
                6: 'Meters',
                7: 'Kilometers',
                8: 'Microinches',
                9: 'Mils',
                10: 'Yards',
                11: 'Angstroms',
                12: 'Nanometers',
                13: 'Microns',
                14: 'Decimeters',
                15: 'Decameters',
                16: 'Hectometers',
                17: 'Gigameters',
                18: 'Astronomical Units',
                19: 'Light Years',
                20: 'Parsecs'
            }
            
            return units_map.get(units_code, f'Unknown ({units_code})')
            
        except Exception:
            return 'Unknown'
    
    def _assess_quality(self) -> Dict[str, Any]:
        """Assess the quality of the DXF file."""
        if not self.processor.current_doc:
            return {}
        
        quality_issues = []
        quality_score = 100
        
        # Check for common issues
        entities = self.processor.get_entities()
        
        # Check for duplicate entities
        duplicate_count = self._count_duplicates(entities)
        if duplicate_count > 0:
            quality_issues.append(f"Found {duplicate_count} potential duplicate entities")
            quality_score -= min(duplicate_count * 2, 20)
        
        # Check for very small entities
        small_entities = self._count_small_entities(entities)
        if small_entities > 0:
            quality_issues.append(f"Found {small_entities} very small entities")
            quality_score -= min(small_entities, 15)
        
        # Check for entities on layer 0
        layer_0_count = len([e for e in entities if e.dxf.layer == '0'])
        if layer_0_count > len(entities) * 0.5:
            quality_issues.append("More than 50% of entities are on layer 0")
            quality_score -= 10
        
        # Check for overlapping entities
        overlapping_count = self._count_overlapping_entities(entities)
        if overlapping_count > 0:
            quality_issues.append(f"Found {overlapping_count} potentially overlapping entities")
            quality_score -= min(overlapping_count, 10)
        
        quality_level = self._classify_quality(quality_score)
        
        return {
            'quality_score': max(quality_score, 0),
            'quality_level': quality_level,
            'issues': quality_issues,
            'issue_count': len(quality_issues)
        }
    
    def _count_duplicates(self, entities: List) -> int:
        """Count potential duplicate entities."""
        # Simplified duplicate detection
        # In a real implementation, this would be more sophisticated
        duplicate_count = 0
        
        lines = [e for e in entities if e.dxftype() == 'LINE']
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                if (abs(line1.dxf.start.x - line2.dxf.start.x) < 0.001 and
                    abs(line1.dxf.start.y - line2.dxf.start.y) < 0.001 and
                    abs(line1.dxf.end.x - line2.dxf.end.x) < 0.001 and
                    abs(line1.dxf.end.y - line2.dxf.end.y) < 0.001):
                    duplicate_count += 1
        
        return duplicate_count
    
    def _count_small_entities(self, entities: List) -> int:
        """Count very small entities that might be artifacts."""
        small_count = 0
        threshold = 0.01  # Adjust based on typical drawing scale
        
        for entity in entities:
            if entity.dxftype() == 'LINE':
                start = entity.dxf.start
                end = entity.dxf.end
                length = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
                if length < threshold:
                    small_count += 1
            elif entity.dxftype() in ['CIRCLE', 'ARC']:
                if entity.dxf.radius < threshold:
                    small_count += 1
        
        return small_count
    
    def _count_overlapping_entities(self, entities: List) -> int:
        """Count potentially overlapping entities."""
        # Simplified overlapping detection
        # This is a basic implementation
        overlapping_count = 0
        
        lines = [e for e in entities if e.dxftype() == 'LINE']
        for i, line1 in enumerate(lines):
            for line2 in lines[i+1:]:
                if self._lines_overlap(line1, line2):
                    overlapping_count += 1
        
        return overlapping_count
    
    def _lines_overlap(self, line1, line2) -> bool:
        """Check if two lines overlap."""
        # Simplified overlap detection
        # Check if lines are parallel and close
        tolerance = 0.001
        
        # Get line vectors
        v1 = (line1.dxf.end.x - line1.dxf.start.x, line1.dxf.end.y - line1.dxf.start.y)
        v2 = (line2.dxf.end.x - line2.dxf.start.x, line2.dxf.end.y - line2.dxf.start.y)
        
        # Check if vectors are parallel (cross product near zero)
        cross_product = abs(v1[0] * v2[1] - v1[1] * v2[0])
        
        if cross_product < tolerance:
            # Lines are parallel, check if they're close
            # This is a simplified check
            dist1 = ((line1.dxf.start.x - line2.dxf.start.x)**2 + 
                    (line1.dxf.start.y - line2.dxf.start.y)**2)**0.5
            return dist1 < tolerance
        
        return False
    
    def _classify_quality(self, score: int) -> str:
        """Classify quality level based on score."""
        if score >= 90:
            return 'Excellent'
        elif score >= 75:
            return 'Good'
        elif score >= 60:
            return 'Fair'
        elif score >= 40:
            return 'Poor'
        else:
            return 'Very Poor'
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on analysis."""
        if not self.current_analysis:
            return []
        
        recommendations = []
        
        # Get analysis data
        complexity = self.current_analysis.get('complexity_metrics', {})
        quality = self.current_analysis.get('quality_assessment', {})
        layers = self.current_analysis.get('layer_analysis', {})
        
        # Complexity recommendations
        complexity_level = complexity.get('complexity_level', '')
        if complexity_level in ['Complex', 'Very Complex']:
            recommendations.append("Consider simplifying the drawing to improve performance")
        
        # Quality recommendations
        quality_score = quality.get('quality_score', 100)
        if quality_score < 75:
            recommendations.append("Review and clean up the drawing to improve quality")
        
        if quality.get('issue_count', 0) > 0:
            recommendations.append("Address the identified quality issues")
        
        # Layer recommendations
        layer_count = layers.get('layer_count', 0)
        if layer_count == 1:
            recommendations.append("Consider organizing entities into multiple layers")
        elif layer_count > 20:
            recommendations.append("Consider consolidating layers to reduce complexity")
        
        # Entity-specific recommendations
        basic_info = self.current_analysis.get('basic_info', {})
        entity_counts = basic_info.get('entity_counts', {})
        
        if entity_counts.get('LINE', 0) > 1000:
            recommendations.append("Large number of lines detected - consider using polylines where appropriate")
        
        if entity_counts.get('SPLINE', 0) > 100:
            recommendations.append("Many splines detected - consider simplifying curves if possible")
        
        # Default recommendation if no specific issues
        if not recommendations:
            recommendations.append("Drawing appears to be well-structured")
        
        return recommendations
    
    def generate_report(self) -> str:
        """
        Generate a comprehensive text report of the analysis.
        
        Returns:
            Formatted text report
        """
        if not self.current_analysis:
            return "No analysis data available"
        
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append("DXF FILE ANALYSIS REPORT")
        report_lines.append("=" * 60)
        
        # File information
        file_info = self.current_analysis.get('file_info', {})
        report_lines.append(f"\nFile: {file_info.get('filename', 'Unknown')}")
        report_lines.append(f"Size: {file_info.get('file_size_mb', 0)} MB")
        report_lines.append(f"DXF Version: {file_info.get('dxf_version', 'Unknown')}")
        report_lines.append(f"Units: {file_info.get('units', 'Unknown')}")
        
        # Basic statistics
        basic_info = self.current_analysis.get('basic_info', {})
        report_lines.append(f"\nTotal Entities: {basic_info.get('total_entities', 0)}")
        report_lines.append(f"Layers: {len(basic_info.get('layers', []))}")
        
        # Dimensions
        dimensions = self.current_analysis.get('dimensions', {})
        if dimensions:
            report_lines.append(f"Width: {dimensions.get('width', 0):.2f}")
            report_lines.append(f"Height: {dimensions.get('height', 0):.2f}")
        
        # Quality assessment
        quality = self.current_analysis.get('quality_assessment', {})
        report_lines.append(f"\nQuality Score: {quality.get('quality_score', 0)}/100")
        report_lines.append(f"Quality Level: {quality.get('quality_level', 'Unknown')}")
        
        # Complexity
        complexity = self.current_analysis.get('complexity_metrics', {})
        report_lines.append(f"Complexity Level: {complexity.get('complexity_level', 'Unknown')}")
        report_lines.append(f"Complexity Score: {complexity.get('complexity_score', 0)}")
        
        # Recommendations
        recommendations = self.current_analysis.get('recommendations', [])
        if recommendations:
            report_lines.append("\nRECOMMENDATIONS:")
            for i, rec in enumerate(recommendations, 1):
                report_lines.append(f"{i}. {rec}")
        
        report_lines.append("\n" + "=" * 60)
        
        return "\n".join(report_lines) 