# test_agent_auth.py
# Dieser Test identifiziert Probleme mit der Authentifizierung und dem Selenium-Start

import sys
import os
import json
import requests
import traceback
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import logging

# Konfiguration und Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_agent_auth")

class TestAgentAuth:
    def __init__(self, incident_id=None, token=None, api_host="localhost:8002"):
        self.incident_id = incident_id
        self.token = token
        self.api_host = api_host
        self.driver = None
        
        logger.info(f"Test initialisiert mit: incident_id={incident_id}, api_host={api_host}")
        logger.info(f"Token: {token[:20]}...{token[-10:] if token else None}")

    def test_auth(self):
        """Teste die Authentifizierung gegen die API"""
        logger.info(f"=== AUTHENTIFIZIERUNGSTEST ===")
        
        try:
            # 1. Test: Incident Status abrufen
            logger.info(f"[TEST 1] GET /incidents/{self.incident_id}")
            
            # Debug-Ausgabe der kompletten Header
            headers = {"Authorization": f"Bearer {self.token}"}
            logger.info(f"Headers: {headers}")
            
            response = requests.get(
                f"http://{self.api_host}/incidents/{self.incident_id}",
                headers=headers
            )
            
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
            
            # 2. Test: Token-Details anzeigen - dekodieren des JWT
            logger.info(f"[TEST 2] Token-Analyse")
            
            try:
                # JWT besteht aus 3 Teilen: header.payload.signature
                token_parts = self.token.split('.')
                if len(token_parts) == 3:
                    import base64
                    
                    # Header dekodieren (Teil 1)
                    header_b64 = token_parts[0]
                    # Padding hinzufügen wenn nötig
                    if len(header_b64) % 4 != 0:
                        header_b64 += '=' * (4 - len(header_b64) % 4)
                    header = json.loads(base64.b64decode(header_b64).decode('utf-8'))
                    logger.info(f"Token Header: {header}")
                    
                    # Payload dekodieren (Teil 2)
                    payload_b64 = token_parts[1]
                    # Padding hinzufügen wenn nötig
                    if len(payload_b64) % 4 != 0:
                        payload_b64 += '=' * (4 - len(payload_b64) % 4)
                    payload = json.loads(base64.b64decode(payload_b64).decode('utf-8'))
                    logger.info(f"Token Payload: {payload}")
                    
                    # Prüfe Expiration
                    if 'exp' in payload:
                        from datetime import datetime
                        exp_time = datetime.fromtimestamp(payload['exp'])
                        now = datetime.now()
                        logger.info(f"Token läuft ab am: {exp_time}, Aktuelle Zeit: {now}")
                        logger.info(f"Token ist {'abgelaufen' if exp_time < now else 'gültig'}")
            except Exception as e:
                logger.error(f"Fehler beim Dekodieren des Tokens: {str(e)}")

            # 3. Test: Versuch mit modifiziertem Header
            logger.info(f"[TEST 3] Mit explizitem 'Bearer'-Präfix")
            response = requests.get(
                f"http://{self.api_host}/incidents/{self.incident_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            logger.info(f"Status Code: {response.status_code}")
            
            # 4. Test: Token mit PATCH testen
            logger.info(f"[TEST 4] PATCH-Request auf /incidents/{self.incident_id}")
            response = requests.patch(
                f"http://{self.api_host}/incidents/{self.incident_id}",
                json={"status": "processing", "agent_log": "Test log entry"},
                headers={"Authorization": f"Bearer {self.token}"}
            )
            logger.info(f"Status Code: {response.status_code}")
            logger.info(f"Response: {response.text[:200]}")
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Fehler im Auth-Test: {str(e)}")
            traceback.print_exc()
            return False

    def test_selenium(self):
        """Teste den Selenium WebDriver-Start"""
        logger.info(f"=== SELENIUM-TEST ===")
        
        try:
            logger.info("Chrome-Optionen konfigurieren...")
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            # Headless-Modus für Test deaktivieren
            # chrome_options.add_argument('--headless')
            
            # Ermittle den ChromeDriver-Pfad
            logger.info("ChromeDriver-Pfad ermitteln...")
            base_path = ChromeDriverManager().install()
            driver_dir = os.path.dirname(base_path)
            chromedriver_path = os.path.join(driver_dir, "chromedriver.exe")
            
            logger.info(f"Basisverzeichnis: {driver_dir}")
            logger.info(f"ChromeDriver-Pfad: {chromedriver_path}")
            
            # Prüfe, ob chromedriver.exe existiert
            if not os.path.exists(chromedriver_path):
                logger.warning(f"chromedriver.exe nicht gefunden unter {chromedriver_path}")
                # Suche in Unterverzeichnissen
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file.lower() == "chromedriver.exe":
                            chromedriver_path = os.path.join(root, file)
                            logger.info(f"chromedriver.exe gefunden: {chromedriver_path}")
                            break
            
            # Prüfe nochmal, ob der Pfad existiert
            if not os.path.exists(chromedriver_path):
                logger.error(f"chromedriver.exe konnte nicht gefunden werden!")
                return False
            
            # Service erstellen
            service = Service(chromedriver_path)
            
            logger.info("Chrome WebDriver erstellen...")
            logger.info(f"Chrome-Optionen: {chrome_options.arguments}")
            
            # Versuche mit angegebenem Timeout zu erstellen
            try:
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("WebDriver erfolgreich erstellt")
                
                # Versuche die Chrome-Version zu ermitteln
                browser_version = self.driver.capabilities.get('browserVersion', 'unbekannt')
                chromedriver_version = self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unbekannt')
                logger.info(f"Browser-Version: {browser_version}")
                logger.info(f"ChromeDriver-Version: {chromedriver_version}")
                
                # Teste Navigation
                self.driver.get("https://www.google.com")
                logger.info(f"Navigiert zu: {self.driver.title}")
                
                # Zusätzlicher Test: Navigation zur Polizei-Website
                logger.info("Navigiere zur Polizei-Website...")
                self.driver.get("https://portal.onlinewache.polizei.de/de/")
                logger.info(f"Navigiert zu: {self.driver.title}")
                time.sleep(5)  # Kurze Pause für manuelle Beobachtung
                
                # Schließe Browser
                self.driver.quit()
                logger.info("WebDriver erfolgreich geschlossen")
                return True
                
            except Exception as e:
                logger.error(f"Fehler beim Erstellen des WebDrivers: {str(e)}")
                traceback.print_exc()
                
                if self.driver:
                    try:
                        self.driver.quit()
                    except:
                        pass
                
                return False
                
        except Exception as e:
            logger.error(f"Fehler im Selenium-Test: {str(e)}")
            traceback.print_exc()
            return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Verwendung: python test_agent_auth.py <incident_id> <token> [api_host]")
        sys.exit(1)
    
    incident_id = sys.argv[1]
    token = sys.argv[2]
    api_host = sys.argv[3] if len(sys.argv) > 3 else "localhost:8002"
    
    tester = TestAgentAuth(incident_id, token, api_host)
    
    # Führe Tests aus
    auth_success = tester.test_auth()
    selenium_success = tester.test_selenium()
    
    print("\n=== TESTERGEBNISSE ===")
    print(f"Authentifizierung: {'ERFOLGREICH' if auth_success else 'FEHLGESCHLAGEN'}")
    print(f"Selenium: {'ERFOLGREICH' if selenium_success else 'FEHLGESCHLAGEN'}")
    print("======================")
    
    # Wenn beides erfolgreich, sollte der Agent eigentlich funktionieren!
    if auth_success and selenium_success:
        print("\nAlle Tests bestanden! Das Problem muss woanders liegen.")
    elif not auth_success:
        print("\nDas Authentifizierungsproblem muss zuerst gelöst werden.")
    elif not selenium_success:
        print("\nDas Selenium-Problem muss gelöst werden.")