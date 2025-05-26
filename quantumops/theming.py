"""
Theming and branding logic for QuantumOps using qdarktheme.
"""
from typing import Dict, Any, Optional
import qdarktheme
import logging

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.theming module.")

BRANDING_THEMES = {
    "Quantum Blue": {
        "primary": "#00BFFF",
        "info": "#00BFFF",
        "warning": "#FFD600",
        "danger": "#FF5555"
    },
    "Vivid Purple": {
        "primary": "#A259FF",
        "info": "#A259FF",
        "warning": "#FFD600",
        "danger": "#FF5555"
    },
    "Electric Green": {
        "primary": "#00FFB0",
        "info": "#00FFB0",
        "warning": "#FFD600",
        "danger": "#FF5555"
    },
    "Cyber Pink": {
        "primary": "#FF2D95",
        "info": "#FF2D95",
        "warning": "#FFD600",
        "danger": "#FF5555"
    }
}

def setup_qdarktheme(theme_name: str = "light", custom_colors: Optional[Dict[str, Any]] = None) -> None:
    logger.info(f"Called setup_qdarktheme(theme_name={theme_name}, custom_colors={custom_colors})")
    if custom_colors:
        qdarktheme.setup_theme(theme=theme_name, custom_colors=custom_colors)
    else:
        qdarktheme.setup_theme(theme=theme_name)

def get_branding_themes() -> Dict[str, Dict[str, str]]:
    logger.info("Called get_branding_themes()")
    return BRANDING_THEMES 