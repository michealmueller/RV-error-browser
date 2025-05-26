"""
Theming and branding logic for QuantumOps using qdarktheme.
"""
from typing import Dict, Any, Optional
import qdarktheme
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.theming module.")

BRANDING_THEMES = {
    "Quantum Blue":   {"primary": "#2196F3", "accent": "#1976D2"},
    "Vivid Purple":   {"primary": "#9C27B0", "accent": "#7B1FA2"},
    "Electric Green": {"primary": "#00E676", "accent": "#00C853"},
    "Cyber Pink":     {"primary": "#FF4081", "accent": "#C51162"},
}

CURRENT_BRAND = {"primary": "#2196F3", "accent": "#1976D2"}

def setup_qdarktheme(theme_name: str = "light", custom_colors: Optional[Dict[str, Any]] = None) -> None:
    logger.info(f"Called setup_qdarktheme(theme_name={theme_name}, custom_colors={custom_colors})")
    if custom_colors:
        qdarktheme.setup_theme(theme=theme_name, custom_colors=custom_colors)
    else:
        qdarktheme.setup_theme(theme=theme_name)

def get_branding_themes() -> Dict[str, Dict[str, str]]:
    logger.info("Called get_branding_themes()")
    return BRANDING_THEMES 

def get_current_brand_colors():
    """
    Return the current brand's color dictionary (primary, accent).
    """
    return CURRENT_BRAND

def apply_branding_theme(brand: str) -> None:
    """
    Apply a branding theme to the application using qdarktheme and a custom palette.
    Only 'primary' is a valid custom_colors key for qdarktheme.setup_theme.
    See: https://pyqtdarktheme.readthedocs.io/en/stable/reference/theme_color.html
    """
    logger.info(f"Applying branding theme: {brand}")
    app = QApplication.instance()
    theme = BRANDING_THEMES.get(brand, BRANDING_THEMES["Quantum Blue"])
    CURRENT_BRAND.update(theme)
    qdarktheme.setup_theme(
        theme="dark",
        custom_colors={"primary": theme["primary"]},
    )
    # Set palette for accent color (for widgets that use it)
    palette = app.palette()
    palette.setColor(QPalette.Highlight, QColor(theme["primary"]))
    palette.setColor(QPalette.Link, QColor(theme["accent"]))
    app.setPalette(palette) 