# DevOps & Engineering Guide

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