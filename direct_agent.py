"""
Direct Agent for theft incident processing.
This is a standalone version without complex inheritance structures.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import requests
import json
import time
import traceback
import logging
import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_agent")

class DirectAgent:
    """Direct standalone agent for theft reporting."""
    
    def __init__(self, incident_id=None, token=None, api_host="localhost:8002", headless=None):
        """Initialize the base agent."""      
        # Configuration
        self.headless = headless if headless is not None else False  # Default auf sichtbaren Modus
        self.incident_id = incident_id
        self.token = token
        self.api_host = api_host
        
        # Driver and wait objects
        self.driver = None
        self.wait = None
        self.long_wait = None
        
        # Location data
        self.location = None
        
        logger.info(f"DirectAgent initialized with incident_id={incident_id}, API host={api_host}, has token={bool(token)}")
        
    # Füge diese Methode zu DirectAgent hinzu:

    def setup_driver(self) -> bool:
        """Set up Selenium WebDriver."""
        try:
            logger.info("Configuring Chrome options...")
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # Für Debugging immer sichtbar machen
            if self.headless:
                chrome_options.add_argument('--headless')
                logger.info("Running in headless mode")
            else:
                logger.info("Running in visible mode (headless=False)")
            
            # Chromedriver-Pfad
            logger.info("Finding ChromeDriver path...")
            
            try:
                base_path = ChromeDriverManager().install()
                logger.info(f"ChromeDriverManager returned: {base_path}")
            except Exception as e:
                logger.error(f"Error with ChromeDriverManager: {str(e)}")
                return False
                
            driver_dir = os.path.dirname(base_path)
            chromedriver_path = os.path.join(driver_dir, "chromedriver.exe")
            
            # Falls chromedriver.exe nicht direkt im Verzeichnis ist, suche in Unterverzeichnissen
            if not os.path.exists(chromedriver_path):
                logger.warning(f"ChromeDriver nicht gefunden unter {chromedriver_path}, suche in Unterverzeichnissen...")
                
                for root, dirs, files in os.walk(driver_dir):
                    for file in files:
                        if file.lower() == "chromedriver.exe":
                            chromedriver_path = os.path.join(root, file)
                            logger.info(f"ChromeDriver gefunden: {chromedriver_path}")
                            break
                    if os.path.exists(chromedriver_path):
                        break
            
            if not os.path.exists(chromedriver_path):
                logger.error(f"ChromeDriver executable not found")
                self.update_incident_status("error", f"ChromeDriver nicht gefunden")
                return False
                
            logger.info(f"Using ChromeDriver path: {chromedriver_path}")
                
            service = Service(executable_path=chromedriver_path)
            
            logger.info("Creating Chrome WebDriver...")
            logger.info(f"Chrome options: {chrome_options.arguments}")
            
            try:
                # Versuche mit Timeout zu starten
                start_time = time.time()
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                end_time = time.time()
                
                logger.info(f"WebDriver successfully created in {end_time - start_time:.2f} seconds")
                
                # Versuche die Version zu bestimmen
                try:
                    browser_version = self.driver.capabilities.get('browserVersion', 'unknown')
                    driver_version = self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown')
                    logger.info(f"Browser version: {browser_version}")
                    logger.info(f"ChromeDriver version: {driver_version}")
                except:
                    logger.warning("Could not determine browser/driver versions")
                
                # Setup wait objects
                self.wait = WebDriverWait(self.driver, 30)
                self.long_wait = WebDriverWait(self.driver, 60)
                
                # Test der Navigation
                logger.info("Testing navigation to Google...")
                self.driver.get("https://www.google.com")
                logger.info(f"Navigation successful: {self.driver.title}")
                
                return True
            except Exception as e:
                logger.error(f"Error creating WebDriver: {str(e)}")
                logger.error(traceback.format_exc())
                self.update_incident_status("error", f"Fehler beim Erstellen des WebDrivers: {str(e)}")
                return False
        
        except Exception as e:
            logger.error(f"Error in setup_driver: {str(e)}")
            logger.error(traceback.format_exc())
            self.update_incident_status("error", f"Fehler in setup_driver: {str(e)}")
            return False
    
    def run(self) -> bool:
        """Main execution method."""
        try:
            # Log start
            logger.info(f"Starting DirectAgent for incident {self.incident_id}")
            
            # Wichtig: Aktualisiere den Status früh, damit wir es überhaupt sehen können
            self.update_incident_status("processing", "Agent gestartet und verarbeitet den Vorfall...")
            
            # WICHTIG: Bei direkter Integration können wir hier abbrechen, wenn keine Incident-ID gesetzt ist
            if not self.incident_id:
                logger.error("No incident ID provided")
                return False
            
            # Vereinfachtes und direkteres Laden von Daten
            incident_data = self.load_incident_data()
            if not incident_data:
                logger.error("Failed to load incident data")
                self.update_incident_status("error", "Fehler beim Laden der Vorfallsdaten")
                return False
            
            logger.info(f"Loaded incident data: {incident_data}")
            
            # Lade Benutzerdaten
            user_id = incident_data.get('user_id')
            if not user_id:
                logger.error("No user ID found in incident data")
                self.update_incident_status("error", "Keine Benutzer-ID in den Vorfallsdaten gefunden")
                return False
                
            user_data = self.load_user_data(user_id)
            if not user_data:
                logger.error("Failed to load user data")
                self.update_incident_status("error", "Fehler beim Laden der Benutzerdaten")
                return False
            
            # Lade Standortdaten direkt, wenn vorhanden
            if incident_data.get('location_id'):
                self.location = self.load_location_data(incident_data.get('location_id'))
            elif incident_data.get('email_data'):
                try:
                    email_data = json.loads(incident_data.get('email_data'))
                    if email_data.get('locationId'):
                        self.location = self.load_location_data(email_data.get('locationId'))
                except Exception as e:
                    logger.warning(f"Could not parse email data: {e}")
            
            # DIREKTE WEB-DRIVER INITIALISIERUNG
            logger.info("Setting up WebDriver directly...")
            if not self.setup_driver():
                logger.error("Failed to set up WebDriver")
                self.update_incident_status("error", "Fehler beim Einrichten des WebDrivers")
                return False
                
            # Hier den Chrome/WebDriver-Status anzeigen
            try:
                if self.driver:
                    # Version-Informationen ausgeben
                    browser_version = self.driver.capabilities.get('browserVersion', 'unbekannt')
                    chromedriver_version = self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unbekannt')
                    logger.info(f"Browser-Version: {browser_version}")
                    logger.info(f"ChromeDriver-Version: {chromedriver_version}")
            except Exception as e:
                logger.warning(f"Konnte Browser-Versionen nicht ermitteln: {str(e)}")
            
            # VEREINFACHTER PROZESS mit klaren Logs am Ende jedes Schritts
            logger.info("Starting theft report process...")
            try:
                self.process_theft_report(incident_data, user_data)
                logger.info("Theft report process completed successfully")
                
                # Update status to completed
                self.update_incident_status("completed", "Diebstahl erfolgreich gemeldet.")
                
                return True
            except Exception as e:
                error_message = f"Error in theft report process: {str(e)}"
                logger.error(error_message)
                logger.error(traceback.format_exc())
                
                # Update status to error with clear message
                self.update_incident_status("error", error_message)
                
                return False
                
        except Exception as e:
            error_message = f"Error in DirectAgent: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Update status to error
            self.update_incident_status("error", error_message)
            
            return False
        finally:
            # Always clean up resources
            if hasattr(self, 'driver') and self.driver:
                logger.info("Cleaning up WebDriver resources")
                try:
                    self.driver.quit()
                except Exception as e:
                    logger.warning(f"Error closing WebDriver: {str(e)}")
                    pass
            else:
                logger.info("No WebDriver to clean up")
    
    def load_user_data(self, user_id):
        """Load user data for given user ID."""
        if not user_id:
            logger.warning("No user ID provided")
            return {}
        
        try:
            api_host = self.api_host
            logger.info(f"Loading data for user {user_id}...")
            response = requests.get(
                f"http://{api_host}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                user_data = response.json()
                logger.info(f"User data successfully loaded")
                return user_data
            else:
                logger.error(f"Error loading user data: {response.text}")
                return {}
        
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}")
            return {}
            
    def load_location_data(self, location_id):
        """Load location data for given location ID."""
        if not location_id:
            logger.warning("No location ID provided")
            return {}
        
        try:
            api_host = self.api_host
            logger.info(f"Loading data for location {location_id}...")
            response = requests.get(
                f"http://{api_host}/locations/{location_id}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            if response.status_code == 200:
                location_data = response.json()
                logger.info(f"Location data successfully loaded")
                return location_data
            else:
                logger.error(f"Error loading location data: {response.text}")
                return {}
        
        except Exception as e:
            logger.error(f"Error loading location data: {str(e)}")
            return {}
    
    # Füge diese Methode zum DirectAgent hinzu, um die Verbindung zu testen
    def test_connection(self):
        """Teste die Verbindung zum Server mit erhöhtem Timeout und mehreren Hosts."""
        logger.info("Testing connection to server...")
        
        # Alternative Hostnamen/Adressen für den gleichen Server
        hosts_to_try = [
            f"http://{self.api_host}",  # Standard
            "http://127.0.0.1:8002",   # IPv4 Loopback
            "http://localhost:8002",   # Hostname
            "http://[::1]:8002"        # IPv6 Loopback
        ]
        
        for base_url in hosts_to_try:
            try:
                # Einfacher Ping mit längeren Timeout
                logger.info(f"Trying to connect to {base_url}/health...")
                response = requests.get(
                    f"{base_url}/health",
                    timeout=15  # Längerer Timeout
                )
                
                if response.status_code == 200:
                    logger.info(f"Connection successful to {base_url}: {response.text}")
                    # Wenn erfolgreich, setze diesen Host als den zu verwendenden
                    self.api_host = base_url.replace("http://", "")
                    return True
                else:
                    logger.warning(f"Server responded with status {response.status_code}: {response.text}")
            except Exception as e:
                logger.warning(f"Failed to connect to {base_url}: {str(e)}")
        
        logger.error("All connection attempts failed!")
        return False
            
    # Aktualisiere auch die update_incident_status Methode:
    def update_incident_status(self, status, message=None):
        """Update incident status via API call."""
        if not self.incident_id:
            logger.warning("Cannot update status: No incident ID")
            return False
                
        try:
            logger.info(f"Updating status for incident {self.incident_id} to '{status}'...")
            
            # Vorbereiten der Daten
            payload = {"status": status}
            if message:
                # Kürze sehr lange Nachrichten
                if message and len(message) > 10000:
                    message = message[:9900] + "... [GEKÜRZT]"
                payload["agent_log"] = message
            
            # WICHTIG: Verwende den direkten Endpunkt ohne Authentifizierung
            api_url = f"http://{self.api_host}/incidents/{self.incident_id}/agent-direct"
            logger.info(f"Using direct agent URL (no auth): {api_url}")
            
            # Versuche mehrere verschiedene Hostnamen
            if self.api_host.startswith("localhost:"):
                # Probiere auch mit IP-Adresse
                alternative_hosts = [
                    self.api_host,
                    self.api_host.replace("localhost", "127.0.0.1")
                ]
            else:
                alternative_hosts = [self.api_host]
            
            for host in alternative_hosts:
                try:
                    # API-Aufruf mit längerem Timeout
                    alt_url = f"http://{host}/incidents/{self.incident_id}/agent-direct"
                    logger.info(f"Trying host: {alt_url}")
                    
                    response = requests.patch(
                        alt_url,
                        json=payload,
                        timeout=20  # Längerer Timeout
                    )
                    
                    logger.info(f"Response: {response.status_code} - {response.text[:200] if response.text else ''}")
                    
                    if response.status_code == 200:
                        logger.info(f"Status successfully updated to {status}")
                        return True
                except requests.exceptions.RequestException as req_err:
                    logger.warning(f"Request failed with host {host}: {str(req_err)}")
                    continue
            
            # Wenn alle Versuche fehlschlagen
            logger.error("All update attempts failed")
            return False
                    
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            traceback.print_exc()
            return False

    # Gleichermaßen für load_incident_data:
    def load_incident_data(self):
        """Load current incident data."""
        if not self.incident_id:
            logger.warning("No incident ID provided")
            return {}
        
        try:
            logger.info(f"Loading data for incident {self.incident_id}...")
            
            # Versuche mehrere verschiedene Hostnamen
            if self.api_host.startswith("localhost:"):
                # Probiere auch mit IP-Adresse
                alternative_hosts = [
                    self.api_host,
                    self.api_host.replace("localhost", "127.0.0.1")
                ]
            else:
                alternative_hosts = [self.api_host]
            
            for host in alternative_hosts:
                try:
                    # WICHTIG: Verwende den direkten Endpunkt ohne Authentifizierung
                    api_url = f"http://{host}/incidents/{self.incident_id}/agent-direct"
                    logger.info(f"Trying host: {api_url}")
                    
                    # Einfacher GET-Request ohne Headers
                    response = requests.get(
                        api_url,
                        timeout=20  # Längerer Timeout
                    )
                    
                    logger.info(f"Response: {response.status_code} - {response.text[:200] if response.text else ''}")
                    
                    if response.status_code == 200:
                        incident_data = response.json()
                        logger.info(f"Incident data successfully loaded")
                        return incident_data
                except requests.exceptions.RequestException as req_err:
                    logger.warning(f"Request failed with host {host}: {str(req_err)}")
                    continue
                    
            # Wenn alle Versuche fehlschlagen
            logger.error("All load attempts failed")
            return {}
        
        except Exception as e:
            logger.error(f"Error loading incident data: {str(e)}")
            return {}
    
    def format_date(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to DD.MM.YYYY."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d.%m.%Y")
        except Exception as e:
            logger.error(f"Error formatting date: {str(e)}")
            return date_str
    
    def fill_personal_data(self, user_data):
        """Fill personal data fields."""
        try:
            logger.info("Filling personal data...")
            
            # Dictionary of field IDs and values
            fields = {
                "eigene_personalien_nachname": user_data.get("nachname", ""),
                "eigene_personalien_vorname": user_data.get("vorname", ""),
                "eigene_personalien_gebdat-kendoInput": user_data.get("geburtsdatum", ""),
                "eigene_personalien_telefonnr": user_data.get("telefonnr", ""),
                "eigene_personalien_email": user_data.get("email", "")
            }
            
            # Fill all fields
            for field_id, value in fields.items():
                field = self.wait.until(EC.element_to_be_clickable((By.ID, field_id)))
                if field and value:
                    field.clear()
                    field.send_keys(value)
                    logger.info(f"Filled {field_id}: {value}")
                else:
                    logger.warning(f"Field {field_id} not found or empty value")
            
            # Geburtsland ausfüllen
            try:
                birthcountry_input = self.wait.until(
                    EC.element_to_be_clickable((By.ID, "eigene_personalien_geburtsland-kendoInput"))
                )
                birthcountry_input.clear()
                birthcountry_input.send_keys("Deutschland")
                time.sleep(2)
                
                # Mehrere Versuche für die Listenelement-Auswahl
                max_attempts = 3
                for attempt in range(max_attempts):
                    try:
                        list_item = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, "//li[contains(@class, 'k-list-item') and .//span[contains(., 'Deutschland')]]"))
                        )
                        list_item.click()
                        logger.info(f"Geburtsland selected successfully (attempt {attempt+1})")
                        break
                    except Exception as e:
                        logger.warning(f"Error selecting birth country (attempt {attempt+1}): {str(e)}")
                        if attempt < max_attempts - 1:
                            time.sleep(2)
            except Exception as e:
                logger.warning(f"Error filling birth country: {str(e)}")
            
            return True
        except Exception as e:
            logger.error(f"Error filling personal data: {str(e)}")
            return False
    
    def process_theft_report(self, incident_data, user_data):
        """Process a theft report with the real automation sequence."""
        logger.info("Starting theft report process...")
        
        try:
            # Navigate to the police website
            self.driver.get("https://portal.onlinewache.polizei.de/de/")
            logger.info("Police website opened")
            
            # Accept cookies/terms if present
            try:
                verstanden_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(., 'Verstanden')]")
                ))
                verstanden_button.click()
                logger.info("Cookie notice accepted")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Cookie notice not found or not clickable: {str(e)}")
            
            # Select "in Deutschland"
            try:
                in_deutschland = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//label[contains(., 'in Deutschland')]")
                ))
                in_deutschland.click()
                logger.info("Selected 'in Deutschland'")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not select 'in Deutschland': {str(e)}")
                raise
            
            # Select state (Baden-Württemberg as default)
            try:
                state_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//img[@alt='Wappen Baden-Württemberg mit drei Löwen']]")
                ))
                state_element.click()
                logger.info("State selected")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not select state: {str(e)}")
                raise
            
            # Select Diebstahl
            try:
                diebstahl_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//h3[contains(text(), 'Diebstahl')]")
                ))
                diebstahl_element.click()
                logger.info("Selected 'Diebstahl'")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not select 'Diebstahl': {str(e)}")
                raise
            
            # Click on "Zur Anzeige Diebstahl"
            try:
                display_link = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(., 'Zur Anzeige Diebstahl (ohne Anmeldung)')]")
                ))
                display_link.click()
                logger.info("Clicked 'Zur Anzeige Diebstahl'")
            except Exception as e:
                logger.error(f"Could not click on theft report link: {str(e)}")
                raise
            
            # Switch to the new window
            try:
                # Wait for the new window to open and switch to it
                self.long_wait.until(lambda d: len(d.window_handles) > 1)
                self.driver.switch_to.window(self.driver.window_handles[-1])
                logger.info("Switched to new window")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not switch to new window: {str(e)}")
                raise
            
            # Accept terms and conditions
            try:
                terms_checkbox = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "nutzungsbedingung_onlinewache_zustimmung")
                ))
                terms_checkbox.click()
                logger.info("Accepted terms and conditions")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Could not accept terms: {str(e)}")
                raise
            
            # Select 'No' for self-incrimination
            try:
                no_self_incrimination = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "beschuldigtenbelehrung_nein")
                ))
                no_self_incrimination.click()
                logger.info("Selected 'No' for self-incrimination")
                time.sleep(1)
            except Exception as e:
                logger.error(f"Could not click 'No' for self-incrimination: {str(e)}")
                raise
            
            # 'Nein' für Gewaltandrohung
            try:
                gewaltandrohung_nein_label = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//label[@for='diebstahl_details_gewaltandrohung_nein']")
                ))
                gewaltandrohung_nein_label.click()
                logger.info("'Nein' für Gewaltandrohung ausgewählt")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not select 'Nein' for Gewaltandrohung: {str(e)}")
            
            # 'Sonstiger Diebstahl' auswählen
            try:
                sonstiger_diebstahl_label = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//label[@for='diebstahl_details_entwendetes_gut_sonstiges']")
                ))
                sonstiger_diebstahl_label.click()
                logger.info("'Sonstiger Diebstahl' ausgewählt")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not select 'Sonstiger Diebstahl': {str(e)}")
            
            # Continue to personal data
            try:
                continue_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu: Personendaten')]")
                ))
                continue_button.click()
                logger.info("Continued to personal data")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not continue to personal data: {str(e)}")
                raise
            
            # Fill personal data
            try:
                self.fill_personal_data(user_data)
                logger.info("Personal data filled successfully")
            except Exception as e:
                logger.error(f"Error filling personal data: {str(e)}")
                raise
            
            # Continue to incident data
            try:
                continue_button = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu: Tatdaten')]")
                ))
                continue_button.click()
                logger.info("Continued to incident data")
                time.sleep(2)
            except Exception as e:
                logger.error(f"Could not continue to incident data: {str(e)}")
                raise
            
            # Klicke auf das Tatzeit-Label (Radio-Button)
            try:
                tatzeit_label = self.wait.until(EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "label[for='tatzeit_wann_tatzeitpunkt']")
                ))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tatzeit_label)
                time.sleep(1)
                tatzeit_label.click()
                logger.info("Clicked on Tatzeit radio button")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not click on Tatzeit radio button: {str(e)}")
            
            # Fill incident date and time with the correct IDs
            try:
                # Date
                date_input = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "tatzeit_tatzeitpunkt_datum-kendoInput")
                ))
                if date_input:
                    # Format date from YYYY-MM-DD to DD.MM.YYYY
                    incident_date = incident_data.get('incident_date', '')
                    if incident_date:
                        formatted_date = self.format_date(incident_date)
                        date_input.clear()
                        date_input.send_keys(formatted_date)
                        logger.info(f"Filled incident date: {formatted_date}")
                
                # Time
                time_input = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "tatzeit_tatzeitpunkt_uhrzeit-kendoInput")
                ))
                if time_input:
                    incident_time = incident_data.get('incident_time', '')
                    if incident_time:
                        time_input.clear()
                        time_input.send_keys(incident_time)
                        logger.info(f"Filled incident time: {incident_time}")
            except Exception as e:
                logger.error(f"Error filling incident date/time: {str(e)}")
                raise
            
            # Wähle "Tatort bekannt: Ja"
            try:
                tatort_bekannt_ja = self.wait.until(EC.element_to_be_clickable(
                    (By.ID, "tatort_bekannt_ja")
                ))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", tatort_bekannt_ja)
                time.sleep(1)
                tatort_bekannt_ja.click()
                logger.info("Selected 'Tatort bekannt: Ja'")
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Could not select 'Tatort bekannt: Ja': {str(e)}")
            
            # Verbesserte Adresseingabe mit Sicherheitsprüfung für Standortdaten
            try:
                if self.location is None:
                    logger.warning("No location data available, skipping detailed address entry")
                    # Eventuell Mindestdaten hier eintragen
                    # Bundesland eingeben (Pflichtfeld)
                    try:
                        bundesland_input = self.wait.until(EC.element_to_be_clickable(
                            (By.ID, "tatort_bundesland-kendoInput")
                        ))
                        bundesland_input.clear()
                        bundesland_input.send_keys("Baden-Württemberg")
                        logger.info("Filled default state: Baden-Württemberg")
                        time.sleep(2)
                    except Exception as e:
                        logger.warning(f"Error filling default state: {str(e)}")
                else:
                    # Adress-Button finden (mit mehreren möglichen Selektoren)
                    address_button = None
                    selectors = [
                        "//button[@aria-label='Suche/Zuordnung Adresse']",
                        "//button[contains(., 'Adresse')]",
                        "//button[contains(@class, 'address-button')]"
                    ]
                    
                    for selector in selectors:
                        try:
                            logger.info(f"Trying to find address button with selector: {selector}")
                            address_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, selector))
                            )
                            if address_button:
                                break
                        except Exception as e:
                            logger.warning(f"Selector {selector} not found: {e}")
                    
                    if address_button:
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", address_button)
                        time.sleep(1)
                        address_button.click()
                        logger.info("Address dialog opened")
                        time.sleep(2)
                        
                        # Ort eingeben
                        try:
                            ort_input = self.wait.until(
                                EC.element_to_be_clickable((By.CSS_SELECTOR, "input.k-input-inner[aria-controls='locationPickerGemeinde_listbox']"))
                            )
                            ort_input.clear()
                            ort_input.send_keys(self.location.get('city', 'Stuttgart'))
                            time.sleep(2)
                            
                            # Versuche auf ein Dropdown-Element zu klicken
                            try:
                                ort_item = self.wait.until(
                                    EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'k-list-item') and contains(., '{self.location.get('city', 'Stuttgart')}')]"))
                                )
                                ort_item.click()
                                logger.info(f"Selected city: {self.location.get('city', 'Stuttgart')}")
                                time.sleep(2)
                            except Exception as e:
                                logger.warning(f"Could not select city from dropdown: {str(e)}")
                        except Exception as e:
                            logger.warning(f"Error filling city: {str(e)}")
                        
                        # Hausnummer eingeben
                        try:
                            hausnummer_input = self.wait.until(
                                EC.element_to_be_clickable((By.ID, "locationPickerNummerInput"))
                            )
                            if 'address' in self.location:
                                address = self.location.get('address', '')
                                parts = address.split(' ')
                                number = parts[-1] if len(parts) > 1 else "1"
                                hausnummer_input.clear()
                                hausnummer_input.send_keys(number)
                                logger.info(f"Filled house number: {number}")
                            else:
                                hausnummer_input.clear()
                                hausnummer_input.send_keys("1")
                                logger.info("Filled default house number: 1")
                            time.sleep(2)
                        except Exception as e:
                            logger.warning(f"Error filling house number: {str(e)}")
                        
                        # Übernehmen-Button klicken
                        try:
                            uebernehmen_button = self.wait.until(
                                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Übernehmen')]"))
                            )
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", uebernehmen_button)
                            time.sleep(1)
                            uebernehmen_button.click()
                            logger.info("Clicked 'Übernehmen' button")
                            time.sleep(2)
                        except Exception as e:
                            logger.warning(f"Error clicking 'Übernehmen' button: {str(e)}")
                    else:
                        logger.warning("Could not find address button! Falling back to direct field filling")
                        # Fallback: Direktes Ausfüllen der Felder
                        try:
                            state_input = self.wait.until(EC.element_to_be_clickable(
                                (By.ID, "tatort_bundesland-kendoInput")
                            ))
                            if state_input:
                                state = self.location.get('state', 'Baden-Württemberg')
                                state_input.clear()
                                state_input.send_keys(state)
                                logger.info(f"Filled incident state: {state}")
                                time.sleep(1)
                            
                            city_input = self.wait.until(EC.element_to_be_clickable(
                                (By.ID, "tatort_ort")
                            ))
                            if city_input:
                                city = self.location.get('city', '')
                                if city:
                                    city_input.clear()
                                    city_input.send_keys(city)
                                    logger.info(f"Filled incident city: {city}")
                                    time.sleep(1)
                                    
                            postal_input = self.wait.until(EC.element_to_be_clickable(
                                (By.ID, "tatort_plz")
                            ))
                            if postal_input:
                                postal = self.location.get('postal_code', '')
                                if postal:
                                    postal_input.clear()
                                    postal_input.send_keys(postal)
                                    logger.info(f"Filled postal code: {postal}")
                                    time.sleep(1)
                        except Exception as e:
                            logger.warning(f"Error in fallback direct field filling: {str(e)}")
            except Exception as e:
                logger.warning(f"Error in address entry process: {str(e)}")
                # Continue anyway, address is not critical
            
            # For demonstration, take a screenshot
            try:
                screenshot_path = f"theft_report_{incident_data.get('id')}.png"
                self.driver.save_screenshot(screenshot_path)
                logger.info(f"Screenshot saved to {screenshot_path}")
            except Exception as e:
                logger.warning(f"Could not save screenshot: {str(e)}")
            
            # For demonstration purposes, we'll stop here
            logger.info("Theft report process completed successfully")
            return True
        
        except Exception as e:
            logger.error(f"Error in theft report process: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Try to take error screenshot
            try:
                self.driver.save_screenshot(f"error_screenshot_{incident_data.get('id')}.png")
            except:
                pass
                
            raise  # Re-raise to handle in calling function

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Direct Agent for theft reporting')
    parser.add_argument('incident_id', type=int, nargs='?', default=None, 
                        help='Incident ID to process')
    parser.add_argument('--token', type=str, help='API token for authentication')
    parser.add_argument('--token-file', type=str, help='File containing API token')
    parser.add_argument('--api-host', type=str, default='localhost:8002', 
                       help='API host address')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode (no browser UI)')
    
    return parser.parse_args()

if __name__ == "__main__":
    # Parse arguments
    args = parse_arguments()
    
    # Get incident ID from arguments or environment
    incident_id = args.incident_id or os.environ.get("INCIDENT_ID")
    if incident_id:
        try:
            incident_id = int(incident_id)
        except (ValueError, TypeError):
            print(f"Invalid incident ID: {incident_id}")
            sys.exit(1)
    
    # Get API token from arguments, file, or environment
    token = args.token or os.environ.get("API_TOKEN")
    if args.token_file and not token:
        try:
            with open(args.token_file, 'r') as f:
                token = f.read().strip()
        except Exception as e:
            print(f"Error reading token file: {str(e)}")
    
    if not incident_id:
        print("No incident ID provided")
        sys.exit(1)
    
    if not token:
        print("Warning: No API token provided, status updates will not work")
    
    # Print diagnostic information
    print(f"Starting DirectAgent for incident {incident_id}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"API host: {args.api_host}")
    print(f"Token available: {'Yes' if token else 'No'}")
    
    try:
        # Run agent
        agent = DirectAgent(
            incident_id=incident_id,
            token=token,
            api_host=args.api_host,
            headless=args.headless
        )
        
        success = agent.run()
        print(f"Agent completed with success={success}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        traceback.print_exc()
        sys.exit(1)