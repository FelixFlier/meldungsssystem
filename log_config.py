import logging
from logging.handlers import RotatingFileHandler
import sys
import os
from config import get_settings

settings = get_settings()

def setup_logging():
    """
    Konfiguriert das Logging-System für die Anwendung.
    
    Setzt einen Logger auf, der sowohl in die Konsole als auch in eine Datei schreibt
    (falls LOG_FILE in den Einstellungen gesetzt ist).
    """
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    # Root-Logger konfigurieren
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # Logger für die Anwendung
    app_logger = logging.getLogger(settings.APP_NAME)
    app_logger.setLevel(log_level)
    
    # Formatter für die Logs
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console-Handler hinzufügen
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(log_level)
    logger.addHandler(console_handler)
    
    # Datei-Handler hinzufügen, falls konfiguriert
    if settings.LOG_FILE:
        # Stelle sicher, dass das Log-Verzeichnis existiert
        log_dir = os.path.dirname(settings.LOG_FILE)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Rotating-File-Handler, um Log-Dateien zu rotieren
        file_handler = RotatingFileHandler(
            settings.LOG_FILE,
            maxBytes=10485760,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        logger.addHandler(file_handler)
    
    # SQLAlchemy und Alembic Logger einstellen
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    
    # FastAPI und Uvicorn Logger einstellen
    logging.getLogger('fastapi').setLevel(log_level)
    logging.getLogger('uvicorn').setLevel(log_level)
    
    # Warnung, wenn im Debug-Modus
    if settings.DEBUG:
        app_logger.warning("Anwendung läuft im DEBUG-Modus!")
    
    return logger