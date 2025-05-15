# init_db.py
import os
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from pathlib import Path

# Importiere die Modelle und CRUD-Funktionen
from models import Base, Location  # Korrigiert: Location-Modell importieren
from models import UserLocation
import crud
from schemas import LocationCreate

# Bestimme den Pfad zur Datenbank
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "users.db"

# Erstelle Engine
engine = create_engine(f"sqlite:///{DB_PATH}")

# Erstelle alle Tabellen
Base.metadata.create_all(engine)

print(f"Datenbank wurde initialisiert: {DB_PATH}")
print("Alle Tabellen wurden erstellt.")

# Importiere Standortdaten aus Excel, falls vorhanden
excel_path = BASE_DIR / "data" / "polizei_standorte.xlsx"
if excel_path.exists():
    # Erstelle Session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Prüfe, ob bereits Standorte existieren
        existing_count = db.query(Location).count()  # Korrigiert: Location-Modell verwenden
        if existing_count == 0:
            # Lade Excel-Daten
            df = pd.read_excel(excel_path)
            locations_data = df.fillna('').to_dict('records')
            
            # Importiere Standorte
            count = crud.import_locations_from_excel(db, locations_data)
            print(f"{count} Standorte aus Excel importiert")
        else:
            print(f"{existing_count} Standorte bereits vorhanden, kein Import nötig")
    except Exception as e:
        print(f"Fehler beim Importieren der Standorte: {e}")
    finally:
        db.close()
else:
    print(f"Excel-Datei nicht gefunden: {excel_path}")
    print("Erstelle einige Beispiel-Standorte...")
    
    # Erstelle Session
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        count = crud.import_locations_from_excel(db)
        print(f"{count} Beispiel-Standorte erstellt")
    except Exception as e:
        print(f"Fehler beim Erstellen der Beispiel-Standorte: {e}")
    finally:
        db.close()