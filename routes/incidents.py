"""
Incident management routes for the Meldungssystem API.
Handles incident creation, updates, and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List
import logging

import crud
import security
from database import get_db, get_db_sync
import models
from models import User, AuditLog
import schemas
from schemas import IncidentCreate, IncidentUpdate, Incident as IncidentSchema
from services.agent_service import run_agent_task  # Wichtig: Agent-Service importieren
from sqlalchemy.orm import Session
from database import get_db_sync  # Synchrone Session-Factory importieren
from config import get_settings

settings = get_settings()
logger = logging.getLogger(f"{settings.APP_NAME}.incidents")

router = APIRouter()

@router.post("/", response_model=None)
def create_incident(
    incident: schemas.IncidentCreate,
    background_tasks: BackgroundTasks,  # Neu: BackgroundTasks Dependency hinzufügen
    db: Session = Depends(get_db_sync),
    current_user: models.User = Depends(security.get_current_user)
):
    # User-ID setzen, falls nicht vorhanden
    if not incident.user_id:
        incident.user_id = current_user.id
        
    # Vorfall erstellen
    db_incident = crud.create_incident(db=db, incident=incident)
    
    # Lade den Standort, falls vorhanden
    location_name = None
    if db_incident.location_id:
        location = db.query(models.Location).filter(models.Location.id == db_incident.location_id).first()
        if location:
            location_name = location.name
    
    # NEU: Starte den Agent als Hintergrundtask
    background_tasks.add_task(run_agent_task, db_incident.id, db_incident.type)
    logger.info(f"Agent Task für Incident {db_incident.id} vom Typ {db_incident.type} gestartet")
    
    # Response-Objekt erstellen
    response_dict = {
        "id": db_incident.id,
        "type": db_incident.type,
        "incident_date": db_incident.incident_date,
        "incident_time": db_incident.incident_time,
        "email_data": db_incident.email_data,
        "location_id": db_incident.location_id,
        "user_id": db_incident.user_id,
        "status": db_incident.status,
        "created_at": db_incident.created_at,
        # Setze location in der Response als String
        "location": location_name
    }
    
    return response_dict

@router.get("/", response_model=None)  # Entferne das response_model
async def read_user_incidents(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db_sync),  # Verwende die synchrone Session
    current_user: models.User = Depends(security.get_current_user)
):
    incidents = crud.get_user_incidents(db, user_id=current_user.id, skip=skip, limit=limit)
    
    # Konvertiere die Incidents für die Response
    response_incidents = []
    for incident in incidents:
        # Standortname extrahieren, falls vorhanden
        location_name = None
        if hasattr(incident, 'location') and incident.location:
            if isinstance(incident.location, models.Location):
                location_name = incident.location.name
            else:
                location_name = incident.location
        
        # Response-Objekt erstellen
        incident_dict = {
            "id": incident.id,
            "type": incident.type,
            "incident_date": incident.incident_date,
            "incident_time": incident.incident_time,
            "email_data": incident.email_data,
            "location_id": incident.location_id,
            "user_id": incident.user_id,
            "status": incident.status,
            "created_at": incident.created_at,
            "location": location_name  # String statt Objekt
        }
        response_incidents.append(incident_dict)
    
    return response_incidents

# Füge diese zwei Funktionen zu incidents.py hinzu:

@router.get("/{incident_id}/agent-direct", response_model=None)
def read_incident_for_agent_direct(
    incident_id: int, 
    db: Session = Depends(get_db_sync)
):
    """
    TEST-ENDPUNKT: Get incident data for agent WITHOUT authentication.
    WICHTIG: Nur für Tests verwenden!
    """
    incident = crud.get_incident(db, incident_id=incident_id)
    
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    
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

@router.patch("/{incident_id}/agent-direct", response_model=None)
def update_incident_status_for_agent_direct(
    incident_id: int, 
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db_sync)
):
    """
    TEST-ENDPUNKT: Update incident status for agent WITHOUT authentication.
    WICHTIG: Nur für Tests verwenden!
    """
    # Prüfe, ob der Incident existiert
    db_incident = crud.get_incident(db, incident_id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Vorfall nicht gefunden")
    
    # Aktualisiere den Incident
    updated_incident = crud.update_incident(db=db, incident_id=incident_id, incident_update=incident_update)
    
    # Audit Log erstellen
    db.add(AuditLog(
        user_id=None,  # Kein Benutzer (Agent)
        action="update",
        resource_type="incident",
        resource_id=str(incident_id),
        details=f"Agent-Direct: Incident-Status aktualisiert auf {incident_update.status}" if incident_update.status else "Agent-Direct: Incident aktualisiert"
    ))
    db.commit()
    
    return updated_incident

@router.get("/{incident_id}", response_model=IncidentSchema)
@router.get("/{incident_id}", response_model=None)
def read_incident(
    incident_id: int, 
    db: Session = Depends(get_db_sync),
    current_user: models.User = Depends(security.get_current_user)
):
    incident = crud.get_incident(db, incident_id=incident_id)
    
    if incident is None or incident.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Incident not found")
    
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

@router.patch("/{incident_id}", response_model=IncidentSchema)
async def update_incident_status(
    incident_id: int, 
    incident_update: IncidentUpdate,
    db: Session = Depends(get_db_sync),  # Verwende synchrone Session
    current_user: User = Depends(security.get_current_user)
):
    """
    Update the status of an incident.
    Creates an audit log entry for the update.
    """
    # Prüfe, ob der Incident existiert und dem Benutzer gehört
    db_incident = crud.get_incident(db, incident_id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Vorfall nicht gefunden")
    if db_incident.user_id != current_user.id:  # Hier könnte noch eine Admin-Prüfung ergänzt werden
        raise HTTPException(status_code=403, detail="Unzureichende Berechtigung")
    
    # Aktualisiere den Incident
    updated_incident = crud.update_incident(db=db, incident_id=incident_id, incident_update=incident_update)
    
    # Audit Log erstellen
    db.add(AuditLog(
        user_id=current_user.id,
        action="update",
        resource_type="incident",
        resource_id=str(incident_id),
        details=f"Incident-Status aktualisiert auf {incident_update.status}" if incident_update.status else "Incident aktualisiert"
    ))
    db.commit()
    
    return updated_incident