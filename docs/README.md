# QuantumOps

**QuantumOps** is a powerful and intuitive desktop application designed to streamline the management of mobile application builds from Expo Application Services (EAS). It provides a centralized dashboard for DevOps engineers and developers to view, download, and manage Android and iOS builds, monitor the health of web services, and track build history, all from a single, cross-platform interface.

## Key Features

- **Unified Build Dashboard:** View and manage all your Android and iOS builds from EAS in a clean, side-by-side layout.
- **Real-time Service Health:** Monitor the health of your RosieVision and ProjectFlow services with real-time status indicators.
- **EAS Integration:** Fetch the latest builds for both Android and iOS platforms directly from the EAS API.
- **Dynamic Filtering:** Quickly find the builds you're looking for by filtering by version number.
- **Azure Blob Storage Integration:** Download build artifacts and push them directly to your configured Azure Blob Storage container, with in-place progress bars to track the status.
- **Custom File Naming:** All downloaded and uploaded artifacts are named with a clear and consistent convention: `{platform}-{profile}-v{version}-{versionCode}-{fingerprint}.{extension}`.
- **Local Build History:** Keep a persistent, local record of all actions performed within the application, including downloads and uploads.
- **Secure Configuration:** All sensitive credentials and configurations are managed through a simple `.env` file, keeping your secrets out of the codebase.
- **Cross-Platform:** Built with PySide6, QuantumOps runs natively on Windows, macOS, and Linux.

## Getting Started

### Prerequisites

- Python 3.11 or higher
- An Azure account with a configured Storage Blob container
- An Expo account with access to EAS builds

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/quantumops.git
    cd quantumops
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### Configuration

Before running the application, you'll need to configure your environment variables by creating a `.env` file in the root of the project.

1.  **Create the `.env` file:**
    ```bash
    touch .env
    ```

2.  **Add your credentials to the `.env` file:**

    ```dotenv
    # Azure Storage Credentials
    AZURE_STORAGE_ACCOUNT="your_storage_account_name"
    AZURE_STORAGE_CONTAINER="your_container_name"
    AZURE_STORAGE_ACCOUNT_KEY="your_storage_account_key"

    # EAS Credentials
    EAS_ACCOUNT_NAME="your_expo_account_name"
    EAS_PROJECT_ID="your_expo_project_id"
    ```

3.  **Configure the health check endpoints:**

    Open `config/health_endpoints.json` and add the health check URLs for your RosieVision and ProjectFlow services:

    ```json
    {
      "endpoints": {
        "RV-Dev-api": "https://your-rosievision-api.com/health",
        "PF-Dev-api": "https://your-projectflow-api.com/health"
      }
    }
    ```

### Running the Application

Once your configuration is complete, you can launch the application by running:

```bash
python main.py
```

## Development

For information on contributing to the project, running tests, and understanding the project structure, please see the [DevOps Guide](DEVOPS_GUIDE.md).

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
