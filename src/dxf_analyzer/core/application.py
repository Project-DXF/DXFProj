"""
Main application class for DXF Profile Analyzer.
"""

import sys
from PyQt5.QtWidgets import QApplication
from ..gui.main_window import DXFProfileAnalyzer as MainWindow


class DXFProfileAnalyzer:
    """Main application controller for the DXF Profile Analyzer."""
    
    def __init__(self):
        """Initialize the application."""
        self.app = None
        self.main_window = None
    
    def run(self):
        """Start the application."""
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow()
        self.main_window.show()
        return self.app.exec_()
    
    @classmethod
    def main(cls):
        """Main entry point for the application."""
        app = cls()
        sys.exit(app.run()) 