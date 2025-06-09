# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- MVC architecture implementation
- New directory structure for better code organization
- Log streaming model with buffering
- Log controller for coordinating model and view
- Improved error handling and logging
- Dark theme UI with modern styling
- Enhanced Azure service with comprehensive error handling
- New Azure service unit tests with proper mocking
- Improved file metadata handling in Azure service
- Memory management and resource cleanup system
- Configuration validation and fallback mechanisms
- Thread-safe resource tracking
- Comprehensive test coverage (80% minimum)

### Changed
- Restructured codebase to follow MVC pattern
- Separated business logic from UI code
- Enhanced error handling and status updates
- Improved UI feedback mechanisms
- Updated Azure service to use proper error handling and type hints
- Improved Azure service initialization and container management
- Enhanced file metadata handling to include size and last modified time
- Refactored UI-to-controller communication to use proper Qt signals
- Centralized error handling across all components
- Improved resource cleanup and memory management
- Enhanced configuration validation and error handling

### Removed
- Old monolithic code structure
- Direct coupling between UI and business logic
- Old Azure service implementation with limited error handling
- SAS token authentication in favor of Service Principal authentication
- Redundant error handling code
- Unnecessary exception catching

## [0.1.0] - 2024-03-21

### Added
- Initial release
- Basic Azure WebApp log streaming functionality
- Web app selection dropdown
- Log source and system log viewers
- Dark theme UI 