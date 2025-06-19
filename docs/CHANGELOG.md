# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0-beta] - 2025-06-19

### Added
- **Health Check System** with persistent configuration
- **Azure Integration** with mock mode fallback
- **Platform Management** for Android/iOS build operations
- **Configuration Persistence** - Health endpoints saved to JSON files
- **Modern UI** with light theme and Bootstrap-inspired styling
- **Auto-fitting table rows** for better button visibility
- **Expanded log area** with full vertical space utilization
- **Error handling** with user-friendly error messages
- **Environment variable loading** from .env files
- **Health settings dialog** with add/edit/delete functionality

### Changed
- **UI Theme**: Switched from dark to light theme with modern styling
- **Health Endpoints**: Updated to use real RosieVision and ProjectFlow URLs
- **Azure Service**: Enhanced with graceful fallback to mock mode
- **Platform Dropdown**: Improved functionality for Android/iOS build management
- **Log Area**: Removed height constraints for better visibility
- **Table Layout**: Auto-resizing rows for optimal button display

### Fixed
- **Health Settings Persistence**: Endpoints now save and reload properly
- **Delete Endpoint Error**: Fixed NoneType error in health settings dialog
- **Azure Authentication**: Proper handling of missing credentials
- **UI Layout Issues**: Fixed button sizing and table row heights
- **Log Function Calls**: Corrected parameter count in _append_log calls

### Removed
- **Non-existent Web Endpoints**: Removed PF-Dev-web and PF-Staging-web
- **Hard-coded Health URLs**: Replaced with configurable endpoints
- **Height Constraints**: Removed maximum height from log area

## [Unreleased]

### Added
- MVC architecture implementation
- New directory structure for better code organization
- Log streaming model with buffering
- Log controller for coordinating model and view
- Improved error handling and logging

### Changed
- Restructured codebase to follow MVC pattern
- Separated business logic from UI code
- Enhanced error handling and status updates
- Improved UI feedback mechanisms

### Removed
- Old monolithic code structure
- Direct coupling between UI and business logic

## [0.1.0] - 2024-03-21

### Added
- Initial release
- Basic Azure WebApp log streaming functionality
- Web app selection dropdown
- Log source and system log viewers
- Dark theme UI 