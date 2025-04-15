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
    
    # Logger für die Agenten explizit konfigurieren
    agent_logger = logging.getLogger(f"{settings.APP_NAME}.agent")
    agent_logger.setLevel(logging.DEBUG if settings.DEBUG else getattr(logging, settings.AGENT_LOG_LEVEL))
    
    # Formatter für die Logs - detailliertere Informationen
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Alle bestehenden Handler entfernen
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
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
        
        # Zusätzlicher Debug-Log für Entwicklungszwecke
        if settings.DEBUG:
            debug_log_file = os.path.join(log_dir, "debug.log")
            debug_handler = RotatingFileHandler(
                debug_log_file,
                maxBytes=20971520,  # 20 MB
                backupCount=3,
                encoding='utf-8'
            )
            debug_handler.setFormatter(formatter)
            debug_handler.setLevel(logging.DEBUG)
            logger.addHandler(debug_handler)
    
    # Spezifische Log-Level für externe Bibliotheken
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('alembic').setLevel(logging.WARNING)
    logging.getLogger('fastapi').setLevel(log_level)
    logging.getLogger('uvicorn').setLevel(log_level)
    logging.getLogger('selenium').setLevel(logging.INFO if settings.DEBUG else logging.WARNING)
    
    # Warnung, wenn im Debug-Modus
    if settings.DEBUG:
        app_logger.warning("Anwendung läuft im DEBUG-Modus!")
    
    return logger