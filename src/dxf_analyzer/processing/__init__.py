"""
DXF Processing Module

This module contains components for handling DXF files, organized into specialized submodules:
- viewing: DXF file viewing and display
- workflow_processing: Internal DXF processing and analysis
- correction: DXF data correction and cleanup
- loop_detection: Loop detection and analysis
- profile_management: CAD profile management
"""

# Import main components from submodules
from .viewing import DXFViewer, DisplayManager
from .workflow_processing import DXFProcessor, FeatureExtractor, AnalysisEngine
from .correction import DXFCorrector
from .loop_detection import LoopDetector
from .profile_management import ProfileManager

# For backward compatibility, create a new CADWidget that uses the modular components
from .cad_widget_modular import CADWidget

__all__ = [
    # Viewing components
    'DXFViewer', 'DisplayManager',
    # Workflow processing components
    'DXFProcessor', 'FeatureExtractor', 'AnalysisEngine',
    # Correction components
    'DXFCorrector',
    # Loop detection components
    'LoopDetector',
    # Profile management components
    'ProfileManager',
    # Main widget
    'CADWidget'
]
