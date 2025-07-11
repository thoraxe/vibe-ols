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
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    # Control third-party library logging - only show in VERBOSE mode
    if settings.VERBOSE_MODE:
        # In VERBOSE mode, enable all debug logs including third-party libraries
        logging.getLogger().setLevel(logging.DEBUG)
        logger.info("🔍 Verbose mode enabled - all debug logs visible")
    elif settings.DEBUG_MODE:
        # In DEBUG mode, only enable debug logs for our application
        logging.getLogger().setLevel(logging.INFO)  # Keep root at INFO
        
        # Enable debug logging for our application modules
        logging.getLogger("app").setLevel(logging.DEBUG)
        logging.getLogger("__main__").setLevel(logging.DEBUG)
        
        # Suppress noisy third-party library logs
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("asyncio").setLevel(logging.WARNING)
        logging.getLogger("mcp").setLevel(logging.INFO)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("pydantic").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        
        logger.debug("🐛 Debug mode enabled - application debug logs visible")
    else:
        # Normal mode - INFO level for everything
        logging.getLogger().setLevel(logging.INFO)
        
        # Still suppress some noisy libraries even in normal mode
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logger

def get_logger(name: str = __name__) -> logging.Logger:
    """Get a logger instance for the given name."""
    return logging.getLogger(name) 