"""
Health check and system information routes for the Meldungssystem API.
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from typing import List

import security
from database import get_db, get_db_sync
from models import User, AuditLog
from config import get_settings
import crud

settings = get_settings()

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    Simple health check endpoint to verify the API is running.
    """
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION
    }

@router.get("/profile")
async def read_user_profile(current_user: User = Depends(security.get_current_user)):
    """
    Simplified user profile endpoint without complex validation.
    """
    # Manuelle JSON-Serialisierung ohne komplexe Validierung
    return {
        "id": current_user.id,
        "username": current_user.username,
        "vorname": current_user.vorname,
        "nachname": current_user.nachname,
        "email": current_user.email,
        "firma": current_user.firma,
        "telefonnr": current_user.telefonnr,
        "geburtsdatum": current_user.geburtsdatum,
        "geburtsort": current_user.geburtsort,
        "geburtsland": current_user.geburtsland,
        "ort": current_user.ort,
        "strasse": current_user.strasse,
        "hausnummer": current_user.hausnummer,
        "is_active": True if current_user.is_active else False
    }

@router.get("/basic-profile")
async def get_basic_profile(current_user: User = Depends(security.get_current_user)):
    """
    Minimal user profile information, useful for UI components.
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "name": f"{current_user.vorname} {current_user.nachname}".strip()
    }

@router.get("/auth-status")
async def check_auth_status(current_user: User = Depends(security.get_current_user)):
    """
    Check if the current authentication token is valid.
    """
    return {"authenticated": True, "user_id": current_user.id}

@router.get("/activities")
async def read_user_activities(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db_sync),  # Verwende synchrone Session
    current_user: User = Depends(security.get_current_user)
):
    """
    Get all activity logs for the current user with pagination support.
    """
    activities = crud.get_user_audit_logs(db, current_user.id, skip, limit)
    return activities