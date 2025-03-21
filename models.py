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


class Incident(Base):
    """Vorfallmodell für die Datenbank"""
    __tablename__ = "incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)
    incident_date = Column(String, nullable=False)
    incident_time = Column(String, nullable=False)
    excel_data = Column(Text, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    agent_log = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="incidents")


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