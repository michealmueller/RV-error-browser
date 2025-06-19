# DevOps & Engineering Guide

## DevOps Best Practices
- **Infrastructure-as-Code:** All environments and web apps are config-driven (see `config/`)
- **Least Privilege:** Azure credentials use Service Principal with minimal required permissions
- **CI/CD:** Use GitHub Actions (see `.github/workflows/build.yml`) for build, test, and packaging
- **Testing:** Unit and integration tests in `tests/` directory; use `pytest`
- **Linting & Formatting:** Enforced via pre-commit hooks (`.pre-commit-config.yaml`)
- **Secrets Management:** Use environment variables for all secrets; never commit secrets to source
- **Health Monitoring:** Real-time health checks for development and staging environments
- **Configuration Persistence:** Settings automatically saved and reloaded across sessions

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
- **Mock Mode Fallback:** Graceful handling of missing credentials with mock operations
- **Environment Variables:** Automatic loading from `.env` files for configuration

## Health Monitoring System
- **Configuration:** Health endpoints stored in `config/health_endpoints.json`
- **Real-time Monitoring:** Continuous health checks with configurable intervals
- **UI Integration:** Health status displayed in main window with visual indicators
- **Persistence:** Endpoints automatically saved when modified through settings dialog
- **Error Handling:** Graceful handling of network issues and service unavailability

## Platform Management
- **Android/iOS Support:** Platform-specific build operations and device management
- **Context Switching:** Platform dropdown controls build context and operations
- **Device Integration:** Direct install capabilities for both platforms
- **Build Operations:** Platform-aware upload, download, and installation workflows

## Configuration Management
- **Environment Variables:** Loaded from `.env` file on application startup
- **JSON Configuration:** All settings stored in human-readable JSON format
- **Auto-save:** Configuration changes automatically persisted
- **Validation:** Configuration validation with user-friendly error messages

## Security
- Never hard-code secrets; always use environment variables or config files
- Use Azure RBAC and managed identities where possible
- Graceful fallback to mock mode when credentials are unavailable
- Secure handling of sensitive configuration data

## Error Handling Patterns
- **Graceful Degradation:** Application continues to function with reduced capabilities
- **User Feedback:** Clear error messages and status indicators
- **Logging:** Comprehensive logging for debugging and monitoring
- **Mock Operations:** Fallback operations when external services are unavailable

---
For more, see the project overview and config reference. 