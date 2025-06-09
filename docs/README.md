# QuantumOps

A modern build management and deployment tool for mobile applications, built with PySide6.

## Features

- Fetch and manage mobile builds (Android/iOS)
- Download builds from Azure DevOps
- Upload builds to Azure Blob Storage
- Preview build metadata and artifacts
- Direct installation to connected devices
- Service Principal authentication for Azure
- Modern, responsive UI
- Automated documentation archiving system

## Requirements

- Python 3.11 or higher
- PySide6
- Azure Identity
- Azure Storage Blob
- ADB (for Android builds)
- ideviceinstaller (for iOS builds)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/rosievision/quantumops.git
cd quantumops
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate  # Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package:
```bash
pip install -e .
```

## Configuration

1. Set up Azure Service Principal:
   - Create a service principal in Azure AD
   - Assign appropriate RBAC roles
   - Configure environment variables:
     ```
     AZURE_TENANT_ID=your_tenant_id
     AZURE_CLIENT_ID=your_client_id
     AZURE_CLIENT_SECRET=your_client_secret
     ```

2. Configure build settings in `config/eas.json`

## Usage

Run the application:
```bash
quantumops
```

### Build Management

- View available builds
- Download builds
- Upload to Azure Blob Storage
- Preview build metadata
- Install to connected devices
- Share build URLs

### Development

1. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

2. Run tests:
```bash
python tests/config/run_tests.py
```

3. Run GUI tests:
```bash
./tests/config/run_gui_tests.sh
```

## Project Structure

```
quantumops/
├── config/                 # Configuration files
├── docs/                   # Documentation
├── scripts/               # Build and utility scripts
│   ├── archive_docs.sh    # Documentation archiving script
│   └── setup_cron.sh      # Cron job setup for archiving
├── archives/              # Archived documentation
├── tests/                 # Test files and configuration
├── quantumops/           # Main package
│   ├── models/           # Data models
│   ├── views/            # UI components
│   └── controllers/      # Business logic
└── ...
```

## Documentation

- [Project Overview](PROJECT_OVERVIEW.md)
- [Configuration Reference](CONFIG_REFERENCE.md)
- [DevOps Guide](DEVOPS_GUIDE.md)
- [Archiving System](ARCHIVING.md) - Documentation archiving and context optimization
- [Bug Analysis](BUG_ANALYSIS.md)
- [Changelog](CHANGELOG.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.