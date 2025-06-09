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

## Usage

Run the application:
```bash
python main.py
```

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

# PostgreSQL Viewer

A modern application for managing and viewing PostgreSQL databases.

## Features

- Connect to PostgreSQL databases
- View and edit table data
- Execute custom SQL queries
- Export data to various formats
- Multiple layout options (Classic Tabbed, Split View, Dashboard)
- Health monitoring
- Log viewing
- Database integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/postgresql-viewer.git
cd postgresql-viewer
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

1. Set up database connection:
   - Set database connection parameters in `.env` file
   - Configure SSL settings if needed

2. Configure logging:
   - Set log level in `.env` file
   - Configure log file location

## Usage

Run the application:
```bash
python main.py
```

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