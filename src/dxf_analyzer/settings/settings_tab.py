from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QLineEdit, QPushButton, QMessageBox)
from ..database.profile_database import ProfileDatabase

class SettingsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.profile_database = ProfileDatabase()
        self.initUI()
        
    def initUI(self):
        """Initialize the settings tab UI"""
        layout = QVBoxLayout()
        
        # Database Connection Settings
        db_group = QVBoxLayout()
        db_group.addWidget(QLabel("Database Connection Settings"))
        
        # Server
        server_layout = QHBoxLayout()
        server_layout.addWidget(QLabel("Server:"))
        self.server_input = QLineEdit(self)
        self.server_input.setText("DESKTOP-I4EU9RQ\\SQLEXPRESS")
        server_layout.addWidget(self.server_input)
        db_group.addLayout(server_layout)
        
        # Database Name
        db_layout = QHBoxLayout()
        db_layout.addWidget(QLabel("Database:"))
        self.db_name_input = QLineEdit(self)
        self.db_name_input.setText("DXFProfiles")
        db_layout.addWidget(self.db_name_input)
        db_group.addLayout(db_layout)
        
        # Test Connection Button
        test_button = QPushButton("Test Connection", self)
        test_button.clicked.connect(self.test_connection)
        db_group.addWidget(test_button)
        
        layout.addLayout(db_group)
        layout.addStretch()
        self.setLayout(layout)
    
    def test_connection(self):
        """Test the database connection with current settings"""
        try:
            conn_str = (
                'DRIVER={ODBC Driver 17 for SQL Server};'
                f'SERVER={self.server_input.text()};'
                f'DATABASE={self.db_name_input.text()};'
                'Trusted_Connection=yes;'
                'TrustServerCertificate=yes;'
            )
            
            # Test connection
            db = ProfileDatabase(conn_str)
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Profiles")
                count = cursor.fetchone()[0]
            
            QMessageBox.information(
                self,
                "Connection Test",
                f"Connection successful!\nFound {count} profiles in database."
            )
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Connection Error",
                f"Failed to connect to database:\n{str(e)}"
            )