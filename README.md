# RVEB - RosieVision Error Browser

A modern PostgreSQL error log viewer application built with PySide6.

## Features

- Connect to PostgreSQL databases
- View and analyze error logs in real-time
- Manage multiple database connections
- Color-coded log messages with timestamps
- Modern UI with professional styling
- Cross-platform support (Windows, macOS, Linux)
- Connection persistence
- Custom table formatting for error details
- Comprehensive logging system

python -m pytest tests/unit/test_app.py -v## UI Features

The application features a modern, professional interface with:

- Clean, flat design with rounded corners
- Professional color scheme with consistent styling
- Split-pane interface for efficient workflow:
  - Left panel: Connection management and log output
  - Right panel: Query results with custom formatting
- Menu bar with File, View, and Help sections
- Connection management through a dedicated dialog
- Real-time log window with color-coded messages
- Custom table formatting for error details
- Responsive layout with proper spacing and padding
- Modern typography using Segoe UI font
- Visual feedback for user interactions
- Proper cleanup on window close

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/msquared86/RV-error-browser.git
cd RV-error-browser
```

2. Install dependencies:
```bash
pip install -e .
```

3. Run the application:
```bash
python main.py
```

### From Package

```bash
pip install RosieVision-Error-Browser
rosievision-error-browser
```

## Development

### Running Tests

The project uses pytest for testing. To run the tests:

```bash
pytest
```

The test suite includes:
- Unit tests for all components
- Integration tests for database operations
- Build process tests
- GitHub Actions workflow tests

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration and deployment. The pipeline:

1. Runs the test suite
2. Builds executables for Windows, macOS, and Linux
3. Creates a release with the built executables

The pipeline will fail if:
- Any tests fail
- The build process fails
- The release creation fails

### Building Executables

To build executables locally:

```bash
python build.py
```

This will create platform-specific executables in the `dist` directory.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

All pull requests must pass the CI/CD pipeline before being merged.