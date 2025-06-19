"""
Health check model for QuantumOps.
"""
import logging
from typing import Dict, Optional
import requests
from PySide6.QtCore import QObject, Signal, QTimer
from datetime import datetime

logger = logging.getLogger(__name__)

class HealthCheckModel(QObject):
    """Model for handling health check operations."""
    
    status_updated = Signal(str, bool)  # webapp_name, is_healthy
    error_occurred = Signal(str)  # error message
    
    def __init__(self):
        super().__init__()
        self.webapps = {
            "RV-Dev-api": "https://rv-dev-api.azurewebsites.net/health",
            "RV-Staging-api": "https://rv-staging-api.azurewebsites.net/health",
            "PF-Dev-web": "https://pf-dev-web.azurewebsites.net/health",
            "PF-Dev-api": "https://pf-dev-api.azurewebsites.net/health",
            "PF-Staging-web": "https://pf-staging-web.azurewebsites.net/health",
            "PF-Staging-api": "https://pf-staging-api.azurewebsites.net/health"
        }
        self.health_status: Dict[str, bool] = {}
        self.last_check: Dict[str, datetime] = {}
        self._timer = QTimer()
        self._timer.timeout.connect(self.check_all_health)
        self._interval = 30000  # Default 30 seconds
        
    def start_monitoring(self) -> None:
        """Start health check monitoring."""
        self._timer.start(self._interval)
        self.check_all_health()  # Initial check
        
    def stop_monitoring(self) -> None:
        """Stop health check monitoring."""
        self._timer.stop()
        
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
        """Check health status for a specific web app."""
        try:
            response = requests.get(url, timeout=5)
            is_healthy = response.status_code == 200
            self.health_status[webapp] = is_healthy
            self.last_check[webapp] = datetime.now()
            self.status_updated.emit(webapp, is_healthy)
            logger.info(f"Health check for {webapp}: {'Healthy' if is_healthy else 'Unhealthy'}")
        except Exception as e:
            self.health_status[webapp] = False
            self.last_check[webapp] = datetime.now()
            self.status_updated.emit(webapp, False)
            self.error_occurred.emit(f"Error checking {webapp}: {str(e)}")
            logger.error(f"Health check error for {webapp}: {str(e)}")
            
    def get_health_status(self, webapp: str) -> Optional[bool]:
        """Get the health status for a specific web app."""
        return self.health_status.get(webapp)
        
    def get_last_check(self, webapp: str) -> Optional[datetime]:
        """Get the last check time for a specific web app."""
        return self.last_check.get(webapp) 