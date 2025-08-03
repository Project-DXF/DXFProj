import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QComboBox, QFileDialog, QTabWidget, 
                            QTextEdit, QGroupBox, QGridLayout, QMessageBox, QSplitter,
                            QCheckBox, QToolBar, QAction, QLineEdit, QScrollArea, QDialog,
                            QTreeWidget, QTreeWidgetItem, QGraphicsScene, QGraphicsView,
                            QProgressBar, QHeaderView, QTableWidget, QTableWidgetItem, QFormLayout, QTabBar)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QBrush, QCursor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal, QTimer
import ezdxf

from ..database import ProfileDatabase
from ..processing import CADWidget
from ..image_processing import ImageProcessingTab
from ..settings import SettingsTab
from ..settings.theme_manager import ThemeManager
from ..core.event_manager import EventManager
# TODO: Update these imports when modules are restructured
# from profile_matching.feature_comparison import FeatureComparisonTab
# from profile_matching.best_match import BestMatchTab
# from die_suggestion.die_prediction import DiePredictionTab


class DXFProfileAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.theme_manager = ThemeManager()
        self.event_manager = EventManager()
        self.current_dxf_file = None
        self.current_dxf_doc = None
        self.initUI()
        
    def initUI(self):
        self._setup_ui()
        
        self.event_manager.dxf_loaded.connect(self.on_dxf_loaded)
        self.event_manager.theme_changed.connect(self.toggle_theme)
        
    def _setup_ui(self):
        self.setWindowTitle("DXF Profile Analyzer")
        self.setGeometry(100, 100, 1400, 900)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        self.create_cad_viewer_tab()
        self.create_image_processing_tab()
        self.create_settings_tab()
        
        self.apply_theme()
        
        self._set_cursor_pointers()
        
        if hasattr(self, 'theme_action'):
            self.theme_action.triggered.connect(self.toggle_theme)
        
    def _set_cursor_pointers(self):
        def set_cursor_for_widget(widget):
            if isinstance(widget, (QPushButton, QCheckBox, QComboBox)):
                widget.setCursor(QCursor(Qt.PointingHandCursor))
            elif isinstance(widget, QTabWidget):
                widget.setCursor(QCursor(Qt.PointingHandCursor))
            elif isinstance(widget, QGroupBox):
                widget.setCursor(QCursor(Qt.ArrowCursor))
            elif hasattr(widget, 'setCursor'):
                if (hasattr(widget, 'clicked') or hasattr(widget, 'toggled')) and not isinstance(widget, QGroupBox):
                    widget.setCursor(QCursor(Qt.PointingHandCursor))
            
            # Recursively process child widgets
            for child in widget.findChildren(QWidget):
                set_cursor_for_widget(child)
        
        for widget in QApplication.allWidgets():
            set_cursor_for_widget(widget)
        
    def apply_theme(self):
        self.setStyleSheet(self.theme_manager.get_stylesheet())
        
    def toggle_theme(self, dark_mode: bool):
        self.theme_manager.toggle_theme(dark_mode)
        self.apply_theme()
        
        if hasattr(self, 'cad_widget'):
            self.cad_widget.apply_theme()
            
    @property
    def dark_mode(self) -> bool:
        return self.theme_manager.dark_mode
    
    @property
    def colors(self) -> dict:
        return self.theme_manager.colors
            
    def on_dxf_loaded(self, file_path: str, doc: object):
        self.current_dxf_file = file_path
        self.current_dxf_doc = doc
        
        if hasattr(self, 'image_processing_tab'):
            self.image_processing_tab.set_current_dxf(file_path)
            
    def create_cad_viewer_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.cad_widget = CADWidget(self)
        layout.addWidget(self.cad_widget)
        
        self.tab_widget.addTab(tab, "CAD Viewer")
        
    def create_settings_tab(self):
        self.settings_tab = SettingsTab(self)
        self.tab_widget.addTab(self.settings_tab, "Settings")
        
    def create_image_processing_tab(self):
        self.image_processing_tab = ImageProcessingTab(self)
        self.tab_widget.addTab(self.image_processing_tab, "Image Processing")
        
    def upload_dxf(self, source_tab=""):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF File",
            "",
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_name and hasattr(self, 'cad_widget'):
            self.cad_widget.load_dxf(file_name)
            if source_tab != "cad_viewer":
                self.tab_widget.setCurrentIndex(0)
            
    def correct_dxf(self):
        pass
        
    def generate_profile(self):
        pass
        
    def process_profile(self):
        pass
        
    def export_pdf(self):
        pass
    
    def open_dxf_file(self):
        """Open and process a DXF file"""
        try:
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            
            file_name, _ = QFileDialog.getOpenFileName(
                self,
                "Open DXF File",
                "",  # Start in current directory
                "DXF Files (*.dxf);;All Files (*)",
                options=options
            )
            
            if file_name:
                print(f"Selected file: {file_name}")  # Debug output
                if os.path.exists(file_name):
                    # Process the DXF file
                    self.statusBar().showMessage(f"Processing {file_name}...")
                    # Your DXF processing code here
                    return True
                else:
                    QMessageBox.warning(self, "Error", f"File not found: {file_name}")
                    
            return False
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open file:\n{str(e)}")
            return False

def main():
    app = QApplication(sys.argv)
    window = DXFProfileAnalyzer()
    window.show()
    sys.exit(app.exec_())