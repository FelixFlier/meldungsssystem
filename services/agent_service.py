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

settings = get_settings()
logger = logging.getLogger(settings.APP_NAME)

async def run_agent_task(incident_id: int, incident_type: str):
    """
    Runs the agent for an incident as a background task.
    
    Args:
        incident_id: The ID of the incident to process
        incident_type: The type of incident (diebstahl, sachbeschaedigung)
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logger.info(f"Starte Agent für Incident {incident_id} vom Typ {incident_type}")
        
        # Bestimme Pfade und verifiziere ihre Existenz
        agent_file = 'agents/diebstahl_agent.py' if incident_type == 'diebstahl' else 'agents/sachbeschaedigung_agent.py'
        base_dir = Path(__file__).resolve().parent.parent
        agent_path = base_dir / agent_file
        
        if not agent_path.exists():
            error_msg = f"Agent-Datei nicht gefunden: {agent_path}"
            logger.error(error_msg)
            update_incident_status(incident_id, "error", error_msg)
            return False
        
        # Pfade ausgeben für Diagnose
        logger.info(f"Base directory: {base_dir}")
        logger.info(f"Agent path: {agent_path}")
        logger.info(f"Working directory: {os.getcwd()}")
        
        # Umgebungsvariablen für Python setzen
        env = os.environ.copy()
        env["PYTHONPATH"] = str(base_dir)
        env["PYTHONUNBUFFERED"] = "1"  # Wichtig für unbuffered Output
        env["INCIDENT_ID"] = str(incident_id)  # Incident-ID an den Agenten übergeben
        env["API_HOST"] = "localhost:8000"  # Explizit den API-Host setzen
        
        # Generiere temporären API-Token für den Agenten (als File und als Env-Variable)
        token = security.create_access_token(
            data={"sub": "agent", "incident_id": incident_id}, 
            expires_delta=timedelta(minutes=30)
        )
        env["API_TOKEN"] = token
        
        # Token auch in temporäre Datei schreiben
        token_file = base_dir / f"token_{incident_id}.tmp"
        with open(token_file, "w") as f:
            f.write(token)
        
        logger.info(f"Token für Incident {incident_id} generiert und gespeichert")
        
        # Zusätzliche Incident-Informationen speichern für den Agenten
        try:
            from utils.db_utils import get_sync_session
            with get_sync_session() as db:
                incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
                if incident:
                    incident_info = {
                        "id": incident.id,
                        "type": incident.type,
                        "date": incident.incident_date,
                        "time": incident.incident_time,
                        "user_id": incident.user_id
                    }
                    
                    # Speichere Incident-Informationen in temporärer Datei
                    incident_file = base_dir / f"incident_{incident_id}.tmp"
                    with open(incident_file, "w") as f:
                        json.dump(incident_info, f)
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Incident-Informationen: {str(e)}")
        
        # Aktualisiere den Status vor der Ausführung
        update_incident_status(incident_id, "processing", "Agent wird gestartet...")
        
        # Increased timeout to prevent premature termination
        timeout = 300  # 5 minutes
        
        # Zusätzliche Kommandozeilenargumente für den Agenten
        cmd_args = [
            sys.executable,
            str(agent_path),
            str(incident_id),
            "--token-file", str(token_file),
            "--api-host", env["API_HOST"]
        ]
        
        logger.info(f"Führe Befehl aus: {' '.join(cmd_args)}")
        
        # Führe den Agenten in einem separaten Prozess aus
        process = subprocess.Popen(
            cmd_args,
            env=env,
            cwd=str(base_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
        )
        
        logger.info(f"Agent-Prozess gestartet mit PID: {process.pid}")
        
        # Prozessausgabe nicht blockierend lesen
        try:
            stdout_data, stderr_data = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            # Kill process if it takes too long
            process.kill()
            stdout_data, stderr_data = process.communicate()
            stderr_data += f"\nProcess killed after {timeout} seconds timeout."
        
        # Temporäre Dateien aufräumen
        if token_file.exists():
            token_file.unlink()
        
        incident_file = base_dir / f"incident_{incident_id}.tmp"
        if incident_file.exists():
            incident_file.unlink()
        
        # Speichere Ausgabe im Incident
        log_data = f"---- AGENT LOG {datetime.now()} ----\n\nSTDOUT:\n{stdout_data}\n\nSTDERR:\n{stderr_data}"
        update_incident_status(incident_id, status=None, agent_log=log_data)
        
        # Check exit code
        if process.returncode != 0:
            logger.error(f"Agent process failed with exit code {process.returncode}")
            update_incident_status(incident_id, "error", log_data + "\n\nAgent beendet mit Fehlercode " + str(process.returncode))
            return False
        
        # Zeige Ausgabe an
        if stdout_data:
            logger.info(f'Agent Output:\n{stdout_data}')
        if stderr_data:
            logger.error(f'Agent Error:\n{stderr_data}')
        
        logger.info(f"Agent execution completed for incident {incident_id}")
        update_incident_status(incident_id, "completed", log_data + "\n\nAgent erfolgreich abgeschlossen.")
        return True
    except Exception as e:
        logger.error(f'Error running agent: {str(e)}')
        traceback.print_exc()
        
        # Update incident status to error with synchronous approach
        error_msg = f"Fehler beim Ausführen des Agenten: {str(e)}\n{traceback.format_exc()}"
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