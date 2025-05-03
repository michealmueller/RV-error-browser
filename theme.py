"""
Theme configuration for the database viewer application.
"""

from PySide6.QtGui import QColor, QPalette

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