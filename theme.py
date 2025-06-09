"""
Theme configuration for the database viewer application.
"""

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication
import logging

logger = logging.getLogger(__name__)

class ModernTheme:
    """Modern theme colors and styles"""
    COLORS = {
        'background': '#f5f5f5',
        'surface': '#ffffff',
        'primary': '#2196f3',
        'primary_dark': '#1976d2',
        'text': '#333333',
        'text_secondary': '#666666',
        'border': '#e0e0e0',
        'success': '#4caf50',
        'error': '#f44336',
        'warning': '#ff9800',
        'info': '#2196f3'
    }
    
    @classmethod
    def apply(cls, app):
        """Apply the modern theme to the application"""
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.Window, QColor(cls.COLORS['background']))
        palette.setColor(QPalette.WindowText, QColor(cls.COLORS['text']))
        palette.setColor(QPalette.Base, QColor(cls.COLORS['surface']))
        palette.setColor(QPalette.AlternateBase, QColor(cls.COLORS['background']))
        palette.setColor(QPalette.Text, QColor(cls.COLORS['text']))
        palette.setColor(QPalette.Button, QColor(cls.COLORS['surface']))
        palette.setColor(QPalette.ButtonText, QColor(cls.COLORS['text']))
        palette.setColor(QPalette.Link, QColor(cls.COLORS['primary']))
        palette.setColor(QPalette.Highlight, QColor(cls.COLORS['primary']))
        palette.setColor(QPalette.HighlightedText, QColor(cls.COLORS['surface']))
        
        app.setPalette(palette)
        
    @classmethod
    def get_stylesheet(cls):
        """Get the application stylesheet"""
        return f"""
            QMainWindow {{
                background-color: {cls.COLORS['background']};
            }}
            
            QWidget {{
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }}
            
            QPushButton {{
                background-color: {cls.COLORS['primary']};
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 4px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background-color: {cls.COLORS['primary_dark']};
            }}
            
            QPushButton:pressed {{
                background-color: {cls.COLORS['primary_dark']};
            }}
            
            QLineEdit, QComboBox {{
                padding: 6px;
                border: 1px solid {cls.COLORS['border']};
                border-radius: 4px;
                background-color: {cls.COLORS['surface']};
            }}
            
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {cls.COLORS['primary']};
            }}
            
            QLabel {{
                color: {cls.COLORS['text']};
            }}
            
            QTextBrowser {{
                background-color: {cls.COLORS['surface']};
                border: 1px solid {cls.COLORS['border']};
                border-radius: 4px;
                padding: 8px;
            }}
            
            QTableWidget {{
                background-color: {cls.COLORS['surface']};
                border: none;
                gridline-color: {cls.COLORS['border']};
            }}
            
            QTableWidget::item {{
                padding: 6px;
            }}
            
            QHeaderView::section {{
                background-color: {cls.COLORS['background']};
                padding: 6px;
                border: none;
                border-bottom: 1px solid {cls.COLORS['border']};
            }}
            
            QSplitter::handle {{
                background-color: {cls.COLORS['border']};
                height: 4px;
            }}
            
            QSplitter::handle:hover {{
                background-color: {cls.COLORS['primary']};
            }}
        """

