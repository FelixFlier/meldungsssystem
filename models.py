from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """Benutzermodell für die Datenbank"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    nachname = Column(String, nullable=False)
    vorname = Column(String, nullable=False)
    geburtsdatum = Column(String, nullable=False)
    geburtsort = Column(String, nullable=False)
    geburtsland = Column(String, nullable=False)
    telefonnr = Column(String, nullable=False)
    email = Column(String, nullable=False)
    firma = Column(String, nullable=True)
    ort = Column(String, nullable=False)
    strasse = Column(String, nullable=False)
    hausnummer = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    
    incidents = relationship("Incident", back_populates="user")
    user_locations = relationship("UserLocation", back_populates="user", cascade="all, delete-orphan")


class Incident(Base):
    """Vorfallmodell für die Datenbank"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    incident_date = Column(String, nullable=False)
    incident_time = Column(String, nullable=False)
    email_data = Column(Text, nullable=True)  # Neu: JSON-String mit extrahierten E-Mail-Daten
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)  # Neu: Beziehung zu Location
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    agent_log = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="incidents")
    location = relationship("Location", back_populates="incidents")  # Neu: Beziehung zu Location
    user_location_id = Column(Integer, ForeignKey("user_locations.id"), nullable=True)
    user_location = relationship("UserLocation", back_populates="incidents")


class AuditLog(Base):
    """Audit-Log für wichtige Systemaktionen"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    user = relationship("User")
    
class UserLocation(Base):
    """Benutzerdefinierte Tatort-Standorte"""
    __tablename__ = "user_locations"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # z.B. "Büro Stuttgart"
    staat = Column(String, default="Deutschland", nullable=False)
    bundesland = Column(String, nullable=False)
    ort = Column(String, nullable=False)
    strasse = Column(String, nullable=False)
    hausnummer = Column(String, nullable=False)
    zusatz_info = Column(Text, nullable=True)  # z.B. "Im 24/7 Shop"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="user_locations")
    incidents = relationship("Incident", back_populates="user_location")


class Location(Base):
    """Standortmodell für die Datenbank"""
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    postal_code = Column(String, nullable=True)
    address = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    incidents = relationship("Incident", back_populates="location")  # Neu: Beziehung zu Incident