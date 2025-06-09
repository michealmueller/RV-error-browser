# QuantumOps Project Overview

QuantumOps is a cross-platform build management and deployment tool for mobile applications, designed for DevOps teams managing Android and iOS builds. It integrates with Azure DevOps, Azure Blob Storage, and device management tools to streamline the build, distribution, and installation process.

## Purpose
- Centralize mobile build management (fetch, preview, download, upload, install, share)
- Integrate with Azure services for secure, scalable artifact storage and retrieval
- Provide a modern, responsive UI for DevOps workflows

## Architecture
- **UI Layer:** PySide6-based desktop application
- **Controllers:** Orchestrate business logic, connect UI to models
- **Models:** Handle data, Azure API integration, and build metadata
- **Config:** JSON-driven configuration for environments, web apps, and build settings
- **Logging:** Real-time log streaming from Azure Web Apps

## Main Components
- `main.py`: Application entry point
- `quantumops/views/`: UI dialogs and main window
- `quantumops/controllers/`: Business logic, Azure integration, log streaming
- `quantumops/models/`: Data models for builds, logs, and Azure
- `config/`: Environment and web app configuration
- `tests/`: Unit and integration tests

## Key Features
- Build artifact preview and metadata
- Download/upload to Azure Blob Storage
- Direct install to Android/iOS devices
- Service Principal authentication for Azure
- Configurable Azure Web App log streaming
- Build history tracking and export

## Extensibility
- Add new cloud providers or artifact stores via modular controllers/models
- Extend UI with new dialogs or actions
- Integrate additional device management tools

## Security
- Uses environment variables and config files for secrets
- Follows least privilege and DevSecOps best practices

---
For more details, see the other documentation files in `docs/`. 