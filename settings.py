"""
Settings helpers for QuantumOps using QSettings.
"""
import logging
from typing import Any, Optional

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)
logger.info("Loaded quantumops.settings module.")


def get_setting(
    key: str, default: Optional[Any] = None, settings: Optional[QSettings] = None
) -> Any:
    """Get a value from QSettings."""
    logger.info(f"Called get_setting(key={key}, default={default})")
    if settings is None:
        settings = QSettings()
    return settings.value(key, default)


def set_setting(key: str, value: Any, settings: Optional[QSettings] = None) -> None:
    """Set a value in QSettings."""
    logger.info(f"Called set_setting(key={key}, value={value})")
    if settings is None:
        settings = QSettings()
    settings.setValue(key, value)
    settings.sync()


def sync_settings(settings: Optional[QSettings] = None) -> None:
    """Sync QSettings to disk."""
    logger.info("Called sync_settings()")
    if settings is None:
        settings = QSettings()
    settings.sync()