class ThemeManager:
    def __init__(self):
        self.themes = {
            'light': {
                'name': 'Light',
                'palette': {
                    'window': '#f0f0f0',
                    'window_text': '#000000',
                    'base': '#ffffff',
                    'alternate_base': '#f5f5f5',
                    'text': '#000000',
                    'button': '#e0e0e0',
                    'button_text': '#000000',
                    'bright_text': '#ffffff',
                    'highlight': '#0078d7',
                    'highlight_text': '#ffffff',
                    'link': '#0000ff',
                    'link_visited': '#800080',
                    'error': '#ff0000',
                    'warning': '#ffa500',
                    'success': '#008000',
                    'info': '#0000ff'
                }
            },
            'dark': {
                'name': 'Dark',
                'palette': {
                    'window': '#2d2d2d',
                    'window_text': '#ffffff',
                    'base': '#1e1e1e',
                    'alternate_base': '#2d2d2d',
                    'text': '#ffffff',
                    'button': '#3d3d3d',
                    'button_text': '#ffffff',
                    'bright_text': '#ffffff',
                    'highlight': '#0078d7',
                    'highlight_text': '#ffffff',
                    'link': '#4a9eff',
                    'link_visited': '#b15dff',
                    'error': '#ff6b6b',
                    'warning': '#ffd93d',
                    'success': '#6bff6b',
                    'info': '#4a9eff'
                }
            },
            'high_contrast': {
                'name': 'High Contrast',
                'palette': {
                    'window': '#000000',
                    'window_text': '#ffffff',
                    'base': '#000000',
                    'alternate_base': '#000000',
                    'text': '#ffffff',
                    'button': '#000000',
                    'button_text': '#ffffff',
                    'bright_text': '#ffffff',
                    'highlight': '#ffff00',
                    'highlight_text': '#000000',
                    'link': '#00ffff',
                    'link_visited': '#ff00ff',
                    'error': '#ff0000',
                    'warning': '#ffff00',
                    'success': '#00ff00',
                    'info': '#00ffff'
                }
            },
            'electric_green': {
                'name': 'Electric Green',
                'palette': {
                    'window': '#1a1a1a',
                    'window_text': '#00ff00',
                    'base': '#000000',
                    'alternate_base': '#1a1a1a',
                    'text': '#00ff00',
                    'button': '#003300',
                    'button_text': '#00ff00',
                    'bright_text': '#ffffff',
                    'highlight': '#00ff00',
                    'highlight_text': '#000000',
                    'link': '#00ff00',
                    'link_visited': '#00cc00',
                    'error': '#ff0000',
                    'warning': '#ffff00',
                    'success': '#00ff00',
                    'info': '#00ffff'
                }
            },
            'cyber_pink': {
                'name': 'Cyber Pink',
                'palette': {
                    'window': '#1a1a1a',
                    'window_text': '#ff00ff',
                    'base': '#000000',
                    'alternate_base': '#1a1a1a',
                    'text': '#ff00ff',
                    'button': '#330033',
                    'button_text': '#ff00ff',
                    'bright_text': '#ffffff',
                    'highlight': '#ff00ff',
                    'highlight_text': '#000000',
                    'link': '#ff00ff',
                    'link_visited': '#cc00cc',
                    'error': '#ff0000',
                    'warning': '#ffff00',
                    'success': '#00ff00',
                    'info': '#00ffff'
                }
            }
        }
        
    def apply_theme(self, app, theme_name: str) -> None:
        """
        Apply a theme to the application.
        
        Args:
            app: QApplication instance
            theme_name: Name of the theme to apply
        """
        if theme_name not in self.themes:
            logger.warning(f"Theme '{theme_name}' not found, using 'light' theme")
            theme_name = 'light'
            
        theme = self.themes[theme_name]
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.Window, QColor(theme['palette']['window']))
        palette.setColor(QPalette.WindowText, QColor(theme['palette']['window_text']))
        palette.setColor(QPalette.Base, QColor(theme['palette']['base']))
        palette.setColor(QPalette.AlternateBase, QColor(theme['palette']['alternate_base']))
        palette.setColor(QPalette.Text, QColor(theme['palette']['text']))
        palette.setColor(QPalette.Button, QColor(theme['palette']['button']))
        palette.setColor(QPalette.ButtonText, QColor(theme['palette']['button_text']))
        palette.setColor(QPalette.BrightText, QColor(theme['palette']['bright_text']))
        palette.setColor(QPalette.Highlight, QColor(theme['palette']['highlight']))
        palette.setColor(QPalette.HighlightedText, QColor(theme['palette']['highlight_text']))
        palette.setColor(QPalette.Link, QColor(theme['palette']['link']))
        palette.setColor(QPalette.LinkVisited, QColor(theme['palette']['link_visited']))
        
        app.setPalette(palette)
        logger.info(f"Applied theme: {theme['name']}")
        
    def get_theme_names(self) -> list:
        """
        Get list of available theme names.
        
        Returns:
            List of theme names
        """
        return [theme['name'] for theme in self.themes.values()]
        
    def get_theme_colors(self, theme_name: str) -> dict:
        """
        Get colors for a specific theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            Dictionary of color names and values
        """
        if theme_name not in self.themes:
            logger.warning(f"Theme '{theme_name}' not found, using 'light' theme")
            theme_name = 'light'
            
        return self.themes[theme_name]['palette']
        
    def get_color(self, theme_name: str, color_name: str) -> str:
        """
        Get a specific color from a theme.
        
        Args:
            theme_name: Name of the theme
            color_name: Name of the color
            
        Returns:
            Color value as hex string
        """
        if theme_name not in self.themes:
            logger.warning(f"Theme '{theme_name}' not found, using 'light' theme")
            theme_name = 'light'
            
        theme = self.themes[theme_name]
        if color_name not in theme['palette']:
            logger.warning(f"Color '{color_name}' not found in theme '{theme_name}'")
            return '#000000'
            
        return theme['palette'][color_name]
        
    def get_stylesheet(self, theme_name: str) -> str:
        """
        Get stylesheet for a theme.
        
        Args:
            theme_name: Name of the theme
            
        Returns:
            CSS stylesheet string
        """
        if theme_name not in self.themes:
            logger.warning(f"Theme '{theme_name}' not found, using 'light' theme")
            theme_name = 'light'
            
        theme = self.themes[theme_name]
        colors = theme['palette']
        
        return f"""
            QMainWindow {{
                background-color: {colors['window']};
                color: {colors['window_text']};
            }}
            
            QWidget {{
                background-color: {colors['window']};
                color: {colors['window_text']};
            }}
            
            QLineEdit, QTextEdit, QPlainTextEdit {{
                background-color: {colors['base']};
                color: {colors['text']};
                border: 1px solid {colors['button']};
                padding: 2px;
            }}
            
            QPushButton {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: 1px solid {colors['button']};
                padding: 5px;
                border-radius: 3px;
            }}
            
            QPushButton:hover {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QPushButton:pressed {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QComboBox {{
                background-color: {colors['base']};
                color: {colors['text']};
                border: 1px solid {colors['button']};
                padding: 2px;
            }}
            
            QComboBox::drop-down {{
                border: none;
            }}
            
            QComboBox::down-arrow {{
                image: none;
                border: none;
            }}
            
            QTableWidget {{
                background-color: {colors['base']};
                color: {colors['text']};
                gridline-color: {colors['button']};
                border: 1px solid {colors['button']};
            }}
            
            QTableWidget::item {{
                padding: 5px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QHeaderView::section {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                padding: 5px;
                border: 1px solid {colors['button']};
            }}
            
            QMenuBar {{
                background-color: {colors['window']};
                color: {colors['window_text']};
            }}
            
            QMenuBar::item {{
                background-color: {colors['window']};
                color: {colors['window_text']};
                padding: 5px;
            }}
            
            QMenuBar::item:selected {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QMenu {{
                background-color: {colors['window']};
                color: {colors['window_text']};
                border: 1px solid {colors['button']};
            }}
            
            QMenu::item {{
                background-color: {colors['window']};
                color: {colors['window_text']};
                padding: 5px;
            }}
            
            QMenu::item:selected {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QStatusBar {{
                background-color: {colors['window']};
                color: {colors['window_text']};
            }}
            
            QToolBar {{
                background-color: {colors['window']};
                color: {colors['window_text']};
                border: none;
            }}
            
            QToolBar::separator {{
                width: 1px;
                background-color: {colors['button']};
                margin: 5px;
            }}
            
            QToolButton {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: 1px solid {colors['button']};
                padding: 5px;
                border-radius: 3px;
            }}
            
            QToolButton:hover {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QToolButton:pressed {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QSplitter::handle {{
                background-color: {colors['button']};
            }}
            
            QSplitter::handle:horizontal {{
                width: 4px;
            }}
            
            QSplitter::handle:vertical {{
                height: 4px;
            }}
            
            QScrollBar:vertical {{
                background-color: {colors['window']};
                width: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {colors['button']};
                min-height: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:vertical:hover {{
                background-color: {colors['highlight']};
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            
            QScrollBar:horizontal {{
                background-color: {colors['window']};
                height: 12px;
                margin: 0px;
            }}
            
            QScrollBar::handle:horizontal {{
                background-color: {colors['button']};
                min-width: 20px;
                border-radius: 6px;
            }}
            
            QScrollBar::handle:horizontal:hover {{
                background-color: {colors['highlight']};
            }}
            
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            
            QMessageBox {{
                background-color: {colors['window']};
                color: {colors['window_text']};
            }}
            
            QMessageBox QPushButton {{
                background-color: {colors['button']};
                color: {colors['button_text']};
                border: 1px solid {colors['button']};
                padding: 5px;
                border-radius: 3px;
                min-width: 80px;
            }}
            
            QMessageBox QPushButton:hover {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
            
            QMessageBox QPushButton:pressed {{
                background-color: {colors['highlight']};
                color: {colors['highlight_text']};
            }}
        """ 