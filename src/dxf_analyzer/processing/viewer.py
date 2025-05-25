import sys
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QToolBar, QAction, QGraphicsView, 
                            QGraphicsScene, QMessageBox, QShortcut, QApplication)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QKeySequence
from PyQt5.QtCore import Qt
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.pyqt import PyQtBackend

class DXFViewer(QDialog):
    def __init__(self, parent=None, dxf_file=None, dark_mode=False):
        super().__init__(parent)
        self.dark_mode = dark_mode
        self.dxf_file = dxf_file
        self.setWindowTitle("DXF Viewer")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set up the main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Create toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
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
        
        # Add zoom in/out buttons with tooltips
        zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon()), "Zoom In", self)
        zoom_in_action.setToolTip("Zoom In (Mouse Wheel Up)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon()), "Zoom Out", self)
        zoom_out_action.setToolTip("Zoom Out (Mouse Wheel Down)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        # Add fit to view button with tooltip
        fit_action = QAction(QIcon.fromTheme("zoom-fit-best", QIcon()), "Fit to View", self)
        fit_action.setToolTip("Fit Drawing to View (Ctrl+0)")
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
            
            QGraphicsView {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                background-color: {colors['surface'].name()};
                border-radius: 4px;
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