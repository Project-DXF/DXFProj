"""
Unit tests for the core application module.
"""

import pytest
from unittest.mock import Mock, patch
from src.dxf_analyzer.core.application import DXFProfileAnalyzer


class TestDXFProfileAnalyzer:
    """Test cases for the DXFProfileAnalyzer class."""
    
    def test_init(self):
        """Test application initialization."""
        app = DXFProfileAnalyzer()
        assert app.app is None
        assert app.main_window is None
    
    @patch('src.dxf_analyzer.core.application.QApplication')
    @patch('src.dxf_analyzer.core.application.MainWindow')
    def test_run(self, mock_main_window, mock_qapp):
        """Test application run method."""
        # Setup mocks
        mock_app_instance = Mock()
        mock_qapp.return_value = mock_app_instance
        mock_app_instance.exec_.return_value = 0
        
        mock_window_instance = Mock()
        mock_main_window.return_value = mock_window_instance
        
        # Test
        app = DXFProfileAnalyzer()
        result = app.run()
        
        # Assertions
        mock_qapp.assert_called_once()
        mock_main_window.assert_called_once()
        mock_window_instance.show.assert_called_once()
        mock_app_instance.exec_.assert_called_once()
        assert result == 0 