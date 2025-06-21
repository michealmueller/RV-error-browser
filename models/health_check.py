"""
Health check model for QuantumOps.
"""
import logging
import json
from pathlib import Path
from typing import Dict, Optional
import requests
from PySide6.QtCore import QObject, Signal, QTimer, QThread, Qt
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheckWorker(QThread):
    """Worker thread for health checks."""
    
    check_complete = Signal(str, bool)  # webapp_name, is_healthy
    error_occurred = Signal(str)  # error message
    
    def __init__(self, webapp: str, url: str):
        super().__init__()
        self.webapp = webapp
        self.url = url
        
    def run(self):
        """Run the health check."""
        try:
            response = requests.get(self.url, timeout=5)
            is_healthy = response.status_code == 200
            self.check_complete.emit(self.webapp, is_healthy)
        except Exception as e:
            self.error_occurred.emit(f"Error checking {self.webapp}: {str(e)}")
            self.check_complete.emit(self.webapp, False)

class HealthCheckModel(QObject):
    """Model for handling health check operations."""
    
    status_updated = Signal(str, bool)  # webapp_name, is_healthy
    error_occurred = Signal(str)  # error message
    
    def __init__(self, webapps: list):
        super().__init__()
        self.config_file = Path("config/health_endpoints.json")
        
        # Always load the default/fallback endpoints first
        self.webapps = self._load_endpoints()
        
        # Then, update or merge with any webapps passed from the main config
        if webapps:
            for app in webapps:
                if hasattr(app, 'name') and hasattr(app, 'health_check_url') and app.health_check_url:
                    self.webapps[app.name] = app.health_check_url

        self.health_status: Dict[str, bool] = {}
        self.last_check: Dict[str, datetime] = {}
        self._timer = QTimer()
        self._timer.timeout.connect(self.check_all_health)
        self._interval = 30000  # Default 30 seconds
        self._workers: Dict[str, HealthCheckWorker] = {}
        
    def _load_endpoints(self) -> Dict[str, str]:
        """Load health check endpoints from configuration file."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    data = json.load(f)
                    return data.get("endpoints", {})
            else:
                # Default endpoints if config file doesn't exist
                logger.info("Health endpoints config file not found, using and saving default endpoints.")
                default_endpoints = {
                    "RV-Dev-api": "https://rv-dev-api.azurewebsites.net/health",
                    "RV-Staging-api": "https://rv-staging-api.azurewebsites.net/health",
                    "PF-Dev-web": "https://pf-dev-web.azurewebsites.net/health",
                    "PF-Dev-api": "https://pf-dev-api.azurewebsites.net/health",
                    "PF-Staging-web": "https://pf-staging-web.azurewebsites.net/health",
                    "PF-Staging-api": "https://pf-staging-api.azurewebsites.net/health"
                }
                self._save_endpoints(default_endpoints)
                return default_endpoints
        except Exception as e:
            logger.error(f"Failed to load health endpoints: {e}")
            return {}
            
    def _save_endpoints(self, endpoints: Dict[str, str]) -> None:
        """Save health check endpoints to configuration file."""
        try:
            # Ensure config directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {"endpoints": endpoints}
            with open(self.config_file, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Health endpoints saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save health endpoints: {e}")
            
    def start_monitoring(self) -> None:
        """Start health check monitoring."""
        self._timer.start(self._interval)
        # Delay initial check by 1 second to not block startup
        QTimer.singleShot(1000, self.check_all_health)
        
    def stop_monitoring(self) -> None:
        """Stop health check monitoring."""
        self._timer.stop()
        # Stop any running workers
        for worker in self._workers.values():
            if worker.isRunning():
                worker.quit()
                worker.wait()
        self._workers.clear()
        
    def set_interval(self, interval_ms: int) -> None:
        """Set the health check interval in milliseconds."""
        self._interval = interval_ms
        if self._timer.isActive():
            self._timer.setInterval(interval_ms)
            
    def check_all_health(self) -> None:
        """Check health status for all web apps."""
        for webapp, url in self.webapps.items():
            self.check_health(webapp, url)
            
    def check_health(self, webapp: str, url: str) -> None:
        """Check health status for a specific web app asynchronously."""
        # Clean up previous worker if it exists
        if webapp in self._workers:
            old_worker = self._workers[webapp]
            if old_worker.isRunning():
                old_worker.quit()
                old_worker.wait()
            old_worker.deleteLater()
            
        # Create new worker
        worker = HealthCheckWorker(webapp, url)
        worker.check_complete.connect(self._handle_check_complete)
        worker.error_occurred.connect(self.error_occurred)
        self._workers[webapp] = worker
        worker.start()
        
    def _handle_check_complete(self, webapp: str, is_healthy: bool) -> None:
        """Handle completion of a health check."""
        self.health_status[webapp] = is_healthy
        self.last_check[webapp] = datetime.now()
        self.status_updated.emit(webapp, is_healthy)
        logger.info(f"Health check for {webapp}: {'Healthy' if is_healthy else 'Unhealthy'}")
            
    def get_health_status(self, webapp: str) -> Optional[bool]:
        """Get the health status for a specific web app."""
        return self.health_status.get(webapp)
        
    def get_last_check(self, webapp: str) -> Optional[datetime]:
        """Get the last check time for a specific web app."""
        return self.last_check.get(webapp) 