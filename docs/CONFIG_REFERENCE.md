# Configuration Reference

This document describes the configuration files used by QuantumOps and their structure.

## `config/eas.json`
- **Purpose:** Stores build and environment settings for different deployment stages (development, staging, production).
- **Structure:**
  - `cli`: CLI version and app version source
  - `build`: Per-environment build settings and environment variables
  - `submit`: iOS App Store Connect app ID
- **Usage:** Used to configure build environments and secrets for mobile builds.

## `config/webapps.json`
- **Purpose:** Lists Azure Web Apps and their resource groups for log streaming and deployment.
- **Structure:**
  ```json
  [
    { "name": "my-webapp-1", "resource_group": "my-resource-group-1" },
    { "name": "my-webapp-2", "resource_group": "my-resource-group-2" }
  ]
  ```
- **Usage:** The UI presents a dropdown for selecting the active web app; the selected value is used for log streaming and Azure operations.

## Environment Variables
- **Purpose:** Store secrets and sensitive configuration (e.g., Azure credentials).
- **Usage:**
  - `AZURE_TENANT_ID`, `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` for Service Principal authentication
  - Other secrets as required by your build or deployment process

## Adding New Configurations
- Place new config files in the `config/` directory
- Document their structure and usage in this file

---
For more details, see the project overview and DevOps guide. 