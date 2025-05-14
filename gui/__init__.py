import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QComboBox, QFileDialog, QTabWidget, 
                             QTextEdit, QGroupBox, QGridLayout, QMessageBox, QSplitter,
                             QCheckBox, QGraphicsView, QGraphicsScene, QGraphicsItem,
                             QDialog, QShortcut, QToolBar, QAction, QGraphicsProxyWidget)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPen, QBrush, QKeySequence, QTransform, QPainter
from PyQt5.QtCore import Qt, QSize, QRectF, QPointF
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.pyqt import PyQtBackend

class DXFViewer(QDialog):
    def __init__(self, parent=None, dxf_file=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.setWindowTitle("DXF Viewer")
        self.setGeometry(100, 100, 800, 600)
        self.dxf_file = dxf_file
        
        # Set up the layout
        main_layout = QVBoxLayout(self)
        
        # Create toolbar
        toolbar = QToolBar()
        
        # Add zoom in/out buttons
        zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon()), "Zoom In", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon()), "Zoom Out", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        # Add fit to view button
        fit_action = QAction(QIcon.fromTheme("zoom-fit-best", QIcon()), "Fit to View", self)
        fit_action.triggered.connect(self.fit_to_view)
        toolbar.addAction(fit_action)
        
        main_layout.addWidget(toolbar)
        
        # Create graphics view for the DXF display
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.graphics_view.setBackgroundBrush(QBrush(
            QColor(self.parent().colors['background'].name())
        ))
        
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        main_layout.addWidget(self.graphics_view)
        
        # Set up keyboard shortcuts
        QShortcut(QKeySequence.ZoomIn, self, self.zoom_in)
        QShortcut(QKeySequence.ZoomOut, self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.fit_to_view)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        
        # Load the DXF file if provided
        if self.dxf_file:
            self.load_dxf(self.dxf_file)
            
        # Apply theme
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the current theme to the dialog"""
        # Get colors from parent
        colors = self.parent().colors
        
        # Set up the stylesheet
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {colors['background'].name()};
                color: {colors['text'].name()};
            }}
            
            QToolBar {{
                background-color: {colors['surface'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                spacing: 5px;
                padding: 2px;
            }}
            
            QToolBar QToolButton {{
                background-color: {colors['primary'].name()};
                color: white;
                border-radius: 4px;
                padding: 4px;
                margin: 2px;
            }}
            
            QToolBar QToolButton:hover {{
                background-color: {colors['secondary'].name()};
            }}
            
            QGraphicsView {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                background-color: {colors['surface'].name()};
                color: {'#000' if not self.dark_mode else '#fff'};
            }}
        """)
        
    def load_dxf(self, filename):
        """Load and render a DXF file"""
        self.dxf_file = filename
        self.setWindowTitle(f"DXF Viewer - {os.path.basename(filename)}")
        self.graphics_scene.clear()
        
        try:
            # Print debug info
            print(f"Loading DXF in popup viewer: {filename}")
            
            # Load the DXF file
            doc = ezdxf.readfile(filename)
            
            # Count entities
            msp = doc.modelspace()
            entity_count = sum(1 for _ in msp)
            print(f"Fullscreen viewer entity count: {entity_count}")
            
            # Set up render context with default config
            context = RenderContext(doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            # Render the model space entities
            frontend.draw_layout(doc.modelspace())
            
            # Check if we have items in the scene
            item_count = len(self.graphics_scene.items()) 
            print(f"Fullscreen graphics scene items: {item_count}")
            
            if item_count == 0:
                self.show_error_message("DXF file loaded but no visible entities found")
                return
                
            # Make sure we can see the content (reset view transforms)
            self.graphics_view.resetTransform()
            
            # Get the bounding rectangle
            bounds = self.graphics_scene.itemsBoundingRect()
            print(f"Fullscreen scene bounds: {bounds}")
            
            if bounds.width() < 1 or bounds.height() < 1:
                print("Warning: Very small or invalid bounding box in fullscreen view")
                # Set a minimum size to avoid scaling issues
                bounds = QRectF(bounds.x(), bounds.y(), max(bounds.width(), 10), max(bounds.height(), 10))
            
            # Update the scene rect to match the bounds
            self.graphics_scene.setSceneRect(bounds.adjusted(-10, -10, 10, 10))
            
            # Fit everything into view with a margin
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
            
            # Force update
            self.graphics_view.update()
            
        except Exception as e:
            print(f"Error loading DXF in fullscreen: {str(e)}")
            import traceback
            traceback.print_exc()
            self.show_error_message(f"Failed to load DXF file: {str(e)}")
    
    def show_error_message(self, message):
        """Show an error message in a QMessageBox"""
        QMessageBox.critical(self, "Error", message)
    
    def zoom_in(self):
        """Zoom in by scaling the view"""
        self.graphics_view.scale(1.2, 1.2)
        
    def zoom_out(self):
        """Zoom out by scaling the view"""
        self.graphics_view.scale(1/1.2, 1/1.2)
        
    def fit_to_view(self):
        """Fit the entire drawing to the view"""
        bounds = self.graphics_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            # Add a small margin around the content
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
        
    def wheelEvent(self, event):
        """Handle mouse wheel events for zooming"""
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def resizeEvent(self, event):
        """Handle resize events to keep the drawing properly scaled"""
        super().resizeEvent(event)
        QApplication.processEvents()  # Make sure the resize is processed
        if self.dxf_file and not self.graphics_scene.items() == []:
            # Refit the view when the dialog is resized
            self.fit_to_view()
            
    def showEvent(self, event):
        """Handle show events to ensure the drawing is properly displayed"""
        super().showEvent(event)
        QApplication.processEvents()  # Make sure the show is processed
        if self.dxf_file and not self.graphics_scene.items() == []:
            # Fit the view when the dialog is shown
            self.fit_to_view()

class CADWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_dxf = None
        self.placeholder_label = None
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Add controls at the top
        controls_layout = QHBoxLayout()
        controls_layout.setAlignment(Qt.AlignRight)
        
        # Create expand button
        self.expand_btn = QPushButton()
        self.expand_btn.setIcon(QIcon('gui/expand_icon.png'))
        self.expand_btn.setToolTip("View in Full Screen")
        self.expand_btn.clicked.connect(self.open_fullscreen)
        self.expand_btn.setFixedSize(32, 32)
        self.expand_btn.setEnabled(False)  # Disabled until a DXF is loaded
        controls_layout.addWidget(self.expand_btn)
        
        layout.addLayout(controls_layout)
        
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
        
        layout.addWidget(self.graphics_view)
        
        # Add placeholder text when no DXF is loaded
        self.add_placeholder("No DXF loaded\nUse 'Upload DXF' to load a file")
        
    def add_placeholder(self, text, is_error=False):
        """Add a placeholder text to the graphics scene"""
        # Clear any existing placeholder
        if self.placeholder_label is not None:
            self.graphics_scene.removeItem(self.graphics_scene.items()[-1])
            self.placeholder_label = None
            
        # Create new placeholder
        self.placeholder_label = QLabel(text)
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setStyleSheet(f"""
            color: {self.parent.colors['error' if is_error else 'text_light'].name()};
            font-size: 14px;
            background: transparent;
        """)
        self.graphics_scene.addWidget(self.placeholder_label)
        
    def load_dxf(self, filename):
        """Load and render a DXF file"""
        self.current_dxf = filename
        
        # Completely clear the scene
        self.graphics_scene.clear()
        self.placeholder_label = None
        
        try:
            # Print debug info
            print(f"Loading DXF: {filename}")
            
            # Load the DXF file
            doc = ezdxf.readfile(filename)
            
            # Count entities
            msp = doc.modelspace()
            entity_count = sum(1 for _ in msp)
            print(f"Entity count: {entity_count}")
            
            # Extract DXF information
            info = self.extract_dxf_info(doc)
            
            # Set up render context with default config
            context = RenderContext(doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            # Render the model space entities
            frontend.draw_layout(doc.modelspace())
            
            # Check if we have items in the scene
            item_count = len(self.graphics_scene.items()) 
            print(f"Graphics scene items: {item_count}")
            
            if item_count == 0:
                self.add_placeholder("DXF file loaded but no visible entities found", True)
                return False
                
            # Enable the expand button
            self.expand_btn.setEnabled(True)
            
            # Make sure we can see the content (reset view transforms)
            self.graphics_view.resetTransform()
            
            # Get the bounding rectangle
            bounds = self.graphics_scene.itemsBoundingRect()
            print(f"Scene bounds: {bounds}")
            
            if bounds.width() < 1 or bounds.height() < 1:
                print("Warning: Very small or invalid bounding box")
                # Set a minimum size to avoid scaling issues
                bounds = QRectF(bounds.x(), bounds.y(), max(bounds.width(), 10), max(bounds.height(), 10))
            
            # Update the scene rect to match the bounds
            self.graphics_scene.setSceneRect(bounds.adjusted(-10, -10, 10, 10))
            
            # Fit everything into view with a margin
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
            
            # Force update
            self.graphics_view.update()
            
            # Return the info dict if successful
            return info
            
        except Exception as e:
            print(f"Error loading DXF: {str(e)}")
            import traceback
            traceback.print_exc()
            
            # Add the placeholder back
            self.add_placeholder(f"Failed to load DXF file: {str(e)}", True)
            
            # Return False if failed
            return False
    
    def extract_dxf_info(self, doc):
        """Extract basic information from a DXF document"""
        info = {}
        
        # Get DXF version
        info['DXF Version'] = doc.dxfversion
        
        # Get drawing units
        units = {
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
        try:
            unit = doc.header.get('$INSUNITS', 0)
            info['Units'] = units.get(unit, 'Unknown')
        except:
            info['Units'] = 'Unknown'
        
        # Count entities in model space
        msp = doc.modelspace()
        entity_counts = {}
        
        for entity in msp:
            entity_type = entity.dxftype()
            entity_counts[entity_type] = entity_counts.get(entity_type, 0) + 1
        
        info['Entity Counts'] = entity_counts
        
        # Get extents if available
        try:
            extmin = doc.header.get('$EXTMIN')
            extmax = doc.header.get('$EXTMAX')
            if extmin and extmax:
                width = extmax[0] - extmin[0]
                height = extmax[1] - extmin[1]
                info['Width'] = f"{width:.2f}"
                info['Height'] = f"{height:.2f}"
                info['Area'] = f"{width * height:.2f}"
        except:
            pass
        
        return info
    
    def open_fullscreen(self):
        """Open the full screen DXF viewer"""
        if self.current_dxf:
            viewer = DXFViewer(self.parent, self.current_dxf, self.parent.dark_mode)
            viewer.exec_()

    def resizeEvent(self, event):
        """Handle resize events to keep the drawing properly scaled"""
        super().resizeEvent(event)
        QApplication.processEvents()  # Make sure the resize is processed
        self.refresh_view()
            
    def showEvent(self, event):
        """Handle show events to ensure the drawing is properly displayed"""
        super().showEvent(event)
        QApplication.processEvents()  # Make sure the show is processed
        self.refresh_view()
    
    def refresh_view(self):
        """Refresh the view to ensure the drawing is properly displayed"""
        if self.current_dxf and not self.graphics_scene.items() == []:
            # Get the bounding rectangle
            bounds = self.graphics_scene.itemsBoundingRect()
            if not bounds.isEmpty():
                # Add a small margin and fit to view
                self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
                print(f"View refreshed with bounds: {bounds}")

class DXFProfileAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.apply_theme()
        self.initUI()

    def initUI(self):
        # Set window properties
        self.setWindowTitle('DXF Profile Analyzer V3')
        self.setGeometry(100, 100, 1200, 800)

        # Create central widget and main layout
        central_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(12)
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create theme toggle in a horizontal layout
        theme_layout = QHBoxLayout()
        theme_layout.setAlignment(Qt.AlignRight)
        
        self.theme_toggle = QCheckBox("Dark Theme")
        self.theme_toggle.setChecked(self.dark_mode)
        self.theme_toggle.stateChanged.connect(self.toggle_theme)
        theme_layout.addWidget(self.theme_toggle)
        
        main_layout.addLayout(theme_layout)

        # Create top control section
        top_control = self.create_top_control_section()
        main_layout.addWidget(top_control)

        # Create main tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setMovable(True)
        main_layout.addWidget(self.tab_widget)

        # Add tabs
        self.tab_widget.addTab(self.create_cad_viewer_tab(), "CAD Viewer")
        self.tab_widget.addTab(self.create_feature_comparison_tab(), "Feature Comparison")
        self.tab_widget.addTab(self.create_image_comparison_tab(), "Image Comparison")
        self.tab_widget.addTab(self.create_best_match_tab(), "Best Match")
        self.tab_widget.addTab(self.create_die_prediction_tab(), "Die Prediction")
        
        # Select the CAD Viewer tab by default
        self.tab_widget.setCurrentIndex(0)

        # Status bar
        self.statusBar().showMessage('Ready')
        self.statusBar().setFont(QFont("Segoe UI", 9))

    def apply_theme(self):
        """Apply a consistent visual theme to the application"""
        # Define light and dark color palettes
        light_colors = {
            'primary': QColor(156, 39, 176),    # Purple
            'secondary': QColor(186, 104, 200), # Light Purple
            'accent': QColor(255, 87, 34),      # Deep Orange
            'background': QColor(248, 249, 250),
            'surface': QColor(255, 255, 255),
            'text': QColor(44, 62, 80),
            'text_light': QColor(127, 140, 141),
            'error': QColor(231, 76, 60)
        }
        
        dark_colors = {
            'primary': QColor(124, 77, 255),    # Purple
            'secondary': QColor(157, 126, 245), # Light Purple
            'accent': QColor(255, 111, 0),      # Orange
            'background': QColor(33, 33, 33),
            'surface': QColor(48, 48, 48),
            'text': QColor(237, 240, 242),
            'text_light': QColor(176, 182, 186),
            'error': QColor(255, 82, 82)
        }
        
        # Set colors based on theme
        self.colors = dark_colors if self.dark_mode else light_colors
        
        # Set application style
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {self.colors['background'].name()};
                color: {self.colors['text'].name()};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                background-color: {self.colors['surface'].name()};
            }}
            
            QTabBar::tab {{
                background-color: {'#444' if self.dark_mode else '#e6e6e6'};
                color: {self.colors['text'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-bottom-color: transparent;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['surface'].name()};
                border-bottom-color: {self.colors['surface'].name()};
                border-top: 2px solid {self.colors['primary'].name()};
            }}
            
            QTabBar::tab:hover:!selected {{
                background-color: {'#505050' if self.dark_mode else '#f2f2f2'};
            }}
            
            QPushButton {{
                background-color: {self.colors['primary'].name()};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['secondary'].name()};
                border: 1px solid {self.colors['primary'].name()};
            }}
            
            QPushButton:pressed {{
                background-color: {'#6200ea' if self.dark_mode else '#7b1fa2'};
            }}
            
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                margin-top: 1.5ex;
                padding-top: 1.5ex;
                background-color: {self.colors['surface'].name()};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                color: {self.colors['text'].name()};
            }}
            
            QComboBox {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                padding: 5px 10px;
                background-color: {'#3a3a3a' if self.dark_mode else 'white'};
                min-width: 100px;
            }}
            
            QComboBox::drop-down {{
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid {'#555' if self.dark_mode else '#ddd'};
            }}
            
            QLabel {{
                color: {self.colors['text'].name()};
            }}
            
            QTextEdit {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                background-color: {'#3a3a3a' if self.dark_mode else 'white'};
            }}
            
            QCheckBox {{
                color: {self.colors['text'].name()};
                spacing: 5px;
            }}
            
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 3px;
                border: 1px solid {'#777' if self.dark_mode else '#ccc'};
            }}
            
            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary'].name()};
                border: 1px solid {self.colors['primary'].name()};
                image: url(check.png);
            }}
            
            QCheckBox::indicator:unchecked:hover {{
                border: 1px solid {self.colors['primary'].name()};
            }}
            
            QStatusBar {{
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text_light'].name()};
                border-top: 1px solid {'#555' if self.dark_mode else '#ddd'};
            }}
        """)
        
        # Set default font
        app_font = QFont("Segoe UI", 10)
        QApplication.setFont(app_font)
        
    def toggle_theme(self, state):
        """Toggle between light and dark theme"""
        self.dark_mode = (state == Qt.Checked)
        self.apply_theme()
        
        # Update placeholder colors and styles that were set directly
        self.update_component_styles()
        
    def update_component_styles(self):
        """Update styles for components that need special handling after theme change"""
        # This method updates components that were styled directly (not via stylesheet)
        self.statusBar().setFont(QFont("Segoe UI", 9))
        
        # Update Process button style
        for child in self.findChildren(QPushButton):
            if child.text() == "Process" or child.text() == "Predict Performance":
                child.setStyleSheet(f"""
                    background-color: {self.colors['accent'].name()};
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                """)
        
        # Update CAD widget if it exists
        if hasattr(self, 'cad_widget') and self.cad_widget:
            # Update graphics view background
            self.cad_widget.graphics_view.setBackgroundBrush(QBrush(
                QColor(self.colors['background'].name())
            ))
            
            # Update placeholder text color
            for item in self.cad_widget.graphics_scene.items():
                if isinstance(item, QGraphicsProxyWidget):
                    widget = item.widget()
                    if isinstance(widget, QLabel):
                        widget.setStyleSheet(f"""
                            color: {self.colors['text_light'].name()};
                            font-size: 14px;
                """)
        
        # We need to refresh the UI to make sure all changes are applied
        self.repaint()

    def create_top_control_section(self):
        """Create the top control section with buttons and alloy selection"""
        group_box = QGroupBox("Profile Analysis Controls")
        layout = QHBoxLayout()
        layout.setSpacing(10)

        # Upload DXF Button
        upload_btn = QPushButton("Upload DXF")
        upload_btn.setIcon(QIcon.fromTheme("document-open"))
        upload_btn.clicked.connect(self.upload_dxf)
        layout.addWidget(upload_btn)

        # Correct DXF Button
        correct_btn = QPushButton("Correct DXF")
        correct_btn.clicked.connect(self.correct_dxf)
        layout.addWidget(correct_btn)

        # Alloy Selection Dropdown
        alloy_label = QLabel("Alloy:")
        alloy_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(alloy_label)
        
        alloy_combo = QComboBox()
        alloy_combo.addItems(["6060", "6063", "6082"])
        layout.addWidget(alloy_combo)

        # Generate Profile Button
        generate_btn = QPushButton("Generate Profile")
        generate_btn.clicked.connect(self.generate_profile)
        layout.addWidget(generate_btn)

        # Process Button
        process_btn = QPushButton("Process")
        process_btn.setStyleSheet(f"""
            background-color: {self.colors['accent'].name()};
            color: white;
        """)
        process_btn.clicked.connect(self.process_profile)
        layout.addWidget(process_btn)

        # Export PDF Button
        pdf_btn = QPushButton("Export PDF")
        pdf_btn.clicked.connect(self.export_pdf)
        layout.addWidget(pdf_btn)

        group_box.setLayout(layout)
        return group_box

    def create_cad_viewer_tab(self):
        """Create CAD Viewer tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # CAD Viewer Group
        cad_group = QGroupBox("CAD View")
        cad_layout = QVBoxLayout()
        
        # Create our custom CAD viewer widget
        self.cad_widget = CADWidget(self)
        cad_layout.addWidget(self.cad_widget)
        
        cad_group.setLayout(cad_layout)
        layout.addWidget(cad_group)

        # Information panel
        info_group = QGroupBox("Profile Information")
        info_layout = QVBoxLayout()
        
        # Sketch Number Display
        sketch_layout = QHBoxLayout()
        sketch_label = QLabel("Sketch Number:")
        sketch_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.sketch_display = QLabel("---")
        self.sketch_display.setStyleSheet(f"color: {self.colors['primary'].name()};")
        sketch_layout.addWidget(sketch_label)
        sketch_layout.addWidget(self.sketch_display)
        sketch_layout.addStretch()
        info_layout.addLayout(sketch_layout)

        # Calculated Parameters Display
        self.params_text = QTextEdit()
        self.params_text.setReadOnly(True)
        self.params_text.setMaximumHeight(150)
        self.params_text.setPlaceholderText("Profile parameters will be displayed here")
        info_layout.addWidget(self.params_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        widget.setLayout(layout)
        return widget

    def create_feature_comparison_tab(self):
        """Create Feature Comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Split view
        splitter = QSplitter(Qt.Vertical)
        
        # Reference Profile
        ref_group = QGroupBox("Reference Profile")
        ref_layout = QVBoxLayout()
        ref_label = QLabel("Reference CAD Viewer")
        ref_label.setAlignment(Qt.AlignCenter)
        ref_label.setStyleSheet(f"""
            background-color: {'#3a3a3a' if self.dark_mode else '#f8f9fa'};
            border: 1px dashed {'#555' if self.dark_mode else '#ddd'};
            border-radius: 4px;
            padding: 20px;
            font-size: 14px;
            color: {self.colors['text_light'].name()};
        """)
        ref_label.setMinimumHeight(200)
        ref_layout.addWidget(ref_label)
        ref_group.setLayout(ref_layout)
        splitter.addWidget(ref_group)

        # Similar Profiles
        similar_group = QGroupBox("Similar Profiles")
        similar_layout = QVBoxLayout()
        similar_grid = QGridLayout()
        similar_grid.setSpacing(10)
        
        for i in range(5):
            profile_widget = QWidget()
            profile_layout = QVBoxLayout()
            profile_layout.setSpacing(5)
            
            cad_label = QLabel(f"Profile {i+1}")
            cad_label.setAlignment(Qt.AlignCenter)
            cad_label.setStyleSheet(f"""
                background-color: {'#3a3a3a' if self.dark_mode else '#f8f9fa'};
                border: 1px solid {'#555' if self.dark_mode else '#eee'};
                border-radius: 4px;
                padding: 10px;
            """)
            cad_label.setFixedSize(150, 100)
            
            similarity_label = QLabel(f"Similarity: {80-i*5}%")
            similarity_label.setAlignment(Qt.AlignCenter)
            if i < 2:
                similarity_label.setStyleSheet(f"color: {self.colors['accent'].name()}; font-weight: bold;")
            
            profile_layout.addWidget(cad_label)
            profile_layout.addWidget(similarity_label)
            profile_widget.setLayout(profile_layout)
            
            similar_grid.addWidget(profile_widget, i//3, i%3)
            
        similar_layout.addLayout(similar_grid)
        similar_group.setLayout(similar_layout)
        splitter.addWidget(similar_group)
        
        layout.addWidget(splitter, 1)

        # Find Similar Button
        find_similar_btn = QPushButton("Find Similar Profiles")
        find_similar_btn.clicked.connect(self.find_similar_profiles)
        layout.addWidget(find_similar_btn)

        widget.setLayout(layout)
        return widget

    def create_image_comparison_tab(self):
        """Create Image Comparison tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Split view
        splitter = QSplitter(Qt.Vertical)
        
        # Reference Profile
        ref_group = QGroupBox("Reference Profile")
        ref_layout = QVBoxLayout()
        ref_label = QLabel("Reference Image")
        ref_label.setAlignment(Qt.AlignCenter)
        ref_label.setStyleSheet(f"""
            background-color: {'#3a3a3a' if self.dark_mode else '#f8f9fa'};
            border: 1px dashed {'#555' if self.dark_mode else '#ddd'};
            border-radius: 4px;
            padding: 20px;
            font-size: 14px;
            color: {self.colors['text_light'].name()};
        """)
        ref_label.setMinimumHeight(200)
        ref_layout.addWidget(ref_label)
        ref_group.setLayout(ref_layout)
        splitter.addWidget(ref_group)

        # Similar Profiles
        similar_group = QGroupBox("Similar Profiles")
        similar_layout = QVBoxLayout()
        similar_grid = QGridLayout()
        similar_grid.setSpacing(10)
        
        for i in range(5):
            profile_widget = QWidget()
            profile_layout = QVBoxLayout()
            profile_layout.setSpacing(5)
            
            img_label = QLabel(f"Profile {i+1}")
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet(f"""
                background-color: {'#3a3a3a' if self.dark_mode else '#f8f9fa'};
                border: 1px solid {'#555' if self.dark_mode else '#eee'};
                border-radius: 4px;
                padding: 10px;
            """)
            img_label.setFixedSize(150, 100)
            
            similarity_label = QLabel(f"Similarity: {80-i*5}%")
            similarity_label.setAlignment(Qt.AlignCenter)
            if i < 2:
                similarity_label.setStyleSheet(f"color: {self.colors['accent'].name()}; font-weight: bold;")
            
            profile_layout.addWidget(img_label)
            profile_layout.addWidget(similarity_label)
            profile_widget.setLayout(profile_layout)
            
            similar_grid.addWidget(profile_widget, i//3, i%3)
            
        similar_layout.addLayout(similar_grid)
        similar_group.setLayout(similar_layout)
        splitter.addWidget(similar_group)
        
        layout.addWidget(splitter, 1)

        # Find Similar Button
        find_similar_btn = QPushButton("Find Similar Images")
        find_similar_btn.clicked.connect(self.find_similar_images)
        layout.addWidget(find_similar_btn)

        widget.setLayout(layout)
        return widget

    def create_best_match_tab(self):
        """Create Best Match tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Best Match Profiles
        best_match_group = QGroupBox("Best Match Profiles")
        best_match_layout = QVBoxLayout()
        best_match_grid = QGridLayout()
        best_match_grid.setSpacing(20)
        
        for i in range(3):
            match_widget = QWidget()
            match_layout = QVBoxLayout()
            
            rank_label = QLabel(f"Rank #{i+1}")
            rank_label.setAlignment(Qt.AlignCenter)
            rank_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
            if i == 0:
                rank_label.setStyleSheet(f"color: {self.colors['accent'].name()};")
            
            img_label = QLabel(f"Profile {i+1}")
            img_label.setAlignment(Qt.AlignCenter)
            img_label.setStyleSheet(f"""
                background-color: {'#3a3a3a' if self.dark_mode else '#f8f9fa'};
                border: 1px solid {'#555' if self.dark_mode else '#eee'};
                border-radius: 4px;
                padding: 10px;
            """)
            img_label.setFixedSize(200, 150)
            
            similarity_label = QLabel(f"Similarity: {95-i*8}%")
            similarity_label.setAlignment(Qt.AlignCenter)
            if i == 0:
                similarity_label.setStyleSheet(f"color: {self.colors['accent'].name()}; font-weight: bold;")
            
            match_layout.addWidget(rank_label)
            match_layout.addWidget(img_label)
            match_layout.addWidget(similarity_label)
            match_widget.setLayout(match_layout)
            
            best_match_grid.addWidget(match_widget, 0, i)
            
        best_match_layout.addLayout(best_match_grid)
        best_match_group.setLayout(best_match_layout)
        layout.addWidget(best_match_group)

        # Find Best Match Button
        find_best_match_btn = QPushButton("Find Best Match")
        find_best_match_btn.clicked.connect(self.find_best_match)
        layout.addWidget(find_best_match_btn)

        widget.setLayout(layout)
        return widget

    def create_die_prediction_tab(self):
        """Create Die Prediction tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(15, 15, 15, 15)

        # Performance Prediction Group
        perf_group = QGroupBox("Performance Prediction")
        perf_layout = QGridLayout()
        perf_layout.setSpacing(15)
        perf_layout.setColumnStretch(1, 1)
        perf_layout.setColumnStretch(3, 1)
        
        # Performance Parameters
        params = [
            ("Alloy", "6063"),
            ("Billet Length", "750 mm"),
            ("Butt Length", "25 mm"),
            ("Acceleration Time", "12 s"),
            ("Extrusion Time", "65 s"),
            ("Cycle Time", "110 s"),
            ("Puller Speed", "1.2 m/min"),
            ("Ram Speed", "8.5 mm/s"),
            ("Peak Stem Force", "850 tons"),
            ("Die Force", "650 tons"),
            ("Billet Temp (Head)", "475 °C"),
            ("Billet Temp (Tail)", "460 °C"),
            ("Exit Temp (Front)", "520 °C"),
            ("Exit Temp (Rear)", "515 °C"),
            ("Recovery", "92%"),
            ("Front End Scrap", "1.5 m"),
            ("Back-end Scrap", "0.8 m")
        ]
        
        for i, (param, value) in enumerate(params):
            label = QLabel(param + ":")
            label.setFont(QFont("Segoe UI", 9, QFont.Bold))
            
            value_label = QLabel(value if i < 3 else "--")
            value_label.setStyleSheet(f"color: {self.colors['primary'].name()};")
            
            perf_layout.addWidget(label, i//2, (i%2)*2)
            perf_layout.addWidget(value_label, i//2, (i%2)*2 + 1)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)

        # Predict Button
        predict_btn = QPushButton("Predict Performance")
        predict_btn.setStyleSheet(f"""
            background-color: {self.colors['accent'].name()};
            color: white;
            font-weight: bold;
            padding: 10px;
            font-size: 12px;
        """)
        predict_btn.clicked.connect(self.predict_performance)
        layout.addWidget(predict_btn)

        widget.setLayout(layout)
        return widget

    # Placeholder methods for button actions
    def upload_dxf(self):
        """Upload and display a DXF file"""
        # Select DXF file with dialog
        filename, _ = QFileDialog.getOpenFileName(
            self, 
            "Upload DXF", 
            os.path.join(os.getcwd(), "DXF/Edited"),  # Start in the DXF folder if it exists
            "DXF Files (*.dxf)"
        )
        
        if not filename:
            return  # User canceled the dialog
            
        print(f"Selected DXF file: {filename}")
        self.statusBar().showMessage(f'Loading: {filename}...')
        
        # Make sure CAD widget is initialized
        if not hasattr(self, 'cad_widget'):
            self.statusBar().showMessage(f'CAD viewer not initialized')
            return
            
        # Load the DXF file in the CAD viewer
        dxf_info = self.cad_widget.load_dxf(filename)
        
        if dxf_info:
            # Update status bar
            self.statusBar().showMessage(f'Loaded: {filename}')
            
            # Extract sketch number from filename
            try:
                sketch_number = os.path.basename(filename)
                # Remove extension and keep only alphanumeric part
                sketch_number = os.path.splitext(sketch_number)[0]
                if not sketch_number.startswith("SK"):
                    sketch_number = f"SK{sketch_number}"
                self.sketch_display.setText(sketch_number)
            except:
                self.sketch_display.setText("Unknown")
            
            # Display DXF information in the params text area
            info_text = ""
            for key, value in dxf_info.items():
                if key == 'Entity Counts':
                    info_text += f"{key}:\n"
                    for entity, count in value.items():
                        info_text += f"  - {entity}: {count}\n"
                else:
                    info_text += f"{key}: {value}\n"
            
            self.params_text.setText(info_text)
        else:
            self.statusBar().showMessage(f'Failed to load: {filename}')

    def correct_dxf(self):
        QMessageBox.information(self, "DXF Correction", "Performing DXF correction...")

    def generate_profile(self):
        QMessageBox.information(self, "Profile Generation", "Generating profile...")

    def process_profile(self):
        QMessageBox.information(self, "Profile Processing", "Processing profile...")

    def export_pdf(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export PDF", "", "PDF Files (*.pdf)")
        if filename:
            self.statusBar().showMessage(f'Exported to: {filename}')

    def find_similar_profiles(self):
        QMessageBox.information(self, "Similar Profiles", "Finding similar profiles by features...")

    def find_similar_images(self):
        QMessageBox.information(self, "Similar Images", "Finding similar profiles by images...")

    def find_best_match(self):
        QMessageBox.information(self, "Best Match", "Finding best matching profiles...")

    def predict_performance(self):
        QMessageBox.information(self, "Performance Prediction", "Predicting extrusion performance...")

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    main_window = DXFProfileAnalyzer()
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()