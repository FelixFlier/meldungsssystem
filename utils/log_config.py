"""
Logging configuration for the application.
"""

import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from config import get_settings

settings = get_settings()

def setup_logging():
    """
    Configures the logging system for the application.
    
    Sets up a logger that writes to both console and a file
    (if LOG_FILE is set in settings).
    """
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    # Configure root logger
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Logger for the application
    app_logger = logging.getLogger(settings.APP_NAME)
    app_logger.setLevel(log_level)
    
    # Formatter for logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # Add file handler if configured
    if settings.LOG_FILE:
        # Ensure log directory exists
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Rotating file handler to rotate log files
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10485760,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # Set log levels for external libraries
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(log_level)
    logging.getLogger('uvicorn').setLevel(log_level)
    
    # Warning if in debug mode
    if settings.DEBUG:
        app_logger.warning("Anwendung läuft im DEBUG-Modus!")
    
    return logger