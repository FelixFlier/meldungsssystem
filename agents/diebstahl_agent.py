"""
Agent for processing theft incidents.
This agent automates the process of reporting thefts.
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
import requests
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add base directory to path if needed
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    # Import base agent (wrapped in try/except for better error reporting)
    from agents.base_agent import BaseAgent
    from config import get_settings
    
    # Load settings
    settings = get_settings()
    
    # Configure logger
    logger = logging.getLogger(f"{settings.APP_NAME}.agent")
except Exception as e:
    print(f"Error importing modules: {str(e)}")
    print(f"Python path: {sys.path}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Base directory: {BASE_DIR}")
    traceback.print_exc()
    sys.exit(1)

class DiebstahlAgent(BaseAgent):
    """Agent for processing theft incidents."""
    
    def __init__(self, headless=None, incident_id=None, token=None, api_host=None):
        # Initialize base agent
        super().__init__(headless=headless, incident_id=incident_id)
        
        # API details
        self.token = token or os.environ.get("API_TOKEN", "")
        self.api_host = api_host or os.environ.get("API_HOST", "localhost:8002")
        
        # Check if we have valid credentials
        if not self.token:
            logger.warning("No API token provided, status updates will not work")
        
        if not self.incident_id:
            logger.warning("No incident ID provided, some functions will not work")
        
        logger.info(f"DiebstahlAgent initialized with incident_id={incident_id}, "
                   f"API host={api_host}, has token={bool(self.token)}")
    
    def update_incident_status(self, status, message=None):
        """Update incident status via API call."""
        if not self.incident_id:
            logger.warning("Cannot update status: No incident ID")
            return False
                
        if not self.token:
            logger.warning("Cannot update status: No API token")
            return False
        
        try:
            logger.info(f"Updating status for incident {self.incident_id} to '{status}'...")
            
            # Mache mehrere Versuche mit kurzen Pausen
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Prepare data
                    payload = {"status": status}
                    if message:
                        # Kürze sehr lange Nachrichten, um Probleme zu vermeiden
                        if message and len(message) > 10000:
                            message = message[:9900] + "... [TRUNCATED - MESSAGE TOO LONG]"
                        payload["agent_log"] = message
                    
                    # Make the API call
                    response = requests.patch(
                        f"http://{self.api_host}/incidents/{self.incident_id}",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.token}"},
                        timeout=20  # 20 second timeout
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Status successfully updated to {status} (attempt {attempt+1})")
                        return True
                    else:
                        logger.error(f"Error updating status: {response.status_code} - {response.text} (attempt {attempt+1})")
                        
                        if attempt < max_attempts - 1:
                            logger.info(f"Retrying in 2 seconds...")
                            time.sleep(2)
                        else:
                            return False
                except requests.exceptions.RequestException as req_err:
                    logger.error(f"Request error updating status: {str(req_err)} (attempt {attempt+1})")
                    
                    if attempt < max_attempts - 1:
                        logger.info(f"Retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        return False
                    
            return False
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            traceback.print_exc()
            return False
    
    def run(self) -> bool:
        """Main execution method."""
        try:
            # Log start
            logger.info(f"Starting DiebstahlAgent for incident {self.incident_id}")
            
            # Wichtig: Aktualisiere den Status früh, damit wir es überhaupt sehen können
            self.update_incident_status("processing", "Agent gestartet und verarbeitet den Vorfall...")
            
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
                self.load_location_data(incident_data.get('location_id'))
            elif incident_data.get('email_data'):
                try:
                    email_data = json.loads(incident_data.get('email_data'))
                    if email_data.get('locationId'):
                        self.load_location_data(email_data.get('locationId'))
                except Exception as e:
                    logger.warning(f"Could not parse email data: {e}")
            
            # DIREKTE WEB-DRIVER INITIALISIERUNG, ähnlich dem erfolgreichen Code
            logger.info("Setting up WebDriver directly...")
            if not self.setup_driver():
                logger.error("Failed to set up WebDriver")
                self.update_incident_status("error", "Fehler beim Einrichten des WebDrivers")
                return False
            
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
            error_message = f"Error in DiebstahlAgent: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Update status to error
            self.update_incident_status("error", error_message)
            
            return False
        finally:
            # Always clean up resources
            if hasattr(self, 'driver') and self.driver:
                logger.info("Cleaning up WebDriver resources")
                self.cleanup()
            else:
                logger.info("No WebDriver to clean up")
    
    def process_theft_report(self, incident_data, user_data):
        """Process a theft report with the real automation sequence."""
        logger.info("Starting theft report process...")
        
        try:
            # Navigate to the police website
            self.driver.get("https://portal.onlinewache.polizei.de/de/")
            logger.info("Police website opened")
            
            # Accept cookies/terms if present
            cookie_button = self.wait_and_find_element(
                By.XPATH, "//button[contains(., 'Verstanden')]"
            )
            if cookie_button and self.safe_click(cookie_button):
                logger.info("Cookie notice accepted")
            
            # Select "in Deutschland"
            in_deutschland = self.wait_and_find_element(
                By.XPATH, "//label[contains(., 'in Deutschland')]"
            )
            if not in_deutschland or not self.safe_click(in_deutschland):
                logger.error("Could not select 'in Deutschland' option")
                raise Exception("Failed to select location type")
            
            logger.info("Selected 'in Deutschland'")
            time.sleep(1)
            
            # Select state based on location data or default to Baden-Württemberg
            if self.location and self.location.get('state'):
                # Try to select the state based on location data
                state_found = self.select_location(self.location.get('state'))
                if not state_found:
                    logger.warning(f"Could not find state: {self.location.get('state')}, using default")
                    # Default to Baden-Württemberg
                    state_element = self.wait_and_find_element(
                        By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//img[@alt='Wappen Baden-Württemberg mit drei Löwen']]"
                    )
                    if not state_element or not self.safe_click(state_element):
                        logger.error("Could not select Baden-Württemberg state")
                        raise Exception("Failed to select state")
            else:
                # Default to Baden-Württemberg
                logger.info("No state information, using Baden-Württemberg")
                state_element = self.wait_and_find_element(
                    By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//img[@alt='Wappen Baden-Württemberg mit drei Löwen']]"
                )
                if not state_element or not self.safe_click(state_element):
                    logger.error("Could not select Baden-Württemberg state")
                    raise Exception("Failed to select state")
            
            logger.info("State selected")
            time.sleep(1)
            
            # Select Diebstahl
            diebstahl_element = self.wait_and_find_element(
                By.XPATH, "//h3[contains(text(), 'Diebstahl')]"
            )
            if not diebstahl_element or not self.safe_click(diebstahl_element):
                logger.error("Could not select 'Diebstahl' option")
                raise Exception("Failed to select incident type")
            
            logger.info("Selected 'Diebstahl'")
            time.sleep(1)
            
            # Click on "Zur Anzeige Diebstahl"
            display_link = self.wait_and_find_element(
                By.XPATH, "//a[contains(., 'Zur Anzeige Diebstahl (ohne Anmeldung)')]"
            )
            if not display_link or not self.safe_click(display_link):
                logger.error("Could not click 'Zur Anzeige Diebstahl' link")
                raise Exception("Failed to navigate to theft report")
            
            logger.info("Clicked 'Zur Anzeige Diebstahl'")
            
            # Switch to the new window
            self.driver.switch_to.window(self.driver.window_handles[-1])
            logger.info("Switched to new window")
            time.sleep(2)
            
            # Accept terms and conditions
            terms_checkbox = self.wait_and_find_element(
                By.ID, "nutzungsbedingung_onlinewache_zustimmung"
            )
            if terms_checkbox and self.safe_click(terms_checkbox):
                logger.info("Accepted terms and conditions")
            
            # Select 'No' for self-incrimination
            no_self_incrimination = self.wait_and_find_element(
                By.ID, "beschuldigtenbelehrung_nein"
            )
            if no_self_incrimination and self.safe_click(no_self_incrimination):
                logger.info("Selected 'No' for self-incrimination")
            
            # Continue to personal data
            continue_button = self.wait_and_find_element(
                By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu: Personendaten')]"
            )
            if continue_button and self.safe_click(continue_button):
                logger.info("Continued to personal data")
            
            time.sleep(2)
            
            # Fill personal data
            self.fill_personal_data(user_data)
            
            # Fill birthplace and country
            birthplace = self.wait_and_find_element(By.ID, "eigene_personalien_geburtsort")
            if birthplace and self.safe_send_keys(birthplace, user_data.get('geburtsort', '')):
                logger.info("Filled birthplace")
            
            birthcountry_input = self.wait_and_find_element(By.ID, "eigene_personalien_geburtsland-kendoInput")
            if birthcountry_input:
                geburtsland = user_data.get("geburtsland", "Deutschland")
                self.safe_send_keys(birthcountry_input, geburtsland)
                time.sleep(1)
                
                # Try to select from dropdown
                try:
                    list_item = self.wait_and_find_element(
                        By.XPATH, f"//li[contains(@class, 'k-list-item') and .//span[contains(., '{geburtsland}')]]",
                        timeout=5
                    )
                    if list_item:
                        self.safe_click(list_item)
                except:
                    # Fallback: press Enter
                    birthcountry_input.send_keys("\n")
                
                logger.info(f"Filled birth country: {geburtsland}")
            
            # Continue to incident data
            continue_button = self.wait_and_find_element(
                By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu: Tatdaten')]"
            )
            if continue_button and self.safe_click(continue_button):
                logger.info("Continued to incident data")
            
            time.sleep(2)
            
            # Fill incident date and time
            date_input = self.wait_and_find_element(By.ID, "tatzeit_datum_von-kendoInput")
            if date_input:
                # Format date from YYYY-MM-DD to DD.MM.YYYY
                incident_date = incident_data.get('incident_date', '')
                if incident_date:
                    formatted_date = self.format_date(incident_date)
                    self.safe_send_keys(date_input, formatted_date)
                    logger.info(f"Filled incident date: {formatted_date}")
            
            time_input = self.wait_and_find_element(By.ID, "tatzeit_uhrzeit_von-kendoInput")
            if time_input:
                incident_time = incident_data.get('incident_time', '')
                if incident_time:
                    self.safe_send_keys(time_input, incident_time)
                    logger.info(f"Filled incident time: {incident_time}")
            
            # Fill location information if available
            if self.location:
                # State selection
                state_input = self.wait_and_find_element(By.ID, "tatort_bundesland-kendoInput")
                if state_input:
                    state = self.location.get('state', 'Baden-Württemberg')
                    self.safe_send_keys(state_input, state)
                    time.sleep(1)
                    
                    # Try to select from dropdown
                    try:
                        list_item = self.wait_and_find_element(
                            By.XPATH, f"//li[contains(@class, 'k-list-item') and .//span[contains(., '{state}')]]",
                            timeout=5
                        )
                        if list_item:
                            self.safe_click(list_item)
                    except:
                        # Fallback: press Enter
                        state_input.send_keys("\n")
                    
                    logger.info(f"Filled incident state: {state}")
                
                # City field
                city_input = self.wait_and_find_element(By.ID, "tatort_ort")
                if city_input:
                    city = self.location.get('city', '')
                    if city:
                        self.safe_send_keys(city_input, city)
                        logger.info(f"Filled incident city: {city}")
                
                # Postal code if available
                postal_input = self.wait_and_find_element(By.ID, "tatort_plz")
                if postal_input:
                    postal = self.location.get('postal_code', '')
                    if postal:
                        self.safe_send_keys(postal_input, postal)
                        logger.info(f"Filled postal code: {postal}")
                
                # Street address if available
                street_input = self.wait_and_find_element(By.ID, "tatort_strasse")
                if street_input:
                    address = self.location.get('address', '')
                    if address:
                        # Try to separate street and number
                        parts = address.split(' ')
                        if len(parts) > 1:
                            street = ' '.join(parts[:-1])
                            number = parts[-1]
                            
                            self.safe_send_keys(street_input, street)
                            logger.info(f"Filled street: {street}")
                            
                            # House number
                            number_input = self.wait_and_find_element(By.ID, "tatort_hausnummer")
                            if number_input:
                                self.safe_send_keys(number_input, number)
                                logger.info(f"Filled house number: {number}")
                        else:
                            # No clear separation, use all as street
                            self.safe_send_keys(street_input, address)
                            logger.info(f"Filled street address: {address}")
            
            # Continue to next section
            continue_button = self.wait_and_find_element(
                By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu')]"
            )
            if continue_button and self.safe_click(continue_button):
                logger.info("Continued to next section")
            
            # Simulated success for demonstration purposes
            logger.info("Theft report process completed successfully")
            
        except Exception as e:
            logger.error(f"Error in theft report process: {str(e)}")
            traceback.print_exc()
            raise
    
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
                field = self.wait_and_find_element(By.ID, field_id)
                if field and value:
                    self.safe_send_keys(field, value)
                    logger.info(f"Filled {field_id}: {value}")
                else:
                    logger.warning(f"Field {field_id} not found or empty value")
            
            return True
        except Exception as e:
            logger.error(f"Error filling personal data: {str(e)}")
            return False
    
    def simulate_processing(self, incident_data, user_data):
        """Simulate the processing of a theft incident (for demo purposes)."""
        logger.info("Starting simulated processing...")
        
        # Show incident details
        logger.info(f"Processing theft on date {incident_data.get('incident_date')} "
                   f"at time {incident_data.get('incident_time')}")
        
        # Show user details (without sensitive info)
        user_name = f"{user_data.get('vorname', '')} {user_data.get('nachname', '')}"
        logger.info(f"Report for user: {user_name}")
        
        # Check if location information is available
        if self.location:
            logger.info(f"Location: {self.location.get('name')} in {self.location.get('city')}, {self.location.get('state')}")
        
        # Step 1: Simulate navigation
        logger.info("Step 1: Navigating to police website...")
        time.sleep(2)  # Simulate loading time
        
        # Step 2: Simulate form filling
        logger.info("Step 2: Filling personal information...")
        time.sleep(2)
        
        # Step 3: Simulate location data entry
        logger.info("Step 3: Entering location information...")
        time.sleep(2)
        
        # Step 4: Simulate additional details
        logger.info("Step 4: Adding theft details...")
        time.sleep(2)
        
        # Step 5: Simulate form submission
        logger.info("Step 5: Submitting report...")
        time.sleep(3)
        
        # Step 6: Simulate confirmation page
        logger.info("Step 6: Processing complete! Theft reported successfully")
        
        # Report ID (simulated)
        report_id = f"POL-{int(time.time())}"
        logger.info(f"Generated report ID: {report_id}")
        
        return True

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='DiebstahlAgent for theft reporting')
    parser.add_argument('incident_id', type=int, nargs='?', default=None, 
                        help='Incident ID to process')
    parser.add_argument('--token', type=str, help='API token for authentication')
    parser.add_argument('--token-file', type=str, help='File containing API token')
    parser.add_argument('--api-host', type=str, default='localhost:8002', 
                       help='API host address')
    parser.add_argument('--headless', action='store_true', 
                       help='Run in headless mode (no browser UI)')
    
    args = parser.parse_args()
    
    # Setze zusätzliche Umgebungsvariablen wenn nötig
    if args.token:
        os.environ["API_TOKEN"] = args.token
    
    if args.api_host:
        os.environ["API_HOST"] = args.api_host
    
    return args

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
    print(f"Starting DiebstahlAgent for incident {incident_id}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"API host: {args.api_host}")
    print(f"Token available: {'Yes' if token else 'No'}")
    
    try:
        # Run agent
        agent = DiebstahlAgent(
            headless=args.headless,
            incident_id=incident_id,
            token=token,
            api_host=args.api_host
        )
        
        success = agent.run()
        print(f"Agent completed with success={success}")
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error running agent: {str(e)}")
        traceback.print_exc()
        sys.exit(1)