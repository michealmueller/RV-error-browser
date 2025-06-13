# QuantumOps - Mobile Build Manager

A modern application for managing mobile builds across different platforms.

## Features

- Manage Android and iOS builds
- Upload and download builds from Azure Storage
- Track build status and metadata
- View build history
- Multiple layout options (Classic Tabbed, Split View, Dashboard)
- Health monitoring
- Log viewing
- Database integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/quantumops.git
cd quantumops
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

1. Set up Azure credentials:
   - Set `AZURE_STORAGE_ACCOUNT` environment variable
   - Configure Azure service principal credentials

2. Configure database connection:
   - Set database connection parameters in `.env` file

To connect to a database, you must first add a new connection using the "Add Connection" button in the UI. Once a connection is saved, you must set an environment variable to provide the password.

The application constructs the environment variable name from the connection name by converting it to uppercase, replacing hyphens with underscores, and appending `_DB_PASSWORD`.

For example, if you create a connection named `RV-Dev`, you must set the following environment variable before launching the application:

```bash
export RV_DEV_PASSWORD="your_password_here"
```

## Usage

Run the application:
```bash
python main.py
```

## Development

### Security

The application uses parameterized queries to prevent SQL injection vulnerabilities. All user-supplied input is safely quoted, ensuring that the database remains secure.

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