# schemas.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    agent_log: Optional[str] = None

class UserBase(BaseModel):
    username: str
    nachname: str
    vorname: str
    geburtsdatum: str
    geburtsort: str
    geburtsland: str
    telefonnr: str
    email: str
    firma: Optional[str] = None
    ort: str
    strasse: str
    hausnummer: str

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    nachname: Optional[str] = None
    vorname: Optional[str] = None
    geburtsdatum: Optional[str] = None
    geburtsort: Optional[str] = None
    geburtsland: Optional[str] = None
    telefonnr: Optional[str] = None
    email: Optional[str] = None
    firma: Optional[str] = None
    ort: Optional[str] = None
    strasse: Optional[str] = None
    hausnummer: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime = None
    updated_at: Optional[datetime] = None
    is_active: Optional[bool] = True
    
    class Config:
        from_attributes = True
        # Optional: JSON-Serialisierer konfigurieren
        json_encoders = {
            datetime: lambda dt: dt.isoformat() if dt else None
        }

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int

class TokenData(BaseModel):
    username: Optional[str] = None

class IncidentBase(BaseModel):
    type: str
    incident_date: str
    incident_time: str
    email_data: Optional[str] = None
    location_id: Optional[int] = None  # Explizit als Optional definieren

class IncidentCreate(IncidentBase):
    user_id: Optional[int] = None
    # location_id ist bereits in IncidentBase definiert

class Incident(IncidentBase):
    id: int
    user_id: int
    status: str
    created_at: datetime
    location: Optional[str] = None  # Name des Standorts (wird aus location_id abgeleitet)
    
    class Config:
        from_attributes = True

# Neue Schemas für Locations
class LocationBase(BaseModel):
    name: str
    city: str
    state: str
    postal_code: Optional[str] = None
    address: Optional[str] = None

class LocationCreate(LocationBase):
    pass

class Location(LocationBase):
    id: int
    
    class Config:
        from_attributes = True