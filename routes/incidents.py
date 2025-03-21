"""
Incident management routes for the Meldungssystem API.
Handles incident creation, updates, and retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import List

import crud
import security
from database import get_db, get_db_sync
import models
from models import User, AuditLog
from schemas import (
    IncidentCreate, 
    Incident as IncidentSchema, 
    IncidentUpdate
)
from services.agent_service import run_agent_task  # Import agent service

router = APIRouter()

@router.post("/", response_model=IncidentSchema)
async def create_incident(
    incident: IncidentCreate, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(get_db_sync),  # Verwende synchrone Session
    current_user: User = Depends(security.get_current_user),
    request: Request = None
):
    """
    Create a new incident and start a background agent to process it.
    Creates an audit log entry for the incident creation.
    """
    # Benutzer-ID aus dem authentifizierten Benutzer übernehmen
    incident.user_id = current_user.id
    
    # Incident in Datenbank speichern
    db_incident = crud.create_incident(db=db, incident=incident)
    
    # Audit Log erstellen
    db.add(AuditLog(
        user_id=current_user.id,
        action="create",
        resource_type="incident",
        resource_id=str(db_incident.id),
        ip_address=request.client.host if request and request.client else None,
        details=f"Incident vom Typ {incident.type} erstellt"
    ))
    db.commit()
    
    # Agent im Hintergrund starten
    background_tasks.add_task(run_agent_task, db_incident.id, incident.type)
    
    return db_incident

@router.get("/", response_model=List[IncidentSchema])
async def read_user_incidents(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db_sync),  # Verwende synchrone Session
    current_user: User = Depends(security.get_current_user)
):
    """
    Get all incidents for the current user with pagination support.
    """
    incidents = crud.get_user_incidents(db, user_id=current_user.id, skip=skip, limit=limit)
    return incidents

@router.get("/{incident_id}", response_model=IncidentSchema)
async def read_incident(
    incident_id: int, 
    db: Session = Depends(get_db_sync),  # Verwende synchrone Session
    current_user: User = Depends(security.get_current_user)
):
    """
    Get details of a specific incident by ID.
    Users can only access their own incidents.
    """
    db_incident = crud.get_incident(db, incident_id=incident_id)
    if db_incident is None:
        raise HTTPException(status_code=404, detail="Vorfall nicht gefunden")
    if db_incident.user_id != current_user.id:  # Hier könnte noch eine Admin-Prüfung ergänzt werden
        raise HTTPException(status_code=403, detail="Unzureichende Berechtigung")
    return db_incident

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