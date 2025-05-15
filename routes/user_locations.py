"""
User location management routes for the Meldungssystem API.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

import crud
import security
from database import get_db_sync
from models import User, AuditLog
from schemas import UserLocation, UserLocationCreate, UserLocationUpdate

router = APIRouter()

@router.get("/", response_model=List[UserLocation])
async def read_user_locations(
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Get all locations for the current user."""
    locations = crud.get_user_locations(db, user_id=current_user.id)
    return locations

@router.get("/{location_id}", response_model=UserLocation)
async def read_user_location(
    location_id: int,
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Get a specific user location."""
    location = crud.get_user_location(db, location_id=location_id)
    
    if not location or location.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Standort nicht gefunden")
    
    return location

@router.post("/", response_model=UserLocation)
async def create_user_location(
    location: UserLocationCreate,
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Create a new user location."""
    db_location = crud.create_user_location(db, location=location, user_id=current_user.id)
    
    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="create",
        resource_type="user_location",
        resource_id=str(db_location.id),
        details=f"Standort '{location.name}' erstellt"
    ))
    db.commit()
    
    return db_location

@router.put("/{location_id}", response_model=UserLocation)
async def update_user_location(
    location_id: int,
    location_update: UserLocationUpdate,
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Update a user location."""
    # Check ownership
    existing_location = crud.get_user_location(db, location_id=location_id)
    
    if not existing_location or existing_location.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Standort nicht gefunden")
    
    updated_location = crud.update_user_location(db, location_id=location_id, location_update=location_update)
    
    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="update",
        resource_type="user_location",
        resource_id=str(location_id),
        details=f"Standort aktualisiert"
    ))
    db.commit()
    
    return updated_location

@router.delete("/{location_id}")
async def delete_user_location(
    location_id: int,
    current_user: User = Depends(security.get_current_user),
    db: Session = Depends(get_db_sync)
):
    """Delete a user location."""
    # Check ownership
    existing_location = crud.get_user_location(db, location_id=location_id)
    
    if not existing_location or existing_location.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Standort nicht gefunden")
    
    success = crud.delete_user_location(db, location_id=location_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Fehler beim Löschen des Standorts")
    
    # Audit log
    db.add(AuditLog(
        user_id=current_user.id,
        action="delete",
        resource_type="user_location",
        resource_id=str(location_id),
        details=f"Standort gelöscht"
    ))
    db.commit()
    
    return {"detail": "Standort erfolgreich gelöscht"}