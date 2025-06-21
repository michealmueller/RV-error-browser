import pytest

from main_window import DatabaseApp


@pytest.fixture
def app(qtbot):
    """Create the application window."""
    window = DatabaseApp()
    qtbot.addWidget(window)
    return window


def test_log_message_types(app):
    """Test different types of log messages."""
    # Test info message
    app.log_message("Test info message", "INFO")
    assert "INFO" in app.log_output.toPlainText()
    assert "Test info message" in app.log_output.toPlainText()

    # Test error message
    app.log_message("Test error message", "ERROR")
    assert "ERROR" in app.log_output.toPlainText()
    assert "Test error message" in app.log_output.toPlainText()

    # Test warning message
    app.log_message("Test warning message", "WARNING")
    assert "WARNING" in app.log_output.toPlainText()
    assert "Test warning message" in app.log_output.toPlainText()

    # Test success message
    app.log_message("Test success message", "SUCCESS")
    assert "SUCCESS" in app.log_output.toPlainText()
    assert "Test success message" in app.log_output.toPlainText()


def test_log_clear(app):
    """Test clearing the log."""
    # Add some messages
    app.log_message("Test message 1", "INFO")
    app.log_message("Test message 2", "ERROR")

    # Clear the log
    app.clear_log()
    assert app.log_output.toPlainText() == ""


def test_log_formatting(app):
    """Test log message formatting."""
    # Test timestamp format
    app.log_message("Test message", "INFO")
    log_text = app.log_output.toPlainText()
    assert "[" in log_text
    assert "]" in log_text
    assert "INFO" in log_text
    assert "Test message" in log_text


def test_log_scroll(app):
    """Test that the log scrolls to the bottom when new messages are added."""
    # Add initial message
    app.log_message("Initial message", "INFO")
    initial_scroll = app.log_output.verticalScrollBar().value()

    # Add more messages
    for i in range(10):
        app.log_message(f"Message {i}", "INFO")

    # Check that the scroll position has changed
    final_scroll = app.log_output.verticalScrollBar().value()
    assert final_scroll > initial_scroll


def test_log_maximum_size(app):
    """Test that the log doesn't grow indefinitely."""
    # Add many messages
    for i in range(1000):
        app.log_message(f"Message {i}", "INFO")

    # Check that the log size is reasonable
    log_size = len(app.log_output.toPlainText())
    assert log_size < 1000000  # Less than 1MB
