from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QMessageBox
from PyQt5.QtGui import QBrush, QColor, QPainter
from PyQt5.QtCore import Qt, QRectF
import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.pyqt import PyQtBackend

class DisplayManager:    
    def __init__(self, graphics_view: QGraphicsView, graphics_scene: QGraphicsScene):
        self.graphics_view = graphics_view
        self.graphics_scene = graphics_scene
        self.current_doc = None
        self.current_file = None
        self.dark_mode = False
        self._setup_graphics_view()
    
    def _setup_graphics_view(self):
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
    
    def set_background_color(self, color: QColor):
        self.graphics_view.setBackgroundBrush(QBrush(color))
    
    def set_theme(self, dark_mode: bool):
        self.dark_mode = dark_mode
        
        if self.current_file:
            self.load_dxf(self.current_file)
    
    def load_dxf(self, filename: str) -> bool:
        try:
            print(f"Loading DXF: {filename}")
            
            self.graphics_scene.clear()
            
            self.current_doc = ezdxf.readfile(filename)
            self.current_file = filename
            
            msp = self.current_doc.modelspace()
            entity_count = sum(1 for _ in msp)
            print(f"Entity count: {entity_count}")
            
            context = RenderContext(self.current_doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            frontend.draw_layout(self.current_doc.modelspace())
            
            self._apply_theme_to_rendered_items()
            
            item_count = len(self.graphics_scene.items())
            print(f"Graphics scene items: {item_count}")
            
            if item_count == 0:
                self._show_error("DXF file loaded but no visible entities found")
                return False
            
            self._fit_content_to_view()
            
            return True
            
        except Exception as e:
            print(f"Error loading DXF: {str(e)}")
            import traceback
            traceback.print_exc()
            self._show_error(f"Failed to load DXF file: {str(e)}")
            return False
    

    def _apply_theme_to_rendered_items(self):
        line_color = QColor(0, 0, 0) if not self.dark_mode else QColor(255, 255, 255)        
        for item in self.graphics_scene.items():
            if hasattr(item, 'pen') and hasattr(item, 'setPen'):
                try:
                    pen = item.pen()
                    pen.setColor(line_color)
                    item.setPen(pen)
                except:
                    continue
    
    def _fit_content_to_view(self):
        self.graphics_view.resetTransform()
        
        bounds = self.graphics_scene.itemsBoundingRect()
        if bounds.width() < 1 or bounds.height() < 1:
            bounds = QRectF(bounds.x(), bounds.y(), max(bounds.width(), 10), max(bounds.height(), 10))
        
        self.graphics_scene.setSceneRect(bounds.adjusted(-10, -10, 10, 10))
        
        self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
        
        self.graphics_view.update()
    
    def zoom_in(self, factor: float = 1.2):
        self.graphics_view.scale(factor, factor)
    
    def zoom_out(self, factor: float = 1.2):
        self.graphics_view.scale(1/factor, 1/factor)
    
    def fit_to_view(self):  
        bounds = self.graphics_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
    
    def refresh_view(self):
        self.graphics_view.update()
    
    def clear_display(self):
        self.graphics_scene.clear()
        self.current_doc = None
        self.current_file = None
    
    def get_current_doc(self):
        return self.current_doc
    
    def get_current_file(self):
        return self.current_file
    
    def _show_error(self, message: str):
        QMessageBox.critical(None, "Display Error", message)
    
    def add_placeholder_text(self, text: str, is_error: bool = False):
        from PyQt5.QtWidgets import QLabel, QGraphicsProxyWidget
        from PyQt5.QtGui import QFont
        
        self.graphics_scene.clear()
        
        placeholder_label = QLabel(text)
        placeholder_label.setAlignment(Qt.AlignCenter)
        placeholder_label.setWordWrap(True)
        placeholder_label.setFont(QFont("Segoe UI", 12))
        
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
            if self.dark_mode:
                placeholder_label.setStyleSheet("""
                    QLabel {
                        color: #ccc;
                        background-color: rgba(60, 60, 60, 0.8);
                        border: 2px dashed #666;
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
        
        placeholder_proxy = QGraphicsProxyWidget()
        placeholder_proxy.setWidget(placeholder_label)
        self.graphics_scene.addItem(placeholder_proxy)
        
        scene_rect = self.graphics_view.rect()
        placeholder_proxy.setPos(
            scene_rect.width() / 2 - placeholder_label.width() / 2,
            scene_rect.height() / 2 - placeholder_label.height() / 2
        ) 