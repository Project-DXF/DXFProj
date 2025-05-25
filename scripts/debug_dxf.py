import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsView, QGraphicsScene, QVBoxLayout, QWidget
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt

import ezdxf
from ezdxf.addons.drawing import Frontend, RenderContext
from ezdxf.addons.drawing.pyqt import PyQtBackend

class DXFDebugger(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DXF Debug Viewer")
        self.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)
        
        self.graphics_view = QGraphicsView()
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_scene = QGraphicsScene()
        self.graphics_view.setScene(self.graphics_scene)
        
        layout.addWidget(self.graphics_view)
        self.setCentralWidget(central_widget)
        
    def load_dxf(self, filename):
        print(f"Attempting to load: {filename}")
        self.graphics_scene.clear()
        
        try:
            # Load the DXF file
            doc = ezdxf.readfile(filename)
            print(f"DXF version: {doc.dxfversion}")
            print(f"Header variables: {len(doc.header)}")
            
            # Count entities in model space
            msp = doc.modelspace()
            entity_count = 0
            entity_types = {}
            
            for entity in msp:
                entity_count += 1
                entity_type = entity.dxftype()
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
            
            print(f"Total entities: {entity_count}")
            print(f"Entity types: {entity_types}")
            
            # Set up render context
            print("Setting up render context...")
            context = RenderContext(doc)
            backend = PyQtBackend(self.graphics_scene)
            frontend = Frontend(context, backend)
            
            # Render the model space entities
            print("Drawing layout...")
            frontend.draw_layout(doc.modelspace())
            
            # Fit everything into view
            self.graphics_view.fitInView(self.graphics_scene.itemsBoundingRect(), Qt.KeepAspectRatio)
            
            print(f"Scene items: {len(self.graphics_scene.items())}")
            print(f"Scene rect: {self.graphics_scene.itemsBoundingRect()}")
            
            return True
            
        except Exception as e:
            print(f"Error loading DXF file: {str(e)}")
            traceback.print_exc()
            return False

def main():
    app = QApplication(sys.argv)
    
    viewer = DXFDebugger()
    viewer.show()
    
    # Load test DXF from command line argument or use a default
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        filename = "DXF/Edited/RAB5965.dxf"
    
    if os.path.exists(filename):
        viewer.load_dxf(filename)
    else:
        print(f"File not found: {filename}")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main() 