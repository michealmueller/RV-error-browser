# QuantumOps

A modern build management and deployment tool for mobile applications, built with PySide6.

## Feature Table

| Feature                                      | Description                                                      | Status        |
|----------------------------------------------|------------------------------------------------------------------|---------------|
| Fetch and manage mobile builds (Android/iOS) | View, filter, and manage builds for Android and iOS              | Implemented   |
| Download builds from Azure DevOps            | Download build artifacts from Azure DevOps pipelines              | Implemented   |
| Upload builds to Azure Blob Storage          | Upload Android/iOS builds to Azure Blob Storage from the UI       | Implemented   |
| Preview build metadata and artifacts         | View build details and metadata in the UI                         | Implemented   |
| Direct installation to connected devices     | Install builds directly to connected Android/iOS devices          | Implemented   |
| Service Principal authentication for Azure   | Secure authentication for Azure services                          | Implemented   |
| Modern, responsive UI                        | User-friendly, modern interface                                   | Implemented   |
| Build history tracking and export            | Track and export build history                                    | Implemented   |
| Configurable Azure Web App log streaming     | Real-time log streaming from Azure Web Apps                       | Implemented   |
| Share build URLs                             | Generate and share URLs for builds                                | Implemented   |
| Config-driven design                         | Use JSON for environments, web apps, and build settings           | Implemented   |
| Security best practices                      | Environment variables, least privilege, DevSecOps                 | Implemented   |
| Extensibility for new providers/stores       | Design allows adding new cloud providers and artifact stores      | Planned       |
| Automated tests and CI                       | Comprehensive unit tests and CI integration                       | Implemented   |
| Documentation and guides                     | User and developer documentation                                  | Implemented   |

## Features

- Fetch and manage mobile builds (Android/iOS)
- Download builds from Azure DevOps
- Upload builds to Azure Blob Storage (fully implemented, robust, and tested)
- Preview build metadata and artifacts
- Direct installation to connected devices
- Service Principal authentication for Azure
- Modern, responsive UI

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
- Upload builds to Azure Blob Storage (Android/iOS) directly from the UI
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
├── tests/                 # Test files and configuration
├── quantumops/           # Main package
│   ├── models/           # Data models
│   ├── views/            # UI components
│   └── controllers/      # Business logic
└── ...
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Implementation Notes

- The Azure Blob Storage upload feature is now fully implemented and integrated from the UI to the backend.
- Upload actions in the UI for both Android and iOS builds now trigger the backend upload logic, with progress and error handling.
- The backend logic is robust, with comprehensive unit tests covering all edge cases and error scenarios.
- The test suite is in sync with the code, ensuring future changes are caught by CI.