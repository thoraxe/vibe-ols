"""
Logging configuration for the Vibe OLS application.
Sets up comprehensive logging with file and console output.
"""

import logging
import sys
from .config import settings

def setup_logging():
    """Configure application logging."""
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Create logger
    logger = logging.getLogger(__name__)
    
    # Set specific log levels for different components
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.DEBUG)
    
    # Enable debug logging if environment variable is set
    if settings.DEBUG_MODE:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name) 