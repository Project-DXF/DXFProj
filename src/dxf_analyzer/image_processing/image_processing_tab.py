import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QFileDialog, QGroupBox, QScrollArea,
                            QMessageBox, QSplitter, QDialog, QTreeWidget,
                            QTreeWidgetItem, QGraphicsScene, QGraphicsView)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap, QPainter
import numpy as np

from .image_analyzer import ImageAnalyzer
from .similarity_finder import SimilarityFinder
from ..database import ProfileDatabase


class ImageProcessingTab(QWidget):    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.current_dxf = None
        self.current_doc = None
        self.image_analyzer = ImageAnalyzer()
        self.similarity_finder = SimilarityFinder()
        self.profile_database = ProfileDatabase()
        self.is_updating = False
        self.initUI()
        
        if self.parent and hasattr(self.parent, 'event_manager'):
            self.parent.event_manager.dxf_loaded.connect(self.on_dxf_loaded)
        
    def on_dxf_loaded(self, file_path, doc):
        if self.is_updating:
            return
            
        self.is_updating = True
        try:
            self.current_dxf = file_path
            self.current_doc = doc
            self.update_current_dxf_display()
        finally:
            self.is_updating = False
        
    def set_current_dxf(self, file_path):
        if self.is_updating:
            return
            
        self.is_updating = True
        try:
            self.current_dxf = file_path
            if file_path:
                self.update_current_dxf_display()
                
                if self.parent and hasattr(self.parent, 'event_manager'):
                    self.parent.event_manager.update_dxf(file_path, None)
        finally:
            self.is_updating = False
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        toolbar = QHBoxLayout()
        upload_dxf_btn = QPushButton("Upload DXF")
        upload_dxf_btn.clicked.connect(lambda: self.parent.upload_dxf("image_processing"))
        upload_dxf_btn.setMinimumWidth(150)
        
        find_similar_btn = QPushButton("Find Similar DXF Files")
        find_similar_btn.clicked.connect(self.find_similar_files)
        find_similar_btn.setMinimumWidth(150)
        
        toolbar.addWidget(upload_dxf_btn)
        toolbar.addWidget(find_similar_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        splitter = QSplitter(Qt.Horizontal)
        
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        current_dxf_group = QGroupBox("Current DXF")
        current_dxf_layout = QVBoxLayout()
        
        self.current_dxf_scene = QGraphicsScene()
        self.current_dxf_view = QGraphicsView(self.current_dxf_scene)
        self.current_dxf_view.setMinimumSize(400, 300)
        current_dxf_layout.addWidget(self.current_dxf_view)
        
        self.current_dxf_info = QLabel("No DXF file loaded")
        self.current_dxf_info.setWordWrap(True)
        current_dxf_layout.addWidget(self.current_dxf_info)
        
        current_dxf_group.setLayout(current_dxf_layout)
        left_layout.addWidget(current_dxf_group)
        
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        similar_group = QGroupBox("Similar DXF Files")
        similar_layout = QVBoxLayout()
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.similar_dxfs_layout = QVBoxLayout(scroll_content)
        scroll.setWidget(scroll_content)
        similar_layout.addWidget(scroll)
        
        similar_group.setLayout(similar_layout)
        right_layout.addWidget(similar_group)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([400, 600])
        
        layout.addWidget(splitter)
        
    def update_current_dxf_display(self):
        if not self.current_dxf:
            self.current_dxf_info.setText("No DXF file loaded")
            return
            
        try:
            dxf_image = self.image_analyzer._dxf_to_image(self.current_dxf)
            if dxf_image is not None:
                height, width = dxf_image.shape
                bytes_per_line = width
                q_img = QImage(dxf_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
                
                self.current_dxf_scene.clear()
                pixmap = QPixmap.fromImage(q_img)
                self.current_dxf_scene.addPixmap(pixmap)
                
                self.current_dxf_view.setRenderHint(QPainter.Antialiasing)
                self.current_dxf_view.setRenderHint(QPainter.SmoothPixmapTransform)
                self.current_dxf_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.current_dxf_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
                self.current_dxf_view.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
                self.current_dxf_view.setSceneRect(self.current_dxf_scene.itemsBoundingRect())
                self.current_dxf_view.fitInView(self.current_dxf_scene.sceneRect(), Qt.KeepAspectRatio)
                
                self.current_dxf_info.setText(f"Current DXF: {os.path.basename(self.current_dxf)}")
            else:
                self.current_dxf_info.setText("Failed to convert DXF to image")
            
        except Exception as e:
            print(f"Error displaying DXF: {str(e)}")
            self.current_dxf_info.setText(f"Error displaying DXF: {str(e)}")
            
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, 'current_dxf_view') and self.current_dxf_scene.items():
            self.current_dxf_view.fitInView(self.current_dxf_scene.sceneRect(), Qt.KeepAspectRatio)
            
    def create_similar_dxf_widget(self, dxf_data):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        
        preview_scene = QGraphicsScene()
        preview_view = QGraphicsView(preview_scene)
        preview_view.setFixedSize(200, 150)
        
        dxf_image = self.image_analyzer._dxf_to_image(dxf_data['path'])
        if dxf_image is not None:
            height, width = dxf_image.shape
            bytes_per_line = width
            q_img = QImage(dxf_image.data, width, height, bytes_per_line, QImage.Format_Grayscale8)
            preview_scene.addPixmap(QPixmap.fromImage(q_img))
            preview_view.fitInView(preview_scene.sceneRect(), Qt.KeepAspectRatio)
        
        layout.addWidget(preview_view)
        
        info_panel = QWidget()
        info_layout = QVBoxLayout(info_panel)
        
        info_layout.addWidget(QLabel(f"File: {dxf_data['filename']}"))
        info_layout.addWidget(QLabel(f"Similarity: {dxf_data['similarity']}%"))
        info_layout.addWidget(QLabel(f"Database ID: {dxf_data['id']}"))
        
        params_btn = QPushButton("View Parameters")
        params_btn.clicked.connect(lambda: self.show_parameters(dxf_data))
        info_layout.addWidget(params_btn)
        
        load_btn = QPushButton("Load This DXF")
        load_btn.clicked.connect(lambda: self.load_similar_dxf(dxf_data['path']))
        info_layout.addWidget(load_btn)
        
        layout.addWidget(info_panel)
        return widget
        
    def show_parameters(self, dxf_data):
        params = self.profile_database.get_profile_parameters(dxf_data['id'])
        if not params:
            QMessageBox.warning(self, "No Parameters", "No parameters found for this DXF file")
            return
            
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Parameters - {dxf_data['filename']}")
        dialog.setMinimumSize(500, 400)
        
        layout = QVBoxLayout(dialog)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(["Parameter", "Value", "Unit"])
        tree.setAlternatingRowColors(True)
        
        for category, category_params in params.items():
            category_item = QTreeWidgetItem([category])
            tree.addTopLevelItem(category_item)
            
            for param_name, param_data in category_params.items():
                param_item = QTreeWidgetItem([
                    param_name,
                    str(param_data['value']),
                    param_data['unit']
                ])
                category_item.addChild(param_item)
        
        layout.addWidget(tree)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec_()
        
    def load_similar_dxf(self, dxf_path):
        if self.parent:
            self.parent.cad_widget.load_dxf(dxf_path)
            self.parent.tab_widget.setCurrentIndex(0)
            
    def clear_similar_dxfs(self):
        while self.similar_dxfs_layout.count():
            item = self.similar_dxfs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
    def find_similar_files(self):
        if not self.current_dxf:
            QMessageBox.warning(self, "No DXF File", "Please load a DXF file first")
            return
            
        self.clear_similar_dxfs()
        
        try:
            similar_files = self.similarity_finder.find_similar_dxfs(self.current_dxf)
            
            for dxf_data in similar_files:
                widget = self.create_similar_dxf_widget(dxf_data)
                self.similar_dxfs_layout.addWidget(widget)
            
            self.similar_dxfs_layout.addStretch()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to find similar files: {str(e)}")
            
    def update_database_path(self, path: str):
        self.similarity_finder.set_database_path(path) 