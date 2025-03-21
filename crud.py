"""
CRUD operations for database models with SQLAlchemy 2.0 API.
Consistent use of synchronous functions for backward compatibility.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, select
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas
import security

# --- User Operations (Synchronous) ---

def get_user(db, user_id: int):
    """Get a user by ID."""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db, username: str):
    """Get a user by username."""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db, user: schemas.UserCreate):
    """Create a new user."""
    hashed_password = security.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        password=hashed_password,
        nachname=user.nachname,
        vorname=user.vorname,
        geburtsdatum=user.geburtsdatum,
        geburtsort=user.geburtsort,
        geburtsland=user.geburtsland,
        telefonnr=user.telefonnr,
        email=user.email,
        firma=user.firma,
        ort=user.ort,
        strasse=user.strasse,
        hausnummer=user.hausnummer
    )
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Benutzername bereits vergeben"
        )

def update_user(db, user_id: int, user_update: schemas.UserUpdate):
    """Update a user's information."""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Incident Operations (Synchronous) ---

def get_incident(db, incident_id: int):
    """Get an incident by ID."""
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()

def create_incident(db, incident: schemas.IncidentCreate):
    """Create a new incident."""
    db_incident = models.Incident(
        type=incident.type,
        incident_date=incident.incident_date,
        incident_time=incident.incident_time,
        excel_data=incident.excel_data,
        user_id=incident.user_id,
        status="pending"
    )
    db.add(db_incident)
    db.commit()
    db.refresh(db_incident)
    return db_incident

def update_incident(db, incident_id: int, incident_update: schemas.IncidentUpdate):
    """Update an incident."""
    db_incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
    if not db_incident:
        return None
    
    update_data = incident_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_incident, key, value)
    
    db.commit()
    db.refresh(db_incident)
    return db_incident

def get_user_incidents(db, user_id: int, skip: int = 0, limit: int = 100):
    """Get all incidents for a user."""
    return db.query(models.Incident).filter(models.Incident.user_id == user_id).offset(skip).limit(limit).all()

# --- Audit Log Operations (Synchronous) ---

def get_user_audit_logs(db, user_id: int, skip: int = 0, limit: int = 100):
    """Get all audit logs for a user."""
    return db.query(models.AuditLog).filter(
        models.AuditLog.user_id == user_id
    ).order_by(models.AuditLog.timestamp.desc()).offset(skip).limit(limit).all()

def create_audit_log(db, user_id: int, action: str, resource_type: str, 
                     resource_id: str = None, ip_address: str = None, details: str = None):
    """Create a new audit log entry."""
    db_log = models.AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details=details
    )
    db.add(db_log)
    db.commit()
    return db_log

# --- Legacy aliases for backward compatibility ---
# These are just aliases to the functions above for code that might still be using them

get_user_sync = get_user
get_user_by_username_sync = get_user_by_username
create_user_sync = create_user
update_user_sync = update_user
get_incident_sync = get_incident
create_incident_sync = create_incident
update_incident_sync = update_incident
get_user_incidents_sync = get_user_incidents