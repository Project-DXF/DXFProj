"""
Modular CAD Widget

A modern, modular CAD widget that uses the new processing architecture
with specialized components for different functionalities.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QGraphicsView, QGraphicsScene, QLabel, QGroupBox, 
                            QFormLayout, QLineEdit, QSplitter, QMessageBox,
                            QFileDialog, QToolBar, QAction, QTextEdit, QTabWidget,
                            QProgressBar, QComboBox, QScrollArea, QTreeWidget, 
                            QTreeWidgetItem, QHeaderView)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QFont, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
import ezdxf
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Import the new modular components
from .viewing import DisplayManager
from .workflow_processing import DXFProcessor, FeatureExtractor, AnalysisEngine
from .correction import DXFCorrector, GeometryFixer, CleanupTools
from .loop_detection import LoopDetector, PathAnalyzer, LoopVisualizer
from .profile_management import ProfileManager
from .profile_management.feature_calculator import AdvancedFeatureCalculator
from .profile_management.profile_database import ProfileDatabase


class ProcessingWorker(QThread):
    """Worker thread for long-running processing operations."""
    
    progress_updated = pyqtSignal(int, str)
    processing_completed = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            result = self.operation(*self.args, **self.kwargs)
            self.processing_completed.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class CADWidget(QWidget):
    """Modern modular CAD widget using the new processing architecture."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_file = None
        self.current_doc = None
        
        # Initialize modular components
        self._init_components()
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create UI
        self._init_ui()
        
        # Connect signals
        self._connect_signals()
    
    def _init_components(self):
        """Initialize the modular processing components."""
        # Create graphics scene and view first
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView()
        self.graphics_view.setScene(self.graphics_scene)
        
        # Initialize components
        self.display_manager = DisplayManager(self.graphics_view, self.graphics_scene)
        self.dxf_processor = DXFProcessor()
        self.feature_extractor = FeatureExtractor()
        self.analysis_engine = AnalysisEngine()
        self.dxf_corrector = DXFCorrector()
        self.geometry_fixer = GeometryFixer()
        self.cleanup_tools = CleanupTools()
        self.loop_detector = LoopDetector()
        self.path_analyzer = PathAnalyzer()
        self.loop_visualizer = LoopVisualizer(self.graphics_scene)
        self.profile_manager = ProfileManager()
        self.feature_calculator = AdvancedFeatureCalculator()
        self.profile_database = ProfileDatabase()
        
        # Worker thread for processing
        self.processing_worker = None
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for main areas
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        
        # Left panel (CAD viewer)
        viewer_panel = self._create_viewer_panel()
        
        # Right panel (Controls and information)
        control_panel = self._create_control_panel()
        
        # Add panels to splitter
        splitter.addWidget(viewer_panel)
        splitter.addWidget(control_panel)
        splitter.setSizes([800, 400])  # Initial sizes
        
        main_layout.addWidget(splitter)
    
    def _create_viewer_panel(self):
        """Create the CAD viewer panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Configure graphics view
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Set background color and theme
        if self.parent and hasattr(self.parent, 'colors'):
            self.display_manager.set_background_color(self.parent.colors['background'])
            if hasattr(self.parent, 'dark_mode'):
                self.display_manager.set_theme(self.parent.dark_mode)
        
        layout.addWidget(self.graphics_view)
        
        # Add status bar
        self.status_label = QLabel("Ready - Upload a DXF file to begin")
        layout.addWidget(self.status_label)
        
        # Add placeholder text
        self.display_manager.add_placeholder_text("Drop a DXF file here or click Upload DXF")
        
        return panel
    
    def _create_toolbar(self):
        """Create the toolbar with actions."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        
        # File operations
        upload_action = QAction(QIcon.fromTheme("document-open"), "Upload DXF", self)
        upload_action.setToolTip("Upload DXF File (Ctrl+O)")
        upload_action.triggered.connect(self.upload_dxf)
        toolbar.addAction(upload_action)
        
        toolbar.addSeparator()
        
        # View operations
        zoom_in_action = QAction(QIcon.fromTheme("zoom-in"), "Zoom In", self)
        zoom_in_action.setToolTip("Zoom In (Mouse Wheel Up)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out"), "Zoom Out", self)
        zoom_out_action.setToolTip("Zoom Out (Mouse Wheel Down)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        fit_action = QAction(QIcon.fromTheme("zoom-fit-best"), "Fit to View", self)
        fit_action.setToolTip("Fit Drawing to View (Ctrl+0)")
        fit_action.triggered.connect(self.fit_to_view)
        toolbar.addAction(fit_action)
        
        return toolbar
    
    def _create_control_panel(self):
        """Create the control panel with input fields and action buttons."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Input Information section
        input_group = QGroupBox("Input Information")
        input_layout = QFormLayout()
        input_layout.setSpacing(10)
        
        # Sketch Number field
        self.sketch_number_field = QLineEdit()
        self.sketch_number_field.setPlaceholderText("Enter sketch number")
        input_layout.addRow("Sketch Number:", self.sketch_number_field)
        
        # Profile Number field  
        self.profile_number_field = QLineEdit()
        self.profile_number_field.setPlaceholderText("Enter profile number")
        input_layout.addRow("Profile Number:", self.profile_number_field)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Actions section
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        # Create action buttons
        self.upload_dxf_btn = QPushButton("Upload DXF")
        self.upload_dxf_btn.clicked.connect(self.upload_dxf)
        actions_layout.addWidget(self.upload_dxf_btn)
        
        self.correct_dxf_btn = QPushButton("Correct DXF")
        self.correct_dxf_btn.clicked.connect(self.correct_dxf)
        self.correct_dxf_btn.setEnabled(False)
        actions_layout.addWidget(self.correct_dxf_btn)
        
        self.display_loops_btn = QPushButton("Display Loops")
        self.display_loops_btn.clicked.connect(self.detect_loops)
        self.display_loops_btn.setEnabled(False)
        actions_layout.addWidget(self.display_loops_btn)
        
        self.process_btn = QPushButton("Process")
        self.process_btn.clicked.connect(self.process_dxf)
        self.process_btn.setEnabled(False)
        actions_layout.addWidget(self.process_btn)
        
        self.upload_profile_btn = QPushButton("Upload New Profile")
        self.upload_profile_btn.clicked.connect(self.save_profile)
        self.upload_profile_btn.setEnabled(False)
        actions_layout.addWidget(self.upload_profile_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Processed Parameters section with tree view
        params_group = QGroupBox("Processed Parameters")
        params_layout = QVBoxLayout()
        
        # Create tree widget for parameters
        self.params_tree = QTreeWidget()
        self.params_tree.setHeaderLabels(["Parameter", "Value", "Unit"])
        self.params_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.params_tree.setAlternatingRowColors(True)
        self.params_tree.setRootIsDecorated(True)
        
        # Create scroll area for the tree
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.params_tree)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        params_layout.addWidget(scroll_area)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
        # Apply theme styling
        self._apply_control_panel_styling()
        
        return panel
    
    def _apply_control_panel_styling(self):
        """Apply styling to the control panel based on current theme."""
        # Get theme colors from parent
        if self.parent and hasattr(self.parent, 'colors') and hasattr(self.parent, 'dark_mode'):
            colors = self.parent.colors
            dark_mode = self.parent.dark_mode
            
            # Button styling
            button_style = f"""
                QPushButton {{
                    padding: 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    min-height: 20px;
                    background-color: {colors['primary'].name()};
                    color: {'white' if dark_mode else 'white'};
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {colors['secondary'].name()};
                }}
                QPushButton:pressed {{
                    background-color: {colors['secondary'].darker(120).name()};
                }}
                QPushButton:disabled {{
                    background-color: {'#555' if dark_mode else '#BDBDBD'};
                    color: {'#888' if dark_mode else '#757575'};
                }}
            """
            
            # Apply to all buttons
            for btn in [self.upload_dxf_btn, self.correct_dxf_btn, self.display_loops_btn, 
                       self.process_btn, self.upload_profile_btn]:
                btn.setStyleSheet(button_style)
            
            # Tree widget styling
            tree_style = f"""
                QTreeWidget {{
                    background-color: {colors['surface'].name()};
                    color: {colors['text'].name()};
                    border: 1px solid {'#555' if dark_mode else '#ddd'};
                    border-radius: 4px;
                    selection-background-color: {colors['primary'].lighter(150).name()};
                }}
                QTreeWidget::item {{
                    padding: 4px;
                    border-bottom: 1px solid {'#444' if dark_mode else '#eee'};
                }}
                QTreeWidget::item:selected {{
                    background-color: {colors['primary'].name()};
                    color: white;
                }}
                QTreeWidget::item:hover {{
                    background-color: {colors['primary'].lighter(180).name()};
                }}
                QHeaderView::section {{
                    background-color: {colors['primary'].name()};
                    color: white;
                    padding: 8px;
                    border: none;
                    font-weight: bold;
                }}
            """
            
            if hasattr(self, 'params_tree'):
                self.params_tree.setStyleSheet(tree_style)
            
            # Input field styling
            input_style = f"""
                QLineEdit {{
                    padding: 8px;
                    border: 1px solid {'#555' if dark_mode else '#ddd'};
                    border-radius: 4px;
                    background-color: {colors['surface'].name()};
                    color: {colors['text'].name()};
                }}
                QLineEdit:focus {{
                    border-color: {colors['primary'].name()};
                }}
                QLineEdit:read-only {{
                    background-color: {'#333' if dark_mode else '#f5f5f5'};
                    color: {'#aaa' if dark_mode else '#666'};
                }}
            """
            
            # Apply to all input fields
            for field in [self.sketch_number_field, self.profile_number_field]:
                field.setStyleSheet(input_style)
            
            # Status label styling
            status_style = f"""
                QLabel {{
                    padding: 5px;
                    background: {colors['surface'].name()};
                    border-top: 1px solid {'#555' if dark_mode else '#ddd'};
                    color: {colors['text'].name()};
                }}
            """
            self.status_label.setStyleSheet(status_style)
            
            # Toolbar styling
            toolbar_style = f"""
                QToolBar {{
                    spacing: 5px;
                    padding: 5px;
                    background: {colors['background'].name()};
                    border-bottom: 1px solid {'#555' if dark_mode else '#ddd'};
                }}
                QToolButton {{
                    padding: 8px;
                    border-radius: 4px;
                    background: {colors['surface'].name()};
                    color: {colors['text'].name()};
                }}
                QToolButton:hover {{
                    background: {colors['primary'].lighter(150).name()};
                }}
                QToolButton:pressed {{
                    background: {colors['primary'].name()};
                }}
            """
            
            # Find and style the toolbar
            toolbar = self.findChild(QToolBar)
            if toolbar:
                toolbar.setStyleSheet(toolbar_style)
    
    def _connect_signals(self):
        """Connect signals and slots."""
        pass  # Signals are connected in individual methods

    def upload_dxf(self):
        """Handle DXF file upload."""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF File",
            "",
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_name:
            self.load_dxf(file_name)

    def load_dxf(self, filename):
        """Load a DXF file."""
        try:
            self.current_file = filename
            
            # Load using display manager
            success = self.display_manager.load_dxf(filename)
            
            if success:
                # Load document for processing
                self.current_doc = ezdxf.readfile(filename)
                
                # Update file info
                self._update_file_info()
                
                # Enable processing buttons
                self._enable_processing_buttons()
                
                self.status_label.setText(f"Loaded: {os.path.basename(filename)}")
            else:
                self.status_label.setText("Failed to load DXF file")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load DXF file: {str(e)}")
            self.status_label.setText("Error loading file")

    def _update_file_info(self):
        """Update file information display."""
        if not self.current_doc:
            return
        
        try:
            # Clear the parameters tree when a new file is loaded
            self.params_tree.clear()
            
            # Add a placeholder item
            placeholder_item = QTreeWidgetItem(self.params_tree)
            placeholder_item.setText(0, "Click 'Process' to calculate parameters")
            placeholder_item.setText(1, "")
            placeholder_item.setText(2, "")
            
        except Exception as e:
            print(f"Error updating file info: {e}")

    def _enable_processing_buttons(self):
        """Enable processing buttons when a file is loaded."""
        self.correct_dxf_btn.setEnabled(True)
        self.display_loops_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.upload_profile_btn.setEnabled(True)

    def correct_dxf(self):
        """Apply DXF corrections."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Applying corrections...")
        
        try:
            # Apply corrections
            self.dxf_corrector.load_document(self.current_doc)
            results = self.dxf_corrector.correct_dxf()
            
            # Show results
            message = f"Corrections applied:\n"
            for correction in results.get('corrections_applied', []):
                message += f"- {correction.get('operation', 'Unknown')}: {correction.get('message', '')}\n"
            
            QMessageBox.information(self, "Corrections Applied", message)
            
            # Refresh display
            self.display_manager.refresh_view()
            self.status_label.setText("Corrections applied")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply corrections: {str(e)}")
            self.status_label.setText("Error applying corrections")

    def detect_loops(self):
        """Detect and highlight loops."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Detecting loops...")
        
        try:
            # Detect loops
            self.loop_detector.set_document(self.current_doc)
            loops_data = self.loop_detector.detect_loops()
            
            # Highlight loops
            success = self.loop_visualizer.highlight_loops(loops_data)
            
            if success:
                loop_count = loops_data.get('total_loops', 0)
                self.status_label.setText(f"Found and highlighted {loop_count} loops")
            else:
                self.status_label.setText("No loops found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to detect loops: {str(e)}")
            self.status_label.setText("Error detecting loops")

    def process_dxf(self):
        """Process the DXF file and extract features."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Processing DXF file...")
        
        try:
            print("Starting DXF processing...")
            
            # Use the advanced feature calculator
            self.feature_calculator.set_document(self.current_doc)
            features = self.feature_calculator.calculate_all_features()
            
            print(f"Features calculated: {len(features)}")
            if features:
                print("Feature keys:", list(features.keys())[:10])  # Show first 10 keys
            
            # Update the parameters tree with calculated features
            self._update_parameters_tree(features)
            
            self.status_label.setText("Processing completed")
            
            if len(features) > 0:
                QMessageBox.information(self, "Processing Complete", 
                                      f"DXF file processed successfully. {len(features)} features calculated.")
            else:
                QMessageBox.warning(self, "Processing Complete", 
                                  "DXF file processed but no features could be calculated. Check console for details.")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Failed to process DXF: {str(e)}")
            self.status_label.setText("Error processing file")

    def save_profile(self):
        """Save the current profile."""
        if not self.current_doc:
            QMessageBox.warning(self, "Save Profile", "Please load a DXF file first")
            return
        
        # Get input information
        sketch_number = self.sketch_number_field.text().strip()
        profile_number = self.profile_number_field.text().strip()
        
        if not sketch_number or not profile_number:
            QMessageBox.warning(self, "Save Profile", "Please enter both sketch number and profile number")
            return
        
        try:
            # Extract parameters from the tree
            parameters = self._extract_parameters_from_tree()
            
            # Create metadata
            metadata = {
                'Sketch Number': sketch_number,
                'Profile Number': profile_number,
                'Input Filename': os.path.basename(self.current_file),
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Processing Status': 'Success',
                'Source File Path': self.current_file
            }
            
            # Save to database
            success, message = self.profile_database.save_profile(metadata, parameters)
            
            if success:
                QMessageBox.information(self, "Save Profile", message)
                self.status_label.setText("Profile saved to database")
            else:
                QMessageBox.critical(self, "Save Profile", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")
            # Update metadata with error information
            if 'metadata' in locals():
                metadata['Processing Status'] = f'Error: {str(e)}'
                # Try to save error information
                try:
                    self.profile_database.save_profile(metadata, parameters)
                except:
                    pass

    def _update_parameters_tree(self, features: Dict[str, Any]):
        """Update the parameters tree with calculated features."""
        self.params_tree.clear()
        
        if not features:
            return
        
        # Define parameter categories and their display information
        categories = {
            'Basic Properties': {
                'number_of_loops': ('Number of Loops', ''),
                'profile_type': ('Profile Type', ''),
                'profile_area': ('Profile Area', 'mm²'),
                'outer_area': ('Outer Area', 'mm²'),
                'inner_area': ('Inner Area', 'mm²'),
                'hollow_ratio': ('Hollow Ratio', ''),
                'outer_perimeter': ('Outer Perimeter', 'mm'),
                'total_perimeter': ('Total Perimeter', 'mm'),
                'number_of_mandrels': ('Number of Mandrels', ''),
            },
            'Dimensions': {
                'bounding_box_width': ('Bounding Box Width', 'mm'),
                'bounding_box_height': ('Bounding Box Height', 'mm'),
                'bounding_box_area': ('Bounding Box Area', 'mm²'),
                'max_width': ('Max Width', 'mm'),
                'max_height': ('Max Height', 'mm'),
                'aspect_ratio': ('Aspect Ratio', ''),
            },
            'Extrusion Ratios': {
                'er_p22': ('ER for P22', ''),
                'er_p40': ('ER for P40', ''),
                'er_p55': ('ER for P55', ''),
                'holes_p22': ('Holes for P22', ''),
                'holes_p40': ('Holes for P40', ''),
                'holes_p55': ('Holes for P55', ''),
            },
            'Geometric Properties': {
                'compactness': ('Compactness', ''),
                'solidity': ('Solidity', ''),
                'ccd': ('Circumscribing Circle Diameter', 'mm'),
                'min_radius_outer': ('Min Radius (Outer)', 'mm'),
                'max_radius_outer': ('Max Radius (Outer)', 'mm'),
            },
            'Wall Thickness': {
                'max_wall_thickness': ('Max Wall Thickness', 'mm'),
                'min_wall_thickness': ('Min Wall Thickness', 'mm'),
                'avg_wall_thickness': ('Average Wall Thickness', 'mm'),
                'wall_thickness_variability': ('Wall Thickness Variability', 'mm'),
            },
            'Moments of Inertia': {
                'moment_of_inertia_x': ('Moment of Inertia (Ix)', 'mm⁴'),
                'moment_of_inertia_y': ('Moment of Inertia (Iy)', 'mm⁴'),
                'polar_moment_of_inertia': ('Polar Moment of Inertia', 'mm⁴'),
                'product_of_inertia': ('Product of Inertia', 'mm⁴'),
            },
            'Distance Metrics': {
                'euclidean_distance': ('Euclidean Distance', ''),
                'cosine_similarity': ('Cosine Similarity', ''),
            },
            'Mass Vectors': {
                'mass_vector_top_left': ('Top-Left Quadrant', ''),
                'mass_vector_top_right': ('Top-Right Quadrant', ''),
                'mass_vector_bottom_left': ('Bottom-Left Quadrant', ''),
                'mass_vector_bottom_right': ('Bottom-Right Quadrant', ''),
            },
            'Complexity Factors': {
                'complexity_factor_c1': ('C1 (Ps/As)', ''),
                'complexity_factor_c2': ('C2 (Ps/Ws)', ''),
                'complexity_factor_c3': ('C3 (CCD/Tm)', ''),
                'complexity_factor_c4': ('C4 (Groover)', ''),
                'complexity_factor_c5': ('C5 (Qamar)', ''),
            }
        }
        
        # Add Fourier descriptors
        fourier_category = {}
        for i in range(1, 11):
            key = f'fourier_descriptor_{i}'
            fourier_category[key] = (f'Fourier Descriptor {i}', '')
        categories['Fourier Descriptors'] = fourier_category
        
        # Create tree items for each category
        for category_name, params in categories.items():
            category_item = QTreeWidgetItem(self.params_tree)
            category_item.setText(0, category_name)
            category_item.setExpanded(True)
            
            # Set category item styling
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            for param_key, (param_name, unit) in params.items():
                if param_key in features:
                    value = features[param_key]
                    
                    # Format the value
                    if isinstance(value, float):
                        if abs(value) < 0.001:
                            formatted_value = f"{value:.6f}"
                        elif abs(value) < 1:
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = str(value)
                    
                    param_item = QTreeWidgetItem(category_item)
                    param_item.setText(0, param_name)
                    param_item.setText(1, formatted_value)
                    param_item.setText(2, unit)
        
        # Handle mandrel features separately
        mandrel_features = {k: v for k, v in features.items() if k.startswith('mandrel_')}
        if mandrel_features:
            mandrel_category = QTreeWidgetItem(self.params_tree)
            mandrel_category.setText(0, "Mandrel Analysis")
            mandrel_category.setExpanded(True)
            
            font = mandrel_category.font(0)
            font.setBold(True)
            mandrel_category.setFont(0, font)
            
            for mandrel_key, mandrel_data in mandrel_features.items():
                mandrel_item = QTreeWidgetItem(mandrel_category)
                mandrel_item.setText(0, mandrel_key.replace('_', ' ').title())
                mandrel_item.setExpanded(False)
                
                mandrel_params = {
                    'area': ('Area', 'mm²'),
                    'perimeter': ('Perimeter', 'mm'),
                    'compactness': ('Compactness', ''),
                    'solidity': ('Solidity', ''),
                    'aspect_ratio': ('Aspect Ratio', ''),
                    'distance_from_cog_to_centroid': ('Distance from COG to Centroid', 'mm'),
                    'thickness_std_plus_x': ('Thickness Std (+X)', 'mm'),
                    'thickness_std_plus_y': ('Thickness Std (+Y)', 'mm'),
                    'thickness_std_minus_x': ('Thickness Std (-X)', 'mm'),
                    'thickness_std_minus_y': ('Thickness Std (-Y)', 'mm'),
                }
                
                for param_key, (param_name, unit) in mandrel_params.items():
                    if param_key in mandrel_data:
                        value = mandrel_data[param_key]
                        
                        if isinstance(value, float):
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = str(value)
                        
                        param_item = QTreeWidgetItem(mandrel_item)
                        param_item.setText(0, param_name)
                        param_item.setText(1, formatted_value)
                        param_item.setText(2, unit)

    def _extract_parameters_from_tree(self) -> Dict[str, Any]:
        """Extract all parameters from the tree widget."""
        parameters = {}
        
        root = self.params_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_name = category_item.text(0)
            
            category_params = {}
            for j in range(category_item.childCount()):
                param_item = category_item.child(j)
                param_name = param_item.text(0)
                param_value = param_item.text(1)
                param_unit = param_item.text(2)
                
                # Try to convert to appropriate type
                try:
                    if '.' in param_value:
                        param_value = float(param_value)
                    elif param_value.isdigit():
                        param_value = int(param_value)
                except ValueError:
                    pass  # Keep as string
                
                category_params[param_name] = {
                    'value': param_value,
                    'unit': param_unit
                }
            
            parameters[category_name] = category_params
        
        return parameters

    def zoom_in(self):
        """Zoom in the view."""
        self.display_manager.zoom_in()

    def zoom_out(self):
        """Zoom out the view."""
        self.display_manager.zoom_out()

    def fit_to_view(self):
        """Fit the drawing to view."""
        self.display_manager.fit_to_view()

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming."""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.dxf') for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.dxf'):
                    self.load_dxf(file_path)
                    break
    
    def apply_theme(self):
        """Apply the current theme to the widget."""
        self._apply_control_panel_styling()
        
        # Update display manager background and theme
        if self.parent and hasattr(self.parent, 'colors'):
            self.display_manager.set_background_color(self.parent.colors['background'])
            
            # Set theme mode for DXF rendering
            if hasattr(self.parent, 'dark_mode'):
                self.display_manager.set_theme(self.parent.dark_mode) 