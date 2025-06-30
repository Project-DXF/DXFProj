from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                            QLabel, QFileDialog, QGroupBox, QGridLayout,
                            QCheckBox, QLineEdit)

from ..database import ProfileDatabase

class SettingsTab(QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.profile_database = ProfileDatabase() 
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        theme_group = QGroupBox("Theme Settings")
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(10)
        theme_layout.setContentsMargins(16, 16, 16, 16)
        
        self.dark_mode_checkbox = QCheckBox("Dark Mode")
        self.dark_mode_checkbox.setChecked(self.parent.dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(lambda state: self.parent.toggle_theme(bool(state)))
        theme_layout.addWidget(self.dark_mode_checkbox)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        db_group = QGroupBox("Database Settings")
        db_layout = QGridLayout()
        db_layout.setSpacing(10)
        db_layout.setContentsMargins(16, 16, 16, 16)
        
        db_path_label = QLabel("Database Save Path:")
        self.db_path_input = QLineEdit()
        self.db_path_input.setText(str(self.profile_database.db_path))
        self.db_path_input.setMinimumWidth(300)
        self.db_path_input.setReadOnly(True)
        browse_btn = QPushButton("Browse...")
        browse_btn.setMinimumWidth(100)
        
        browse_btn.clicked.connect(self.browse_db_path)
        
        db_layout.addWidget(db_path_label, 0, 0)
        db_layout.addWidget(self.db_path_input, 0, 1)
        db_layout.addWidget(browse_btn, 0, 2)
        db_layout.setColumnStretch(1, 1)
        
        self.db_status_label = QLabel("")
        self.db_status_label.setStyleSheet("color: #666; font-size: 9pt;")
        db_layout.addWidget(self.db_status_label, 1, 0, 1, 3)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        layout.addStretch()
        
    def browse_db_path(self):
        current_path = self.db_path_input.text()
        new_path, _ = QFileDialog.getSaveFileName(
            self,
            "Select Database Location",
            current_path,
            "Excel Files (*.xlsx);;All Files (*.*)"
        )
        
        if new_path:
            if not new_path.endswith('.xlsx'):
                new_path += '.xlsx'
            
            success = self.profile_database.set_db_path(new_path)
            if success:
                self.db_path_input.setText(new_path)
                self.db_status_label.setText("Database location updated successfully")
                self.db_status_label.setStyleSheet("color: green; font-size: 9pt;")
                if hasattr(self.parent, 'cad_widget'):
                    self.parent.cad_widget.profile_database.set_db_path(new_path)
            else:
                self.db_status_label.setText("Failed to update database location")
                self.db_status_label.setStyleSheet("color: red; font-size: 9pt;")
            
    def get_db_path(self):
        return self.db_path_input.text() 