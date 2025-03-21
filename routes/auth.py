"""
Authentication routes for the Meldungssystem API.
Handles login, token generation, and CSRF tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
import secrets
from datetime import timedelta

from database import get_db, get_db_sync
from models import AuditLog
import security
from schemas import Token
from config import get_settings

settings = get_settings()

router = APIRouter()

@router.get("/csrf-token")
async def get_csrf_token():
    """Gibt ein CSRF-Token für das Frontend zurück.""" 
    token = secrets.token_hex(32)
    return {"csrf_token": token}

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None
):
    """
    Generate an access token using username and password authentication.
    Creates an audit log entry for the login attempt.
    """
    # Verwende einen synchronen Kontext-Manager
    from utils.db_utils import get_sync_session
    
    with get_sync_session() as db_sync:
        user = security.authenticate_user(db_sync, form_data.username, form_data.password)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Ungültige Anmeldedaten",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Audit Log erstellen
        audit_log = AuditLog(
            user_id=user.id,
            action="login",
            resource_type="user",
            resource_id=str(user.id),
            ip_address=request.client.host if request and request.client else None,
            details="Login erfolgreich"
        )
        db_sync.add(audit_log)
        db_sync.commit()
        
        # Token erstellen
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            data={"sub": user.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer", "user_id": user.id}