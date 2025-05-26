# QuantumOps

QuantumOps is a cross-platform desktop DevOps tool built with PySide6, designed for error log browsing, mobile build management, and seamless Azure integration. The application provides a robust, branded, and user-friendly interface for managing PostgreSQL error logs, monitoring Android/iOS builds via EAS CLI, and pushing artifacts to Azure Blob Storage.

## Key Features
- **Tabbed Interface**: Error Browser, Android Builds, iOS Builds (via `QTabWidget`)
- **Error Browser**: Browse/query PostgreSQL error logs, manage connections (add/edit/delete, persisted via QSettings), styled auto-resizing table
- **Mobile Build Management**: EAS CLI integration for Android/iOS builds, build metadata, download links, error messages, Azure Blob Storage upload with SAS token
- **Always-Visible Log Area**: Persistent, resizable, color-coded log/terminal area, menu option to toggle visibility
- **Theming & Branding**: Light/dark themes and multiple branding themes (Quantum Blue, Vivid Purple, Electric Green, Cyber Pink) using pyqtdarktheme, runtime switching, full UI refresh
- **SAS Token Management**: Expiration label color-coded (green/yellow/red), update via menu, persisted in QSettings
- **Robust Error Handling**: All error dialogs use `setText` for main message and `setInformativeText` for technical details; handles missing files, JSON parsing errors, CLI failures
- **UI Consistency**: Android/iOS tabs have identical layouts; main window auto-resizes to fit table content; JSON viewer removed for simplicity

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
1. Clone the repository and set up a Python 3.11 virtual environment.
2. Install dependencies from `requirements.txt`.
3. For EAS CLI features, ensure Node.js and EAS CLI are installed (`yarn install`).
4. Run the app with `python main.py` or use the provided executables from CI artifacts.

## Development
- **Running Tests**: Uses pytest for unit, integration, and build process tests. Run with `pytest`.
- **Building Executables Locally**: Run `python build.py` to create platform-specific executables in the `dist` directory.

## CI/CD Pipeline
- Runs the test suite
- Builds executables for Windows, macOS, and Linux
- Uploads build artifacts for each OS
- Fails if any tests or build steps fail

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run the test suite
5. Submit a pull request

All pull requests must pass the CI/CD pipeline before being merged.

## Best Practices & Guidance
- Follows Pythonic, modular, and scalable code practices (PEP 8, DRY, KISS)
- DevOps automation is cross-platform, reproducible, and secure
- UI/UX is consistent, accessible, and brandable
- All major features, workflows, and technical decisions are documented and automated for maintainability and scalability

## Credits
- QuantumOps team, all major libraries, and OpenAI GPT-4 for technical design and code generation

## License
MIT

---
For more details, see the workflow/spec files. For troubleshooting PyInstaller or Qt plugin issues, refer to the official documentation and community discussions.