# QuantumOps

A modern build management and deployment tool for mobile applications, built with PySide6.

**Current Version:** 1.0.0-beta  
**Status:** Fully functional with Azure integration and health monitoring

## Feature Table

| Feature                                      | Description                                                      | Status        |
|----------------------------------------------|------------------------------------------------------------------|---------------|
| Fetch and manage mobile builds (Android/iOS) | View, filter, and manage builds for Android and iOS              | ✅ Implemented   |
| Download builds from Azure DevOps            | Download build artifacts from Azure DevOps pipelines              | ✅ Implemented   |
| Upload builds to Azure Blob Storage          | Upload Android/iOS builds to Azure Blob Storage from the UI       | ✅ Implemented   |
| Preview build metadata and artifacts         | View build details and metadata in the UI                         | ✅ Implemented   |
| Direct installation to connected devices     | Install builds directly to connected Android/iOS devices          | ✅ Implemented   |
| Service Principal authentication for Azure   | Secure authentication for Azure services                          | ✅ Implemented   |
| Modern, responsive UI                        | User-friendly, modern interface with light theme                  | ✅ Implemented   |
| Build history tracking and export            | Track and export build history                                    | ✅ Implemented   |
| Configurable Azure Web App log streaming     | Real-time log streaming from Azure Web Apps                       | ✅ Implemented   |
| Share build URLs                             | Generate and share URLs for builds                                | ✅ Implemented   |
| Config-driven design                         | Use JSON for environments, web apps, and build settings           | ✅ Implemented   |
| **Health Monitoring System**                 | Real-time health checks for development and staging environments  | ✅ **NEW** |
| **Platform Management**                      | Android/iOS specific build operations and device management       | ✅ **NEW** |
| **Configuration Persistence**                | Save and reload health endpoints and build settings               | ✅ **NEW** |
| **Mock Mode Fallback**                       | Graceful handling of missing Azure credentials                    | ✅ **NEW** |
| Security best practices                      | Environment variables, least privilege, DevSecOps                 | ✅ Implemented   |
| Extensibility for new providers/stores       | Design allows adding new cloud providers and artifact stores      | 🔄 Planned       |
| Automated tests and CI                       | Comprehensive unit tests and CI integration                       | ✅ Implemented   |
| Documentation and guides                     | User and developer documentation                                  | ✅ Implemented   |

## New Features in 1.0.0-beta

### 🏥 Health Monitoring System
- **Real-time Health Checks**: Monitor development and staging environments
- **Persistent Configuration**: Health endpoints saved to `config/health_endpoints.json`
- **Configurable Endpoints**: Add, edit, or remove health check URLs through settings
- **Visual Status Indicators**: Clear health status display in the UI

### 📱 Platform Management
- **Android/iOS Support**: Platform-specific build operations and device management
- **Context Switching**: Platform dropdown controls build context and operations
- **Device Integration**: Direct install capabilities for both platforms

### 🎨 UI Improvements
- **Modern Light Theme**: Clean, professional interface with Bootstrap-inspired styling
- **Auto-fitting Layouts**: Table rows automatically resize for optimal button visibility
- **Expanded Log Area**: Full vertical space utilization for better log viewing
- **Responsive Design**: Improved layout and user experience

### 🔧 Configuration & Persistence
- **Environment Variable Loading**: Automatic loading from `.env` files
- **Configuration Persistence**: Settings saved and reloaded automatically
- **Mock Mode Fallback**: Graceful handling of missing Azure credentials

## Features

- Fetch and manage mobile builds (Android/iOS)
- Download builds from Azure DevOps
- Upload builds to Azure Blob Storage (fully implemented, robust, and tested)
- Preview build metadata and artifacts
- Direct installation to connected devices
- Service Principal authentication for Azure
- Modern, responsive UI with light theme
- **Real-time health monitoring for development and staging environments**
- **Platform-specific build management and operations**

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
python -m venv qops_venv
source qops_venv/bin/activate  # Linux/macOS
# or
.\qops_venv\Scripts\activate  # Windows
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

1. Create a `.env` file in the project root:
```bash
# Azure Storage Configuration
AZURE_STORAGE_ACCOUNT=your-storage-account-name
AZURE_STORAGE_CONTAINER=mobile-builds
AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key

# Azure Service Principal Authentication
AZURE_CLIENT_ID=your-client-id
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id
```

2. Configure build settings in `config/eas.json`

3. Health endpoints are automatically configured in `config/health_endpoints.json`

## Usage

Run the application:
```bash
python main.py
```

### Build Management

- View available builds
- Download builds
- Upload builds to Azure Blob Storage (Android/iOS) directly from the UI
- Preview build metadata
- Install to connected devices
- Share build URLs

### Health Monitoring

- Access via **Settings → Health Check Settings**
- Add, edit, or remove health check endpoints
- View real-time health status
- Configure monitoring intervals

### Platform Operations

- Use the **Platform** dropdown to switch between Android and iOS
- Platform-specific build operations and device management
- Context-aware UI and functionality

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
│   ├── health_endpoints.json  # Health monitoring endpoints
│   ├── eas.json              # Build configuration
│   └── webapps.json          # Azure Web Apps
├── docs/                   # Documentation
├── scripts/               # Build and utility scripts
├── tests/                 # Test files and configuration
├── views/                 # UI components and dialogs
├── controllers/           # Business logic and controllers
├── models/                # Data models
├── services/              # Azure service integration
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
- **Health monitoring system provides real-time visibility into service health.**
- **Platform management enables efficient Android/iOS build operations.**
- **Configuration persistence ensures settings are maintained across sessions.**