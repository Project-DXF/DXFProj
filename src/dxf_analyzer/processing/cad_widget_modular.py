"""
Modular CAD Widget

A modern, modular CAD widget that uses the new processing architecture
with specialized components for different functionalities.
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QGraphicsView, QGraphicsScene, QLabel, QGroupBox, 
                            QFormLayout, QLineEdit, QSplitter, QMessageBox,
                            QFileDialog, QToolBar, QAction, QTextEdit, QTabWidget,
                            QProgressBar, QComboBox)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QFont, QDragEnterEvent, QDropEvent
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
import ezdxf
import os
from pathlib import Path

# Import the new modular components
from .viewing import DisplayManager
from .workflow_processing import DXFProcessor, FeatureExtractor, AnalysisEngine
from .correction import DXFCorrector, GeometryFixer, CleanupTools
from .loop_detection import LoopDetector, PathAnalyzer, LoopVisualizer
from .profile_management import ProfileManager


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
        layout.setSpacing(20)
        
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
        
        # Processed Parameters section
        params_group = QGroupBox("Processed Parameters")
        params_layout = QFormLayout()
        params_layout.setSpacing(8)
        
        # Parameter fields (read-only)
        self.length_field = QLineEdit()
        self.length_field.setReadOnly(True)
        params_layout.addRow("Length:", self.length_field)
        
        self.width_field = QLineEdit()
        self.width_field.setReadOnly(True)
        params_layout.addRow("Width:", self.width_field)
        
        self.height_field = QLineEdit()
        self.height_field.setReadOnly(True)
        params_layout.addRow("Height:", self.height_field)
        
        self.material_field = QLineEdit()
        self.material_field.setReadOnly(True)
        params_layout.addRow("Material:", self.material_field)
        
        self.thickness_field = QLineEdit()
        self.thickness_field.setReadOnly(True)
        params_layout.addRow("Thickness:", self.thickness_field)
        
        params_group.setLayout(params_layout)
        layout.addWidget(params_group)
        
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
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
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
            for field in [self.sketch_number_field, self.profile_number_field, self.length_field,
                         self.width_field, self.height_field, self.material_field, self.thickness_field]:
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
            # Get basic file info
            msp = self.current_doc.modelspace()
            entities = list(msp)
            
            # Calculate basic dimensions
            if entities:
                try:
                    extents = msp.get_extents()
                    if extents:
                        width = extents.max.x - extents.min.x
                        height = extents.max.y - extents.min.y
                        
                        self.width_field.setText(f"{width:.2f}")
                        self.height_field.setText(f"{height:.2f}")
                except:
                    pass
            
            # Set default values for other fields
            self.length_field.setText("N/A")
            self.material_field.setText("Unknown")
            self.thickness_field.setText("N/A")
            
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
            # Extract features
            self.feature_extractor.set_document(self.current_doc)
            features = self.feature_extractor.extract_geometric_features()
            
            # Analyze the file
            self.analysis_engine.set_document(self.current_doc)
            analysis = self.analysis_engine.analyze_dxf()
            
            # Update parameter fields with extracted data
            if features and 'overall' in features:
                overall = features['overall']
                if 'dimensions' in overall:
                    dims = overall['dimensions']
                    self.length_field.setText(f"{dims.get('length', 0):.2f}")
                    self.width_field.setText(f"{dims.get('width', 0):.2f}")
                    self.height_field.setText(f"{dims.get('height', 0):.2f}")
            
            self.status_label.setText("Processing completed")
            QMessageBox.information(self, "Processing Complete", "DXF file processed successfully")
            
        except Exception as e:
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
            # Create profile data
            profile_data = {
                'name': f"Profile_{profile_number}",
                'description': f"Profile from sketch {sketch_number}",
                'category': 'Custom',
                'sketch_number': sketch_number,
                'profile_number': profile_number,
                'source_file': self.current_file,
                'parameters': {
                    'length': self.length_field.text(),
                    'width': self.width_field.text(),
                    'height': self.height_field.text(),
                    'material': self.material_field.text(),
                    'thickness': self.thickness_field.text()
                }
            }
            
            # Save profile
            result = self.profile_manager.create_profile(profile_data)
            
            if result.get('success'):
                QMessageBox.information(self, "Save Profile", "Profile saved successfully")
                self.status_label.setText("Profile saved")
            else:
                QMessageBox.critical(self, "Save Profile", f"Failed to save profile: {result.get('error')}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")

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