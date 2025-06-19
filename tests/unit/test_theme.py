import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from theming import apply_branding_theme, BRANDING_THEMES

@pytest.mark.parametrize("brand,theme", BRANDING_THEMES.items())
def test_apply_branding_theme_sets_palette(qapp, brand, theme):
    apply_branding_theme(brand)
    palette = qapp.palette()
    # Check that the highlight and link colors match the theme
    assert palette.color(QPalette.Highlight).name().lower() == QColor(theme["primary"]).name().lower()
    assert palette.color(QPalette.Link).name().lower() == QColor(theme["accent"]).name().lower()


def test_apply_branding_theme_unknown_brand(qapp, caplog):
    # Should not raise, should log a warning
    apply_branding_theme("Nonexistent Brand")
    # Should fallback to Quantum Blue
    palette = qapp.palette()
    assert palette.color(QPalette.Highlight).name().lower() == QColor(BRANDING_THEMES["Quantum Blue"]["primary"]).name().lower() 