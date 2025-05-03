# PostgreSQL Database Viewer

A modern PySide6-based application for viewing PostgreSQL database tables with real-time logging functionality.

## Features

- Connect to PostgreSQL databases
- Query and display table data
- Real-time logging with timestamps
- Clear log functionality
- Auto-scrolling log window
- Dynamic table column headers
- Pre-configured database connections
- Modern UI with resizable panels
- JSON formatting for details column

## Installation

### From Source

1. Clone the repository:
```bash
git clone https://github.com/yourusername/postgresql-viewer.git
cd postgresql-viewer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python main.py
```

### Using pip

```bash
pip install postgresql-viewer
postgresql-viewer
```

## Building Executable

To build a standalone executable:

```bash
pyinstaller postgresql_viewer.spec
```

The executable will be created in the `dist` directory.

## Usage

1. Enter PostgreSQL connection details
2. Enter the table name to query
3. Click 'Connect' to establish database connection
4. Click 'Get Logs' to fetch and display table data
5. Use 'Clear All' to reset the log window and results

## Development

### Project Structure

```
postgresql-viewer/
├── main.py              # Application entry point
├── app.py               # Main application window and logic
├── theme.py             # Modern theme configuration
├── delegates.py         # Custom table delegates
├── dialogs.py           # Dialog windows
├── requirements.txt     # Python dependencies
├── postgresql_viewer.spec  # PyInstaller configuration
└── README.md            # Project documentation
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.