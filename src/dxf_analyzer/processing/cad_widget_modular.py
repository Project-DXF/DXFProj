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
        
        # Set background color
        if self.parent and hasattr(self.parent, 'colors'):
            self.display_manager.set_background_color(self.parent.colors['background'])
        
        layout.addWidget(self.graphics_view)
        
        # Add status bar
        self.status_label = QLabel("Ready - Upload a DXF file to begin")
        self.status_label.setStyleSheet("padding: 5px; background: #f0f0f0; border-top: 1px solid #ddd;")
        layout.addWidget(self.status_label)
        
        # Add placeholder text
        self.display_manager.add_placeholder_text("Drop a DXF file here or click Upload DXF")
        
        return panel
    
    def _create_toolbar(self):
        """Create the toolbar with actions."""
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(24, 24))
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 5px;
                padding: 5px;
                background: transparent;
            }
            QToolButton {
                padding: 8px;
                border-radius: 4px;
                background: #f0f0f0;
            }
            QToolButton:hover {
                background: #e0e0e0;
            }
            QToolButton:pressed {
                background: #d0d0d0;
            }
        """)
        
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
        
        toolbar.addSeparator()
        
        # Processing operations
        self.correct_action = QAction(QIcon.fromTheme("tools-check-spelling"), "Correct DXF", self)
        self.correct_action.setToolTip("Fix incomplete lines and errors")
        self.correct_action.triggered.connect(self.correct_dxf)
        self.correct_action.setEnabled(False)
        toolbar.addAction(self.correct_action)
        
        self.loops_action = QAction(QIcon.fromTheme("view-refresh"), "Detect Loops", self)
        self.loops_action.setToolTip("Detect and highlight loops")
        self.loops_action.triggered.connect(self.detect_loops)
        self.loops_action.setEnabled(False)
        toolbar.addAction(self.loops_action)
        
        return toolbar
    
    def _create_control_panel(self):
        """Create the control panel with tabs."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.tab_widget.addTab(self._create_info_tab(), "File Info")
        self.tab_widget.addTab(self._create_analysis_tab(), "Analysis")
        self.tab_widget.addTab(self._create_processing_tab(), "Processing")
        self.tab_widget.addTab(self._create_profile_tab(), "Profile")
        
        layout.addWidget(self.tab_widget)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        return panel
    
    def _create_info_tab(self):
        """Create the file information tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # File information group
        info_group = QGroupBox("File Information")
        info_layout = QFormLayout()
        
        self.file_name_field = QLineEdit()
        self.file_name_field.setReadOnly(True)
        self.file_size_field = QLineEdit()
        self.file_size_field.setReadOnly(True)
        self.dxf_version_field = QLineEdit()
        self.dxf_version_field.setReadOnly(True)
        self.units_field = QLineEdit()
        self.units_field.setReadOnly(True)
        
        info_layout.addRow("File Name:", self.file_name_field)
        info_layout.addRow("File Size:", self.file_size_field)
        info_layout.addRow("DXF Version:", self.dxf_version_field)
        info_layout.addRow("Units:", self.units_field)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Entity statistics group
        stats_group = QGroupBox("Entity Statistics")
        stats_layout = QFormLayout()
        
        self.total_entities_field = QLineEdit()
        self.total_entities_field.setReadOnly(True)
        self.layers_count_field = QLineEdit()
        self.layers_count_field.setReadOnly(True)
        self.lines_count_field = QLineEdit()
        self.lines_count_field.setReadOnly(True)
        self.arcs_count_field = QLineEdit()
        self.arcs_count_field.setReadOnly(True)
        
        stats_layout.addRow("Total Entities:", self.total_entities_field)
        stats_layout.addRow("Layers:", self.layers_count_field)
        stats_layout.addRow("Lines:", self.lines_count_field)
        stats_layout.addRow("Arcs:", self.arcs_count_field)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        layout.addStretch()
        return tab
    
    def _create_analysis_tab(self):
        """Create the analysis results tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Analysis results text area
        self.analysis_text = QTextEdit()
        self.analysis_text.setReadOnly(True)
        self.analysis_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.analysis_text)
        
        # Analysis buttons
        buttons_layout = QHBoxLayout()
        
        self.analyze_btn = QPushButton("Analyze File")
        self.analyze_btn.clicked.connect(self.analyze_file)
        self.analyze_btn.setEnabled(False)
        buttons_layout.addWidget(self.analyze_btn)
        
        self.export_analysis_btn = QPushButton("Export Analysis")
        self.export_analysis_btn.clicked.connect(self.export_analysis)
        self.export_analysis_btn.setEnabled(False)
        buttons_layout.addWidget(self.export_analysis_btn)
        
        layout.addLayout(buttons_layout)
        
        return tab
    
    def _create_processing_tab(self):
        """Create the processing operations tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Correction operations
        correction_group = QGroupBox("Correction Operations")
        correction_layout = QVBoxLayout()
        
        self.fix_lines_btn = QPushButton("Fix Incomplete Lines")
        self.fix_lines_btn.clicked.connect(self.fix_incomplete_lines)
        self.fix_lines_btn.setEnabled(False)
        correction_layout.addWidget(self.fix_lines_btn)
        
        self.remove_duplicates_btn = QPushButton("Remove Duplicates")
        self.remove_duplicates_btn.clicked.connect(self.remove_duplicates)
        self.remove_duplicates_btn.setEnabled(False)
        correction_layout.addWidget(self.remove_duplicates_btn)
        
        self.cleanup_btn = QPushButton("General Cleanup")
        self.cleanup_btn.clicked.connect(self.general_cleanup)
        self.cleanup_btn.setEnabled(False)
        correction_layout.addWidget(self.cleanup_btn)
        
        correction_group.setLayout(correction_layout)
        layout.addWidget(correction_group)
        
        # Loop detection operations
        loop_group = QGroupBox("Loop Detection")
        loop_layout = QVBoxLayout()
        
        self.detect_loops_btn = QPushButton("Detect All Loops")
        self.detect_loops_btn.clicked.connect(self.detect_loops)
        self.detect_loops_btn.setEnabled(False)
        loop_layout.addWidget(self.detect_loops_btn)
        
        self.find_largest_loop_btn = QPushButton("Find Largest Loop")
        self.find_largest_loop_btn.clicked.connect(self.find_largest_loop)
        self.find_largest_loop_btn.setEnabled(False)
        loop_layout.addWidget(self.find_largest_loop_btn)
        
        self.clear_highlights_btn = QPushButton("Clear Highlights")
        self.clear_highlights_btn.clicked.connect(self.clear_loop_highlights)
        self.clear_highlights_btn.setEnabled(False)
        loop_layout.addWidget(self.clear_highlights_btn)
        
        loop_group.setLayout(loop_layout)
        layout.addWidget(loop_group)
        
        layout.addStretch()
        return tab
    
    def _create_profile_tab(self):
        """Create the profile management tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Profile information
        profile_group = QGroupBox("Profile Information")
        profile_layout = QFormLayout()
        
        self.profile_name_field = QLineEdit()
        self.profile_name_field.setPlaceholderText("Enter profile name")
        self.profile_description_field = QLineEdit()
        self.profile_description_field.setPlaceholderText("Enter description")
        self.profile_category_combo = QComboBox()
        self.profile_category_combo.addItems([
            "Structural", "Mechanical", "Architectural", 
            "Electrical", "Piping", "HVAC", "Custom"
        ])
        
        profile_layout.addRow("Name:", self.profile_name_field)
        profile_layout.addRow("Description:", self.profile_description_field)
        profile_layout.addRow("Category:", self.profile_category_combo)
        
        profile_group.setLayout(profile_layout)
        layout.addWidget(profile_group)
        
        # Profile operations
        operations_layout = QHBoxLayout()
        
        self.save_profile_btn = QPushButton("Save Profile")
        self.save_profile_btn.clicked.connect(self.save_profile)
        self.save_profile_btn.setEnabled(False)
        operations_layout.addWidget(self.save_profile_btn)
        
        self.load_profile_btn = QPushButton("Load Profile")
        self.load_profile_btn.clicked.connect(self.load_profile)
        operations_layout.addWidget(self.load_profile_btn)
        
        layout.addLayout(operations_layout)
        
        layout.addStretch()
        return tab
    
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
        """Load a DXF file using the display manager."""
        try:
            self.status_label.setText("Loading DXF file...")
            
            # Load using display manager
            success = self.display_manager.load_dxf(filename)
            
            if success:
                self.current_file = filename
                self.current_doc = self.display_manager.get_current_doc()
                
                # Update UI
                self._update_file_info()
                self._enable_processing_buttons()
                
                self.status_label.setText(f"Loaded: {os.path.basename(filename)}")
            else:
                self.status_label.setText("Failed to load DXF file")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load DXF file: {str(e)}")
            self.status_label.setText("Error loading file")
    
    def _update_file_info(self):
        """Update the file information fields."""
        if not self.current_file:
            return
        
        file_path = Path(self.current_file)
        
        # Basic file info
        self.file_name_field.setText(file_path.name)
        self.file_size_field.setText(f"{file_path.stat().st_size / 1024:.1f} KB")
        
        if self.current_doc:
            self.dxf_version_field.setText(self.current_doc.dxfversion)
            
            # Get entity counts
            msp = self.current_doc.modelspace()
            entities = list(msp)
            
            entity_counts = {}
            for entity in entities:
                entity_type = entity.dxftype()
                entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            self.total_entities_field.setText(str(len(entities)))
            self.layers_count_field.setText(str(len(list(self.current_doc.layers))))
            self.lines_count_field.setText(str(entity_counts.get('LINE', 0)))
            self.arcs_count_field.setText(str(entity_counts.get('ARC', 0)))
    
    def _enable_processing_buttons(self):
        """Enable processing buttons when a file is loaded."""
        buttons = [
            self.correct_action, self.loops_action,
            self.analyze_btn, self.fix_lines_btn, self.remove_duplicates_btn,
            self.cleanup_btn, self.detect_loops_btn, self.find_largest_loop_btn,
            self.save_profile_btn
        ]
        
        for button in buttons:
            button.setEnabled(True)
    
    def analyze_file(self):
        """Perform comprehensive file analysis."""
        if not self.current_file:
            return
        
        self.status_label.setText("Analyzing file...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Run analysis in worker thread
        self.processing_worker = ProcessingWorker(
            self.analysis_engine.analyze_file, 
            self.current_file
        )
        self.processing_worker.processing_completed.connect(self._on_analysis_completed)
        self.processing_worker.error_occurred.connect(self._on_processing_error)
        self.processing_worker.start()
    
    def _on_analysis_completed(self, results):
        """Handle completed analysis."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Analysis completed")
        
        # Generate and display report
        report = self.analysis_engine.generate_report()
        self.analysis_text.setText(report)
        self.export_analysis_btn.setEnabled(True)
    
    def _on_processing_error(self, error_message):
        """Handle processing errors."""
        self.progress_bar.setVisible(False)
        self.status_label.setText("Processing error occurred")
        QMessageBox.critical(self, "Processing Error", error_message)
    
    def correct_dxf(self):
        """Apply DXF corrections."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Applying corrections...")
        
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
    
    def detect_loops(self):
        """Detect and highlight loops."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Detecting loops...")
        
        # Detect loops
        self.loop_detector.set_document(self.current_doc)
        loops_data = self.loop_detector.detect_loops()
        
        # Highlight loops
        success = self.loop_visualizer.highlight_loops(loops_data)
        
        if success:
            loop_count = loops_data.get('total_loops', 0)
            self.status_label.setText(f"Found and highlighted {loop_count} loops")
            self.clear_highlights_btn.setEnabled(True)
        else:
            self.status_label.setText("No loops found")
    
    def find_largest_loop(self):
        """Find and highlight the largest loop."""
        if not self.current_doc:
            return
        
        self.status_label.setText("Finding largest loop...")
        
        # Find largest loop
        self.loop_detector.set_document(self.current_doc)
        largest_loop = self.loop_detector.find_largest_loop()
        
        # Highlight largest loop
        success = self.loop_visualizer.highlight_largest_loop(largest_loop)
        
        if success:
            area = largest_loop.get('area', 0)
            self.status_label.setText(f"Highlighted largest loop (area: {area:.2f})")
            self.clear_highlights_btn.setEnabled(True)
        else:
            self.status_label.setText("No loops found")
    
    def clear_loop_highlights(self):
        """Clear loop highlights."""
        self.loop_visualizer.clear_highlights()
        self.clear_highlights_btn.setEnabled(False)
        self.status_label.setText("Loop highlights cleared")
    
    def fix_incomplete_lines(self):
        """Fix incomplete lines."""
        if not self.current_doc:
            return
        
        self.dxf_corrector.load_document(self.current_doc)
        result = self.dxf_corrector.fix_incomplete_lines()
        
        QMessageBox.information(self, "Fix Incomplete Lines", result.get('message', 'Operation completed'))
        self.display_manager.refresh_view()
    
    def remove_duplicates(self):
        """Remove duplicate entities."""
        if not self.current_doc:
            return
        
        self.dxf_corrector.load_document(self.current_doc)
        result = self.dxf_corrector.remove_duplicates()
        
        QMessageBox.information(self, "Remove Duplicates", result.get('message', 'Operation completed'))
        self.display_manager.refresh_view()
    
    def general_cleanup(self):
        """Perform general cleanup operations."""
        if not self.current_doc:
            return
        
        # Apply various cleanup operations
        results = []
        
        # Cleanup layers
        layer_result = self.cleanup_tools.cleanup_layers(self.current_doc)
        results.append(layer_result.get('message', 'Layer cleanup completed'))
        
        # Optimize entities
        entity_result = self.cleanup_tools.optimize_entities(self.current_doc)
        results.append(entity_result.get('message', 'Entity optimization completed'))
        
        # Show results
        message = "Cleanup operations completed:\n" + "\n".join(results)
        QMessageBox.information(self, "General Cleanup", message)
        self.display_manager.refresh_view()
    
    def save_profile(self):
        """Save the current profile."""
        if not self.current_doc:
            return
        
        # Get profile information
        name = self.profile_name_field.text().strip()
        if not name:
            QMessageBox.warning(self, "Save Profile", "Please enter a profile name")
            return
        
        description = self.profile_description_field.text().strip()
        category = self.profile_category_combo.currentText()
        
        # Create profile data
        profile_data = {
            'name': name,
            'description': description,
            'category': category,
            'source_file': self.current_file
        }
        
        # Add analysis data if available
        if hasattr(self.analysis_engine, 'current_analysis') and self.analysis_engine.current_analysis:
            profile_data.update(self.analysis_engine.current_analysis)
        
        # Save profile
        result = self.profile_manager.create_profile(profile_data)
        
        if result.get('success'):
            QMessageBox.information(self, "Save Profile", "Profile saved successfully")
        else:
            QMessageBox.critical(self, "Save Profile", f"Failed to save profile: {result.get('error')}")
    
    def load_profile(self):
        """Load an existing profile."""
        # This would open a profile selection dialog
        # For now, just show a placeholder message
        QMessageBox.information(self, "Load Profile", "Profile loading functionality will be implemented")
    
    def export_analysis(self):
        """Export analysis results."""
        if not hasattr(self.analysis_engine, 'current_analysis'):
            return
        
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Export Analysis",
            "analysis_report.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if file_name:
            try:
                report = self.analysis_engine.generate_report()
                with open(file_name, 'w') as f:
                    f.write(report)
                QMessageBox.information(self, "Export Analysis", "Analysis exported successfully")
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export analysis: {str(e)}")
    
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
            if urls and urls[0].toLocalFile().lower().endswith('.dxf'):
                event.acceptProposedAction()
    
    def dropEvent(self, event: QDropEvent):
        """Handle drop events."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                file_path = urls[0].toLocalFile()
                if file_path.lower().endswith('.dxf'):
                    self.load_dxf(file_path)
                    event.acceptProposedAction() 