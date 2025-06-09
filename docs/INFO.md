# Project Info & AI Memory

This file is designed for AI models and future maintainers to quickly pick up where the last developer left off.

## Key Decisions
- **Config-Driven Design:** All environment, web app, and build settings are loaded from JSON config files for flexibility and reproducibility.
- **Signal/Slot UI Architecture:** All UI actions are connected to business logic via PySide6 signals/slots, not direct method calls.
- **Azure Integration:** Uses Service Principal authentication for all Azure operations; web app/resource group selection is user-configurable.
- **History Tracking:** All build/download/upload/install/share actions are tracked in a local history file for audit and troubleshooting.

## Architectural Notes
- **UI:** PySide6, modular dialogs, and main window
- **Controllers:** Orchestrate logic, connect UI to models, handle Azure API
- **Models:** Data, Azure SDK, and business logic
- **Config:** All in `config/` directory; see `docs/CONFIG_REFERENCE.md`
- **Testing:** `pytest` for all unit/integration tests
- **CI/CD:** GitHub Actions for build/test/package

## Context for AI
- If you are an AI model, read all files in `docs/` and `config/` for context before making changes.
- Always follow best practices for DevOps, security, and Python/PySide6 development.
- If unsure, ask for clarification or check the latest Azure/PySide6 documentation.

---
For more, see the other docs in this directory. 