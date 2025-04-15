from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import secrets
from functools import lru_cache
import os
import re

# Bereinige Umgebungsvariablen von Kommentaren
for key in os.environ:
    if isinstance(os.environ[key], str):
        # Entferne alles nach einem # und Leerzeichen
        os.environ[key] = re.sub(r'\s+#.*$', '', os.environ[key])

class Settings(BaseSettings):
    """Anwendungskonfiguration, die aus Umgebungsvariablen geladen wird."""
    
    # Basiseinstellungen
    APP_NAME: str = "Meldungssystem"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # URLs und Pfade
    BASE_URL: str = "http://localhost:8002"
    API_HOST: str = "localhost:8002"
    API_PREFIX: str = "/api"
    
    # Pfad zum Basis-Verzeichnis
    BASE_DIR: Path = Path(__file__).resolve().parent
    
    # Datenbankeinstellungen
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'users.db'}"
    
    # Sicherheitseinstellungen
    SECRET_KEY: str = os.environ.get("SECRET_KEY", "8d44bf7d5ae0f2b4f1a274b9c15c9fc28dde68f681ef97dd2c77c8a23b4e7a14")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Einstellungen
    CORS_ORIGINS: list = ["*"]
    
    # Selenium Einstellungen
    SELENIUM_HEADLESS: bool = False
    SELENIUM_TIMEOUT: int = 300
    
    # Log-Einstellungen
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "app.log"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_ROTATION: str = "1 day"
    LOG_RETENTION: str = "30 days"
    AGENT_LOG_LEVEL: str = "INFO"
    
    # Upload-Einstellungen
    UPLOAD_DIR: str = "./uploads"
    TEMP_DIR: str = "./temp"
    MAX_UPLOAD_SIZE: int = 10485760  # 10 MB
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Gibt die Anwendungseinstellungen zurück (cached)."""
    return Settings()