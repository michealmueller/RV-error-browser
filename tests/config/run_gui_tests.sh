#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 &
XVFB_PID=$!

# Set display for GUI tests
export DISPLAY=":99"
export QT_QPA_PLATFORM="offscreen"

# Run GUI tests
python -m pytest tests/unit/test_app.py -v -m "gui"

# Cleanup
kill $XVFB_PID
