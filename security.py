"""
Security utilities for authentication and authorization.
Updated to support SQLAlchemy 2.0 async API.
"""

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import models
import schemas
from database import get_db, get_db_sync
from config import get_settings

# Load settings
settings = get_settings()
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 with Password Flow
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a hash from a password."""
    return pwd_context.hash(password)

# --- Synchronous Authentication (for compatibility) ---

# --- Synchronous Authentication (for compatibility) ---

def authenticate_user(db, username: str, password: str):
    """
    Authenticate a user by username and password.
    This is a synchronous version for backwards compatibility.
    """
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_db_sync)):
    """
    Get the current user from a JWT token.
    This is a synchronous version for backwards compatibility.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = schemas.TokenData(username=username)
        
        # Find user in database
        user = db.query(models.User).filter(models.User.username == username).first()
        
        if user is None:
            raise credentials_exception
            
        return user
        
    except JWTError:
        raise credentials_exception

# --- Token Creation Functions ---

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with optional expiration.
    Used by both sync and async code paths.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Async Authentication Functions ---

async def authenticate_user_async(db: AsyncSession, username: str, password: str):
    """Authenticate a user by username and password with async API."""
    result = await db.execute(
        select(models.User).filter(models.User.username == username)
    )
    user = result.scalars().first()
    
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user

async def get_current_user_async(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    """Get the current user from a JWT token with async API."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
            
        token_data = schemas.TokenData(username=username)
        
        # Find user in database
        result = await db.execute(
            select(models.User).filter(models.User.username == username)
        )
        user = result.scalars().first()
        
        if user is None:
            raise credentials_exception
            
        return user
        
    except JWTError:
        raise credentials_exception

# --- Agent Authentication ---

async def get_current_agent_async(token: str = Depends(oauth2_scheme)):
    """Validate an agent token with incident ID."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten für Agent",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        incident_id: int = payload.get("incident_id")
        
        if username != "agent" or incident_id is None:
            raise credentials_exception
            
        return {"username": username, "incident_id": incident_id}
    except JWTError:
        raise credentials_exception

def get_current_agent(token: str = Depends(oauth2_scheme)):
    """Synchronous version of get_current_agent_async."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Ungültige Anmeldedaten für Agent",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        incident_id: int = payload.get("incident_id")
        
        if username != "agent" or incident_id is None:
            raise credentials_exception
            
        return {"username": username, "incident_id": incident_id}
    except JWTError:
        raise credentials_exception