# utils/db_utils.py
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import get_settings

settings = get_settings()

@contextmanager
def get_sync_session():
    """Erzeugt eine synchrone Datenbanksitzung."""
    # Konvertieren Sie die URL zu einer synchronen URL, falls nötig
    sync_url = settings.DATABASE_URL
    if sync_url.startswith('sqlite+aiosqlite:'):
        sync_url = sync_url.replace('sqlite+aiosqlite:', 'sqlite:')
    
    # Erstellen Sie eine synchrone Engine und Session
    engine_sync = create_engine(sync_url, echo=settings.DEBUG)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)
    
    session = session_factory()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()