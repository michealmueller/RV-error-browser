"""
History manager for tracking build operations.
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class BuildHistoryEntry:
    """Represents a single build history entry."""
    build_id: str
    platform: str
    version: str
    operation: str  # download, upload, install, share
    status: str  # success, failed
    timestamp: str
    details: Dict[str, Any]
    error_message: Optional[str] = None

class HistoryManager:
    """Manages build operation history."""
    
    def __init__(self, history_file: Optional[str] = None):
        """Initialize history manager."""
        self.history_file = history_file or str(Path.home() / ".quantumops" / "history.json")
        self._ensure_history_file()
        self._load_history()
        
    def _ensure_history_file(self):
        """Ensure history file and directory exist."""
        history_path = Path(self.history_file)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        if not history_path.exists():
            history_path.write_text("[]")
            
    def _load_history(self):
        """Load history from file."""
        try:
            with open(self.history_file, "r") as f:
                self.history = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load history: {e}")
            self.history = []
            
    def _save_history(self):
        """Save history to file."""
        try:
            with open(self.history_file, "w") as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save history: {e}")
            
    def add_entry(self, entry: BuildHistoryEntry):
        """Add a new history entry."""
        self.history.append(asdict(entry))
        self._save_history()
        
    def get_build_history(self, build_id: str) -> List[Dict[str, Any]]:
        """Get history for a specific build."""
        return [
            entry for entry in self.history
            if entry["build_id"] == build_id
        ]
        
    def get_platform_history(self, platform: str) -> List[Dict[str, Any]]:
        """Get history for a specific platform."""
        return [
            entry for entry in self.history
            if entry["platform"] == platform
        ]
        
    def get_operation_history(self, operation: str) -> List[Dict[str, Any]]:
        """Get history for a specific operation type."""
        return [
            entry for entry in self.history
            if entry["operation"] == operation
        ]
        
    def get_recent_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent history entries."""
        return sorted(
            self.history,
            key=lambda x: x["timestamp"],
            reverse=True
        )[:limit]
        
    def clear_history(self):
        """Clear all history."""
        self.history = []
        self._save_history()
        
    def export_history(self, file_path: str, format: str = "json"):
        """Export history to file."""
        if format == "json":
            with open(file_path, "w") as f:
                json.dump(self.history, f, indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
            
    def record_download(self, build_id: str, platform: str, version: str, status: str, error: Optional[str] = None):
        """Record a download operation."""
        entry = BuildHistoryEntry(
            build_id=build_id,
            platform=platform,
            version=version,
            operation="download",
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details={},
            error_message=error
        )
        self.add_entry(entry)
        
    def record_upload(self, build_id: str, platform: str, version: str, status: str, blob_url: Optional[str] = None, error: Optional[str] = None):
        """Record an upload operation."""
        entry = BuildHistoryEntry(
            build_id=build_id,
            platform=platform,
            version=version,
            operation="upload",
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details={"blob_url": blob_url} if blob_url else {},
            error_message=error
        )
        self.add_entry(entry)
        
    def record_install(self, build_id: str, platform: str, version: str, status: str, device_id: Optional[str] = None, error: Optional[str] = None):
        """Record an installation operation."""
        entry = BuildHistoryEntry(
            build_id=build_id,
            platform=platform,
            version=version,
            operation="install",
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details={"device_id": device_id} if device_id else {},
            error_message=error
        )
        self.add_entry(entry)
        
    def record_share(self, build_id: str, platform: str, version: str, status: str, share_url: Optional[str] = None, error: Optional[str] = None):
        """Record a share operation."""
        entry = BuildHistoryEntry(
            build_id=build_id,
            platform=platform,
            version=version,
            operation="share",
            status=status,
            timestamp=datetime.utcnow().isoformat(),
            details={"share_url": share_url} if share_url else {},
            error_message=error
        )
        self.add_entry(entry) 