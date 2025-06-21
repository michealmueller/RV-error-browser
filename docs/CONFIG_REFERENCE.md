# Configuration Reference

This document describes the configuration files used by QuantumOps and their structure.

## `config/health_endpoints.json`
- **Purpose:** Stores health check endpoints for monitoring system health across different services.
- **Structure:**
  ```json
  {
    "endpoints": {
      "RV-Dev-api": "https://moapidev.rosievision.ai/health",
      "RV-Staging-api": "https://moapistage.rosievision.ai/health",
      "PF-Dev-api": "https://devapi.projectflow.ai/health",
      "PF-Staging-api": "https://stageapi.projectflow.ai/health"
    }
  }
  ```
- **Usage:** Health check system monitors these endpoints and displays status in the UI. Endpoints can be added, edited, or removed through the Health Check Settings dialog.

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

## Environment Variables (.env file)
- **Purpose:** Store secrets and sensitive configuration for Azure integration and authentication.
- **Required Variables:**
  ```bash
  # Azure Storage Configuration
  AZURE_STORAGE_ACCOUNT=your-storage-account-name
  AZURE_STORAGE_CONTAINER=mobile-builds
  AZURE_STORAGE_ACCOUNT_KEY=your-storage-account-key

  # Azure Service Principal Authentication
  AZURE_CLIENT_ID=your-client-id
  AZURE_TENANT_ID=your-tenant-id
  AZURE_CLIENT_SECRET=your-client-secret
  AZURE_SUBSCRIPTION_ID=your-subscription-id
  ```
- **Usage:**
  - Azure Storage operations for build upload/download
  - Service Principal authentication for Azure services
  - Health check monitoring and build management

## Configuration Persistence
- **Health Endpoints**: Automatically saved when modified through the UI
- **Environment Variables**: Loaded from `.env` file on application startup
- **Build Settings**: Persisted in Azure Storage and local configuration

## Adding New Configurations
- Place new config files in the `config/` directory
- Document their structure and usage in this file
- Update the application to load and save new configurations as needed

---
For more details, see the project overview and DevOps guide.
