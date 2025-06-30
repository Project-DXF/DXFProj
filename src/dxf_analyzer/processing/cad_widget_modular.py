from PyQt5.QtWidgets import (QWidget, QGridLayout, QHBoxLayout, QVBoxLayout, QPushButton, 
                            QGraphicsView, QGraphicsScene, QLabel, 
                            QFormLayout, QLineEdit, QSplitter, QMessageBox,
                            QFileDialog, QToolBar, QAction, QTextEdit, QTabWidget,
                            QProgressBar, QComboBox, QScrollArea, QTreeWidget, 
                            QTreeWidgetItem, QHeaderView, QTableWidget, QStackedWidget,
                            QGroupBox, QTableWidgetItem, QCheckBox, QTabBar)
from PyQt5.QtGui import QIcon, QBrush, QColor, QPainter, QFont, QDragEnterEvent, QDropEvent, QCursor
from PyQt5.QtCore import Qt, QSize, QThread, pyqtSignal
import ezdxf
import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
import sys

from .viewing import DisplayManager
from .workflow_processing import DXFProcessor, FeatureExtractor, AnalysisEngine
from .correction import DXFCorrector
from .loop_detection import LoopDetector
from .profile_management import ProfileManager
from .profile_management.feature_calculator import AdvancedFeatureCalculator
from ..database import ProfileDatabase
from ..settings.theme_manager import ThemeManager


