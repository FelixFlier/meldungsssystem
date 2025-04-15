"""
Agent service for running background tasks to process incidents.
Improved version with better error handling and environment setup.
"""

import os
import sys
import json
import traceback
import logging
import subprocess
from datetime import timedelta, datetime
from pathlib import Path

import models
import security
from config import get_settings
import crud
# Cache explizit leeren
get_settings.cache_clear()  
# Einstellungen neu laden
settings = get_settings()

settings = get_settings()
logger = logging.getLogger(settings.APP_NAME)

# Ersetze die Methode run_agent_task in agent_service.py:

async def run_agent_task(incident_id: int, incident_type: str):
    """
    Führt den Agenten direkt im Background-Task aus, statt ihn als separaten Prozess zu starten.
    
    Args:
        incident_id: Die ID des Incidents
        incident_type: Der Typ des Incidents (diebstahl, sachbeschaedigung)
    
    Returns:
        bool: True bei Erfolg, False bei Fehler
    """
    try:
        logger.info(f"Starte Agent für Incident {incident_id} vom Typ {incident_type}")
        
        # Aktualisiere Incident-Status zu Beginn
        update_incident_status(incident_id, "processing", "Agent wird gestartet...")
        
        if incident_type == "diebstahl":
            # DIREKTE AUSFÜHRUNG statt subprocess
            from direct_agent import DirectAgent
            
            # Erstelle DirectAgent-Instanz 
            agent = DirectAgent(
                incident_id=incident_id,
                api_host="localhost:8002",  # Dieser Parameter wird jetzt ignoriert
                headless=False,  # Headless-Modus für Hintergrundausführung
                token=""  # Kein Token nötig, da wir direkte Funktionsaufrufe verwenden
            )
            
            # Override der API-Methoden mit direkten Calls zum CRUD
            # (dies ist ein Monkey-Patch der Agent-Klasse)
            def direct_update_status(self, status, message=None):
                """Direktes Update des Incident-Status ohne HTTP."""
                try:
                    logger.info(f"Direkte Aktualisierung des Status für Incident {self.incident_id} auf '{status}'")
                    
                    # Verwende die synchrone Funktion für Datenbankzugriff
                    from utils.db_utils import get_sync_session
                    from schemas import IncidentUpdate
                    
                    update_data = IncidentUpdate(status=status, agent_log=message)
                    
                    with get_sync_session() as db:
                        updated = crud.update_incident(db, incident_id=self.incident_id, incident_update=update_data) 
                        return bool(updated)
                        
                except Exception as e:
                    logger.error(f"Fehler beim direkten Update des Status: {str(e)}")
                    traceback.print_exc()
                    return False
                    
            def direct_load_incident(self):
                """Direktes Laden der Incident-Daten ohne HTTP."""
                try:
                    logger.info(f"Direktes Laden der Daten für Incident {self.incident_id}")
                    
                    # Verwende die synchrone Funktion für Datenbankzugriff
                    from utils.db_utils import get_sync_session
                    
                    with get_sync_session() as db:
                        incident = crud.get_incident(db, incident_id=self.incident_id)
                        if not incident:
                            logger.error(f"Incident {self.incident_id} nicht gefunden")
                            return {}
                            
                        # Standortname extrahieren, falls vorhanden
                        location_name = None
                        if hasattr(incident, 'location') and incident.location:
                            if isinstance(incident.location, models.Location):
                                location_name = incident.location.name
                            else:
                                location_name = incident.location
                        
                        # Response-Objekt erstellen
                        response_dict = {
                            "id": incident.id,
                            "type": incident.type,
                            "incident_date": incident.incident_date,
                            "incident_time": incident.incident_time,
                            "email_data": incident.email_data,
                            "location_id": incident.location_id,
                            "user_id": incident.user_id,
                            "status": incident.status,
                            "created_at": incident.created_at,
                            "location": location_name,
                            "agent_log": incident.agent_log if hasattr(incident, 'agent_log') else None
                        }
                        
                        return response_dict
                        
                except Exception as e:
                    logger.error(f"Fehler beim direkten Laden der Incident-Daten: {str(e)}")
                    traceback.print_exc()
                    return {}
                    
            def direct_load_user(self, user_id):
                """Direktes Laden der Benutzerdaten ohne HTTP."""
                try:
                    logger.info(f"Direktes Laden der Daten für Benutzer {user_id}")
                    
                    # Verwende die synchrone Funktion für Datenbankzugriff
                    from utils.db_utils import get_sync_session
                    
                    with get_sync_session() as db:
                        user = db.query(models.User).filter(models.User.id == user_id).first()
                        if not user:
                            logger.error(f"Benutzer {user_id} nicht gefunden")
                            return {}
                        
                        # Manuelles Mapping der Benutzerdaten
                        user_dict = {
                            "id": user.id,
                            "username": user.username,
                            "nachname": user.nachname,
                            "vorname": user.vorname,
                            "geburtsdatum": user.geburtsdatum,
                            "geburtsort": user.geburtsort,
                            "geburtsland": user.geburtsland,
                            "telefonnr": user.telefonnr,
                            "email": user.email,
                            "firma": user.firma,
                            "ort": user.ort,
                            "strasse": user.strasse,
                            "hausnummer": user.hausnummer
                        }
                        
                        return user_dict
                        
                except Exception as e:
                    logger.error(f"Fehler beim direkten Laden der Benutzerdaten: {str(e)}")
                    traceback.print_exc()
                    return {}
                    
            def direct_load_location(self, location_id):
                """Direktes Laden der Standortdaten ohne HTTP."""
                try:
                    logger.info(f"Direktes Laden der Daten für Standort {location_id}")
                    
                    # Verwende die synchrone Funktion für Datenbankzugriff
                    from utils.db_utils import get_sync_session
                    
                    with get_sync_session() as db:
                        location = db.query(models.Location).filter(models.Location.id == location_id).first()
                        if not location:
                            logger.error(f"Standort {location_id} nicht gefunden")
                            return {}
                        
                        # Manuelles Mapping der Standortdaten
                        location_dict = {
                            "id": location.id,
                            "name": location.name,
                            "city": location.city,
                            "state": location.state,
                            "postal_code": location.postal_code,
                            "address": location.address
                        }
                        
                        return location_dict
                        
                except Exception as e:
                    logger.error(f"Fehler beim direkten Laden der Standortdaten: {str(e)}")
                    traceback.print_exc()
                    return {}
            
            # Ersetze die HTTP-Methoden durch direkte Datenbankzugriffe
            import types
            agent.update_incident_status = types.MethodType(direct_update_status, agent)
            agent.load_incident_data = types.MethodType(direct_load_incident, agent)
            agent.load_user_data = types.MethodType(direct_load_user, agent)
            agent.load_location_data = types.MethodType(direct_load_location, agent)
            
            # Führe den Agenten aus
            logger.info("Starte direkten Agent ohne Subprocess")
            success = agent.run()
            
            if success:
                logger.info(f"Agent hat erfolgreich für Incident {incident_id} ausgeführt")
                update_incident_status(incident_id, "completed", "Agent hat die Aufgabe erfolgreich abgeschlossen")
            else:
                logger.error(f"Agent Ausführung für Incident {incident_id} fehlgeschlagen")
                update_incident_status(incident_id, "error", "Agent konnte die Aufgabe nicht abschließen")
            
            return success
        else:
            # Für andere Incident-Typen hier weitere Implementierungen hinzufügen
            logger.warning(f"Kein Agent-Handler für Incident-Typ: {incident_type}")
            update_incident_status(incident_id, "error", f"Kein Agent-Handler für Incident-Typ: {incident_type}")
            return False
            
    except Exception as e:
        error_msg = f"Fehler beim Ausführen des Agenten: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        update_incident_status(incident_id, "error", error_msg)
        return False

def update_incident_status(incident_id: int, status: str = None, agent_log: str = None):
    """
    Updates the incident status in the database using synchronous operations.
    
    Args:
        incident_id: The incident ID
        status: The new status (optional)
        agent_log: The agent log to append (optional)
    """
    try:
        # Import here to avoid circular imports
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        
        # Create a synchronous engine
        db_url = settings.DATABASE_URL
        engine = create_engine(db_url, echo=False)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # Use a session
        db = SessionLocal()
        try:
            # Get the incident
            incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
            if incident:
                # Update status if provided
                if status is not None:
                    incident.status = status
                
                # Update agent log if provided
                if agent_log is not None:
                    # Wenn ein Agent-Log existiert, hänge das neue Log an
                    if incident.agent_log:
                        incident.agent_log = incident.agent_log + "\n\n" + agent_log
                    else:
                        incident.agent_log = agent_log
                
                # Commit changes
                db.commit()
                logger.info(f"Incident {incident_id} status updated to {status}")
            else:
                logger.error(f"Incident {incident_id} not found")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error updating incident status: {str(e)}")
        traceback.print_exc()