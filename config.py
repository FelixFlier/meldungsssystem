from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import secrets
from functools import lru_cache


class Settings(BaseSettings):
    """Anwendungskonfiguration, die aus Umgebungsvariablen geladen wird."""
    
    # Basiseinstellungen
    APP_NAME: str = "Meldungssystem"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Pfad zum Basis-Verzeichnis
    BASE_DIR: Path = Path(__file__).resolve().parent
    
    # Datenbankeinstellungen
    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'users.db'}"
    
    # Sicherheitseinstellungen
    SECRET_KEY: str = secrets.token_hex(32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS Einstellungen
    CORS_ORIGINS: list = ["*"]
    
    # Selenium Einstellungen
    SELENIUM_HEADLESS: bool = True
    
    # Log-Einstellungen
    LOG_LEVEL: str = "INFO"
    LOG_FILE: Optional[str] = "app.log"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Gibt die Anwendungseinstellungen zurück (cached)."""
    return Settings()