"""
Display Manager for DXF Graphics

Handles the rendering and display of DXF files in graphics views.
"""

from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox
from PyQt5.QtGui import QBrush, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.pyqt import PyQtBackend


class DisplayManager:
    """Manages DXF file display and rendering operations."""
    
    def __init__(self, graphics_view: QGraphicsView, graphics_scene: QGraphicsScene):
        """
        Initialize the display manager.
        
        Args:
            graphics_view: The QGraphicsView widget for display
            graphics_scene: The QGraphicsScene for rendering
        """
        self.graphics_view = graphics_view
        self.graphics_scene = graphics_scene
        self.current_doc = None
        self.current_file = None
        
        # Configure graphics view
        self._setup_graphics_view()
    
    def _setup_graphics_view(self):
        """Configure the graphics view with optimal settings."""
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    
    def set_background_color(self, color: QColor):
        """Set the background color of the graphics view."""
        self.graphics_view.setBackgroundBrush(QBrush(color))
    
    def load_dxf(self, filename: str) -> bool:
        """
        Load and display a DXF file.
        
        Args:
            filename: Path to the DXF file
            
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            print(f"Loading DXF: {filename}")
            
            # Clear previous content
            self.graphics_scene.clear()
            
            # Load the DXF file
            self.current_doc = ezdxf.readfile(filename)
            self.current_file = filename
            
            # Count entities for debugging
            msp = self.current_doc.modelspace()
            entity_count = sum(1 for _ in msp)
            print(f"Entity count: {entity_count}")
            
            # Set up render context
            context = RenderContext(self.current_doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            # Render the model space entities
            frontend.draw_layout(self.current_doc.modelspace())
            
            # Check if we have items in the scene
            item_count = len(self.graphics_scene.items())
            print(f"Graphics scene items: {item_count}")
            
            if item_count == 0:
                self._show_error("DXF file loaded but no visible entities found")
                return False
            
            # Fit the content to view
            self._fit_content_to_view()
            
            return True
            
        except Exception as e:
            print(f"Error loading DXF: {str(e)}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Failed to load DXF file: {str(e)}")
            return False
    
    def _fit_content_to_view(self):
        """Fit the DXF content to the graphics view."""
        # Reset view transforms
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
    
    def zoom_in(self, factor: float = 1.2):
        """Zoom in by the specified factor."""
        self.graphics_view.scale(factor, factor)
    
    def zoom_out(self, factor: float = 1.2):
        """Zoom out by the specified factor."""
        self.graphics_view.scale(1/factor, 1/factor)
    
    def fit_to_view(self):
        """Fit the entire drawing to the view."""
        bounds = self.graphics_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            # Add a small margin around the content
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
    
    def refresh_view(self):
        """Refresh the graphics view."""
        self.graphics_view.update()
    
    def clear_display(self):
        """Clear the current display."""
        self.graphics_scene.clear()
        self.current_doc = None
        self.current_file = None
    
    def get_current_doc(self):
        """Get the currently loaded DXF document."""
        return self.current_doc
    
    def get_current_file(self):
        """Get the currently loaded file path."""
        return self.current_file
    
    def _show_error(self, message: str):
        """Show an error message."""
        QMessageBox.critical(None, "Display Error", message)
    
    def add_placeholder_text(self, text: str, is_error: bool = False):
        """Add placeholder text to the display."""
        from PyQt5.QtWidgets import QLabel, QGraphicsProxyWidget
        from PyQt5.QtGui import QFont
        
        # Clear any existing content
        self.graphics_scene.clear()
        
        # Create placeholder label
        placeholder_label = QLabel(text)
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setWordWrap(True)
        placeholder_label.setFont(QFont("Segoe UI", 12))
        
        # Style based on error state
        if is_error:
            placeholder_label.setStyleSheet("""
                QLabel {
                    color: #d32f2f;
                    background-color: rgba(255, 235, 238, 0.8);
                    border: 2px dashed #d32f2f;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px;
                }
            """)
        else:
            placeholder_label.setStyleSheet("""
                QLabel {
                    color: #666;
                    background-color: rgba(240, 240, 240, 0.8);
                    border: 2px dashed #ccc;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px;
                }
            """)
        
        # Add to scene
        placeholder_proxy = QGraphicsProxyWidget()
        placeholder_proxy.setWidget(placeholder_label)
        self.graphics_scene.addItem(placeholder_proxy)
        
        # Center the placeholder
        scene_rect = self.graphics_view.rect()
        placeholder_proxy.setPos(
            scene_rect.width() / 2 - placeholder_label.width() / 2,
            scene_rect.height() / 2 - placeholder_label.height() / 2
        ) 