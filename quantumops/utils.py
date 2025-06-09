import logging
import threading
from functools import wraps
from typing import Callable, Any
from PySide6.QtCore import Signal

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_main_thread(func: Callable) -> Callable:
    """Decorator to ensure function runs on main thread. Expects self.main_thread_signal to exist."""
    @wraps(func)
    def wrapper(self, *args: Any, **kwargs: Any) -> Any:
        if threading.current_thread() is threading.main_thread():
            return func(self, *args, **kwargs)
        else:
            self.main_thread_signal.emit(lambda: func(self, *args, **kwargs))
    return wrapper

def log_azure_operation(operation: str) -> Callable:
    """Decorator to log Azure operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Starting Azure operation: {operation}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed Azure operation: {operation}")
                return result
            except Exception as e:
                logger.error(f"Failed Azure operation {operation}: {str(e)}")
                raise
        return wrapper
    return decorator

def log_database_operation(operation: str) -> Callable:
    """Decorator to log database operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger.info(f"Starting database operation: {operation}")
            try:
                result = func(*args, **kwargs)
                logger.info(f"Completed database operation: {operation}")
                return result
            except Exception as e:
                logger.error(f"Failed database operation {operation}: {str(e)}")
                raise
        return wrapper
    return decorator 