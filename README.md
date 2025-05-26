# QuantumOps

QuantumOps is a cross-platform desktop DevOps tool built with PySide6, designed for error log browsing, mobile build management, and seamless Azure integration. The application provides a robust, branded, and user-friendly interface for managing PostgreSQL error logs, monitoring Android/iOS builds via EAS CLI, and pushing artifacts to Azure Blob Storage.

## Key Features
- **Tabbed Interface**: Error Browser, Android Builds, iOS Builds (via `QTabWidget`).
- **PostgreSQL Error Browser**: Add/edit/delete DB connections, browse logs, and query tables with styled results.
- **Mobile Build Management**: Fetch Android/iOS builds using EAS CLI, view build metadata, download links, and errors.
- **Azure Blob Storage Integration**: Push builds to Azure with SAS token authentication, upload status, and error handling.
- **Always-Visible Log Area**: Color-coded, resizable log/terminal area with toggle option.
- **Theming & Branding**: Light/dark themes and multiple branding themes (Quantum Blue, Vivid Purple, Electric Green, Cyber Pink) with runtime switching.
- **SAS Token Management**: Expiration indicator, update via menu, and secure storage in environment variables.
- **Menu Bar**: File, View, Theme, Settings, and Help menus with toggles, theming, and SAS token update actions.
- **Real-Time Log Viewer Tab**: View application logs live within the app.
- **Platform-Specific Azure Uploads**: Builds are uploaded to `android-builds/` or `ios-builds/` subfolders in Azure Blob Storage.
- **Secure Secrets Management**: All sensitive info (SAS token, storage keys) loaded from `.env` and excluded from version control.
- **Modular Codebase**: Core logic split into modules for database, builds, theming, settings, and logging for maintainability.
- **Enhanced Error Browser UI**: Password field removed, table field promoted, and Add/Edit/Delete buttons styled for accessibility and clarity.
- **Accessibility & Usability**: Improved button colors, hover/active states, tooltips, and layout for a modern, accessible experience.

## Recent Improvements
- Modularized all major logic into separate modules for easier maintenance and testing.
- Added a real-time log viewer tab for in-app log monitoring.
- Azure uploads now use platform-specific subfolders for better organization.
- All secrets and tokens are now managed via environment variables and `.env`.
- Menu bar restored and improved with toggles for log area, auto-resize, theming, and SAS token update.
- Error browser tab UI improved: password field removed, table field promoted, and buttons restyled for better accessibility.
- General accessibility and usability improvements throughout the UI.

## DevOps & Automation
- **Cross-Platform Build Automation**: GitHub Actions workflow builds QuantumOps on Windows, macOS, and Linux using a matrix strategy
  - Sets up Python 3.11, caches pip dependencies
  - Installs dependencies from `requirements.txt` and PyInstaller
  - Prints PyInstaller version and custom `quantumops.spec` for traceability
  - Builds a one-file, windowed executable with PyInstaller, including all necessary hidden imports and data files
  - Uploads resulting artifacts for each OS
- **Reproducible Builds**: Requirements and dependencies are pinned for compatibility and reproducibility
- **Spec File**: Custom `quantumops.spec` ensures all resources and hidden imports are included for cross-platform compatibility

## Tech Stack
- **Languages & Frameworks**: Python 3.11, PySide6, pyqtdarktheme
- **DevOps & Cloud**: GitHub Actions, PyInstaller, Azure SDK, Azure Blob Storage
- **Build Management**: EAS CLI (via Node.js, see `package.json`)
- **Database**: PostgreSQL (via psycopg2)
- **Other**: QSettings, requests, Cursor (development environment)

## Getting Started
1. Clone the repository and install dependencies from `requirements.txt`.
2. Create a `.env` file with your Azure credentials and SAS token.
3. Run the app with `python main.py`.

## Development
- Modular Python codebase (see `quantumops/` package).
- PySide6 for UI, qdarktheme for theming, Azure SDK for storage, EAS CLI for build management.
- Automated builds via GitHub Actions for Windows, macOS, and Linux.

## CI/CD Pipeline
- Runs the test suite
- Builds executables for Windows, macOS, and Linux
- Uploads build artifacts for each OS
- Fails if any tests or build steps fail

## Contributing
Contributions are welcome! Please see the [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Best Practices & Guidance
- Follows Pythonic, modular, and scalable code practices (PEP 8, DRY, KISS)
- DevOps automation is cross-platform, reproducible, and secure
- UI/UX is consistent, accessible, and brandable
- All major features, workflows, and technical decisions are documented and automated for maintainability and scalability

## Credits
- QuantumOps Team
- Major libraries: PySide6, qdarktheme, Azure SDK, psycopg2, requests
- OpenAI GPT-4 for technical design/code generation

## License
MIT

---
For more details, see the full documentation and code comments.