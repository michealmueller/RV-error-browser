"""Theme configuration for QuantumOps."""

from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

THEMES = {
    "Quantum Blue": {
        "primary": "#2196F3",
        "secondary": "#1976D2",
        "background": "#FFFFFF",
        "text": "#212121",
        "accent": "#64B5F6"
    },
    "Vivid Purple": {
        "primary": "#9C27B0",
        "secondary": "#7B1FA2",
        "background": "#FFFFFF",
        "text": "#212121",
        "accent": "#BA68C8"
    },
    "Electric Green": {
        "primary": "#4CAF50",
        "secondary": "#388E3C",
        "background": "#FFFFFF",
        "text": "#212121",
        "accent": "#81C784"
    },
    "Cyber Pink": {
        "primary": "#E91E63",
        "secondary": "#C2185B",
        "background": "#FFFFFF",
        "text": "#212121",
        "accent": "#F06292"
    }
}

def apply_branding_theme(theme_name: str) -> QPalette:
    """Apply a branding theme to the application.
    
    Args:
        theme_name: Name of the theme to apply
        
    Returns:
        QPalette: The configured palette
    """
    if theme_name not in THEMES:
        theme_name = "Quantum Blue"  # Default theme
        
    theme = THEMES[theme_name]
    palette = QPalette()
    
    # Set colors
    palette.setColor(QPalette.Window, QColor(theme["background"]))
    palette.setColor(QPalette.WindowText, QColor(theme["text"]))
    palette.setColor(QPalette.Base, QColor(theme["background"]))
    palette.setColor(QPalette.AlternateBase, QColor(theme["accent"]))
    palette.setColor(QPalette.ToolTipBase, QColor(theme["background"]))
    palette.setColor(QPalette.ToolTipText, QColor(theme["text"]))
    palette.setColor(QPalette.Text, QColor(theme["text"]))
    palette.setColor(QPalette.Button, QColor(theme["primary"]))
    palette.setColor(QPalette.ButtonText, QColor(theme["background"]))
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(theme["secondary"]))
    palette.setColor(QPalette.Highlight, QColor(theme["accent"]))
    palette.setColor(QPalette.HighlightedText, QColor(theme["background"]))
    
    return palette 