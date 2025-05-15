"""
CRUD operations for database models with SQLAlchemy 2.0 API.
Updated with location support and consistent use of synchronous functions for backward compatibility.
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

# --- Location Operations (Synchronous) ---

def get_location(db, location_id: int):
    """Get a location by ID."""
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def get_locations(db, skip: int = 0, limit: int = 100):
    """Get all locations with pagination."""
    return db.query(models.Location).offset(skip).limit(limit).all()

def create_location(db, location: schemas.LocationCreate):
    """Create a new location."""
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def import_locations_from_excel(db, locations_data):
    """
    Import locations from Excel data.
    
    Args:
        db: Database session
        locations_data: List of location dictionaries
    
    Returns:
        int: Number of imported locations
    """
    count = 0
    for location_data in locations_data:
        # Check if location already exists
        existing = db.query(models.Location).filter(
            models.Location.name == location_data['name'],
            models.Location.city == location_data['city']
        ).first()
        
        if not existing:
            # Create new location
            db_location = models.Location(
                name=location_data['name'],
                city=location_data['city'],
                state=location_data['state'],
                postal_code=location_data.get('postal_code'),
                address=location_data.get('address')
            )
            db.add(db_location)
            count += 1
    
    db.commit()
    return count

# --- Incident Operations (Synchronous) ---

def get_incident(db, incident_id: int):
    """Get an incident by ID."""
    return db.query(models.Incident).filter(models.Incident.id == incident_id).first()

def create_incident(db, incident: schemas.IncidentCreate):
    """Create a new incident with location support."""
    try:
        # Erstelle ein Dictionary aus dem Schema
        incident_dict = incident.dict()
        
        # Entferne Felder, die nicht direkt im Modell definiert sind
        incident_data = {k: v for k, v in incident_dict.items() if hasattr(models.Incident, k)}
        
        # Füge user_location_id hinzu, falls vorhanden
        if 'user_location_id' in incident_dict:
            incident_data['user_location_id'] = incident_dict['user_location_id']
        
        # Erstelle den Incident
        db_incident = models.Incident(**incident_data)
        db.add(db_incident)
        db.commit()
        db.refresh(db_incident)
        
        return db_incident
    except Exception as e:
        db.rollback()
        raise e

def update_incident(db, incident_id: int, incident_update: schemas.IncidentUpdate):
    """Update an incident."""
    try:
        # Finde den Incident
        db_incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
        if not db_incident:
            return None
        
        # Erstelle ein Dictionary aus dem Update-Schema
        update_data = incident_update.dict(exclude_unset=True)
        
        # Aktualisiere alle angegebenen Felder
        for key, value in update_data.items():
            # Bei location_id auch den location-Namen aktualisieren
            if key == 'location_id' and value is not None:
                location = db.query(models.Location).filter(models.Location.id == value).first()
                if location:
                    setattr(db_incident, 'location', location.name)
            
            setattr(db_incident, key, value)
        
        db.commit()
        db.refresh(db_incident)
        return db_incident
    except Exception as e:
        db.rollback()
        raise e

def delete_incident(db, incident_id: int):
    """Delete an incident."""
    try:
        db_incident = db.query(models.Incident).filter(models.Incident.id == incident_id).first()
        if not db_incident:
            return False
        
        db.delete(db_incident)
        db.commit()
        return True
    except:
        db.rollback()
        return False
    
def get_user_incidents(db, user_id: int, skip: int = 0, limit: int = 100):
    """Get all incidents for a user with location information."""
    return db.query(models.Incident).filter(
        models.Incident.user_id == user_id
    ).offset(skip).limit(limit).all()

def count_user_incidents(db, user_id: int):
    """Count total incidents for a user."""
    return db.query(models.Incident).filter(
        models.Incident.user_id == user_id
    ).count()

def get_incidents_by_status(db, status: str, skip: int = 0, limit: int = 100):
    """Get incidents by status."""
    return db.query(models.Incident).filter(
        models.Incident.status == status
    ).offset(skip).limit(limit).all()

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

# --- User Location Operations (Synchronous) ---

def get_user_location(db, location_id: int):
    """Get a user location by ID."""
    return db.query(models.UserLocation).filter(models.UserLocation.id == location_id).first()

def get_user_locations(db, user_id: int, skip: int = 0, limit: int = 100):
    """Get all locations for a user."""
    return db.query(models.UserLocation).filter(
        models.UserLocation.user_id == user_id
    ).offset(skip).limit(limit).all()

def create_user_location(db, location: schemas.UserLocationCreate, user_id: int):
    """Create a new user location."""
    db_location = models.UserLocation(
        **location.dict(),
        user_id=user_id
    )
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def update_user_location(db, location_id: int, location_update: schemas.UserLocationUpdate):
    """Update a user location."""
    db_location = db.query(models.UserLocation).filter(
        models.UserLocation.id == location_id
    ).first()
    
    if not db_location:
        return None
    
    update_data = location_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

def delete_user_location(db, location_id: int):
    """Delete a user location."""
    db_location = db.query(models.UserLocation).filter(
        models.UserLocation.id == location_id
    ).first()
    
    if not db_location:
        return False
    
    db.delete(db_location)
    db.commit()
    return True

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