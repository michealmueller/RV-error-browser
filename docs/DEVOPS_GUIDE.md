# QuantumOps - DevOps Guide

This guide provides detailed information for developers and DevOps engineers working on the QuantumOps project. It covers the project structure, development environment, testing procedures, and CI/CD pipeline.

## Project Structure

The QuantumOps repository is organized into the following directories:

```
quantumops/
├── config/                 # User-facing configuration files
│   ├── eas.json            # Configuration for the EAS service
│   └── health_endpoints.json # Health check URLs for monitored services
├── docs/                   # Project documentation
├── quantumops/             # Main application source code
│   ├── controllers/      # Application logic and event handling
│   ├── models/           # Data models and business logic
│   ├── services/         # Clients for interacting with external APIs (EAS, Azure)
│   ├── ui_components/    # Reusable UI components
│   └── views/            # Main application views and dialogs
├── scripts/                # Utility and build scripts
├── tests/                  # Unit and integration tests
│   ├── config/             # Test configuration and runners
│   ├── data/               # Test data, including logs and uploads
│   ├── integration/        # Integration tests for services and controllers
│   └── unit/               # Unit tests for individual components
├── .github/                # GitHub Actions workflows
│   └── workflows/
│       ├── build.yml       # CI workflow for building the application
│       └── test.yml        # CI workflow for running tests and checking coverage
├── .env                    # Local environment variables (not version controlled)
├── requirements.txt        # Production dependencies
└── requirements-dev.txt    # Development and testing dependencies
```

## Development Environment

To set up a local development environment, follow these steps:

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

3.  **Install all dependencies:**
    ```bash
    pip install -r requirements.txt -r requirements-dev.txt
    ```

4.  **Configure your local environment:**

    Create a `.env` file in the project root and add the necessary credentials for Azure and EAS, as described in the main [README.md](README.md).

## Testing

The project includes a comprehensive suite of unit and integration tests to ensure code quality and stability.

### Running Tests

-   **Run all tests:**
    ```bash
    pytest
    ```

-   **Run tests with coverage:**
    ```bash
    pytest --cov=quantumops
    ```

### Test Structure

-   **Unit Tests (`tests/unit`):** These tests focus on individual components in isolation, such as UI widgets, data models, and utility functions.
-   **Integration Tests (`tests/integration`):** These tests verify the interactions between different components, such as the controllers and services.

## CI/CD Pipeline

The project uses GitHub Actions for continuous integration and continuous delivery. The workflows are defined in the `.github/workflows` directory.

-   **`test.yml`:** This workflow is triggered on every push to the `main` branch and on all pull requests. It installs the dependencies, runs the full test suite, and checks for test coverage.
-   **`build.yml`:** This workflow is also triggered on every push to the `main` branch. It builds the application for Windows, macOS, and Linux, and uploads the resulting artifacts to be used for releases.

## Code Style and Linting

The project uses `black` for code formatting and `flake8` for linting. These tools are enforced through a pre-commit hook, which can be set up by running:

```bash
pre-commit install
```

This will ensure that all code is automatically formatted and linted before it is committed, maintaining a consistent code style across the project.

## DevOps Best Practices
- **Infrastructure-as-Code:** All environments and web apps are config-driven (see `config/`)
- **Least Privilege:** Azure credentials use Service Principal with minimal required permissions
- **CI/CD:** Use GitHub Actions (see `.github/workflows/build.yml`) for build, test, and packaging
- **Testing:** Unit and integration tests in `tests/` directory; use `pytest`
- **Linting & Formatting:** Enforced via pre-commit hooks (`.pre-commit-config.yaml`)
- **Secrets Management:** Use environment variables for all secrets; never commit secrets to source

## PySide6 Signal/Slot Conventions
- All UI-to-controller communication uses Qt signals (never direct method calls)
- Signals are defined as `Signal(...)` in PySide6 classes
- Connect signals in controllers, not in the UI layer
- Example:
  ```python
  class MainWindow(QMainWindow):
      refresh_requested = Signal()
      ...
      self.refresh_button.clicked.connect(self.refresh_requested.emit)
  ```

## Azure Integration Patterns
- **Blob Storage:** Upload/download builds using Azure SDK, authenticated via Service Principal
- **Web App Logs:** Log streaming via Azure Web App API, selected via config-driven dropdown
- **Resource Selection:** All Azure resources (web apps, storage) are selected/configured via JSON config

## Security
- Never hard-code secrets; always use environment variables or config files
- Use Azure RBAC and managed identities where possible

---
For more, see the project overview and config reference. 