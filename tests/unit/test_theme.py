import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QPalette, QColor
from quantumops.theming import apply_branding_theme, BRANDING_THEMES

def test_theme_colors():
    """Test that theme colors are defined correctly."""
    colors = ModernTheme.COLORS
    assert "background" in colors
    assert "surface" in colors
    assert "primary" in colors
    assert "text" in colors
    assert "border" in colors
    assert "hover" in colors
    assert "error" in colors
    assert "success" in colors
    assert "warning" in colors

def test_theme_stylesheet():
    """Test that the theme stylesheet is generated correctly."""
    stylesheet = ModernTheme.get_stylesheet()
    assert "QMainWindow" in stylesheet
    assert "QPushButton" in stylesheet
    assert "QLineEdit" in stylesheet
    assert "QComboBox" in stylesheet
    assert "QTextEdit" in stylesheet
    assert "QTableWidget" in stylesheet
    assert "QHeaderView" in stylesheet
    assert "QScrollBar" in stylesheet

def test_theme_application(qapp):
    """Test that the theme can be applied to the application."""
    # Apply theme
    ModernTheme.apply(qapp)
    
    # Check palette colors
    palette = qapp.palette()
    assert palette.window().color().name() == ModernTheme.COLORS["background"]
    assert palette.windowText().color().name() == ModernTheme.COLORS["text"]
    assert palette.button().color().name() == ModernTheme.COLORS["surface"]
    assert palette.buttonText().color().name() == ModernTheme.COLORS["text"]

def test_theme_consistency():
    """Test that theme colors are consistent."""
    colors = ModernTheme.COLORS
    
    # Check color formats
    for color in colors.values():
        assert color.startswith("#")
        assert len(color) == 7  # #RRGGBB format
    
    # Check color relationships
    assert colors["background"] != colors["surface"]
    assert colors["primary"] != colors["text"]
    assert colors["error"] != colors["success"]
    assert colors["warning"] != colors["error"]

def test_theme_widget_styles():
    """Test that theme styles are applied to widgets."""
    # Create test widgets
    from PySide6.QtWidgets import QPushButton, QLineEdit, QComboBox
    button = QPushButton()
    line_edit = QLineEdit()
    combo_box = QComboBox()
    
    # Apply theme
    ModernTheme.apply(qapp)
    
    # Check widget styles
    assert button.styleSheet()
    assert line_edit.styleSheet()
    assert combo_box.styleSheet()
    
    # Check specific styles
    button_style = button.styleSheet()
    assert "background-color" in button_style
    assert "color" in button_style
    assert "border" in button_style
    assert "border-radius" in button_style

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