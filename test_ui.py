#!/usr/bin/env python3
"""
Test script for the updated CAD viewer UI
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PyQt5.QtWidgets import QApplication
from dxf_analyzer.gui.main_window import DXFProfileAnalyzer

def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    # Create and show the main window
    window = DXFProfileAnalyzer()
    window.show()
    
    # Run the application
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 