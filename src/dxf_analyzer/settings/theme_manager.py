from PyQt5.QtGui import QColor
from typing import Dict, Any


class ThemeManager:   
    def __init__(self):
        self.dark_mode = False
        self.colors = self._get_light_theme()
        
    def _get_light_theme(self) -> Dict[str, QColor]:
        return {
            'background': QColor('#ffffff'),
            'surface': QColor('#f5f5f5'),
            'primary': QColor('#2196f3'),
            'secondary': QColor('#1976d2'),
            'text': QColor('#000000'),
            'error': QColor('#f44336'),
            'success': QColor('#4caf50'),
            'warning': QColor('#ff9800')
        }
        
    def _get_dark_theme(self) -> Dict[str, QColor]:
        return {
            'background': QColor('#1e1e1e'),
            'surface': QColor('#2d2d2d'),
            'primary': QColor('#2196f3'),
            'secondary': QColor('#1976d2'),
            'text': QColor('#ffffff'),
            'error': QColor('#f44336'),
            'success': QColor('#4caf50'),
            'warning': QColor('#ff9800')
        }
    
    def toggle_theme(self, dark_mode: bool = None):
        if dark_mode is not None:
            self.dark_mode = dark_mode
        else:
            self.dark_mode = not self.dark_mode
            
        self.colors = self._get_dark_theme() if self.dark_mode else self._get_light_theme()
        
    def get_widget_specific_style(self, widget_type: str) -> str:
        styles = {
            'button': self._get_button_style(),
            'tree': self._get_tree_style(),
            'status': self._get_status_style(),
            'toolbar': self._get_toolbar_style(),
            'cad_viewer': self._get_cad_viewer_style(),
            'form': self._get_form_style()
        }
        return styles.get(widget_type, '')
    
    def _get_button_style(self) -> str:
        return f"""
            QPushButton {{
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 20px;
                background-color: {self.colors['primary'].name()};
                color: {'white' if self.dark_mode else 'white'};
                border: none;
            }}
            QPushButton:hover {{
                background-color: {self.colors['secondary'].name()};
            }}
            QPushButton:pressed {{
                background-color: {self.colors['secondary'].darker(120).name()};
            }}
            QPushButton:disabled {{
                background-color: {'#555' if self.dark_mode else '#BDBDBD'};
                color: {'#888' if self.dark_mode else '#757575'};
            }}
        """
    
    def _get_tree_style(self) -> str:
        return f"""
            background-color: {self.colors['surface'].name()};
            alternate-background-color: {'#2a2a2a' if self.dark_mode else '#f8f8f8'};
            color: {self.colors['text'].name()};
            border: 1px solid {'#555' if self.dark_mode else '#ddd'};
            border-radius: 4px;
            gridline-color: {'#444' if self.dark_mode else '#eee'};
            selection-background-color: {self.colors['primary'].name()};
            selection-color: white;
            font-size: 10pt;
        """
    
    def _get_status_style(self) -> str:
        return f"""
            padding: 8px;
            background: {self.colors['surface'].name()};
            border-top: 1px solid {'#555' if self.dark_mode else '#ddd'};
            color: {self.colors['text'].name()};
            font-size: 10pt;
            font-weight: normal;
        """
    
    def _get_toolbar_style(self) -> str:
        return f"""
            spacing: 5px;
            padding: 8px;
            background: {self.colors['background'].name()};
            border-bottom: 1px solid {'#555' if self.dark_mode else '#ddd'};
            border-radius: 4px;
        """
    
    def _get_cad_viewer_style(self) -> str:
        return f"""
            background-color: {self.colors['surface'].name()};
            border: 1px solid {'#555' if self.dark_mode else '#ddd'};
            border-radius: 4px;
        """
    
    def _get_form_style(self) -> str:
        return f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 4px;
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
            }}
            
        """
    
    def get_stylesheet(self) -> str:
        # Define theme-specific colors for QGroupBox
        group_text_color = self.colors['primary'].name() if not self.dark_mode else '#89CFF0'  # Light blue for dark mode
        group_hover_color = self.colors['secondary'].name() if not self.dark_mode else '#00BFFF'  # Deeper blue for hover
        
        return f"""
            QPushButton, QToolButton, QComboBox, QTreeView::branch:has-children,

            QCheckBox {{
                spacing: 8px;
                color: {self.colors['text'].name()};
                padding: 4px;
                border-radius: 4px;
            }}

            QCheckBox:hover {{
                background-color: {self.colors['primary'].lighter(180).name() if not self.dark_mode else self.colors['primary'].darker(180).name()};
            }}

            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {self.colors['primary'].name()};
                background-color: {self.colors['surface'].name()};
            }}

            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary'].name()};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w1IDhMMiA1IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }}

            QCheckBox::indicator:checked:hover {{
                background-color: {self.colors['secondary'].name()};
                border-color: {self.colors['secondary'].name()};
            }}

            QCheckBox::indicator:disabled {{
                border-color: {'#555' if self.dark_mode else '#BDBDBD'};
                background-color: {'#333' if self.dark_mode else '#F5F5F5'};
            }}

            QCheckBox:disabled {{
                color: {'#888' if self.dark_mode else '#757575'};
            }}

            QRadioButton {{
                spacing: 8px;
                color: {self.colors['text'].name()};
                padding: 4px;
                border-radius: 4px;
            }}

            QRadioButton:hover {{
                background-color: {self.colors['primary'].lighter(180).name() if not self.dark_mode else self.colors['primary'].darker(180).name()};
            }}

            QRadioButton::indicator {{
                width: 20px;
                height: 20px;
                border-radius: 10px;
                border: 2px solid {self.colors['primary'].name()};
                background-color: transparent;
            }}

            QRadioButton::indicator:hover {{
                border-color: {self.colors['secondary'].name()};
            }}

            QRadioButton::indicator:checked {{
                background-color: {self.colors['primary'].name()};
                border: 6px solid {self.colors['primary'].name()};
            }}

            QRadioButton::indicator:checked:hover {{
                background-color: white;
                border: 6px solid {self.colors['secondary'].name()};
            }}

            QRadioButton::indicator:disabled {{
                border-color: {'#555' if self.dark_mode else '#BDBDBD'};
                background-color: {'#333' if self.dark_mode else '#F5F5F5'};
            }}

            QRadioButton:disabled {{
                color: {'#888' if self.dark_mode else '#757575'};
            }}

            QComboBox {{
                padding: 8px 12px;
                border: 2px solid {self.colors['primary'].name()};
                border-radius: 6px;
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                min-width: 150px;
            }}

            QComboBox:hover {{
                border-color: {self.colors['secondary'].name()};
            }}

            QComboBox:focus {{
                border-color: {self.colors['secondary'].name()};
                background-color: {self.colors['primary'].lighter(180).name() if not self.dark_mode else self.colors['primary'].darker(180).name()};
            }}

            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}

            QComboBox::down-arrow {{
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMiA0TDYgOEwxMCA0IiBzdHJva2U9IiM2NjY2NjYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIi8+PC9zdmc+);
                width: 12px;
                height: 12px;
            }}

            QComboBox:disabled {{
                background-color: {'#333' if self.dark_mode else '#F5F5F5'};
                border-color: {'#555' if self.dark_mode else '#BDBDBD'};
                color: {'#888' if self.dark_mode else '#757575'};
            }}

            QComboBox QAbstractItemView {{
                border: 2px solid {self.colors['primary'].name()};
                border-radius: 6px;
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                selection-background-color: {self.colors['primary'].name()};
                selection-color: white;
                padding: 4px;
            }}

            QLineEdit {{
                padding: 8px;
                border: 2px solid {'#555' if self.dark_mode else '#ddd'};
                border-radius: 6px;
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
            }}

            QLineEdit:focus {{
                border-color: {self.colors['primary'].name()};
            }}

            QLineEdit:read-only {{
                background-color: {'#333' if self.dark_mode else '#f5f5f5'};
                color: {'#aaa' if self.dark_mode else '#666'};
            }}

            QMainWindow {{
                background-color: {self.colors['background'].name()};
                color: {self.colors['text'].name()};
            }}
            
            QWidget {{
                background-color: {self.colors['background'].name()};
                color: {self.colors['text'].name()};
            }}
            
            QPushButton {{
                padding: 12px;
                border-radius: 6px;
                font-weight: bold;
                min-height: 20px;
                background-color: {self.colors['primary'].name()};
                color: white;
                border: none;
            }}
            
            QPushButton:hover {{
                background-color: {self.colors['secondary'].name()};
            }}
            
            QPushButton:pressed {{
                background-color: {self.colors['secondary'].darker(120).name()};
            }}
            
            QPushButton:disabled {{
                background-color: {'#555' if self.dark_mode else '#BDBDBD'};
                color: {'#888' if self.dark_mode else '#757575'};
            }}
            
            QTabWidget::pane {{
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                background-color: {self.colors['surface'].name()};
                border-radius: 8px;
                margin-top: -1px;
            }}
            
            QTabBar::tab {{
                background-color: {self.colors['surface'].name()};
                color: {self.colors['text'].name()};
                border: 1px solid {'#555' if self.dark_mode else '#ddd'};
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }}
            
            QTabBar::tab:selected {{
                background-color: {self.colors['primary'].name()};
                color: white;
            }}
            
            QGroupBox {{
                background-color: {{ 'rgba(0,0,0,0.04)' if not self.dark_mode else 'rgba(255,255,255,0.05)' }};
                border: 1px solid {group_text_color};
                border-radius: 10px;
                margin-top: 1.2em;
                padding: 20px;
                padding-top: 32px;
            }}
            
            QGroupBox:hover {{
                border-color: {group_hover_color};
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top center;
                background-color: {self.colors['background'].name()};
                color: {group_text_color};
                padding: 2px 10px;
                font-weight: 600;
                margin-top: 8px;
                font-size: 11pt;
                border-radius: 6px;
            }}
            
            QGroupBox:hover::title {{
                color: {group_hover_color};
            }}
            
            QGroupBox QWidget {{
                background-color: transparent;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid {self.colors['primary'].name()};
                background-color: {self.colors['surface'].name()};
            }}

            QCheckBox::indicator:checked {{
                background-color: {self.colors['primary'].name()};
                image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTIiIGhlaWdodD0iMTIiIHZpZXdCb3g9IjAgMCAxMiAxMiIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cGF0aCBkPSJNMTAgM0w1IDhMMiA1IiBzdHJva2U9IndoaXRlIiBzdHJva2Utd2lkdGg9IjIiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPjwvc3ZnPg==);
            }}
        """ 