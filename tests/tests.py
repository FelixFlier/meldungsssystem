# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Pfad zum Hauptverzeichnis hinzufügen
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import Base
from main import app, get_db
from models import User, Incident
from security import get_password_hash


# In-Memory SQLite-Datenbank für Tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """Erstellt eine temporäre In-Memory-Datenbank für Tests."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Datenbank-Schema erstellen
    Base.metadata.create_all(bind=engine)
    
    # Testdaten erstellen
    db = TestingSessionLocal()
    
    # Test-Benutzer erstellen
    test_user = User(
        username="testuser",
        password=get_password_hash("testpassword"),
        nachname="Test",
        vorname="User",
        geburtsdatum="01.01.1990",
        geburtsort="Teststadt",
        geburtsland="Deutschland",
        telefonnr="0123456789",
        email="test@example.com",
        ort="Testort",
        strasse="Teststraße",
        hausnummer="1"
    )
    db.add(test_user)
    db.commit()
    
    # Session zurückgeben
    yield db
    
    # Aufräumen
    db.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """Erstellt einen Test-Client für die FastAPI-Anwendung."""
    
    # Überschreibe die get_db-Dependency mit unserer Test-DB
    def override_get_db():
        try:
            yield test_db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Zurücksetzen
    app.dependency_overrides = {}


@pytest.fixture(scope="function")
def token_header(test_client):
    """Erzeugt einen Token für einen Testbenutzer."""
    response = test_client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "testpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    token_data = response.json()
    return {"Authorization": f"Bearer {token_data['access_token']}"}


# tests/test_auth.py

def test_login_success(test_client):
    """Test für erfolgreiche Anmeldung."""
    response = test_client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "testpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data


def test_login_wrong_password(test_client):
    """Test für Anmeldung mit falschem Passwort."""
    response = test_client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "wrongpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_user_not_found(test_client):
    """Test für Anmeldung mit nicht existierendem Benutzer."""
    response = test_client.post(
        "/token",
        data={
            "username": "nonexistentuser",
            "password": "testpassword",
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 401
    assert "detail" in response.json()


# tests/test_users.py

def test_read_users_me(test_client, token_header):
    """Test für das Abrufen des eigenen Benutzerprofils."""
    response = test_client.get("/users/me/", headers=token_header)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["nachname"] == "Test"
    assert data["vorname"] == "User"
    assert "password" not in data  # Passwort sollte nicht zurückgegeben werden


def test_read_users_me_unauthorized(test_client):
    """Test für unautorisiertes Abrufen des Benutzerprofils."""
    response = test_client.get("/users/me/")
    
    assert response.status_code == 401


def test_update_user(test_client, token_header):
    """Test für das Aktualisieren des Benutzerprofils."""
    update_data = {
        "nachname": "NewLastName",
        "email": "newemail@example.com"
    }
    
    response = test_client.put(
        "/users/me/",
        json=update_data,
        headers=token_header
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["nachname"] == "NewLastName"
    assert data["email"] == "newemail@example.com"
    assert data["vorname"] == "User"  # Unveränderte Felder bleiben gleich


# tests/test_incidents.py

def test_create_incident(test_client, token_header):
    """Test für das Erstellen eines Vorfalls."""
    incident_data = {
        "type": "diebstahl",
        "incident_date": "2023-01-01",
        "incident_time": "12:00"
    }
    
    response = test_client.post(
        "/incidents/",
        json=incident_data,
        headers=token_header
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["type"] == "diebstahl"
    assert data["incident_date"] == "2023-01-01"
    assert data["incident_time"] == "12:00"
    assert data["user_id"] == 1  # Sollte auf den Test-User verweisen


def test_get_incidents(test_client, token_header, test_db):
    """Test für das Abrufen der Vorfälle eines Benutzers."""
    # Erstelle einen Vorfall für den Test-User
    user = test_db.query(User).filter(User.username == "testuser").first()
    incident = Incident(
        type="sachbeschaedigung",
        incident_date="2023-02-02",
        incident_time="14:30",
        user_id=user.id
    )
    test_db.add(incident)
    test_db.commit()
    
    # Rufe Vorfälle ab
    response = test_client.get("/incidents/", headers=token_header)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["type"] == "sachbeschaedigung"
    assert data[0]["incident_date"] == "2023-02-02"
    assert data[0]["incident_time"] == "14:30"