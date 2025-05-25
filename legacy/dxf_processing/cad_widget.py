from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                            QGraphicsView, QGraphicsScene, QLabel, QGraphicsProxyWidget,
                            QGroupBox, QFormLayout, QLineEdit, QSplitter, QMessageBox,
                            QFileDialog, QToolBar, QAction)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QFont, QDragEnterEvent, QDropEvent, QPen
from PyQt5.QtCore import Qt, QRectF, QMimeData, QSize
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
try:
    from ezdxf.addons.drawing.config import Configuration
except ImportError:
    # Fallback for older versions
    Configuration = None
from ezdxf.addons.drawing.pyqt import PyQtBackend
from .viewer import DXFViewer
import json
import os
from utils import connect_segments

class CADWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_dxf = None
        self.placeholder_label = None
        self.placeholder_proxy = None
        
        # Enable drag and drop
        self.setAcceptDrops(True)
        
        # Create main layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create splitter for CAD viewer and control panel
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        
        # Left panel (CAD viewer)
        cad_panel = QWidget()
        cad_layout = QVBoxLayout(cad_panel)
        cad_layout.setContentsMargins(0, 0, 0, 0)
        
        # Add toolbar at the top
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
        
        # Add zoom controls
        zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon()), "Zoom In", self)
        zoom_in_action.setToolTip("Zoom In (Mouse Wheel Up)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon()), "Zoom Out", self)
        zoom_out_action.setToolTip("Zoom Out (Mouse Wheel Down)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        # Add fit to view button
        fit_action = QAction(QIcon.fromTheme("zoom-fit-best", QIcon()), "Fit to View", self)
        fit_action.setToolTip("Fit Drawing to View (Ctrl+0)")
        fit_action.triggered.connect(self.fit_to_view)
        toolbar.addAction(fit_action)
        
        toolbar.addSeparator()
        
        # Create upload button
        self.upload_btn = QPushButton("Upload DXF")
        self.upload_btn.setIcon(QIcon('gui/upload_icon.png'))
        self.upload_btn.setToolTip("Upload DXF File")
        self.upload_btn.clicked.connect(self.upload_dxf)
        self.upload_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                background-color: #2196F3;
                color: white;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        toolbar.addWidget(self.upload_btn)
        
        # Create expand button
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(QIcon('gui/expand_icon.png'))
        self.expand_btn.setToolTip("View in Full Screen")
        self.expand_btn.clicked.connect(self.open_fullscreen)
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.setEnabled(False)  # Disabled until a DXF is loaded
        toolbar.addWidget(self.expand_btn)
        
        cad_layout.addWidget(toolbar)
        
        # Create the graphics view for the DXF
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setBackgroundBrush(QBrush(
            QColor(self.parent.colors['background'].name())
        ))
        
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        cad_layout.addWidget(self.graphics_view)
        
        # Right panel (Controls)
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(15, 15, 15, 15)
        control_layout.setSpacing(20)
        
        # Input Information Group
        input_group = QGroupBox("Input Information")
        input_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        input_layout = QFormLayout()
        input_layout.setSpacing(15)
        
        # Add sketch and profile number fields
        self.sketch_number = QLineEdit()
        self.sketch_number.setToolTip("Enter the sketch number for this profile")
        self.profile_number = QLineEdit()
        self.profile_number.setToolTip("Enter the profile number for this sketch")
        input_layout.addRow("Sketch Number:", self.sketch_number)
        input_layout.addRow("Profile Number:", self.profile_number)
        input_group.setLayout(input_layout)
        
        # Parameters Group
        parameters_group = QGroupBox("Processed Parameters")
        parameters_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        parameters_layout = QFormLayout()
        parameters_layout.setSpacing(15)
        
        # Add parameter fields
        self.parameter_fields = {}
        parameters = ['Length', 'Width', 'Height', 'Material', 'Thickness']
        for param in parameters:
            field = QLineEdit()
            field.setReadOnly(True)
            field.setToolTip(f"Calculated {param.lower()} of the profile")
            field.setStyleSheet("""
                QLineEdit {
                    background-color: #f8f8f8;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 8px;
                    color: #666;
                }
            """)
            self.parameter_fields[param] = field
            parameters_layout.addRow(f"{param}:", field)
        
        parameters_group.setLayout(parameters_layout)
        
        # Action Buttons Group
        actions_group = QGroupBox("Actions")
        actions_group.setFont(QFont("Segoe UI", 10, QFont.Bold))
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(12)
        
        # Add action buttons
        self.correct_dxf_btn = QPushButton("Correct DXF")
        self.correct_dxf_btn.setToolTip("Fix incomplete lines in the DXF file")
        self.correct_dxf_btn.clicked.connect(self.correct_dxf)
        
        self.display_loops_btn = QPushButton("Display Loops")
        self.display_loops_btn.setToolTip("Highlight loops in the diagram")
        self.display_loops_btn.clicked.connect(self.display_loops)
        
        self.process_btn = QPushButton("Process")
        self.process_btn.setToolTip("Calculate and display profile parameters")
        self.process_btn.clicked.connect(self.process_profile)
        
        self.upload_profile_btn = QPushButton("Upload New Profile")
        self.upload_profile_btn.setToolTip("Save the current profile information")
        self.upload_profile_btn.clicked.connect(self.upload_profile)
        
        # Apply style to buttons
        button_style = """
            QPushButton {
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 40px;
                background-color: #2196F3;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #BDBDBD;
                color: #757575;
            }
        """
        
        for btn in [self.correct_dxf_btn, self.display_loops_btn, 
                   self.process_btn, self.upload_profile_btn]:
            btn.setStyleSheet(button_style)
        
        actions_layout.addWidget(self.correct_dxf_btn)
        actions_layout.addWidget(self.display_loops_btn)
        actions_layout.addWidget(self.process_btn)
        actions_layout.addWidget(self.upload_profile_btn)
        actions_group.setLayout(actions_layout)
        
        # Add groups to control panel
        control_layout.addWidget(input_group)
        control_layout.addWidget(parameters_group)
        control_layout.addWidget(actions_group)
        control_layout.addStretch()
        
        # Add panels to splitter
        splitter.addWidget(cad_panel)
        splitter.addWidget(control_panel)
        splitter.setStretchFactor(0, 3)  # CAD viewer gets more space (75%)
        splitter.setStretchFactor(1, 1)  # Control panel gets less space (25%)
        
        main_layout.addWidget(splitter)
        
        # Add placeholder text
        self.add_placeholder("Drag and drop a DXF file here or click Upload DXF")
        
    def add_placeholder(self, text, is_error=False):
        """Add placeholder text to the view"""
        if self.placeholder_proxy:
            self.graphics_scene.removeItem(self.placeholder_proxy)
            
        self.placeholder_label = QLabel(text)
        self.placeholder_label.setStyleSheet(f"""
            color: {'red' if is_error else 'gray'};
            font-size: 14px;
            padding: 20px;
        """)
        
        # Center the label in the scene
        self.placeholder_proxy = self.graphics_scene.addWidget(self.placeholder_label)
        self.placeholder_proxy.setPos(
            (self.graphics_view.width() - self.placeholder_proxy.boundingRect().width()) / 2,
            (self.graphics_view.height() - self.placeholder_proxy.boundingRect().height()) / 2
        )
        
    def load_dxf(self, filename):
        """Load and render a DXF file"""
        # Check if there's an existing DXF and unsaved changes
        if self.current_dxf and self.has_unsaved_changes():
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. If you continue, these changes will be lost and cannot be recovered. Do you want to continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        self.current_dxf = filename
        self.expand_btn.setEnabled(True)
        self.graphics_scene.clear()
        
        try:
            # Load the DXF file
            doc = ezdxf.readfile(filename)
            
            # Set up render context
            context = RenderContext(doc)
            backend = PyQtBackend(self.graphics_scene)
            
            # Configure the frontend with theme-aware colors
            line_color = '#000000' if not self.parent.dark_mode else '#ffffff'
            background_color = '#ffffff' if not self.parent.dark_mode else '#2b2b2b'
            
            # Try to create configuration object for newer ezdxf versions
            config = None
            if Configuration is not None:
                try:
                    config = Configuration(
                        background_color=background_color,
                        default_color=line_color,
                        lineweight_scaling=1.0,
                        min_lineweight=0.13,
                        max_lineweight=2.11,
                        pdsize=1,  # Point display size
                        pdmode=0,  # Point display mode
                        linetype_scaling=1.0,
                        hatch_transparency=255,  # No transparency
                        measurement=None  # Let ezdxf determine from DXF
                    )
                except Exception:
                    config = None
            
            # Create frontend - with or without configuration
            if config is not None:
                frontend = Frontend(context, backend, config)
            else:
                # Fallback for older versions - use default configuration
                frontend = Frontend(context, backend)
            
            # Render the model space entities
            frontend.draw_layout(doc.modelspace())
            
            # Post-process items to ensure correct colors for the current theme
            self._fix_item_colors()
            
            # Render the model space entities
            frontend.draw_layout(doc.modelspace())
            
            # Check if we have items in the scene
            if len(self.graphics_scene.items()) == 0:
                self.add_placeholder("DXF file loaded but no visible entities found", True)
                return
                
            # Make sure we can see the content
            self.graphics_view.resetTransform()
            
            # Get the bounding rectangle
            bounds = self.graphics_scene.itemsBoundingRect()
            
            if bounds.width() < 1 or bounds.height() < 1:
                # Set a minimum size to avoid scaling issues
                bounds = QRectF(bounds.x(), bounds.y(), max(bounds.width(), 10), max(bounds.height(), 10))
            
            # Update the scene rect to match the bounds
            self.graphics_scene.setSceneRect(bounds.adjusted(-10, -10, 10, 10))
            
            # Fit everything into view with a margin
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
            
            # Force update
            self.graphics_view.update()
            
        except Exception as e:
            print(f"Error loading DXF: {str(e)}")
            import traceback
            traceback.print_exc()
            try:
                self.add_placeholder(f"Failed to load DXF file: {str(e)}", True)
            except RuntimeError:
                # If the placeholder widget was deleted, create a new one
                self.placeholder_proxy = None
                self.add_placeholder(f"Failed to load DXF file: {str(e)}", True)
            
    def extract_dxf_info(self, doc):
        """Extract information from the DXF file"""
        info = {
            'entities': [],
            'layers': [],
            'dimensions': {},
            'metadata': {}
        }
        
        # Get model space
        msp = doc.modelspace()
        
        # Count entities by type
        entity_counts = {}
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
            
            # Add to entities list
            info['entities'].append({
                'type': entity_type,
                'handle': entity.dxf.handle,
                'layer': entity.dxf.layer
            })
            
            # Add layer if not already in list
            if entity.dxf.layer not in info['layers']:
                info['layers'].append(entity.dxf.layer)
                
        # Add entity counts to metadata
        info['metadata']['entity_counts'] = entity_counts
        
        # Get drawing dimensions
        try:
            # Try to get bounding box using extents
            extents = msp.get_extents()
            if extents:
                info['dimensions'] = {
                    'width': extents.max.x - extents.min.x,
                    'height': extents.max.y - extents.min.y,
                    'min_x': extents.min.x,
                    'min_y': extents.min.y,
                    'max_x': extents.max.x,
                    'max_y': extents.max.y
                }
        except:
            # Fallback: calculate manually
            try:
                x_coords = []
                y_coords = []
                for entity in msp:
                    if hasattr(entity, 'get_points'):
                        points = list(entity.get_points())
                        if points:
                            x_coords.extend([p.x for p in points])
                            y_coords.extend([p.y for p in points])
                
                if x_coords and y_coords:
                    info['dimensions'] = {
                        'width': max(x_coords) - min(x_coords),
                        'height': max(y_coords) - min(y_coords),
                        'min_x': min(x_coords),
                        'min_y': min(y_coords),
                        'max_x': max(x_coords),
                        'max_y': max(y_coords)
                    }
            except:
                pass
                
        return info
        
    def open_fullscreen(self):
        """Open the DXF in a fullscreen viewer"""
        if self.current_dxf:
            viewer = DXFViewer(self.parent, self.current_dxf, self.parent.dark_mode)
            viewer.exec_()
            
    def resizeEvent(self, event):
        """Handle resize events to keep the drawing properly scaled"""
        super().resizeEvent(event)
        if self.current_dxf and not self.graphics_scene.items() == []:
            self.fit_to_view()
            
    def showEvent(self, event):
        """Handle show events to ensure the drawing is properly displayed"""
        super().showEvent(event)
        if self.current_dxf and not self.graphics_scene.items() == []:
            self.fit_to_view()
            
    def _fix_item_colors(self):
        """Fix the colors of rendered items based on the current theme"""
        target_color = QColor('#000000') if not self.parent.dark_mode else QColor('#ffffff')
        
        for item in self.graphics_scene.items():
            try:
                # Handle different types of graphics items
                if hasattr(item, 'pen'):
                    current_pen = item.pen()
                    # Check if the current color is problematic (white in light mode, black in dark mode)
                    current_color = current_pen.color()
                    
                    # In light mode, change white/light colors to black
                    # In dark mode, change black/dark colors to white
                    if not self.parent.dark_mode:
                        if (current_color.name().lower() in ['#ffffff', '#white'] or 
                            current_color.lightness() > 200):
                            new_pen = QPen(current_pen)
                            new_pen.setColor(target_color)
                            item.setPen(new_pen)
                    else:
                        if (current_color.name().lower() in ['#000000', '#black'] or 
                            current_color.lightness() < 55):
                            new_pen = QPen(current_pen)
                            new_pen.setColor(target_color)
                            item.setPen(new_pen)
                            
                elif hasattr(item, 'brush'):
                    # Handle filled items
                    current_brush = item.brush()
                    if current_brush.style() != Qt.NoBrush:
                        current_color = current_brush.color()
                        
                        if not self.parent.dark_mode:
                            if (current_color.name().lower() in ['#ffffff', '#white'] or 
                                current_color.lightness() > 200):
                                new_brush = QBrush(current_brush)
                                new_brush.setColor(target_color)
                                item.setBrush(new_brush)
                        else:
                            if (current_color.name().lower() in ['#000000', '#black'] or 
                                current_color.lightness() < 55):
                                new_brush = QBrush(current_brush)
                                new_brush.setColor(target_color)
                                item.setBrush(new_brush)
                                
            except Exception as e:
                # Skip items that can't be processed
                continue
                
    def refresh_view(self):
        """Refresh the view"""
        if self.current_dxf:
            self.load_dxf(self.current_dxf)
            
    def fit_to_view(self):
        """Fit the entire drawing to the view"""
        if not self.graphics_scene.items():
            return
            
        bounds = self.graphics_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            # Add a small margin around the content
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
            
    def correct_dxf(self):
        """Handle DXF correction: connect broken/disconnected line and arc segments"""
        if not self.current_dxf:
            QMessageBox.warning(self, "No DXF Loaded", "Please load a DXF file first.")
            return
        try:
            # Load the DXF document
            doc = ezdxf.readfile(self.current_dxf)
            msp = doc.modelspace()
            # Extract line and arc entities
            entities = [e for e in msp if e.dxftype() in ("LINE", "ARC")]
            # Connect segments
            new_entities = connect_segments(entities)
            num_added = len(new_entities) - len(entities)
            # Remove old lines/arcs
            for e in entities:
                msp.delete_entity(e)
            # Add back original and new entities
            for e in new_entities:
                msp.add_entity(e)
            # Save to a temp file and reload
            temp_path = self.current_dxf + ".corrected.dxf"
            doc.saveas(temp_path)
            self.load_dxf(temp_path)
            QMessageBox.information(self, "DXF Correction Complete", f"Correction complete. {num_added} connections added. View updated.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to correct DXF: {str(e)}")
        
    def display_loops(self):
        """Handle loop display"""
        QMessageBox.information(self, "Info", "Loop display functionality will be implemented later")
        
    def process_profile(self):
        """Handle profile processing"""
        QMessageBox.information(self, "Info", "Profile processing functionality will be implemented later")
        
    def upload_profile(self):
        """Handle profile upload"""
        # For now, just save the information locally
        profile_data = {
            'sketch_number': self.sketch_number.text(),
            'profile_number': self.profile_number.text(),
            'parameters': {param: field.text() for param, field in self.parameter_fields.items()}
        }
        
        # Save to a local JSON file
        try:
            with open('profile_data.json', 'w') as f:
                json.dump(profile_data, f, indent=4)
            QMessageBox.information(self, "Success", "Profile data saved locally to profile_data.json")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile data: {str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.dxf') for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        """Handle drop events"""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.dxf'):
                    self.load_dxf(file_path)
                    break

    def upload_dxf(self):
        """Handle DXF file upload"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF File",
            "",
            "DXF Files (*.dxf);;All Files (*.*)"
        )
        if file_name:
            self.load_dxf(file_name)

    def has_unsaved_changes(self):
        """Check if there are unsaved changes"""
        # For now, just check if any parameter fields have been modified
        return any(field.text() for field in self.parameter_fields.values())

    def zoom_in(self):
        """Zoom in by scaling the view"""
        self.graphics_view.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out by scaling the view"""
        self.graphics_view.scale(1/1.2, 1/1.2)

    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()