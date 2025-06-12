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
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
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

        zoom_in_action = QAction(QIcon.fromTheme("zoom-in", QIcon()), "Zoom In", self)
        zoom_in_action.setToolTip("Zoom In (Mouse Wheel Up)")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)
        
        zoom_out_action = QAction(QIcon.fromTheme("zoom-out", QIcon()), "Zoom Out", self)
        zoom_out_action.setToolTip("Zoom Out (Mouse Wheel Down)")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)
        
        toolbar.addSeparator()
        
        fit_action = QAction(QIcon.fromTheme("zoom-fit-best", QIcon()), "Fit to View", self)
        fit_action.setToolTip("Fit Drawing to View (Ctrl+0)")
        fit_action.triggered.connect(self.fit_to_view)
        toolbar.addAction(fit_action)
        
        main_layout.addWidget(toolbar)
        
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
        
        QShortcut(QKeySequence.ZoomIn, self, self.zoom_in)
        QShortcut(QKeySequence.ZoomOut, self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self.fit_to_view)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.close)
        
        if self.dxf_file:
            self.load_dxf(self.dxf_file)
            
        self.apply_theme()

    def apply_theme(self):
        colors = self.parent().colors
        
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
        self.dxf_file = filename
        self.setWindowTitle(f"DXF Viewer - {os.path.basename(filename)}")
        self.graphics_scene.clear()
        
        try:
            doc = ezdxf.readfile(filename)
            
            msp = doc.modelspace()
            entity_count = sum(1 for _ in msp)
            
            context = RenderContext(doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            frontend.draw_layout(doc.modelspace())
            
            item_count = len(self.graphics_scene.items()) 
            
            if item_count == 0:
                self.show_error_message("DXF file loaded but no visible entities found")
                return
                
            self.graphics_view.resetTransform()
            
            bounds = self.graphics_scene.itemsBoundingRect()
            
            if bounds.width() < 1 or bounds.height() < 1:
                bounds = QRectF(bounds.x(), bounds.y(), max(bounds.width(), 10), max(bounds.height(), 10))            
            self.graphics_scene.setSceneRect(bounds.adjusted(-10, -10, 10, 10))
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
            self.graphics_view.update()
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.show_error_message(f"Failed to load DXF file: {str(e)}")
    
    def show_error_message(self, message):
        QMessageBox.critical(self, "Error", message)
    
    def zoom_in(self):
        self.graphics_view.scale(1.2, 1.2)
        
    def zoom_out(self):
        self.graphics_view.scale(1/1.2, 1/1.2)
        
    def fit_to_view(self):
        bounds = self.graphics_scene.itemsBoundingRect()
        if not bounds.isEmpty():
            self.graphics_view.fitInView(bounds.adjusted(-5, -5, 5, 5), Qt.KeepAspectRatio)
        
    def wheelEvent(self, event):
        if event.angleDelta().y() > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QApplication.processEvents() 
        if self.dxf_file and not self.graphics_scene.items() == []:
            self.fit_to_view()
            
    def showEvent(self, event):
        super().showEvent(event)
        QApplication.processEvents() 
        if self.dxf_file and not self.graphics_scene.items() == []:
            self.fit_to_view() 