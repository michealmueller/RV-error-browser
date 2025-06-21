import logging
import sys


def setup_logging():
    """Set up the root logger for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler("quantumops.log"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    logging.info("Logging configured.")
