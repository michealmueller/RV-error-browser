# PostgreSQL Error Browser

A modern application for browsing and managing PostgreSQL error logs.

## Features

- Connect to PostgreSQL databases
- Browse error logs in a table view
- Save and manage multiple database connections
- Multiple themes (Light, Dark, High Contrast)
- Auto-refresh functionality
- Rich logging with timestamps
- Split view layout
- Connection management
- Settings persistence

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/postgres-error-browser.git
cd postgres-error-browser
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

1. Set up PostgreSQL database:
   - Create a database with an `error_logs` table
   - The table should have columns: `type`, `message`, `details`

2. Configure database connection:
   - Use the application's connection dialog to add database connections
   - Connections are saved in `~/.postgres_error_browser/settings.json`

## Usage

Run the application:
```bash
python main.py
```

### Main Features

1. Connection Management:
   - Add, edit, and delete database connections
   - Save connection details securely
   - Auto-connect to last used connection

2. Log Browsing:
   - View error logs in a table format
   - Sort and filter logs
   - Auto-refresh functionality
   - Clear logs

3. UI Features:
   - Multiple themes (Light, Dark, High Contrast)
   - Split view layout
   - Status bar with messages
   - Menu bar with common actions
   - Toolbar for quick access

## Development

### Running Tests

```bash
pytest tests/unit/ tests/integration/ -v
```

### Code Style

The project uses:
- Black for code formatting
- isort for import sorting
- flake8 for linting
- mypy for type checking

Run all checks:
```bash
pre-commit run --all-files
```

## License

© 2024 Rosie Vision 