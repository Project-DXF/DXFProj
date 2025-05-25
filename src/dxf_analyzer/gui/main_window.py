import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QPushButton, QLabel, QComboBox, QFileDialog, QTabWidget, 
                            QTextEdit, QGroupBox, QGridLayout, QMessageBox, QSplitter,
                            QCheckBox, QToolBar, QAction)
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QBrush
from PyQt5.QtCore import Qt, QSize
from ..processing.cad_widget import CADWidget
# TODO: Update these imports when modules are restructured
# from profile_matching.feature_comparison import FeatureComparisonTab
# from profile_matching.best_match import BestMatchTab
# from image_processing.image_comparison import ImageComparisonTab
# from die_suggestion.die_prediction import DiePredictionTab

class DXFProfileAnalyzer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.dark_mode = False
        self.colors = {
            'background': QColor('#ffffff'),
            'surface': QColor('#f5f5f5'),
            'primary': QColor('#2196f3'),
            'secondary': QColor('#1976d2'),
            'text': QColor('#000000')
        }
        self.initUI()
        
    def initUI(self):
        # Set window properties
        self.setWindowTitle('DXF Profile Analyzer')
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Create toolbar
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # Add theme toggle
        theme_action = QAction(QIcon.fromTheme("preferences-desktop-theme"), "Toggle Dark Mode", self)
        theme_action.triggered.connect(lambda: self.toggle_theme(not self.dark_mode))
        toolbar.addAction(theme_action)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # Create tabs
        self.create_cad_viewer_tab()
        # TODO: Uncomment when modules are restructured
        # self.create_feature_comparison_tab()
        # self.create_image_comparison_tab()
        # self.create_best_match_tab()
        # self.create_die_prediction_tab()
        
        # Apply initial theme
        self.apply_theme()
        
    def apply_theme(self):
        """Apply the current theme to the application"""
        # Update colors based on theme
        if self.dark_mode:
            self.colors = {
                'background': QColor('#1e1e1e'),
                'surface': QColor('#2d2d2d'),
                'primary': QColor('#2196f3'),
                'secondary': QColor('#1976d2'),
                'text': QColor('#ffffff')
            }
        else:
            self.colors = {
                'background': QColor('#ffffff'),
                'surface': QColor('#f5f5f5'),
                'primary': QColor('#2196f3'),
                'secondary': QColor('#1976d2'),
                'text': QColor('#000000')
            }
            
        # Set up the stylesheet
        self.setStyleSheet(f"""
            QMainWindow {{
                background-color: {self.colors['background'].name()};
                color: {self.colors['text'].name()};
            }}
            
            QWidget {{
                background-color: {self.colors['background'].name()};
                color: {self.colors['text'].name()};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                background-color: {self.colors['surface'].name()};
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                padding: 8px 16px;
                margin-right: 2px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['primary'].name()};
                color: white;
            }}
            
            QPushButton {{
                background-color: {self.colors['primary'].name()};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['secondary'].name()};
            }}
            
            QPushButton:disabled {{
                background-color: {'#555' if self.dark_mode else '#ccc'};
                color: {'#888' if self.dark_mode else '#666'};
            }}
            
            QComboBox {{
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                padding: 4px;
                border-radius: 4px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }}
            
            QGroupBox {{
                background-color: {self.colors['surface'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 1em;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
            }}
            
            QTextEdit {{
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
            }}
        """)
        
        # Update component styles
        self.update_component_styles()
        
    def toggle_theme(self, state):
        """Toggle between light and dark theme"""
        self.dark_mode = state
        self.apply_theme()
        
    def update_component_styles(self):
        """Update styles for components that need special handling"""
        # Update CAD widget background
        if hasattr(self, 'cad_widget'):
            self.cad_widget.graphics_view.setBackgroundBrush(QBrush(self.colors['background']))
            
    def create_cad_viewer_tab(self):
        """Create the CAD viewer tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create CAD widget
        self.cad_widget = CADWidget(self)
        layout.addWidget(self.cad_widget)
        
        self.tab_widget.addTab(tab, "CAD Viewer")
        
    # TODO: Uncomment when modules are restructured
    # def create_feature_comparison_tab(self):
    #     """Create the feature comparison tab"""
    #     self.feature_comparison_tab = FeatureComparisonTab(self)
    #     self.tab_widget.addTab(self.feature_comparison_tab, "Feature Comparison")
    #     
    # def create_image_comparison_tab(self):
    #     """Create the image comparison tab"""
    #     self.image_comparison_tab = ImageComparisonTab(self)
    #     self.tab_widget.addTab(self.image_comparison_tab, "Image Comparison")
    #     
    # def create_best_match_tab(self):
    #     """Create the best match tab"""
    #     self.best_match_tab = BestMatchTab(self)
    #     self.tab_widget.addTab(self.best_match_tab, "Best Match")
    #     
    # def create_die_prediction_tab(self):
    #     """Create the die prediction tab"""
    #     self.die_prediction_tab = DiePredictionTab(self)
    #     self.tab_widget.addTab(self.die_prediction_tab, "Die Prediction")
        
    def upload_dxf(self):
        """Handle DXF file upload"""
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF File",
            "",
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_name:
            self.cad_widget.load_dxf(file_name)
            
    def correct_dxf(self):
        """Handle DXF correction"""
        pass
        
    def generate_profile(self):
        """Handle profile generation"""
        pass
        
    def process_profile(self):
        """Handle profile processing"""
        pass
        
    def export_pdf(self):
        """Handle PDF export"""
        pass

def main():
    app = QApplication(sys.argv)
    window = DXFProfileAnalyzer()
    window.show()
    sys.exit(app.exec_()) 