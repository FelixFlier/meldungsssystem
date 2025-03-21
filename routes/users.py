"""
User management routes for the Meldungssystem API.
Handles user creation, profile management, and user data retrieval.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

import crud
import security
from database import get_db, get_db_sync
from models import User, AuditLog
from schemas import UserCreate, UserUpdate, User as UserSchema

router = APIRouter()

@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db_sync)):
    """
    Create a new user account with the provided data.
    Returns 400 if username already exists.
    """
    db_user = crud.get_user_by_username_sync(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Benutzername bereits registriert")
    return crud.create_user_sync(db=db, user=user)

@router.get("/me/", response_model=UserSchema)
async def read_users_me(current_user: User = Depends(security.get_current_user)):
    """
    Get current user profile with explicit conversion to ensure all fields
    are correctly serialized.
    """
    # Explicitly convert the model to dict with all required fields
    user_dict = {
        "id": current_user.id,
        "username": current_user.username,
        "nachname": current_user.nachname, 
        "vorname": current_user.vorname,
        "geburtsdatum": current_user.geburtsdatum,
        "geburtsort": current_user.geburtsort,
        "geburtsland": current_user.geburtsland,
        "telefonnr": current_user.telefonnr,
        "email": current_user.email,
        "firma": current_user.firma,
        "ort": current_user.ort,
        "strasse": current_user.strasse,
        "hausnummer": current_user.hausnummer,
        "created_at": current_user.created_at,
        "updated_at": current_user.updated_at if hasattr(current_user, 'updated_at') else None,
        "is_active": current_user.is_active if current_user.is_active is not None else True
    }
    return user_dict

@router.put("/me/", response_model=UserSchema)
async def update_user_me(
    user_update: UserUpdate, 
    current_user: User = Depends(security.get_current_user), 
    db: Session = Depends(get_db_sync)  # Verwende get_db_sync für synchrone Operationen
):
    # Verwende synchrone Funktion
    updated_user = crud.update_user_sync(db=db, user_id=current_user.id, user_update=user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    
    # Audit Log erstellen
    db.add(AuditLog(
        user_id=current_user.id,
        action="update",
        resource_type="user",
        resource_id=str(current_user.id),
        details="Benutzer aktualisiert"
    ))
    db.commit()  # Synchrones commit
    
    return updated_user

@router.get("/{user_id}", response_model=UserSchema)
async def read_user(
    user_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(security.get_current_user)
):
    """
    Get user profile by ID. Users can only access their own profile 
    unless they have admin privileges.
    """
    # Nur eigene Daten oder Admin darf Benutzer abrufen
    if current_user.id != user_id:  # Hier könnte noch eine Admin-Prüfung ergänzt werden
        raise HTTPException(status_code=403, detail="Unzureichende Berechtigung")
    
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    return db_user