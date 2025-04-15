# tests/test_crud_operations.py
import unittest
import sys
import os
from pathlib import Path

# Pfade einrichten
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import crud
import models
import schemas
from utils.db_utils import get_sync_session

class TestCRUDOperations(unittest.TestCase):
    """Tests für CRUD-Operationen."""
    
    def setUp(self):
        """Test-Setup mit Testdaten."""
        # Testdaten erstellen
        self.test_location = {
            "name": "Test Location",
            "city": "Test City",
            "state": "Test State",
            "postal_code": "12345",
            "address": "Test Address 123"
        }
        
        self.test_user_data = {
            "username": "testuser",
            "password": "testpassword",
            "nachname": "Test",
            "vorname": "User",
            "geburtsdatum": "01.01.1990",
            "geburtsort": "Test City",
            "geburtsland": "Test Country",
            "telefonnr": "123456789",
            "email": "test@example.com",
            "ort": "Test City",
            "strasse": "Test Street",
            "hausnummer": "123"
        }
        
        self.test_incident_data = {
            "type": "diebstahl",
            "incident_date": "2025-02-09",
            "incident_time": "09:24",
            "email_data": '{"date":"2025-02-09","time":"09:24","location":"Test Location","confidence":0.95}'
        }
    
    def test_location_crud(self):
        """Testet CRUD-Operationen für Standorte."""
        with get_sync_session() as db:
            # Create
            location_schema = schemas.LocationCreate(**self.test_location)
            location = crud.create_location(db, location_schema)
            self.assertIsNotNone(location)
            self.assertEqual(location.name, self.test_location["name"])
            
            # Read
            fetched_location = crud.get_location(db, location.id)
            self.assertIsNotNone(fetched_location)
            self.assertEqual(fetched_location.name, self.test_location["name"])
            
            # Update
            update_data = schemas.LocationCreate(
                name="Updated Location",
                city=self.test_location["city"],
                state=self.test_location["state"]
            )
            updated_location = crud.update_location(db, location.id, update_data)
            self.assertEqual(updated_location.name, "Updated Location")
            
            # Delete
            result = crud.delete_location(db, location.id)
            self.assertTrue(result)
            deleted_check = crud.get_location(db, location.id)
            self.assertIsNone(deleted_check)
    
    def test_fuzzy_matching(self):
        """Testet das Fuzzy-Matching für Standorte."""
        with get_sync_session() as db:
            # Testdaten einfügen
            location_schema = schemas.LocationCreate(**self.test_location)
            location = crud.create_location(db, location_schema)
            
            # Verschiedene Fuzzy-Matching-Tests
            test_cases = [
                ("Test Location", True),     # Exakte Übereinstimmung
                ("TestLocation", True),      # Ohne Leerzeichen
                ("Test Lcation", True),      # Tippfehler
                ("Location Test", True),     # Umgekehrte Reihenfolge
                ("Completely Different", False)  # Keine Übereinstimmung
            ]
            
            for search_term, should_match in test_cases:
                result = crud.find_location_by_fuzzy_name(db, search_term)
                if should_match:
                    self.assertIsNotNone(result, f"Failed to match: {search_term}")
                    self.assertEqual(result.id, location.id)
                else:
                    self.assertIsNone(result, f"Should not match: {search_term}")
            
            # Aufräumen
            db.delete(location)
            db.commit()
    
    def test_incident_with_location(self):
        """Testet die Integration von Incidents mit Standorten."""
        with get_sync_session() as db:
            # Benutzer erstellen
            hashed_password = "hashed_" + self.test_user_data["password"]
            user = models.User(
                **{k: v for k, v in self.test_user_data.items() if k != "password"},
                password=hashed_password
            )
            db.add(user)
            db.commit()
            
            # Standort erstellen
            location_schema = schemas.LocationCreate(**self.test_location)
            location = crud.create_location(db, location_schema)
            
            # Incident mit Standort erstellen
            incident_data = self.test_incident_data.copy()
            incident_data["user_id"] = user.id
            incident_data["location_id"] = location.id
            
            incident_schema = schemas.IncidentCreate(**incident_data)
            incident = crud.create_incident(db, incident_schema)
            
            # Überprüfungen
            self.assertEqual(incident.location_id, location.id)
            
            # Detaillierte Incident-Abfrage
            incident_detail = crud.get_incident(db, incident.id)
            self.assertEqual(incident_detail.location.name, self.test_location["name"])
            
            # Benutzer-Incidents abfragen
            user_incidents = crud.get_user_incidents(db, user.id)
            self.assertEqual(len(user_incidents), 1)
            self.assertEqual(user_incidents[0].id, incident.id)
            
            # Aufräumen
            db.delete(incident)
            db.delete(location)
            db.delete(user)
            db.commit()

if __name__ == '__main__':
    unittest.main()