class ProcessingWorker(QThread):
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_file = None
        self.current_doc = None
        self.is_updating = False
        self._init_components()
        self.setAcceptDrops(True)
        self._init_ui()
        self._connect_signals()
    
    def _init_components(self):
        self.graphics_scene = QGraphicsScene()
        self.graphics_view = QGraphicsView()
        self.graphics_view.setScene(self.graphics_scene)
        self.display_manager = DisplayManager(self.graphics_view, self.graphics_scene)
        self.dxf_processor = DXFProcessor()
        self.feature_extractor = FeatureExtractor()
        self.analysis_engine = AnalysisEngine()
        self.correction = DXFCorrector()
        self.loop_detector = LoopDetector()
        self.profile_manager = ProfileManager()
        self.feature_calculator = AdvancedFeatureCalculator()
        self.profile_database = ProfileDatabase()
        self.processing_worker = None
    
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)        
        viewer_panel = self._create_viewer_panel()
        control_panel = self._create_control_panel()
        splitter.addWidget(viewer_panel)
        splitter.addWidget(control_panel)
        splitter.setSizes([800, 400])  
        main_layout.addWidget(splitter)
    
    def _create_viewer_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.graphics_view.setRenderHint(QPainter.Antialiasing)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        if self.parent and hasattr(self.parent, 'colors'):
            self.display_manager.set_background_color(self.parent.colors['background'])
            if hasattr(self.parent, 'dark_mode'):
                self.display_manager.set_theme(self.parent.dark_mode)
        
        layout.addWidget(self.graphics_view)
        
        self.status_label = QLabel("Ready - Upload a DXF file to begin")
        layout.addWidget(self.status_label)

        self.display_manager.add_placeholder_text("Drop a DXF file here or click Upload DXF")
        
        return panel
    
    def _create_control_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        input_group = QGroupBox("Input Information")
        input_layout = QHBoxLayout()

        sketch_layout = QVBoxLayout()
        sketch_label = QLabel("Sketch Number:")
        self.sketch_number_field = QLineEdit()
        self.sketch_number_field.setPlaceholderText("Enter sketch number")
        sketch_layout.addWidget(sketch_label)
        sketch_layout.addWidget(self.sketch_number_field)

        profile_layout = QVBoxLayout()
        profile_label = QLabel("Profile Number:")
        self.profile_number_field = QLineEdit()
        self.profile_number_field.setPlaceholderText("Enter profile number")
        profile_layout.addWidget(profile_label)
        profile_layout.addWidget(self.profile_number_field)

        input_layout.addLayout(sketch_layout)
        input_layout.addLayout(profile_layout)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        actions_group = QGroupBox("Actions")
        actions_layout = QGridLayout()
        actions_layout.setSpacing(5)
        
        self.upload_dxf_btn = QPushButton("Upload DXF")
        self.upload_dxf_btn.clicked.connect(self.upload_dxf)
        actions_layout.addWidget(self.upload_dxf_btn, 0, 0)

        self.correct_dxf_btn = QPushButton("Correct DXF")
        self.correct_dxf_btn.clicked.connect(self.correct_dxf)
        self.correct_dxf_btn.setEnabled(False)
        actions_layout.addWidget(self.correct_dxf_btn, 0, 1)
        
        self.display_loops_btn = QPushButton("Display Loops")
        self.display_loops_btn.clicked.connect(self.detect_loops)
        self.display_loops_btn.setEnabled(False)
        actions_layout.addWidget(self.display_loops_btn, 0, 2)
        
        self.process_btn = QPushButton("Process")
        self.process_btn.clicked.connect(self.process_dxf)
        self.process_btn.setEnabled(False)
        actions_layout.addWidget(self.process_btn, 0, 3)
        
        self.upload_profile_btn = QPushButton("Upload New Profile")
        self.upload_profile_btn.clicked.connect(self.save_profile)
        self.upload_profile_btn.setEnabled(False)
        actions_layout.addWidget(self.upload_profile_btn, 0, 4)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        params_group = QGroupBox("Processed Parameters")
        params_layout = QVBoxLayout()

        toolbar = QHBoxLayout()
        self.expand_all_btn = QPushButton("Expand All")
        self.collapse_all_btn = QPushButton("Collapse All")
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search parameters...")

        toolbar.addWidget(self.expand_all_btn)
        toolbar.addWidget(self.collapse_all_btn)
        toolbar.addStretch()
        toolbar.addWidget(QLabel("Search:"))
        toolbar.addWidget(search_box)

        params_layout.addLayout(toolbar)

        self.view_stack = QStackedWidget()

        self.params_tree = QTreeWidget()
        self.params_tree.setHeaderLabels(["Parameter", "Value", "Unit"])
        self.params_tree.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.params_tree.setAlternatingRowColors(True)
        self.params_tree.setRootIsDecorated(True)
        self.params_tree.setItemsExpandable(True)
        self.view_stack.addWidget(self.params_tree)

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.view_stack)
        params_layout.addWidget(splitter)

        self.expand_all_btn.clicked.connect(lambda: self.params_tree.expandAll())
        self.collapse_all_btn.clicked.connect(lambda: self.params_tree.collapseAll())
        search_box.textChanged.connect(self._filter_parameters)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        self._apply_control_panel_styling()
        return panel
    
    def _filter_parameters(self, text):
        if self.view_stack.currentIndex() == 0:  
            self._filter_tree_items(self.params_tree.invisibleRootItem(), text.lower())

    def _filter_tree_items(self, item, text):
        visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_visible = self._filter_tree_items(child, text)
            
            item_text = child.text(0).lower()
            if text in item_text or not text:
                child_visible = True
                
            child.setHidden(not child_visible)
            if child_visible:
                visible = True
        
        return visible

    def _apply_control_panel_styling(self):
        if self.parent and hasattr(self.parent, 'colors') and hasattr(self.parent, 'dark_mode'):
            colors = self.parent.colors
            dark_mode = self.parent.dark_mode
            
            interactive_style = ""
            
            button_style = f"""
                QPushButton {{
                    padding: 12px;
                    border-radius: 6px;
                    font-weight: bold;
                    min-height: 20px;
                    background-color: {colors['primary'].name()};
                    color: white;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: {colors['secondary'].name()};
                }}
                QPushButton:pressed {{
                    background-color: {colors['secondary'].darker(120).name()};
                }}
                QPushButton:disabled {{
                    background-color: {'#555' if dark_mode else '#BDBDBD'};
                    color: {'#888' if dark_mode else '#757575'};
                }}
            """
            
            tree_style = f"""
                QTreeWidget {{
                    background-color: {colors['surface'].name()};
                    alternate-background-color: {'#2a2a2a' if dark_mode else '#f8f8f8'};
                    color: {colors['text'].name()};
                    border: 1px solid {'#555' if dark_mode else '#ddd'};
                    border-radius: 4px;
                    selection-background-color: {colors['primary'].name()};
                    selection-color: white;
                }}
                
                QTreeWidget::item {{
                    padding: 6px 4px;
                    border-bottom: 1px solid {'#444' if dark_mode else '#eee'};
                }}
                
                QTreeWidget::item:hover {{
                    background-color: {colors['primary'].lighter(160).name() if not dark_mode else colors['primary'].darker(160).name()};
                    color: {'white' if dark_mode else colors['text'].name()};
                }}
                
                QTreeWidget::item:selected {{
                    background-color: {colors['primary'].name()};
                    color: white;
                }}
                
                QTreeWidget::branch:has-children:hover {{
                    background-color: {colors['primary'].lighter(180).name()};
                    border-radius: 2px;
                }}
            """
            
            header_style = f"""
                QHeaderView::section {{
                    background-color: {colors['primary'].name()};
                    color: white;
                    padding: 8px 4px;
                    border: none;
                    border-right: 1px solid {colors['primary'].darker(120).name()};
                    font-weight: bold;
                }}
                
                QHeaderView::section:hover {{
                    background-color: {colors['primary'].lighter(110).name()};
                }}
            """
            
            input_style = f"""
                QLineEdit {{
                    padding: 8px;
                    border: 1px solid {'#555' if dark_mode else '#ddd'};
                    border-radius: 4px;
                    background-color: {colors['surface'].name()};
                    color: {colors['text'].name()};
                }}
                QLineEdit:focus {{
                    border-color: {colors['primary'].name()};
                    border-width: 2px;
                }}
            """
            
            toolbar_style = f"""
                QToolBar {{
                    spacing: 5px;
                    padding: 8px;
                    background: {colors['background'].name()};
                    border-bottom: 1px solid {'#555' if dark_mode else '#ddd'};
                    border-radius: 4px;
                }}
                QToolButton {{
                    padding: 10px;
                    border-radius: 6px;
                    background: {colors['surface'].name()};
                    color: {colors['text'].name()};
                    border: 1px solid {'#555' if dark_mode else '#ddd'};
                    min-width: 24px;
                    min-height: 24px;
                }}
                QToolButton:hover {{
                    background: {colors['primary'].lighter(150).name()};
                    color: white;
                    border-color: {colors['primary'].name()};
                }}
                QToolButton:pressed {{
                    background: {colors['primary'].name()};
                    color: white;
                    border-color: {colors['primary'].darker(120).name()};
                }}
            """
            
            self.setStyleSheet(interactive_style + input_style)
            
            for btn in [self.upload_dxf_btn, self.correct_dxf_btn, self.display_loops_btn, 
                    self.process_btn, self.upload_profile_btn, self.expand_all_btn, self.collapse_all_btn]:
                btn.setStyleSheet(button_style)
            
            if hasattr(self, 'params_tree'):
                self.params_tree.setStyleSheet(tree_style + header_style)
                font = self.params_tree.font()
                font.setPointSize(10)
                self.params_tree.setFont(font)
                self.params_tree.setIndentation(20)
                self.params_tree.setMouseTracking(True)
            
            toolbar = self.findChild(QToolBar)
            if toolbar:
                toolbar.setStyleSheet(toolbar_style)

    def _connect_signals(self):
        pass

    def upload_dxf(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Select DXF File",
            "",
            "DXF Files (*.dxf);;All Files (*)"
        )
        
        if file_name:
            self.load_dxf(file_name)

    def load_dxf(self, filename):
        if self.is_updating:
            return
            
        self.is_updating = True
        try:
            self.current_file = filename
            success = self.display_manager.load_dxf(filename)
            if success:
                self.current_doc = ezdxf.readfile(filename)
                self._update_file_info()
                self._enable_processing_buttons()
                
                self.status_label.setText(f"Loaded: {os.path.basename(filename)}")
                
                if self.parent and hasattr(self.parent, 'event_manager'):
                    self.parent.event_manager.update_dxf(filename, self.current_doc)
            else:
                self.status_label.setText("Failed to load DXF file")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load DXF file: {str(e)}")
            self.status_label.setText("Error loading file")
        finally:
            self.is_updating = False

    def _update_file_info(self):
        if not self.current_doc:
            return
        
        try:
            self.params_tree.clear()
            
            placeholder_item = QTreeWidgetItem(self.params_tree)
            placeholder_item.setText(0, "Click 'Process' to calculate parameters")
            placeholder_item.setText(1, "")
            placeholder_item.setText(2, "")
            
        except Exception as e:
            pass

    def _enable_processing_buttons(self):
        self.correct_dxf_btn.setEnabled(True)
        self.display_loops_btn.setEnabled(True)
        self.process_btn.setEnabled(True)
        self.upload_profile_btn.setEnabled(True)

  
    def correct_dxf(self):
        if not self.current_doc:
            QMessageBox.warning(self, "No Document", "No DXF document loaded")
            return
        
        self.status_label.setText("Applying corrections...")
        
        try:
            self.correction.load_document(self.current_doc)
            duplicates_removed = self.correction.remove_duplicate_entities()
            new_connections = self.correction.connect_gaps_with_lines(max_distance=0.01)
            validation_issues = self.correction.validate_document()
            correction_summary = self.correction.get_correction_summary()
            message = f"Corrections Applied Successfully!\n\n{correction_summary}"
            
            if validation_issues:
                message += f"\n\nValidation Warnings:\n"
                message += "\n".join(f"• {issue}" for issue in validation_issues[:5])  
                if len(validation_issues) > 5:
                    message += f"\n... and {len(validation_issues) - 5} more issues"
            
            QMessageBox.information(self, "Corrections Applied", message)
            
            self.display_manager.refresh_view()
            self.status_label.setText(f"Corrections applied - {duplicates_removed} duplicates removed, {len(new_connections)} gaps connected")
            
        except ValueError as e:
            QMessageBox.warning(self, "Invalid Input", f"Invalid input: {str(e)}")
            self.status_label.setText("Invalid input for corrections")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply corrections: {str(e)}")
            self.status_label.setText("Error applying corrections")
            
    def detect_loops(self):
        if not self.current_doc:
            return
        
        self.status_label.setText("Detecting loops...")
        
        try:
            self.loop_detector.set_document(self.current_doc)
            total_loops = self.loop_detector.run_visualizer()
            
            if total_loops > 0:
                self.status_label.setText(f"Found and highlighted {total_loops} loops")
            else:
                self.status_label.setText("No loops found")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to detect loops: {str(e)}")
            self.status_label.setText("Error detecting loops")

    def process_dxf(self):  
        if not self.current_doc:
            return
        
        self.status_label.setText("Processing DXF file...")
        
        try:
            self.feature_calculator.set_document(self.current_doc)
            features = self.feature_calculator.calculate_all_features()
            self._update_parameters_tree(features)
            self.status_label.setText("Processing completed")
            if len(features) > 0:
                QMessageBox.information(self, "Processing Complete", 
                                      f"DXF file processed successfully. {len(features)} features calculated.")
            else:
                QMessageBox.warning(self, "Processing Complete", 
                                  "DXF file processed but no features could be calculated. Check console for details.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process DXF: {str(e)}")
            self.status_label.setText("Error processing file")

    def save_profile(self):
        if not self.current_doc:
            QMessageBox.warning(self, "Save Profile", "Please load a DXF file first")
            return
        
        sketch_number = self.sketch_number_field.text().strip()
        profile_number = self.profile_number_field.text().strip()
        
        if not sketch_number or not profile_number:
            QMessageBox.warning(self, "Save Profile", "Please enter both sketch number and profile number")
            return
        
        try:
            parameters = self._extract_parameters_from_tree()
            metadata = {
                'Sketch Number': sketch_number,
                'Profile Number': profile_number,
                'Input Filename': os.path.basename(self.current_file),
                'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Processing Status': 'Success',
                'Source File Path': self.current_file
            }
            success, message = self.profile_database.save_profile(metadata, parameters)
            
            if success:
                QMessageBox.information(self, "Save Profile", message)
                self.status_label.setText("Profile saved to database")
            else:
                QMessageBox.critical(self, "Save Profile", message)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save profile: {str(e)}")
            if 'metadata' in locals():
                metadata['Processing Status'] = f'Error: {str(e)}'
                try:
                    self.profile_database.save_profile(metadata, parameters)
                except:
                    pass

    def _update_parameters_tree(self, features: Dict[str, Any]):
        self.params_tree.clear()
        
        if not features:
            return
        
        categories = {
            'Basic Properties': {
                'number_of_loops': ('Number of Loops', ''),
                'profile_type': ('Profile Type', ''),
                'profile_area': ('Profile Area', 'mm²'),
                'outer_area': ('Outer Area', 'mm²'),
                'inner_area': ('Inner Area', 'mm²'),
                'hollow_ratio': ('Hollow Ratio', ''),
                'outer_perimeter': ('Outer Perimeter', 'mm'),
                'total_perimeter': ('Total Perimeter', 'mm'),
                'number_of_mandrels': ('Number of Mandrels', ''),
            },
            'Dimensions': {
                'bounding_box_width': ('Bounding Box Width', 'mm'),
                'bounding_box_height': ('Bounding Box Height', 'mm'),
                'bounding_box_area': ('Bounding Box Area', 'mm²'),
                'max_width': ('Max Width', 'mm'),
                'max_height': ('Max Height', 'mm'),
                'aspect_ratio': ('Aspect Ratio', ''),
            },
            'Extrusion Ratios': {
                'er_p22': ('ER for P22', ''),
                'er_p40': ('ER for P40', ''),
                'er_p55': ('ER for P55', ''),
                'holes_p22': ('Holes for P22', ''),
                'holes_p40': ('Holes for P40', ''),
                'holes_p55': ('Holes for P55', ''),
            },
            'Geometric Properties': {
                'compactness': ('Compactness', ''),
                'solidity': ('Solidity', ''),
                'ccd': ('Circumscribing Circle Diameter', 'mm'),
                'min_radius_outer': ('Min Radius (Outer)', 'mm'),
                'max_radius_outer': ('Max Radius (Outer)', 'mm'),
            },
            'Wall Thickness': {
                'max_wall_thickness': ('Max Wall Thickness', 'mm'),
                'min_wall_thickness': ('Min Wall Thickness', 'mm'),
                'avg_wall_thickness': ('Average Wall Thickness', 'mm'),
                'wall_thickness_variability': ('Wall Thickness Variability', 'mm'),
            },
            'Moments of Inertia': {
                'moment_of_inertia_x': ('Moment of Inertia (Ix)', 'mm⁴'),
                'moment_of_inertia_y': ('Moment of Inertia (Iy)', 'mm⁴'),
                'polar_moment_of_inertia': ('Polar Moment of Inertia', 'mm⁴'),
                'product_of_inertia': ('Product of Inertia', 'mm⁴'),
            },
            'Distance Metrics': {
                'euclidean_distance': ('Euclidean Distance', ''),
                'cosine_similarity': ('Cosine Similarity', ''),
            },
            'Mass Vectors': {
                'mass_vector_top_left': ('Top-Left Quadrant', ''),
                'mass_vector_top_right': ('Top-Right Quadrant', ''),
                'mass_vector_bottom_left': ('Bottom-Left Quadrant', ''),
                'mass_vector_bottom_right': ('Bottom-Right Quadrant', ''),
            },
            'Complexity Factors': {
                'complexity_factor_c1': ('C1 (Ps/As)', ''),
                'complexity_factor_c2': ('C2 (Ps/Ws)', ''),
                'complexity_factor_c3': ('C3 (CCD/Tm)', ''),
                'complexity_factor_c4': ('C4 (Groover)', ''),
                'complexity_factor_c5': ('C5 (Qamar)', ''),
            }
        }
        
        fourier_category = {}
        for i in range(1, 11):
            key = f'fourier_descriptor_{i}'
            fourier_category[key] = (f'Fourier Descriptor {i}', '')
        categories['Fourier Descriptors'] = fourier_category
        
        for category_name, params in categories.items():
            category_item = QTreeWidgetItem(self.params_tree)
            category_item.setText(0, category_name)
            category_item.setExpanded(True)
            
            font = category_item.font(0)
            font.setBold(True)
            category_item.setFont(0, font)
            
            if self.parent and hasattr(self.parent, 'colors'):
                colors = self.parent.colors
                dark_mode = hasattr(self.parent, 'dark_mode') and self.parent.dark_mode
                
                category_color = colors['primary'].lighter(180) if not dark_mode else colors['primary'].darker(140)
                category_item.setBackground(0, QBrush(category_color))
                category_item.setBackground(1, QBrush(category_color))
                category_item.setBackground(2, QBrush(category_color))
            
            for param_key, (param_name, unit) in params.items():
                if param_key in features:
                    value = features[param_key]
                    
                    if isinstance(value, float):
                        if abs(value) < 0.001:
                            formatted_value = f"{value:.6f}"
                        elif abs(value) < 1:
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = f"{value:.2f}"
                    else:
                        formatted_value = str(value)
                    
                    param_item = QTreeWidgetItem(category_item)
                    param_item.setText(0, param_name)
                    param_item.setText(1, formatted_value)
                    param_item.setText(2, unit)
                    
                    param_font = param_item.font(0)
                    param_font.setWeight(QFont.Normal)  
                    param_item.setFont(0, param_font)
                    param_item.setFont(1, param_font)
                    param_item.setFont(2, param_font)
        
        mandrel_features = {k: v for k, v in features.items() if k.startswith('mandrel_')}
        if mandrel_features:
            mandrel_category = QTreeWidgetItem(self.params_tree)
            mandrel_category.setText(0, "Mandrel Analysis")
            mandrel_category.setExpanded(True)
            
            font = mandrel_category.font(0)
            font.setBold(True)
            mandrel_category.setFont(0, font)
            
            if self.parent and hasattr(self.parent, 'colors'):
                colors = self.parent.colors
                dark_mode = hasattr(self.parent, 'dark_mode') and self.parent.dark_mode
                
                mandrel_color = colors['secondary'].lighter(180) if not dark_mode else colors['secondary'].darker(140)
                mandrel_category.setBackground(0, QBrush(mandrel_color))
                mandrel_category.setBackground(1, QBrush(mandrel_color))
                mandrel_category.setBackground(2, QBrush(mandrel_color))
            
            for mandrel_key, mandrel_data in mandrel_features.items():
                mandrel_item = QTreeWidgetItem(mandrel_category)
                mandrel_item.setText(0, mandrel_key.replace('_', ' ').title())
                mandrel_item.setExpanded(False)
                
                sub_font = mandrel_item.font(0)
                sub_font.setBold(True)
                mandrel_item.setFont(0, sub_font)
                
                mandrel_params = {
                    'area': ('Area', 'mm²'),
                    'perimeter': ('Perimeter', 'mm'),
                    'compactness': ('Compactness', ''),
                    'solidity': ('Solidity', ''),
                    'aspect_ratio': ('Aspect Ratio', ''),
                    'distance_from_cog_to_centroid': ('Distance from COG to Centroid', 'mm'),
                    'thickness_std_plus_x': ('Thickness Std (+X)', 'mm'),
                    'thickness_std_plus_y': ('Thickness Std (+Y)', 'mm'),
                    'thickness_std_minus_x': ('Thickness Std (-X)', 'mm'),
                    'thickness_std_minus_y': ('Thickness Std (-Y)', 'mm'),
                }
                
                for param_key, (param_name, unit) in mandrel_params.items():
                    if param_key in mandrel_data:
                        value = mandrel_data[param_key]
                        
                        if isinstance(value, float):
                            formatted_value = f"{value:.4f}"
                        else:
                            formatted_value = str(value)
                        
                        param_item = QTreeWidgetItem(mandrel_item)
                        param_item.setText(0, param_name)
                        param_item.setText(1, formatted_value)
                        param_item.setText(2, unit)
                        
                        param_font = param_item.font(0)
                        param_font.setWeight(QFont.Normal)  
                        param_item.setFont(0, param_font)
                        param_item.setFont(1, param_font)
                        param_item.setFont(2, param_font)

    def _extract_parameters_from_tree(self) -> Dict[str, Any]:
        parameters = {}
        
        root = self.params_tree.invisibleRootItem()
        for i in range(root.childCount()):
            category_item = root.child(i)
            category_name = category_item.text(0)
            
            category_params = {}
            for j in range(category_item.childCount()):
                param_item = category_item.child(j)
                param_name = param_item.text(0)
                param_value = param_item.text(1)
                param_unit = param_item.text(2)
                
                try:
                    if '.' in param_value:
                        param_value = float(param_value)
                    elif param_value.isdigit():
                        param_value = int(param_value)
                except ValueError:
                    pass
                
                category_params[param_name] = {
                    'value': param_value,
                    'unit': param_unit
                }
            
            parameters[category_name] = category_params
        
        return parameters

    def zoom_in(self):
        self.display_manager.zoom_in()

    def zoom_out(self):
        self.display_manager.zoom_out()

    def fit_to_view(self):
        self.display_manager.fit_to_view()

    def wheelEvent(self, event):
        modifiers = event.modifiers()

        is_mac = sys.platform == 'darwin'
        required_modifier = Qt.MetaModifier if is_mac else Qt.ControlModifier

        if modifiers & required_modifier:
            if event.angleDelta().y() > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        else:
            event.ignore()


    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.dxf') for url in urls):
                event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.dxf'):
                    self.load_dxf(file_path)
                    break
    
    def apply_theme(self):
        self._apply_control_panel_styling()
        
        if self.parent and hasattr(self.parent, 'colors'):
            self.display_manager.set_background_color(self.parent.colors['background'])
            
            if hasattr(self.parent, 'dark_mode'):
                self.display_manager.set_theme(self.parent.dark_mode)
                
        if not self.current_file:
            self.display_manager.add_placeholder_text("Drop a DXF file here or click Upload DXF")