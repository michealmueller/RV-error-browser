import pytest
from PySide6.QtGui import QPalette, QColor
from quantumops.theming import apply_branding_theme, BRANDING_THEMES

@pytest.mark.parametrize("brand,theme", BRANDING_THEMES.items())
def test_apply_branding_theme_sets_palette(app, brand, theme):
    apply_branding_theme(brand)
    palette = app.palette()
    # Check that the highlight and link colors match the theme
    assert palette.color(QPalette.Highlight).name().lower() == QColor(theme["primary"]).name().lower()
    assert palette.color(QPalette.Link).name().lower() == QColor(theme["accent"]).name().lower()


def test_apply_branding_theme_unknown_brand(app, caplog):
    # Should not raise, should log a warning
    apply_branding_theme("Nonexistent Brand")
    # Should fallback to Quantum Blue
    palette = app.palette()
    assert palette.color(QPalette.Highlight).name().lower() == QColor(BRANDING_THEMES["Quantum Blue"]["primary"]).name().lower() 