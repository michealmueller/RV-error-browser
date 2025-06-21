# QuantumOps Project Overview

QuantumOps is a desktop application for DevOps teams to streamline the management of mobile application builds from Expo Application Services (EAS). It provides a unified interface to view, download, and manage Android and iOS builds, and to monitor the health of associated web services.

## Purpose
- **Centralize Build Management:** Provide a single dashboard for viewing and interacting with Android and iOS builds from EAS.
- **Simplify DevOps Workflows:** Automate the process of fetching build lists, downloading artifacts, and pushing them to Azure Blob Storage.
- **Monitor Service Health:** Offer a real-time view of the health of configured web services (e.g., RosieVision, ProjectFlow).
- **Enhance Developer Productivity:** Reduce the need for command-line tools and web UIs by consolidating common tasks into one application.

## Architecture
- **UI Layer:** A responsive desktop application built with PySide6, providing a modern and intuitive user experience.
- **Controllers:** A layer of controller objects that manage the application's business logic, connecting the UI to the underlying data models.
- **Models:** A set of data models responsible for handling all interactions with external services, including fetching data from the EAS API, checking service health, and managing build history.
- **Services:** Dedicated modules for interacting with external APIs, including `EasService` for Expo builds and `AzureService` for blob storage.
- **Configuration:** A `config` directory containing JSON files for managing EAS settings (`eas.json`) and health check endpoints (`health_endpoints.json`).

## Main Components
- `main.py`: The main entry point for the application.
- `views/`: Contains all UI components, including the main window, build tables, and dialogs.
- `controllers/`: Manages the application's logic, including build operations and health checks.
- `models/`: Handles data management and API interactions.
- `services/`: Provides dedicated clients for interacting with EAS and Azure services.
- `config/`: Stores all user-configurable settings.

## Key Features
- **Dual Build Views:** Separate, side-by-side tables for Android and iOS builds, allowing for easy comparison and management.
- **Dynamic Filtering:** Filter builds by version using a dynamically populated dropdown menu.
- **Real-time Health Checks:** Automatically monitor and display the health status of configured RosieVision and ProjectFlow services.
- **EAS Integration:** Fetch build lists for both Android and iOS platforms directly from the Expo Application Services (EAS) API.
- **Azure Blob Storage Integration:** Download build artifacts with a single click and push them directly to a configured Azure Blob Storage container.
- **Local Build History:** Maintain a local, persistent history of all build-related actions for auditing and troubleshooting.
- **Secure Credential Management:** Load Azure and EAS credentials securely from a `.env` file.
- **In-place Progress Bars:** Visual feedback for downloads and uploads directly in the build tables.
- **Custom File Naming:** Downloaded and uploaded artifacts are named with a clear and consistent convention: `{platform}-{profile}-v{version}-{versionCode}-{fingerprint}.{extension}`.

## Extensibility
- The modular design of the services layer allows for the future addition of new cloud providers or build services.
- The UI can be extended with new views and dialogs to support additional functionality.

## Security
- All sensitive credentials, including Azure and EAS tokens, are managed through a `.env` file and are not hard-coded in the application.
- The application follows the principle of least privilege, only requiring the necessary permissions to perform its tasks.

---
For more detailed information on specific topics, please refer to the other documentation files in this directory. 