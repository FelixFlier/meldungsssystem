# tests/test_api.py
import unittest
import sys
import os
import json
import requests
from pathlib import Path

# Pfade einrichten
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

class TestAPI(unittest.TestCase):
    """Tests für die API-Endpunkte."""
    
    def setUp(self):
        """Test-Setup mit Anmeldung."""
        self.base_url = "http://localhost:8000"
        
        # Anmeldung
        login_data = {
            "username": "testuser",
            "password": "testpassword"
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/token",
                data=login_data
            )
            
            if response.status_code == 200:
                response_data = response.json()
                self.token = response_data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
            else:
                self.token = None
                self.headers = {}
                print(f"Login fehlgeschlagen: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Fehler bei der Anmeldung: {e}")
            self.token = None
            self.headers = {}
    
    def test_locations_endpoint(self):
        """Testet den Locations-API-Endpunkt."""
        if not self.token:
            self.skipTest("Keine Anmeldung möglich, Test wird übersprungen")
        
        response = requests.get(
            f"{self.base_url}/locations/",
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        locations = response.json()
        self.assertIsInstance(locations, list)
        
        if locations:
            location = locations[0]
            self.assertIn("id", location)
            self.assertIn("name", location)
            self.assertIn("city", location)
            self.assertIn("state", location)
    
    def test_location_detail_endpoint(self):
        """Testet den Location-Detail-API-Endpunkt."""
        if not self.token:
            self.skipTest("Keine Anmeldung möglich, Test wird übersprungen")
        
        # Zuerst alle Standorte abrufen
        response = requests.get(
            f"{self.base_url}/locations/",
            headers=self.headers
        )
        
        if response.status_code != 200 or not response.json():
            self.skipTest("Keine Standorte verfügbar, Test wird übersprungen")
        
        location_id = response.json()[0]["id"]
        
        # Einzelnen Standort abrufen
        detail_response = requests.get(
            f"{self.base_url}/locations/{location_id}",
            headers=self.headers
        )
        
        self.assertEqual(detail_response.status_code, 200)
        location = detail_response.json()
        self.assertEqual(location["id"], location_id)
    
    def test_incidents_with_location(self):
        """Testet die Incidents-API mit Standortinformationen."""
        if not self.token:
            self.skipTest("Keine Anmeldung möglich, Test wird übersprungen")
        
        # Neuen Vorfall erstellen
        incident_data = {
            "type": "diebstahl",
            "incident_date": "2025-02-09",
            "incident_time": "09:24",
            "email_data": json.dumps({
                "date": "2025-02-09",
                "time": "09:24",
                "location": "Hessental",
                "confidence": 0.95
            })
        }
        
        response = requests.post(
            f"{self.base_url}/incidents/",
            headers=self.headers,
            json=incident_data
        )
        
        self.assertEqual(response.status_code, 200)
        created_incident = response.json()
        incident_id = created_incident["id"]
        
        # Vorfall abrufen
        get_response = requests.get(
            f"{self.base_url}/incidents/{incident_id}",
            headers=self.headers
        )
        
        self.assertEqual(get_response.status_code, 200)
        incident = get_response.json()
        self.assertEqual(incident["id"], incident_id)
        self.assertEqual(incident["incident_date"], "2025-02-09")
        self.assertEqual(incident["incident_time"], "09:24")
        
        # Standort sollte enthalten sein, wenn er aufgelöst werden konnte
        if "location" in incident:
            self.assertIsNotNone(incident["location"])

if __name__ == '__main__':
    unittest.main()