import pytest
from PySide6.QtWidgets import QApplication, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPainter, QStyleOptionViewItem
from delegates import DetailsDelegate

@pytest.fixture
def table():
    """Create a table widget with test data."""
    table = QTableWidget(1, 1)
    table.setItem(0, 0, QTableWidgetItem("Test message"))
    return table

@pytest.fixture
def delegate():
    """Create a details delegate."""
    return DetailsDelegate()

def test_delegate_initialization(delegate):
    """Test that the delegate initializes correctly."""
    assert isinstance(delegate, DetailsDelegate)

def test_delegate_paint(delegate, table):
    """Test that the delegate paints correctly."""
    # Create a painter and style option
    painter = QPainter()
    option = QStyleOptionViewItem()
    option.rect = table.rect()
    
    # Test painting
    delegate.paint(painter, option, table.model().index(0, 0))

def test_delegate_size_hint(delegate, table):
    """Test that the delegate calculates size correctly."""
    # Get size hint
    size = delegate.sizeHint(QStyleOptionViewItem(), table.model().index(0, 0))
    
    # Verify size
    assert isinstance(size, QSize)
    assert size.width() > 0
    assert size.height() > 0

def test_format_details():
    """Test that details are formatted correctly."""
    # Test JSON formatting
    json_details = '{"key": "value"}'
    formatted = DetailsDelegate.format_details(json_details)
    assert "<pre>" in formatted
    assert "key" in formatted
    assert "value" in formatted
    
    # Test plain text formatting
    text_details = "Plain text message"
    formatted = DetailsDelegate.format_details(text_details)
    assert text_details in formatted

def test_delegate_style(delegate):
    """Test that the delegate applies correct styling."""
    # Test HTML formatting
    details = "Test message"
    formatted = DetailsDelegate.format_details(details)
    assert "font-family" in formatted
    assert "font-size" in formatted
    assert "color" in formatted
    assert "background-color" in formatted
    assert "padding" in formatted
    assert "border" in formatted
    assert "border-radius" in formatted

def test_delegate_performance(delegate, table):
    """Test delegate performance with large data."""
    # Create large test data
    large_data = "Test message " * 1000
    table.setItem(0, 0, QTableWidgetItem(large_data))
    
    # Measure size hint calculation time
    import time
    start_time = time.time()
    delegate.sizeHint(QStyleOptionViewItem(), table.model().index(0, 0))
    end_time = time.time()
    
    # Verify performance
    assert end_time - start_time < 0.1  # Should take less than 100ms 