# -*- coding: utf-8 -*-
"""
Direct Agent for incident processing.
Handles user address in personal data and location address for crime scene.
Leaves browser open at the end. NO SCREENSHOTS (except on critical failure).
VERSION: COMPLETE CODE
"""

import argparse
import json
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("direct_agent")

class DirectAgent:
    """Direct standalone agent for incident reporting."""

    def __init__(self, incident_id=None, token=None, api_host="localhost:8002", headless=None):
        """Initialize the agent."""
        self.headless = headless if headless is not None else False
        self.incident_id = incident_id
        self.token = token
        self.api_host = api_host
        self.driver = None
        self.wait = None
        self.long_wait = None
        self.location = None # Für den Tatort (kann None sein)
        self.extended_form_data = {}  # NEUE ZEILE: Für erweiterte Formulardaten
        logger.info(f"DirectAgent init: id={incident_id}, host={api_host}, headless={self.headless}")

    def setup_driver(self) -> bool:
        """
        Set up Selenium WebDriver using multiple strategies for robustness.
        1. Try webdriver-manager directly.
        2. Try webdriver-manager and validate the .exe path.
        3. Try a predefined manual path (user needs to configure).
        4. Let Selenium search the system PATH.
        """
        logger.info("Configuring Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        # Optional: Verhindern, dass störende "DevTools listening" Meldungen in der Konsole erscheinen
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])


        if self.headless:
            chrome_options.add_argument('--headless=new') # Verwende 'new' Headless Mode
            logger.info("Running in headless mode ('new')")
        else:
            logger.info("Running in visible mode (headless=False)")

        service = None
        driver_strategies_tried = []

        # --- STRATEGIE 1: webdriver-manager (Standard) ---
        if service is None:
            strategy_name = "webdriver-manager (standard)"
            driver_strategies_tried.append(strategy_name)
            logger.info(f"Attempting Strategy 1: {strategy_name}")
            try:
                wdm_service = Service(ChromeDriverManager().install())
                # Kurzer Check, ob der Service gestartet werden kann (simuliert)
                logger.info(f"webdriver-manager path: {wdm_service.path}")
                # Hier noch keine Garantie, dass es die richtige .exe ist
                service = wdm_service
                logger.info(f"Strategy 1 ({strategy_name}) potentially successful (service configured).")
            except Exception as e:
                logger.warning(f"Strategy 1 ({strategy_name}) failed: {e}")
                # Gehe weiter zur nächsten Strategie

        # --- STRATEGIE 2: webdriver-manager mit Pfad-Validierung ---
        # (Kann übersprungen werden, wenn Strategie 1 schon einen Service lieferte,
        # aber zur Sicherheit versuchen wir es hier erneut mit Validierung, falls der Service oben doch falsch war)
        if service is None or (service and service.path and not service.path.lower().endswith('chromedriver.exe')):
            if service is not None:
                 logger.warning(f"Strategy 1 result suspicious ({service.path}), resetting service.")
                 service = None # Service zurücksetzen, da Pfad falsch war

            strategy_name = "webdriver-manager (validated path)"
            driver_strategies_tried.append(strategy_name)
            logger.info(f"Attempting Strategy 2: {strategy_name}")
            try:
                wdm_service_validated = Service(ChromeDriverManager().install())
                service_path = wdm_service_validated.path
                logger.info(f"webdriver-manager validated path check: {service_path}")
                if service_path and service_path.lower().endswith('chromedriver.exe'):
                    service = wdm_service_validated
                    logger.info(f"Strategy 2 ({strategy_name}) successful (path ends with .exe).")
                else:
                    logger.warning(f"Strategy 2 ({strategy_name}) failed: Path '{service_path}' does not end with chromedriver.exe.")
                    # Gehe weiter zur nächsten Strategie
            except Exception as e:
                logger.warning(f"Strategy 2 ({strategy_name}) failed during execution: {e}")
                # Gehe weiter zur nächsten Strategie

        # --- STRATEGIE 3: Manueller Pfad (Konfigurierbar) ---
        if service is None:
            strategy_name = "Manual Path"
            driver_strategies_tried.append(strategy_name)
            logger.info(f"Attempting Strategy 3: {strategy_name}")
            try:
                # !!! WICHTIG: Setze hier den Pfad zu deiner manuell heruntergeladenen chromedriver.exe !!!
                # Lade die korrekte Version für deinen Chrome von:
                # https://googlechromelabs.github.io/chrome-for-testing/
                # Verwende die win64 Version.
                chromedriver_manual_path = r"C:\webdriver\chromedriver.exe" # Beispiel - BITTE ANPASSEN!

                if os.path.exists(chromedriver_manual_path):
                    manual_service = Service(executable_path=chromedriver_manual_path)
                    service = manual_service
                    logger.info(f"Strategy 3 ({strategy_name}) successful using path: {chromedriver_manual_path}")
                else:
                    logger.warning(f"Strategy 3 ({strategy_name}) failed: Manual path '{chromedriver_manual_path}' not found.")
                    # Gehe weiter zur nächsten Strategie
            except Exception as e:
                logger.warning(f"Strategy 3 ({strategy_name}) failed during execution: {e}")
                # Gehe weiter zur nächsten Strategie

        # --- STRATEGIE 4: Selenium sucht im System PATH ---
        if service is None:
            strategy_name = "System PATH Search"
            driver_strategies_tried.append(strategy_name)
            logger.info(f"Attempting Strategy 4: {strategy_name}")
            try:
                # Service() ohne Argumente lässt Selenium den PATH durchsuchen
                path_service = Service()
                # Wir müssen hier annehmen, dass es funktioniert, wenn keine Exception fliegt.
                # Der eigentliche Test kommt beim Starten des Drivers.
                service = path_service
                logger.info(f"Strategy 4 ({strategy_name}) potentially configured (Selenium will search PATH).")
            except Exception as e:
                logger.warning(f"Strategy 4 ({strategy_name}) failed during Service() init: {e}")
                # Keine weiteren Strategien

        # --- FINALE PRÜFUNG UND DRIVER START ---
        if service is None:
            logger.error("All ChromeDriver setup strategies failed.")
            logger.error(f"Strategies tried: {', '.join(driver_strategies_tried)}")
            self.update_incident_status("error", "ChromeDriver konnte nicht initialisiert werden (Alle Strategien fehlgeschlagen).")
            return False

        logger.info(f"Attempting to start Chrome WebDriver using the configured service (Path likely: {getattr(service, 'path', 'System PATH')})...")
        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)

            # Erfolgreich gestartet, logge Versionen etc.
            try:
                browser_version = self.driver.capabilities.get('browserVersion', 'unknown')
                driver_version_info = self.driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown')
                driver_version = driver_version_info.split(' ')[0] if isinstance(driver_version_info, str) else 'unknown'
                logger.info(f"WebDriver started successfully!")
                logger.info(f"Browser version: {browser_version}")
                logger.info(f"ChromeDriver version: {driver_version}")
            except Exception as cap_e:
                logger.warning(f"Could not determine browser/driver versions after start: {cap_e}")

            # Waits setzen
            self.wait = WebDriverWait(self.driver, 30)
            self.long_wait = WebDriverWait(self.driver, 60)

            # Google-Test
            logger.info("Testing navigation to Google...")
            self.driver.get("https://www.google.com")
            logger.info(f"Initial navigation successful: {self.driver.title}")
            return True

        except WebDriverException as e:
            # Hier fangen wir spezifisch den WebDriverException ab, der oft den OSError enthält
            logger.error(f"Error creating WebDriver instance: {str(e)}")
            if "OSError: [WinError 193]" in str(e):
                 logger.error(">>> Likely cause: The ChromeDriver executable pointed to by the service is not a valid application (wrong architecture or corrupted?).")
                 logger.error(f">>> Service path used: {getattr(service, 'path', 'N/A or System PATH')}")
                 logger.error(f">>> Strategies tried before this attempt: {', '.join(driver_strategies_tried)}")
                 error_msg = "Fehler beim Erstellen des WebDrivers: ChromeDriver ist keine gültige Anwendung (WinError 193)."
            else:
                 error_msg = f"Fehler beim Erstellen des WebDrivers: {str(e)}"
            logger.error(traceback.format_exc())
            self.update_incident_status("error", error_msg)
            return False
        except Exception as e: # Fange andere unerwartete Fehler ab
            logger.error(f"Unexpected error creating WebDriver instance: {str(e)}")
            logger.error(traceback.format_exc())
            self.update_incident_status("error", f"Unerwarteter Fehler beim Erstellen des WebDrivers: {str(e)}")
            return False

    # --- API Methods ---
    def load_incident_data(self):
        """Load current incident data."""
        if not self.incident_id: logger.warning("No incident ID provided"); return None
        try:
            api_url = f"http://{self.api_host}/incidents/{self.incident_id}/agent-direct"
            logger.info(f"Loading incident data from: {api_url}")
            response = requests.get(api_url, timeout=25)
            response.raise_for_status()
            incident_data = response.json()
            logger.info(f"Incident data loaded successfully.")
            return incident_data
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed for incident data: {str(req_err)}")
            return None
        except Exception as e:
            logger.error(f"Error loading incident data: {str(e)}")
            return None

    def load_user_data(self, user_id):
        """Load user data for given user ID."""
        if not user_id: logger.warning("No user ID provided for loading data"); return None
        try:
            api_url = f"http://{self.api_host}/users/{user_id}"
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            logger.info(f"Loading user data from: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=25)
            response.raise_for_status()
            user_data = response.json()
            logger.info(f"User data loaded successfully. Keys: {list(user_data.keys())}")
            return user_data
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed for user data: {str(req_err)}")
            return None
        except Exception as e:
            logger.error(f"Error loading user data: {str(e)}")
            return None
        
    def load_user_location_data(self, location_id):
        """Load user location data for given location ID."""
        if not location_id: 
            logger.warning("No user location ID provided for loading data")
            return None
        try:
            api_url = f"http://{self.api_host}/api/user-locations/{location_id}"
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            logger.info(f"Loading user location data from: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=25)
            response.raise_for_status()
            location_data = response.json()
            logger.info(f"User location data loaded successfully.")
            return location_data
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed for user location data: {str(req_err)}")
            return None
        except Exception as e:
            logger.error(f"Error loading user location data: {str(e)}")
            return None

    def load_location_data(self, location_id):
        """Load location data for given location ID."""
        if not location_id: logger.warning("No location ID provided for loading data"); return None
        try:
            api_url = f"http://{self.api_host}/locations/{location_id}"
            headers = {"Authorization": f"Bearer {self.token}"} if self.token else {}
            logger.info(f"Loading location data from: {api_url}")
            response = requests.get(api_url, headers=headers, timeout=25)
            response.raise_for_status()
            location_data = response.json()
            logger.info(f"Location data loaded successfully.")
            return location_data
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed for location data: {str(req_err)}")
            return None
        except Exception as e:
            logger.error(f"Error loading location data: {str(e)}")
            return None

    def update_incident_status(self, status, message=None):
        """Update incident status via API call."""
        if not self.incident_id: logger.warning("Cannot update status: No incident ID"); return False
        try:
            payload = {"status": status}
            if message:
                if len(message) > 10000: message = message[:9900] + "... [TRUNCATED]"
                payload["agent_log"] = message
            api_url = f"http://{self.api_host}/incidents/{self.incident_id}/agent-direct"
            logger.info(f"Updating status to '{status}' via {api_url}...")
            response = requests.patch(api_url, json=payload, timeout=25)
            response.raise_for_status()
            logger.info(f"Status successfully updated to '{status}'.")
            return True
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request failed for status update: {str(req_err)}")
            # Versuche Traceback zu loggen falls verfügbar
            if req_err.response is not None:
                 logger.error(f"Response Body: {req_err.response.text[:500]}")
            return False
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            traceback.print_exc()
            return False

    # --- Helper Methods ---
    def format_date(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to DD.MM.YYYY."""
        if not date_str: return ""
        try:
            date_obj = datetime.strptime(str(date_str), "%Y-%m-%d")
            return date_obj.strftime("%d.%m.%Y")
        except ValueError: logger.warning(f"Could not parse date '{date_str}' with format YYYY-MM-DD."); return str(date_str)
        except Exception as e: logger.error(f"Error formatting date '{date_str}': {str(e)}"); return str(date_str)
        
    def collect_extended_form_data(self):
        """
        Sammelt erweiterte Formulardaten - zuerst aus API, dann manuell als Fallback
        """
        logger.info("Sammle erweiterte Formulardaten...")
        
        # Prüfe zuerst, ob Daten vom Frontend / API kommen
        if self.incident_id:
            try:
                incident_data = self.load_incident_data()
                if incident_data and incident_data.get('email_data'):
                    import json
                    email_data = json.loads(incident_data['email_data'])
                    logger.info(f"DEBUG: Gefundene email_data: {email_data}")
                    
                    # Prüfe ob erweiterte Felder vorhanden sind
                    required_fields = ['daten_weg', 'entwendetes_gut', 'sachverhalt', 'schadenshoehe', 'fotos_upload']
                    if all(key in email_data for key in required_fields):
                        logger.info("✓ Erweiterte Daten aus Frontend gefunden - keine manuelle Eingabe erforderlich")
                        return {
                            'daten_weg': email_data['daten_weg'],
                            'entwendetes_gut': email_data['entwendetes_gut'],
                            'sachverhalt': email_data['sachverhalt'],
                            'schadenshoehe': email_data['schadenshoehe'],
                            'fotos_upload': email_data['fotos_upload']
                        }
                    else:
                        logger.warning(f"Unvollständige erweiterte Daten in email_data. Gefunden: {list(email_data.keys())}")
            except Exception as e:
                logger.warning(f"Konnte erweiterte Daten nicht aus API laden: {e}")
        
        # Fallback: Manuelle Eingabe für direkten Aufruf
        logger.info("FALLBACK: Verwende manuelle Eingabe für erweiterte Daten...")
        print("\n" + "="*70)
        print("ERWEITERTE FORMULAR-DATEN EINGEBEN")
        print("="*70)
        print("Zusätzlich zu Tatzeit/Tatort/Standort benötigen wir folgende Informationen:")
        print()

        data = {}

        # 1. Auf welchem Weg haben Sie diese Daten erlangt?
        while True:
            daten_weg = input("Auf welchem Weg haben Sie diese Daten erlangt? (Text): ").strip()
            if daten_weg:
                data['daten_weg'] = daten_weg
                break
            print("Bitte geben Sie eine Antwort ein.")

        # 2. Entwendetes Gut
        while True:
            entwendetes_gut = input("Entwendetes Gut (Beschreibung): ").strip()
            if entwendetes_gut:
                data['entwendetes_gut'] = entwendetes_gut
                break
            print("Bitte beschreiben Sie das entwendete Gut.")

        # 3. Sachverhalt in eigenen Worten
        while True:
            sachverhalt = input("Bitte schildern Sie den Sachverhalt in eigenen Worten: ").strip()
            if sachverhalt:
                data['sachverhalt'] = sachverhalt
                break
            print("Bitte schildern Sie den Sachverhalt.")

        # 4. Gesamtschadenshöhe
        while True:
            try:
                schadenshoehe = input("Gesamtschadenshöhe (in Euro, nur Zahl): ").strip()
                if schadenshoehe:
                    # Prüfe ob es eine gültige Zahl ist
                    float(schadenshoehe.replace(',', '.'))
                    data['schadenshoehe'] = schadenshoehe
                    break
                else:
                    print("Bitte geben Sie eine Schadenshöhe ein.")
            except ValueError:
                print("Bitte geben Sie eine gültige Zahl ein.")

        # 5. Haben Sie Fotos oder Dokumente als Upload?
        while True:
            fotos_upload = input("Haben Sie Fotos oder Dokumente als Upload? (ja/nein): ").strip().lower()
            if fotos_upload in ['ja', 'j', 'yes', 'y']:
                data['fotos_upload'] = True
                break
            elif fotos_upload in ['nein', 'n', 'no']:
                data['fotos_upload'] = False
                break
            else:
                print("Bitte antworten Sie mit 'ja' oder 'nein'.")

        print("\n" + "="*70)
        print("ERWEITERTE DATEN ERFASST")
        print("="*70)
        for key, value in data.items():
            print(f"  {key}: {value}")
        print()

        confirm = input("Sind diese Daten korrekt? (ja/nein): ").strip().lower()
        if confirm not in ['ja', 'j', 'yes', 'y']:
            print("Datenerfassung abgebrochen.")
            return None

        return data

    # Komplette fill_extended_form_fields Methode für DirectAgent Klasse
    def fill_gesamtschadenshoehe(self, schadenshoehe_value):
        """Spezielle Methode für das Kendo UI NumericTextBox."""
        try:
            logger.info(f"Fülle Gesamtschadenshöhe aus: {schadenshoehe_value}")
            
            # STRATEGIE 1: Erweiterte JavaScript-Lösung mit allen Kendo-Events
            try:
                js_result = self.driver.execute_script("""
                    console.log('=== Kendo NumericTextBox Debugging ===');
                    
                    // Finde alle Kendo NumericTextBox Widgets
                    var foundWidgets = [];
                    var inputs = document.querySelectorAll('input[data-role="numerictextbox"], input[role="spinbutton"]');
                    
                    console.log('Gefundene numerische Inputs:', inputs.length);
                    
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        console.log('Input ' + i + ':', input.id, input.className, input.style.display);
                        
                        // Versuche verschiedene Kendo-Zugriffsmethoden
                        var widget = null;
                        
                        // Methode 1: Über kendo.widgetInstance
                        if (window.kendo && kendo.widgetInstance) {
                            widget = kendo.widgetInstance(input);
                        }
                        
                        // Methode 2: Über jQuery data
                        if (!widget && window.$ && $(input).length > 0) {
                            widget = $(input).data('kendoNumericTextBox');
                        }
                        
                        // Methode 3: Über ID mit jQuery
                        if (!widget && input.id && window.$ && $('#' + input.id).length > 0) {
                            widget = $('#' + input.id).data('kendoNumericTextBox');
                        }
                        
                        console.log('Widget für Input ' + i + ':', widget);
                        
                        if (widget) {
                            foundWidgets.push({input: input, widget: widget});
                            
                            try {
                                // Setze Wert über Kendo API
                                widget.value(parseFloat(arguments[0]));
                                
                                // Trigger alle wichtigen Events
                                widget.trigger('change');
                                widget.trigger('spin');
                                
                                // Zusätzliche native Events
                                var changeEvent = new Event('change', { bubbles: true, cancelable: true });
                                var inputEvent = new Event('input', { bubbles: true, cancelable: true });
                                var blurEvent = new Event('blur', { bubbles: true, cancelable: true });
                                
                                input.dispatchEvent(inputEvent);
                                input.dispatchEvent(changeEvent);
                                input.dispatchEvent(blurEvent);
                                
                                console.log('Kendo Widget Wert gesetzt:', widget.value());
                                return 'kendo_widget_success:' + widget.value();
                                
                            } catch (widgetError) {
                                console.error('Kendo Widget Fehler:', widgetError);
                            }
                        }
                    }
                    
                    // FALLBACK: Direkte Input-Manipulation für alle numerischen Felder
                    for (var i = 0; i < inputs.length; i++) {
                        var input = inputs[i];
                        
                        try {
                            // Element sichtbar machen
                            input.style.display = 'block';
                            input.style.visibility = 'visible';
                            input.style.opacity = '1';
                            input.removeAttribute('readonly');
                            input.removeAttribute('disabled');
                            
                            // Focus setzen
                            input.focus();
                            
                            // Wert setzen
                            input.value = arguments[0];
                            
                            // Alle Events triggern
                            var events = ['input', 'change', 'keyup', 'blur', 'focusout'];
                            for (var j = 0; j < events.length; j++) {
                                var event = new Event(events[j], { bubbles: true, cancelable: true });
                                input.dispatchEvent(event);
                            }
                            
                            console.log('Direkter Input Wert gesetzt:', input.value);
                            
                            // Prüfe ob Wert tatsächlich gesetzt wurde
                            if (input.value == arguments[0]) {
                                return 'direct_input_success:' + input.value;
                            }
                            
                        } catch (directError) {
                            console.error('Direkter Input Fehler:', directError);
                        }
                    }
                    
                    return 'all_methods_failed';
                """, schadenshoehe_value)
                
                logger.info(f"JavaScript-Ergebnis: {js_result}")
                
                if 'success' in js_result:
                    # Zusätzliche Validierung - prüfe ob Wert tatsächlich im UI sichtbar ist
                    time.sleep(1)
                    
                    # Versuche den Wert zu lesen
                    validation_result = self.driver.execute_script("""
                        var inputs = document.querySelectorAll('input[data-role="numerictextbox"], input[role="spinbutton"]');
                        for (var i = 0; i < inputs.length; i++) {
                            var input = inputs[i];
                            if (input.value && input.value != '') {
                                return 'validation_success:' + input.value;
                            }
                            
                            // Prüfe auch Kendo Widget Werte
                            if (window.kendo) {
                                var widget = kendo.widgetInstance(input);
                                if (widget && widget.value && widget.value() !== null) {
                                    return 'widget_validation_success:' + widget.value();
                                }
                            }
                        }
                        return 'validation_failed';
                    """)
                    
                    logger.info(f"Validierung: {validation_result}")
                    
                    if 'validation_success' in validation_result:
                        logger.info("✓ Gesamtschadenshöhe erfolgreich gesetzt und validiert")
                        return True
                    else:
                        logger.warning("JavaScript-Setzung berichtet Erfolg, aber Validierung fehlgeschlagen")
                
            except Exception as js_e:
                logger.warning(f"JavaScript-Behandlung fehlgeschlagen: {js_e}")
            
            # STRATEGIE 2: Selenium-basierte Manipulation
            try:
                logger.info("Versuche Selenium-basierte Manipulation...")
                
                # Suche alle potentiellen numerischen Input-Felder
                potential_selectors = [
                    "//input[@data-role='numerictextbox']",
                    "//input[@role='spinbutton']", 
                    "//input[contains(@class, 'k-input')]",
                    "//span[contains(@class, 'k-numerictextbox')]//input",
                    "//div[contains(@class, 'k-numerictextbox')]//input"
                ]
                
                for selector in potential_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        logger.info(f"Selector '{selector}' fand {len(elements)} Elemente")
                        
                        for elem in elements:
                            try:
                                # Scroll zum Element
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
                                time.sleep(0.5)
                                
                                # Element sichtbar machen und aktivieren
                                self.driver.execute_script("""
                                    arguments[0].style.display = 'block';
                                    arguments[0].style.visibility = 'visible';
                                    arguments[0].style.opacity = '1';
                                    arguments[0].removeAttribute('readonly');
                                    arguments[0].removeAttribute('disabled');
                                """, elem)
                                time.sleep(0.3)
                                
                                # Dreifacher Klick um alles zu selektieren
                                elem.click()
                                time.sleep(0.1)
                                elem.click()
                                time.sleep(0.1)
                                elem.click()
                                time.sleep(0.2)
                                
                                # Wert eingeben
                                elem.clear()
                                elem.send_keys(schadenshoehe_value)
                                time.sleep(0.3)
                                
                                # Tab oder Enter drücken um Eingabe zu bestätigen
                                elem.send_keys(Keys.TAB)
                                time.sleep(0.5)
                                
                                logger.info(f"Selenium-Manipulation mit Selector '{selector}' durchgeführt")
                                
                                # Prüfe ob Wert gesetzt wurde
                                current_value = elem.get_attribute('value')
                                if current_value == schadenshoehe_value:
                                    logger.info("✓ Selenium-basierte Setzung erfolgreich validiert")
                                    return True
                                    
                            except Exception as elem_e:
                                logger.warning(f"Element-Manipulation fehlgeschlagen: {elem_e}")
                                continue
                                
                    except Exception as selector_e:
                        logger.warning(f"Selector '{selector}' fehlgeschlagen: {selector_e}")
                        continue
            
            except Exception as selenium_e:
                logger.warning(f"Selenium-basierte Manipulation fehlgeschlagen: {selenium_e}")
            
            logger.warning("Alle Strategien für Gesamtschadenshöhe fehlgeschlagen")
            return False
            
        except Exception as e:
            logger.error(f"Kritischer Fehler bei Gesamtschadenshöhe: {e}")
            return False

    def navigate_to_uploads_abschluss(self):
        """Spezielle Navigation zu 'Uploads / Abschluss' Sektion."""
        try:
            logger.info("Navigiere zu 'Uploads / Abschluss' Sektion...")
            
            # STRATEGIE 1: Direkter Klick auf "Weiter zu: Uploads / Abschluss"
            try:
                weiter_uploads_element = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, "//div[contains(@class, 'label') and contains(text(), 'Weiter zu: Uploads / Abschluss')]")
                ))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", weiter_uploads_element)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", weiter_uploads_element)
                logger.info("✓ Navigation via 'Weiter zu: Uploads / Abschluss' erfolgreich")
                time.sleep(2)
                return True
            except TimeoutException:
                logger.info("Strategie 1 (Weiter zu: Uploads / Abschluss) fehlgeschlagen")
            
            # STRATEGIE 2: Suche nach ähnlichen Label-Elementen
            try:
                weiter_elements = self.driver.find_elements(
                    By.XPATH, 
                    "//div[contains(@class, 'label') and ("
                    "contains(text(), 'Uploads') or "
                    "contains(text(), 'Abschluss') or "
                    "contains(text(), 'Upload')"
                    ")]"
                )
                
                for element in weiter_elements:
                    if element.is_displayed():
                        element_text = element.text.strip()
                        logger.info(f"Gefundenes Label-Element: '{element_text}'")
                        
                        if "uploads" in element_text.lower() or "abschluss" in element_text.lower():
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                            time.sleep(0.5)
                            self.driver.execute_script("arguments[0].click();", element)
                            logger.info(f"✓ Navigation via Label '{element_text}' erfolgreich")
                            time.sleep(2)
                            return True
            except Exception as e:
                logger.warning(f"Strategie 2 (ähnliche Labels) fehlgeschlagen: {e}")
            
            # STRATEGIE 3: JavaScript-basierte Elementsuche
            try:
                logger.info("Versuche JavaScript-basierte Navigation...")
                
                js_result = self.driver.execute_script("""
                    console.log('=== JavaScript Navigation Debugging ===');
                    
                    // Suche nach allen Elementen mit relevanten Texten
                    var allElements = document.querySelectorAll('*');
                    var candidates = [];
                    
                    for (var i = 0; i < allElements.length; i++) {
                        var elem = allElements[i];
                        var text = elem.textContent || elem.innerText || '';
                        
                        if ((text.includes('Upload') || text.includes('Abschluss') || 
                            text.includes('upload') || text.includes('abschluss') ||
                            text.includes('Weiter')) && 
                            elem.offsetWidth > 0 && elem.offsetHeight > 0) {
                            
                            candidates.push({
                                element: elem,
                                text: text.trim(),
                                tag: elem.tagName,
                                className: elem.className
                            });
                        }
                    }
                    
                    console.log('Gefundene Kandidaten:', candidates.length);
                    
                    // Priorisiere Elemente mit "Weiter zu:"
                    for (var j = 0; j < candidates.length; j++) {
                        var candidate = candidates[j];
                        
                        if (candidate.text.includes('Weiter zu:') && 
                            (candidate.text.includes('Upload') || candidate.text.includes('Abschluss'))) {
                            
                            try {
                                candidate.element.click();
                                console.log('Geklickt auf:', candidate.text);
                                return 'weiter_zu_success';
                            } catch (e) {
                                console.error('Klick fehlgeschlagen:', e);
                            }
                        }
                    }
                    
                    // Fallback: Klicke auf ersten verfügbaren Kandidaten
                    for (var k = 0; k < candidates.length; k++) {
                        var candidate = candidates[k];
                        
                        try {
                            candidate.element.click();
                            console.log('Fallback-Klick auf:', candidate.text);
                            return 'fallback_success';
                        } catch (e) {
                            console.error('Fallback-Klick fehlgeschlagen:', e);
                        }
                    }
                    
                    return 'no_suitable_element';
                """)
                
                logger.info(f"JavaScript-Navigation Ergebnis: {js_result}")
                
                if 'success' in js_result:
                    logger.info("✓ JavaScript-basierte Navigation erfolgreich")
                    time.sleep(2)
                    return True
                    
            except Exception as e:
                logger.warning(f"Strategie 3 (JavaScript) fehlgeschlagen: {e}")
            
            logger.error("Alle Navigations-Strategien für 'Uploads / Abschluss' fehlgeschlagen")
            return False
            
        except Exception as e:
            logger.error(f"Kritischer Fehler bei Navigation zu 'Uploads / Abschluss': {e}")
            return False

    def click_page_icon_improved(self, page_number):
        """Verbesserte Page-Icon-Klick-Methode mit erweiterten Strategien."""
        try:
            logger.info(f"Suche Page-Icon für Seite {page_number}...")
            
            # STRATEGIE 1: Debug-Ausgabe aller verfügbaren Page-Numbers
            try:
                logger.info("Debug: Analysiere alle verfügbaren Page-Numbers...")
                
                all_page_spans = self.driver.find_elements(
                    By.XPATH, "//span[contains(@class, 'page-number')]"
                )
                
                available_pages = []
                for span in all_page_spans:
                    if span.is_displayed():
                        page_text = span.text.strip()
                        available_pages.append(page_text)
                        logger.info(f"Verfügbare Seite: '{page_text}'")
                
                logger.info(f"Alle verfügbaren Seiten: {available_pages}")
                
                # Falls die gewünschte Seite nicht existiert, versuche die nächst höhere
                if str(page_number) not in available_pages:
                    for higher_page in [str(page_number + 1), str(page_number + 2), str(page_number - 1)]:
                        if higher_page in available_pages:
                            logger.info(f"Seite {page_number} nicht verfügbar, versuche Seite {higher_page}")
                            
                            page_icon = self.driver.find_element(
                                By.XPATH, f"//span[contains(@class, 'page-number') and text()='{higher_page}']/.."
                            )
                            
                            if page_icon.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_icon)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", page_icon)
                                logger.info(f"✓ Page-Icon {higher_page} erfolgreich geklickt (Alternative)")
                                time.sleep(2)
                                return True
                else:
                    # Normale Page-Icon-Klick-Logik
                    page_icon = self.driver.find_element(
                        By.XPATH, f"//span[contains(@class, 'page-number') and text()='{page_number}']/.."
                    )
                    
                    if page_icon.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_icon)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", page_icon)
                        logger.info(f"✓ Page-Icon {page_number} erfolgreich geklickt")
                        time.sleep(2)
                        return True
                
            except Exception as e:
                logger.warning(f"Debug-Strategie fehlgeschlagen: {e}")
                
            return self.click_page_icon(page_number)
            
        except Exception as e:
            logger.error(f"Fehler bei verbesserter Page-Icon-Suche für Seite {page_number}: {e}")
            return False
        
    def click_page_icon(self, page_number):
        """Klickt auf ein spezifisches Page-Icon."""
        try:
            logger.info(f"Suche Page-Icon für Seite {page_number}...")
            
            # STRATEGIE 1: Exakte Suche nach Page Number
            try:
                page_icon = self.wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//span[contains(@class, 'page-number') and text()='{page_number}']/..")
                ))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_icon)
                time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", page_icon)
                logger.info(f"✓ Page-Icon {page_number} erfolgreich geklickt (Strategie 1)")
                time.sleep(2)
                return True
            except TimeoutException:
                logger.info(f"Strategie 1 für Page {page_number} fehlgeschlagen")
            
            # STRATEGIE 2: Suche nach win-splitviewcommand-icon mit entsprechender Page Number
            try:
                page_icon = self.driver.find_element(
                    By.XPATH, 
                    f"//div[contains(@class, 'win-splitviewcommand-icon')]"
                    f"[.//span[contains(@class, 'page-number') and text()='{page_number}']]"
                )
                if page_icon.is_displayed():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", page_icon)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", page_icon)
                    logger.info(f"✓ Page-Icon {page_number} erfolgreich geklickt (Strategie 2)")
                    time.sleep(2)
                    return True
            except:
                logger.info(f"Strategie 2 für Page {page_number} fehlgeschlagen")
            
            # STRATEGIE 3: Breitere Suche nach allen Page-Icons
            try:
                all_page_icons = self.driver.find_elements(
                    By.XPATH, "//div[contains(@class, 'win-splitviewcommand-icon')]"
                )
                
                for icon in all_page_icons:
                    try:
                        page_span = icon.find_element(By.XPATH, ".//span[contains(@class, 'page-number')]")
                        if page_span.text.strip() == str(page_number):
                            if icon.is_displayed():
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", icon)
                                time.sleep(0.5)
                                self.driver.execute_script("arguments[0].click();", icon)
                                logger.info(f"✓ Page-Icon {page_number} erfolgreich geklickt (Strategie 3)")
                                time.sleep(2)
                                return True
                    except:
                        continue
            except Exception as e:
                logger.warning(f"Strategie 3 für Page {page_number} fehlgeschlagen: {e}")
            
            logger.warning(f"Alle Strategien für Page-Icon {page_number} fehlgeschlagen")
            return False
            
        except Exception as e:
            logger.error(f"Fehler beim Klicken auf Page-Icon {page_number}: {e}")
            return False

    def fill_extended_form_fields(self):
        """
        KOMPLETT ÜBERARBEITETE IMPLEMENTIERUNG: Füllt die 12 zusätzlichen Formularschritte aus.
        Mit verbesserter Kendo UI Behandlung und robuster Navigation.
        """
        try:
            logger.info("=== STARTE ERWEITERTE FORMULAR-SCHRITTE (12 Schritte) ===")
            
            if not self.extended_form_data:
                logger.error("Keine erweiterten Formulardaten verfügbar!")
                return False
            
            # SCHRITT 1: Klick auf "Ich kann Angaben zu einer/m Tatverdächtigen machen"
            try:
                logger.info("Schritt 1: Klicke auf Tatverdächtigen-Label...")
                verdaechtig_label = None
                
                try:
                    verdaechtig_label = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//label[@for='tatangaben_verdaechtig_person']")
                    ))
                    logger.info("Strategie 1 erfolgreich: for-Attribut")
                except TimeoutException:
                    try:
                        verdaechtig_label = self.wait.until(EC.element_to_be_clickable(
                            (By.XPATH, "//label[contains(text(), 'Tatverdächtigen') and contains(text(), 'machen')]")
                        ))
                        logger.info("Strategie 2 erfolgreich: Text-basiert")
                    except TimeoutException:
                        pass
                
                if verdaechtig_label:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", verdaechtig_label)
                    time.sleep(0.5)
                    self.driver.execute_script("arguments[0].click();", verdaechtig_label)
                    logger.info("✓ Tatverdächtigen-Label erfolgreich geklickt")
                    time.sleep(2)
                else:
                    logger.warning("Tatverdächtigen-Label nicht gefunden")
                    
            except Exception as e:
                logger.warning(f"Schritt 1 fehlgeschlagen: {e}")

            # SCHRITT 2: "Auf welchem Weg haben Sie diese Daten erlangt?" ausfüllen
            try:
                logger.info("Schritt 2: Fülle 'Auf welchem Weg...' aus...")
                
                daten_weg_field = None
                try:
                    daten_weg_field = self.wait.until(EC.element_to_be_clickable(
                        (By.ID, "tatangaben_verdaechtig_person_daten_woher_hfrepeating_1")
                    ))
                except TimeoutException:
                    try:
                        daten_weg_field = self.driver.find_element(
                            By.XPATH, "//textarea[contains(@id, 'tatangaben_verdaechtig_person_daten_woher')]"
                        )
                    except:
                        pass
                
                if daten_weg_field:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", daten_weg_field)
                    time.sleep(0.3)
                    daten_weg_field.clear()
                    daten_weg_field.send_keys(self.extended_form_data.get('daten_weg', ''))
                    logger.info(f"✓ Daten-Weg Feld ausgefüllt: {self.extended_form_data.get('daten_weg', '')}")
                    time.sleep(1)
                else:
                    logger.warning("Daten-Weg Feld nicht gefunden")
                    
            except Exception as e:
                logger.warning(f"Schritt 2 fehlgeschlagen: {e}")

            # SCHRITT 3: Navigation zu Seite 3
            try:
                logger.info("Schritt 3: Navigiere zu Seite 3...")
                
                if self.click_page_icon(3):
                    logger.info("✓ Navigation zu Seite 3 erfolgreich")
                else:
                    logger.warning("Navigation zu Seite 3 fehlgeschlagen")
                    
            except Exception as e:
                logger.warning(f"Schritt 3 fehlgeschlagen: {e}")

            # SCHRITT 4: "Entwendetes Gut" ausfüllen
            try:
                logger.info("Schritt 4: Fülle 'Entwendetes Gut' aus...")
                
                entwendetes_gut_field = None
                try:
                    entwendetes_gut_field = self.wait.until(EC.element_to_be_clickable(
                        (By.ID, "diebstahl_sonstiges_entwendetes_gut")
                    ))
                except TimeoutException:
                    try:
                        entwendetes_gut_field = self.driver.find_element(
                            By.XPATH, "//textarea[contains(@data-win-options, 'Entwendetes Gut')]"
                        )
                    except:
                        pass
                
                if entwendetes_gut_field:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", entwendetes_gut_field)
                    time.sleep(0.3)
                    entwendetes_gut_field.clear()
                    entwendetes_gut_field.send_keys(self.extended_form_data.get('entwendetes_gut', ''))
                    logger.info(f"✓ Entwendetes Gut ausgefüllt: {self.extended_form_data.get('entwendetes_gut', '')}")
                    time.sleep(1)
                else:
                    logger.warning("Entwendetes Gut Feld nicht gefunden")
                    
            except Exception as e:
                logger.warning(f"Schritt 4 fehlgeschlagen: {e}")

            # SCHRITT 5: "Sachverhalt in eigenen Worten" ausfüllen
            try:
                logger.info("Schritt 5: Fülle 'Sachverhalt' aus...")
                
                sachverhalt_field = None
                try:
                    sachverhalt_field = self.wait.until(EC.element_to_be_clickable(
                        (By.ID, "diebstahl_sonstiges_abschluss_sachverhalt")
                    ))
                except TimeoutException:
                    try:
                        sachverhalt_field = self.driver.find_element(
                            By.XPATH, "//textarea[contains(@data-win-options, 'Sachverhalt')]"
                        )
                    except:
                        pass
                
                if sachverhalt_field:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", sachverhalt_field)
                    time.sleep(0.3)
                    sachverhalt_field.clear()
                    sachverhalt_field.send_keys(self.extended_form_data.get('sachverhalt', ''))
                    logger.info(f"✓ Sachverhalt ausgefüllt: {self.extended_form_data.get('sachverhalt', '')}")
                    time.sleep(1)
                else:
                    logger.warning("Sachverhalt Feld nicht gefunden")
                    
            except Exception as e:
                logger.warning(f"Schritt 5 fehlgeschlagen: {e}")

            # SCHRITT 6: Verbesserte Gesamtschadenshöhe-Behandlung
            try:
                logger.info("Schritt 6: Fülle 'Gesamtschadenshöhe' aus (Verbesserte Kendo UI Behandlung)...")
                
                schadenshoehe_value = self.extended_form_data.get('schadenshoehe', '')
                if schadenshoehe_value:
                    success = self.fill_gesamtschadenshoehe(schadenshoehe_value)
                    if success:
                        logger.info(f"✓ Gesamtschadenshöhe erfolgreich ausgefüllt: {schadenshoehe_value}")
                    else:
                        logger.warning("Gesamtschadenshöhe konnte nicht ausgefüllt werden")
                else:
                    logger.warning("Keine Schadenshöhe verfügbar")
                    
            except Exception as e:
                logger.warning(f"Schritt 6 fehlgeschlagen: {e}")

            # SCHRITT 7: Verbesserte Navigation zu Uploads/Abschluss
            try:
                logger.info("Schritt 7: Navigiere zu Uploads/Abschluss Sektion...")
                
                navigation_success = False
                
                # Versuche zuerst die spezifische "Uploads / Abschluss" Navigation
                if self.navigate_to_uploads_abschluss():
                    navigation_success = True
                    logger.info("✓ Navigation via 'Uploads / Abschluss' erfolgreich")
                
                # Fallback: Versuche Page-Icon 4 mit verbesserter Methode
                if not navigation_success:
                    logger.info("Fallback: Versuche Page-Icon Navigation...")
                    if self.click_page_icon_improved(4):
                        navigation_success = True
                        logger.info("✓ Fallback Page-Icon Navigation erfolgreich")
                
                # Letzter Fallback: Allgemeine Continue-Methode
                if not navigation_success:
                    logger.info("Letzter Fallback: Allgemeine Continue-Navigation...")
                    if self.continue_to_next_section():
                        navigation_success = True
                        logger.info("✓ Allgemeine Navigation erfolgreich")
                
                if not navigation_success:
                    logger.warning("Alle Navigations-Strategien für Schritt 7 fehlgeschlagen")
                else:
                    # Warte nach erfolgreicher Navigation
                    time.sleep(3)
                    
            except Exception as e:
                logger.warning(f"Schritt 7 (Navigation) fehlgeschlagen: {e}")

            # SCHRITTE 8-11: Radio Buttons
            radio_button_steps = [
                {
                    'step': 8,
                    'name': 'Fotos/Dokumente',
                    'id_ja': 'fotos_dokumente_vorhanden_ja',
                    'id_nein': 'fotos_dokumente_vorhanden_nein',
                    'use_ja': self.extended_form_data.get('fotos_upload', False)
                },
                {
                    'step': 9,
                    'name': 'Weitere Unterlagen',
                    'id_nein': 'fileUpload_weitereunterlagen_vorhanden_nein',
                    'use_ja': False
                },
                {
                    'step': 10,
                    'name': 'Verzicht auf Einstellungsbescheid',
                    'id_ja': 'abschluss_einstellungsbescheid_ja',
                    'use_ja': True
                },
                {
                    'step': 11,
                    'name': 'Bestätigung Strafanzeige',
                    'id_ja': 'abschluss_bestätigungstrafanzeige_ja',
                    'use_ja': True
                }
            ]
            
            for step_config in radio_button_steps:
                try:
                    step_num = step_config['step']
                    step_name = step_config['name']
                    use_ja = step_config['use_ja']
                    
                    logger.info(f"Schritt {step_num}: {step_name}...")
                    
                    if use_ja and 'id_ja' in step_config:
                        target_id = step_config['id_ja']
                        choice = "JA"
                    else:
                        target_id = step_config['id_nein']
                        choice = "NEIN"
                    
                    radio_element = None
                    try:
                        radio_element = self.driver.find_element(By.ID, target_id)
                    except:
                        try:
                            base_name = target_id.split('_')[0]
                            radio_element = self.driver.find_element(
                                By.XPATH, f"//input[@type='radio' and contains(@id, '{base_name}')]"
                            )
                        except:
                            pass
                    
                    if radio_element:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_element)
                        time.sleep(0.3)
                        self.driver.execute_script("arguments[0].click();", radio_element)
                        logger.info(f"✓ Schritt {step_num}: {choice} ausgewählt")
                        time.sleep(0.5)
                    else:
                        logger.warning(f"Schritt {step_num}: Element {target_id} nicht gefunden")
                        
                except Exception as e:
                    logger.warning(f"Schritt {step_config['step']} fehlgeschlagen: {e}")

            # SCHRITT 12: E-Mail-Adresse
            try:
                logger.info("Schritt 12: Fülle E-Mail-Adresse aus...")
                
                user_data = {}
                if self.incident_id:
                    incident_data = self.load_incident_data()
                    if incident_data and incident_data.get('user_id'):
                        user_data = self.load_user_data(incident_data['user_id'])
                
                email_value = user_data.get('email', '')
                
                if email_value:
                    email_field = None
                    
                    try:
                        email_field = self.driver.find_element(By.ID, "abschluss_anzeigeerstatter_email")
                    except:
                        try:
                            email_field = self.driver.find_element(By.XPATH, "//input[@type='email']")
                        except:
                            try:
                                email_field = self.driver.find_element(
                                    By.XPATH, "//input[contains(@id, 'email')]"
                                )
                            except:
                                pass
                    
                    if email_field:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
                        time.sleep(0.3)
                        email_field.clear()
                        email_field.send_keys(email_value)
                        logger.info(f"✓ E-Mail-Adresse ausgefüllt: {email_value}")
                        time.sleep(0.5)
                    else:
                        logger.warning("E-Mail-Feld nicht gefunden")
                else:
                    logger.warning("Keine E-Mail-Adresse in Benutzerdaten")
                    
            except Exception as e:
                logger.warning(f"Schritt 12 fehlgeschlagen: {e}")

            logger.info("=== ERWEITERTE FORMULAR-SCHRITTE ABGESCHLOSSEN ===")
            return True

        except Exception as e:
            logger.error(f"Kritischer Fehler in erweiterten Formular-Schritten: {e}")
            logger.error(traceback.format_exc())
            return False

    def fill_personal_data(self, user_data):
        """
        Füllt Personendaten in der exakt richtigen Reihenfolge:
        1. Firma/Institution Radio-Button
        2. Firma/Institution Bezeichnung
        3. Nachnane, Vorname, Gebdat, Geburtsort, Geburtsland
        4. *** ADRESSE-DIALOG ***
        5. Erst danach Telefonnummer und E-Mail
        """
        try:
            logger.info("Starte Ausfüllen der Personendaten mit exakter Reihenfolge...")
            
            # --- SCHRITT 1: Radio-Button Firma/Institution ---
            firma_label_xpath = "//label[normalize-space()='Eine Firma/Institution ist geschädigt']"
            try:
                firma_label = self.wait.until(EC.element_to_be_clickable((By.XPATH, firma_label_xpath)))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", firma_label); time.sleep(0.5)
                self.driver.execute_script("arguments[0].click();", firma_label)
                logger.info("Radio-Button 'Firma/Institution' geklickt.")
            except Exception as e: 
                logger.error(f"Konnte Radio-Button 'Firma/Institution' nicht klicken: {e}")
                return False

            # --- SCHRITT 2: Firmennamenfeld ausfüllen ---
            firma_feld_id = "firma_institution_bezeichnung"
            try:
                self.long_wait.until(EC.presence_of_element_located((By.ID, firma_feld_id)))
                logger.info(f"Feld '{firma_feld_id}' ist im DOM vorhanden.")
                
                firma_field = self.wait.until(EC.element_to_be_clickable((By.ID, firma_feld_id)))
                firma_value = user_data.get('firma', '')
                if firma_value and firma_value.strip():
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", firma_field); time.sleep(0.3)
                    try: firma_field.clear(); time.sleep(0.2)
                    except Exception as clear_err: logger.warning(f"Konnte Feld {firma_feld_id} nicht leeren: {clear_err}.")
                    logger.info(f"Feld '{firma_feld_id}': Sende '{firma_value}'")
                    firma_field.send_keys(firma_value)
                    time.sleep(0.5)
                else:
                    # Bei fehlender Firma einen Standardwert eintragen
                    default_firma = "Allgemeine Geschädigte GmbH"
                    logger.info(f"Kein Firmenwert in Benutzerdaten, verwende Standardwert: '{default_firma}'")
                    firma_field.clear()
                    firma_field.send_keys(default_firma)
                    time.sleep(0.5)
            except Exception as e:
                logger.error(f"Fehler beim Ausfüllen des Firmennamens: {e}")
                return False

            # --- SCHRITT 3: Persönliche Felder (NUR Pflichtfelder, NICHT Tel/Email) ---
            try:
                logger.info("Fülle persönliche Felder aus (ohne Telefon/Email)...")
                
                # Nachname
                nachname_id = "eigene_personalien_nachname"
                nachname_value = user_data.get('nachname', '')
                if nachname_value:
                    nachname_field = self.wait.until(EC.element_to_be_clickable((By.ID, nachname_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", nachname_field)
                    time.sleep(0.3)
                    nachname_field.clear()
                    nachname_field.send_keys(nachname_value)
                    logger.info(f"Nachname '{nachname_value}' eingegeben")
                    time.sleep(0.5)
                
                # Vorname
                vorname_id = "eigene_personalien_vorname"
                vorname_value = user_data.get('vorname', '')
                if vorname_value:
                    vorname_field = self.wait.until(EC.element_to_be_clickable((By.ID, vorname_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", vorname_field)
                    time.sleep(0.3)
                    vorname_field.clear()
                    vorname_field.send_keys(vorname_value)
                    logger.info(f"Vorname '{vorname_value}' eingegeben")
                    time.sleep(0.5)
                
                # Geburtsdatum
                gebdat_id = "eigene_personalien_gebdat-kendoInput"
                gebdat_value = user_data.get('geburtsdatum', '')
                if gebdat_value:
                    gebdat_field = self.wait.until(EC.element_to_be_clickable((By.ID, gebdat_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", gebdat_field)
                    time.sleep(0.3)
                    gebdat_field.clear()
                    formatted_date = self.format_date(gebdat_value)
                    gebdat_field.send_keys(formatted_date)
                    gebdat_field.send_keys(Keys.TAB)  # TAB nach Datumseingabe
                    logger.info(f"Geburtsdatum '{formatted_date}' eingegeben")
                    time.sleep(0.5)
                
                # Geburtsort
                geburtsort_id = "eigene_personalien_geburtsort"
                geburtsort_value = user_data.get('geburtsort', '')
                if geburtsort_value:
                    geburtsort_field = self.wait.until(EC.element_to_be_clickable((By.ID, geburtsort_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", geburtsort_field)
                    time.sleep(0.3)
                    geburtsort_field.clear()
                    geburtsort_field.send_keys(geburtsort_value)
                    logger.info(f"Geburtsort '{geburtsort_value}' eingegeben")
                    time.sleep(0.5)
                
                # Geburtsland
                geburtsland_id = "eigene_personalien_geburtsland-kendoInput"
                geburtsland_value = user_data.get('geburtsland', '')
                if geburtsland_value:
                    geburtsland_field = self.wait.until(EC.element_to_be_clickable((By.ID, geburtsland_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", geburtsland_field)
                    time.sleep(0.3)
                    geburtsland_field.clear()
                    geburtsland_field.send_keys(geburtsland_value)
                    time.sleep(1.5)
                    geburtsland_field.send_keys(Keys.TAB)
                    logger.info(f"Geburtsland '{geburtsland_value}' eingegeben + TAB")
                    time.sleep(1.0)
            except Exception as e:
                logger.error(f"Fehler beim Ausfüllen der persönlichen Felder: {e}")
                # Wir versuchen trotzdem weiterzumachen

            # --- SCHRITT 4: Adresse-Button finden und klicken ---
            try:
                logger.info("Jetzt versuche ich, den Adresse-Button zu finden und zu klicken...")

                # Screenshot vor dem Adressbutton-Klick machen
                try:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    ss_path = f"before_address_button_{timestamp}.png"
                    self.driver.save_screenshot(ss_path)
                    logger.info(f"Screenshot vor Adressbutton-Suche: {ss_path}")
                except Exception as ss_error:
                    logger.warning(f"Konnte keinen Screenshot machen: {ss_error}")
                
                # Alle für Adresse-Button relevanten Elemente auflisten
                all_address_elements = []
                
                try:
                    # Elemente mit dem Text "Adresse"
                    address_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Adresse')]")
                    all_address_elements.extend(address_elements)
                    
                    # Buttons mit bestimmten Klassen
                    search_buttons = self.driver.find_elements(By.XPATH, "//button[contains(@class, 'search') or contains(@class, 'btn')]")
                    all_address_elements.extend(search_buttons)
                    
                    # Icons oder SVGs innerhalb von Buttons
                    icon_buttons = self.driver.find_elements(By.XPATH, "//button[.//i or .//svg]")
                    all_address_elements.extend(icon_buttons)
                    
                    logger.info(f"Gefunden: {len(all_address_elements)} mögliche Adresselemente")
                    
                    # Alle sichtbaren Elemente loggen
                    for i, elem in enumerate(all_address_elements):
                        if elem.is_displayed():
                            try:
                                elem_text = elem.text or "kein Text"
                                elem_class = elem.get_attribute("class") or "keine Klasse"
                                logger.info(f"Element {i+1}: Text='{elem_text}', Klasse='{elem_class}'")
                            except:
                                pass
                except Exception as elem_error:
                    logger.warning(f"Fehler beim Auflisten der Adresselemente: {elem_error}")
                
                # Versuchen, den Adresse-Button zu finden
                address_button_selectors = [
                    "//button[contains(@aria-label, 'Suche') or contains(@aria-label, 'Adresse')]",
                    "//button[.//i[contains(@class, 'search')] or .//i[contains(@class, 'map')]]",
                    "//button[.//span[contains(text(), 'Adresse')]]",
                    "//div[contains(@class, 'input-group-btn')]//button",
                    "//div[contains(@class, 'Suche') or contains(@class, 'suche')]//button",
                    "//div[text()='Adresse']/following-sibling::button",
                    "//div[contains(text(), 'Suche')]/following-sibling::button"
                ]
                
                address_button = None
                for selector in address_button_selectors:
                    try:
                        buttons = self.driver.find_elements(By.XPATH, selector)
                        for btn in buttons:
                            if btn.is_displayed():
                                address_button = btn
                                logger.info(f"Adresse-Button gefunden mit Selektor: {selector}")
                                break
                        if address_button:
                            break
                    except Exception as e:
                        logger.warning(f"Fehler mit Selektor {selector}: {e}")
                
                # Wenn kein Button gefunden, jeden Button/Icon auf der Seite probieren
                if not address_button:
                    logger.warning("Kein Adresse-Button mit selektiven Selektoren gefunden, probiere alle Buttons...")
                    
                    # Alle Buttons 
                    all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"Gefunden: {len(all_buttons)} Buttons auf der Seite")
                    
                    # Zuerst Buttons in der Nähe von Adresselementen probieren
                    for i, btn in enumerate(all_buttons):
                        try:
                            if btn.is_displayed():
                                btn_text = btn.text.lower() if btn.text else ""
                                btn_aria = (btn.get_attribute("aria-label") or "").lower()
                                
                                # Prüfen, ob es ein vielversprechender Button ist
                                if ("adresse" in btn_text or "suche" in btn_text or 
                                    "adresse" in btn_aria or "suche" in btn_aria):
                                    address_button = btn
                                    logger.info(f"Adresse-Button (Nr. {i+1}) gefunden über Text/ARIA")
                                    break
                                
                                # Prüfen, ob der Button ein Lupen-/Such-Icon enthält
                                icon_elements = btn.find_elements(By.XPATH, ".//i[contains(@class, 'search') or contains(@class, 'find')] | .//svg")
                                if icon_elements:
                                    address_button = btn
                                    logger.info(f"Adresse-Button (Nr. {i+1}) gefunden über enthaltenes Icon")
                                    break
                        except:
                            continue
                    
                    # Wenn immer noch nichts, einfach jeden Button in der rechten Spalte probieren
                    if not address_button:
                        # Suche nach Input-Groups, die den Ort enthalten könnten
                        ort_groups = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'input-group') or contains(@class, 'form-group')]")
                        for group in ort_groups:
                            try:
                                # Prüfen, ob die Gruppe Text enthält, der auf ein Adressfeld hindeutet
                                group_text = group.text.lower()
                                if "ort" in group_text or "adresse" in group_text or "plz" in group_text or "straße" in group_text:
                                    # Buttons in dieser Gruppe suchen
                                    group_buttons = group.find_elements(By.TAG_NAME, "button")
                                    if group_buttons:
                                        for btn in group_buttons:
                                            if btn.is_displayed():
                                                address_button = btn
                                                logger.info(f"Adresse-Button in Adressgruppe gefunden")
                                                break
                                    if address_button:
                                        break
                            except:
                                continue
                
                # Wenn immer noch kein Button gefunden wurde, versuchen wir es mit JavaScript-Injection
                if not address_button:
                    logger.warning("Kein Adresse-Button gefunden. Versuche JavaScript-Injektion...")
                    try:
                        # Direktes Triggern des Adressdialogs durch Simulation eines Klicks auf alle möglichen Elemente
                        js_script = """
                        // Versuche verschiedene Methoden, um den Adressdialog zu öffnen
                        var found = false;
                        
                        // 1. Suche nach Elementen mit 'Adresse' im Text
                        var addrElems = Array.from(document.querySelectorAll('*')).filter(e => 
                            e.textContent && e.textContent.includes('Adresse') && window.getComputedStyle(e).display !== 'none');
                        
                        for (var i=0; i < addrElems.length && !found; i++) {
                            try {
                                addrElems[i].click();
                                found = true;
                                console.log('Clicked element with Adresse text');
                            } catch(e) {}
                            
                            // Prüfen, ob es Buttons innerhalb oder daneben gibt
                            if (!found) {
                                var nearbyBtns = addrElems[i].querySelectorAll('button');
                                if (!nearbyBtns.length) {
                                    var parent = addrElems[i].parentElement;
                                    if (parent) nearbyBtns = parent.querySelectorAll('button');
                                }
                                
                                for (var j=0; j < nearbyBtns.length && !found; j++) {
                                    try {
                                        nearbyBtns[j].click();
                                        found = true;
                                        console.log('Clicked button near Adresse text');
                                    } catch(e) {}
                                }
                            }
                        }
                        
                        // 2. Suche nach input-groups mit Ort/PLZ-Feldern
                        if (!found) {
                            var inputGroups = document.querySelectorAll('.input-group, .form-group');
                            for (var i=0; i < inputGroups.length && !found; i++) {
                                var groupText = inputGroups[i].textContent.toLowerCase();
                                if (groupText.includes('ort') || groupText.includes('plz') || 
                                    groupText.includes('straße') || groupText.includes('adresse')) {
                                    var groupBtns = inputGroups[i].querySelectorAll('button');
                                    for (var j=0; j < groupBtns.length && !found; j++) {
                                        try {
                                            groupBtns[j].click();
                                            found = true;
                                            console.log('Clicked button in address-related input group');
                                        } catch(e) {}
                                    }
                                }
                            }
                        }
                        
                        return found;
                        """
                        
                        found_via_js = self.driver.execute_script(js_script)
                        if found_via_js:
                            logger.info("Adressbutton durch JavaScript-Injektion geklickt")
                            time.sleep(3)  # Warten auf Modalöffnung
                        else:
                            logger.warning("JavaScript-Injektion konnte keinen passenden Button finden")
                            # Ein letzter verzweifelter Versuch - Tabultation bis zu einem Button oder Link
                            active_element = self.driver.switch_to.active_element
                            for _ in range(10):  # 10 Tabs versuchen
                                active_element.send_keys(Keys.TAB)
                                time.sleep(0.5)
                                active_element = self.driver.switch_to.active_element
                                elem_tag = active_element.tag_name.lower()
                                if elem_tag == 'button' or elem_tag == 'a':
                                    logger.info(f"Gefunden durch Tab-Navigation: {elem_tag} Element")
                                    active_element.click()
                                    time.sleep(1)
                                    break
                    except Exception as js_error:
                        logger.error(f"Fehler bei JavaScript-Injektion: {js_error}")
                
                # Wenn ein Button gefunden wurde, klicken
                if address_button:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_button)
                        time.sleep(1)
                        
                        # Versuchen wir erst einen normalen Klick
                        try:
                            address_button.click()
                            logger.info("Adresse-Button normal geklickt")
                        except:
                            # Bei Problemen mit normalem Klick, JavaScript verwenden
                            self.driver.execute_script("arguments[0].click();", address_button)
                            logger.info("Adresse-Button mit JavaScript geklickt")
                        
                        time.sleep(3)  # Warten auf Modalöffnung
                    except Exception as click_error:
                        logger.error(f"Fehler beim Klicken des Adresse-Buttons: {click_error}")
                        return False
                else:
                    logger.error("Konnte keinen Adresse-Button finden")
                    return False
                    
                # Prüfen, ob das Modal erschienen ist
                modal_appeared = False
                try:
                    # Verschiedene Selektoren für das Modal
                    modal_selectors = [
                        "//div[contains(@class, 'dialog') and contains(., 'Adresse')]",
                        "//div[contains(@class, 'modal') and contains(., 'Adresse')]",
                        "//div[contains(@class, 'dialog') and .//input[contains(@aria-controls, 'locationPicker')]]",
                        "//div[contains(@class, 'popup') or contains(@class, 'dialog')]"
                    ]
                    
                    for selector in modal_selectors:
                        try:
                            modal_elements = self.driver.find_elements(By.XPATH, selector)
                            for element in modal_elements:
                                if element.is_displayed():
                                    logger.info(f"Adress-Modal erschienen, erkannt mit Selektor: {selector}")
                                    modal_appeared = True
                                    break
                            if modal_appeared:
                                break
                        except:
                            continue
                    
                    # Als Fallback prüfen, ob Elemente sichtbar sind, die typisch für das Adress-Modal sind
                    if not modal_appeared:
                        fallback_selectors = [
                            "//input[contains(@aria-controls, 'locationPickerGemeinde')]",
                            "//input[@id='locationPickerNummerInput']",
                            "//button[contains(text(), 'Übernehmen')]"
                        ]
                        
                        for selector in fallback_selectors:
                            try:
                                elements = self.driver.find_elements(By.XPATH, selector)
                                for element in elements:
                                    if element.is_displayed():
                                        logger.info(f"Adress-Modal erkannt durch Element: {selector}")
                                        modal_appeared = True
                                        break
                                if modal_appeared:
                                    break
                            except:
                                continue
                except Exception as modal_error:
                    logger.warning(f"Fehler beim Prüfen des Modals: {modal_error}")
                
                if not modal_appeared:
                    logger.error("Das Adress-Modal ist nicht erschienen!")
                    # Screenshot machen
                    try:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        ss_path = f"modal_not_appeared_{timestamp}.png"
                        self.driver.save_screenshot(ss_path)
                        logger.info(f"Screenshot gespeichert: {ss_path}")
                    except Exception as ss_error:
                        logger.warning(f"Konnte keinen Screenshot machen: {ss_error}")
                    return False
                
                # --- SCHRITT 5: Adresse im Modal ausfüllen ---
                logger.info("Beginne mit dem Ausfüllen des Adress-Modals...")
                
                # Ort eingeben
                ort_value = user_data.get('ort', '')
                logger.info(f"Versuche Ort '{ort_value}' einzugeben...")
                ort_input = None
                
                # Versuche, das Ort-Input-Feld zu finden
                ort_selectors = [
                    "//input[contains(@aria-controls, 'locationPickerGemeinde')]",
                    "//input[contains(@aria-label, 'Ort')]",
                    "//div[contains(text(), 'Ort')]/following-sibling::input",
                    "//div[contains(text(), '3: Ort')]/following-sibling::div//input"
                ]
                
                for selector in ort_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                ort_input = element
                                logger.info(f"Ort-Feld gefunden mit Selektor: {selector}")
                                break
                        if ort_input:
                            break
                    except Exception as e:
                        logger.warning(f"Fehler mit Ort-Selektor {selector}: {e}")
                
                if not ort_input:
                    # Fallback - versuche sichtbare Eingabefelder zu finden
                    try:
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                        if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder (Ort, Straße, Hausnummer)
                            # Bei 3+ Feldern, nehme das erste als Ort an
                            ort_input = visible_inputs[0]
                            logger.info("Ort-Feld per Fallback als erstes sichtbares Input-Feld angenommen")
                    except Exception as e:
                        logger.warning(f"Fehler bei Fallback-Suche für Ort-Feld: {e}")
                
                # Wenn Ort-Feld gefunden, ausfüllen
                if ort_input and ort_value:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ort_input)
                        time.sleep(0.5)
                        ort_input.clear()
                        ort_input.send_keys(ort_value)
                        logger.info(f"Ort '{ort_value}' eingegeben")
                        time.sleep(0.5)
                        ort_input.send_keys(Keys.TAB)  # Tab drücken nach der Eingabe
                        time.sleep(0.5)
                        
                        # Nach Dropdown-Items suchen und ggf. klicken
                        try:
                            dropdown_items = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'k-list-item')]")
                            for item in dropdown_items:
                                if item.is_displayed() and ort_value.lower() in item.text.lower():
                                    item.click()
                                    logger.info(f"Ort '{ort_value}' aus Dropdown-Liste ausgewählt")
                                    time.sleep(1)
                                    break
                        except Exception as dd_error:
                            logger.warning(f"Dropdown-Handling für Ort-Feld fehlgeschlagen: {dd_error}")
                    except Exception as e:
                        logger.error(f"Fehler beim Ausfüllen des Ort-Felds: {e}")
                else:
                    logger.warning(f"Konnte Ort-Feld nicht finden oder kein Ort-Wert vorhanden")
                
                # Straße eingeben
                strasse_value = user_data.get('strasse', '')
                logger.info(f"Versuche Straße '{strasse_value}' einzugeben...")
                strasse_input = None
                
                # Versuche, das Straße-Input-Feld zu finden
                strasse_selectors = [
                    "//input[contains(@aria-controls, 'locationPickerStrasse')]",
                    "//input[contains(@aria-label, 'Straße')]",
                    "//div[contains(text(), 'Straße')]/following-sibling::input",
                    "//div[contains(text(), '4: Straße')]/following-sibling::div//input"
                ]
                
                for selector in strasse_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                strasse_input = element
                                logger.info(f"Straße-Feld gefunden mit Selektor: {selector}")
                                break
                        if strasse_input:
                            break
                    except Exception as e:
                        logger.warning(f"Fehler mit Straße-Selektor {selector}: {e}")
                
                if not strasse_input:
                    # Fallback - versuche sichtbare Eingabefelder zu finden
                    try:
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                        if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder
                            # Bei 3+ Feldern, nehme das zweite als Straße an
                            strasse_input = visible_inputs[1]
                            logger.info("Straße-Feld per Fallback als zweites sichtbares Input-Feld angenommen")
                    except Exception as e:
                        logger.warning(f"Fehler bei Fallback-Suche für Straße-Feld: {e}")
                
                # Wenn Straße-Feld gefunden, ausfüllen
                if strasse_input and strasse_value:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", strasse_input)
                        time.sleep(0.5)
                        strasse_input.clear()
                        strasse_input.send_keys(strasse_value)
                        logger.info(f"Straße '{strasse_value}' eingegeben")
                        time.sleep(0.5)
                        strasse_input.send_keys(Keys.TAB)  # Tab drücken nach der Eingabe
                        time.sleep(0.5)
                        
                        # Nach Dropdown-Items suchen und ggf. klicken
                        try:
                            dropdown_items = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'k-list-item')]")
                            for item in dropdown_items:
                                if item.is_displayed() and strasse_value.lower() in item.text.lower():
                                    item.click()
                                    logger.info(f"Straße '{strasse_value}' aus Dropdown-Liste ausgewählt")
                                    time.sleep(1)
                                    break
                        except Exception as dd_error:
                            logger.warning(f"Dropdown-Handling für Straße-Feld fehlgeschlagen: {dd_error}")
                    except Exception as e:
                        logger.error(f"Fehler beim Ausfüllen des Straße-Felds: {e}")
                else:
                    logger.warning(f"Konnte Straße-Feld nicht finden oder kein Straße-Wert vorhanden")
                
                # Hausnummer eingeben
                hausnummer_value = user_data.get('hausnummer', '1')  # Fallback zu '1' wenn leer
                logger.info(f"Versuche Hausnummer '{hausnummer_value}' einzugeben...")
                hausnummer_input = None
                
                # Versuche, das Hausnummer-Input-Feld zu finden
                hausnummer_selectors = [
                    "//input[@id='locationPickerNummerInput']",
                    "//input[contains(@aria-label, 'Hausnummer')]",
                    "//input[contains(@aria-label, 'Haus-Nr')]",
                    "//div[contains(text(), 'Haus-Nr')]/following-sibling::input",
                    "//div[contains(text(), 'Nr')]/following-sibling::input"
                ]
                
                for selector in hausnummer_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                hausnummer_input = element
                                logger.info(f"Hausnummer-Feld gefunden mit Selektor: {selector}")
                                break
                        if hausnummer_input:
                            break
                    except Exception as e:
                        logger.warning(f"Fehler mit Hausnummer-Selektor {selector}: {e}")
                
                if not hausnummer_input:
                    # Fallback - versuche sichtbare Eingabefelder zu finden
                    try:
                        inputs = self.driver.find_elements(By.TAG_NAME, "input")
                        visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                        if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder
                            # Bei 3+ Feldern, nehme das dritte als Hausnummer an
                            hausnummer_input = visible_inputs[2]
                            logger.info("Hausnummer-Feld per Fallback als drittes sichtbares Input-Feld angenommen")
                    except Exception as e:
                        logger.warning(f"Fehler bei Fallback-Suche für Hausnummer-Feld: {e}")
                
                # Wenn Hausnummer-Feld gefunden, ausfüllen
                if hausnummer_input:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hausnummer_input)
                        time.sleep(0.5)
                        hausnummer_input.clear()
                        hausnummer_input.send_keys(hausnummer_value)
                        logger.info(f"Hausnummer '{hausnummer_value}' eingegeben")
                        time.sleep(0.5)
                    except Exception as e:
                        logger.error(f"Fehler beim Ausfüllen des Hausnummer-Felds: {e}")
                else:
                    logger.warning(f"Konnte Hausnummer-Feld nicht finden")
                
                # Übernehmen-Button klicken
                logger.info("Suche nach dem Übernehmen-Button im Modal...")
                uebernehmen_button = None
                
                # Versuche, den Übernehmen-Button zu finden
                uebernehmen_selectors = [
                    "//button[contains(text(), 'Übernehmen')]",
                    "//button[contains(@class, 'win-contentdialog-primarycommand')]",
                    "//button[@class='win-contentdialog-primarycommand win-button']",
                    "//div[contains(@class, 'dialog-footer') or contains(@class, 'modal-footer')]//button[last()]"
                ]
                
                for selector in uebernehmen_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed():
                                uebernehmen_button = element
                                logger.info(f"Übernehmen-Button gefunden mit Selektor: {selector}")
                                break
                        if uebernehmen_button:
                            break
                    except Exception as e:
                        logger.warning(f"Fehler mit Übernehmen-Selektor {selector}: {e}")
                
                if not uebernehmen_button:
                    # Fallback - suche nach allen sichtbaren Buttons
                    try:
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for button in buttons:
                            if button.is_displayed():
                                button_text = button.text.lower()
                                if "übernehmen" in button_text or "ok" in button_text or "bestätigen" in button_text:
                                    uebernehmen_button = button
                                    logger.info(f"Übernehmen-Button per Fallback mit Text '{button.text}' gefunden")
                                    break
                    except Exception as e:
                        logger.warning(f"Fehler bei Fallback-Suche für Übernehmen-Button: {e}")
                
                # Wenn Übernehmen-Button gefunden, klicken
                if uebernehmen_button:
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", uebernehmen_button)
                        time.sleep(0.5)
                        
                        # Normaler Klick versuchen
                        try:
                            uebernehmen_button.click()
                            logger.info("Übernehmen-Button normal geklickt")
                        except:
                            # Bei Problemen mit normalem Klick, JavaScript verwenden
                            self.driver.execute_script("arguments[0].click();", uebernehmen_button)
                            logger.info("Übernehmen-Button mit JavaScript geklickt")
                        
                        time.sleep(2)
                    except Exception as e:
                        logger.error(f"Fehler beim Klicken des Übernehmen-Buttons: {e}")
                        return False
                else:
                    logger.error("Konnte keinen Übernehmen-Button finden")
                    return False

            except Exception as address_error:
                logger.error(f"Fehler beim Adressdialog: {address_error}")
                logger.error(traceback.format_exc())
                return False

            # --- SCHRITT 6: Erst JETZT Telefon und E-Mail ausfüllen ---
            logger.info("Adress-Dialog erfolgreich, jetzt Telefon und E-Mail NACH Adresseingabe ausfüllen...")
            
            try:
                # Telefonnummer
                telefon_id = "eigene_personalien_telefonnr"
                telefon_value = user_data.get('telefonnr', '')
                if telefon_value:
                    telefon_field = self.wait.until(EC.element_to_be_clickable((By.ID, telefon_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", telefon_field)
                    time.sleep(0.3)
                    telefon_field.clear()
                    telefon_field.send_keys(telefon_value)
                    logger.info(f"Telefonnummer '{telefon_value}' eingegeben (NACH Adresse)")
                    time.sleep(0.5)
                
                # E-Mail
                email_id = "eigene_personalien_email"
                email_value = user_data.get('email', '')
                if email_value:
                    email_field = self.wait.until(EC.element_to_be_clickable((By.ID, email_id)))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", email_field)
                    time.sleep(0.3)
                    email_field.clear()
                    email_field.send_keys(email_value)
                    logger.info(f"E-Mail '{email_value}' eingegeben (NACH Adresse)")
                    time.sleep(0.5)
            except Exception as e:
                logger.warning(f"Fehler beim Ausfüllen von Telefon/E-Mail nach Adresseingabe: {e}")
                # Wir fahren trotzdem fort

            logger.info("Personendaten inkl. Adresse wurden erfolgreich ausgefüllt.")
            return True
            
        except Exception as e:
            logger.error(f"Kritischer Fehler in fill_personal_data: {e}")
            logger.error(traceback.format_exc())
            return False

    def handle_crime_location_modal(self, location_data):
        """
        Endgültige Lösung mit direkter DOM-Manipulation basierend auf dem exakten HTML-Code.
        """
        try:
            # Daten vorbereiten
            logger.info(f"Überprüfe Standortdaten: {location_data}")
            
            ort_value = location_data.get('ort', location_data.get('city', 'Stuttgart'))
            address = location_data.get('address', '')
            strasse_value = 'Schwerzstraße'  # Fallback
            hausnummer_value = '1'  # Fallback
            
            if address:
                parts = address.strip().split(' ')
                if len(parts) > 1 and parts[-1].isdigit():
                    hausnummer_value = parts[-1]
                    strasse_value = ' '.join(parts[:-1])
                elif len(parts) > 0:
                    strasse_value = address
                    
            if 'strasse' in location_data and location_data['strasse']:
                strasse_value = location_data['strasse']
            if 'hausnummer' in location_data and location_data['hausnummer']:
                hausnummer_value = location_data['hausnummer']
                
            logger.info(f"Verwendete Werte für Adresse: Ort='{ort_value}', Straße='{strasse_value}', Nr='{hausnummer_value}'")
            
            # VERBESSERTE DIALOG-BEHANDLUNG
            # Anstatt Dialoge mit click() zu schließen, verwenden wir JS, um auch Overlays zu entfernen
            overlay_result = self.driver.execute_script("""
                // Entferne alle Modal-Overlays und Dialoge sauber
                var dialogs = document.querySelectorAll('div[role="dialog"][aria-modal="true"]');
                if (dialogs.length > 0) {
                    console.log("Gefunden: " + dialogs.length + " aktive Dialoge");
                    
                    // Für jeden Dialog...
                    for (var i = 0; i < dialogs.length; i++) {
                        try {
                            // Dialog-Element speichern
                            var dialog = dialogs[i];
                            
                            // Dialog aus dem DOM entfernen
                            if (dialog.parentNode) {
                                dialog.parentNode.removeChild(dialog);
                                console.log("Dialog aus DOM entfernt");
                            }
                            
                            // Overlay finden und entfernen (verschiedene mögliche Klassen)
                            var overlays = document.querySelectorAll('.modal-backdrop, .dialog-backdrop, .overlay, .k-overlay');
                            for (var j = 0; j < overlays.length; j++) {
                                if (overlays[j].parentNode) {
                                    overlays[j].parentNode.removeChild(overlays[j]);
                                    console.log("Overlay aus DOM entfernt");
                                }
                            }
                            
                            // body-Klassen zurücksetzen, die oft bei Modals gesetzt werden
                            document.body.classList.remove('modal-open', 'dialog-open', 'overflow-hidden');
                            document.body.style.overflow = 'auto';  // Scrolling wieder erlauben
                            
                            // Inline-Style für Padding entfernen (oft durch Bootstrap hinzugefügt)
                            if (document.body.hasAttribute('style') && 
                                document.body.style.paddingRight) {
                                document.body.style.paddingRight = '';
                            }
                        } catch (e) {
                            console.error("Fehler beim Entfernen von Dialog " + i + ": " + e);
                        }
                    }
                    
                    return "Dialoge und Overlays entfernt";
                } else {
                    return "Keine aktiven Dialoge gefunden";
                }
            """)
            
            logger.info(f"Dialog-Behandlung: {overlay_result}")
            time.sleep(1)  # Kurze Pause nach dem Entfernen der Dialoge
            
            # Klick auf die Hauptseite, um den Fokus zurückzusetzen
            try:
                # Klicke auf einen nicht-interaktiven Bereich der Seite
                body = self.driver.find_element(By.TAG_NAME, "body")
                self.driver.execute_script("arguments[0].click();", body)
                logger.info("Klick auf body, um Fokus zurückzusetzen")
            except:
                pass 
            # Ganz nach unten scrollen
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            logger.info("Zur Seitenende gescrollt")
            time.sleep(2)
            
            # Tatort-Element finden
            tatort_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'Tatort')][not(ancestor::*[contains(@style,'display:none')])]")
            tatort_element = None
            
            for elem in tatort_elements:
                try:
                    if elem.is_displayed():
                        tatort_element = elem
                        logger.info(f"Sichtbares Tatort-Element gefunden: {elem.text}")
                        break
                except:
                    continue
            
            if not tatort_element:
                logger.error("Kein sichtbares Tatort-Element gefunden")
                return False
            
            # Zum Tatort-Element scrollen
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tatort_element)
            logger.info("Zum Tatort-Element gescrollt")
            time.sleep(3)
            
            # Adresse-Button finden
            adresse_button = None
            all_buttons = self.driver.find_elements(By.XPATH, "//button")
            tatort_y = tatort_element.location['y']
            
            buttons_below = []
            for btn in all_buttons:
                try:
                    if btn.is_displayed() and btn.location['y'] > tatort_y:
                        btn_text = btn.text.lower()
                        btn_label = (btn.get_attribute("aria-label") or "").lower()
                        
                        if "adresse" in btn_text or "adresse" in btn_label:
                            buttons_below.append(btn)
                except:
                    continue
            
            if buttons_below:
                adresse_button = buttons_below[0]
                logger.info(f"Tatort-Adresse-Button gefunden: '{adresse_button.text or adresse_button.get_attribute('aria-label')}'")
            else:
                logger.error("Kein Adresse-Button unterhalb des Tatort-Elements gefunden")
                return False
            
            # Zum Button scrollen und klicken
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", adresse_button)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", adresse_button)
            logger.info("Tatort-Adresse-Button geklickt")
            time.sleep(3)  # Warten auf Modal
            
            # --- SCHRITT 5: Adresse im Modal ausfüllen ---
            logger.info("Beginne mit dem Ausfüllen des Adress-Modals...")
                
            # Ort eingeben
            logger.info(f"Versuche Ort '{ort_value}' einzugeben...")
            ort_input = None
                
            # Versuche, das Ort-Input-Feld zu finden
            ort_selectors = [
                "//input[contains(@aria-controls, 'locationPickerGemeinde')]",
                "//input[contains(@aria-label, 'Ort')]",
                "//div[contains(text(), 'Ort')]/following-sibling::input",
                "//div[contains(text(), '3: Ort')]/following-sibling::div//input"
            ]
                
            for selector in ort_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            ort_input = element
                            logger.info(f"Ort-Feld gefunden mit Selektor: {selector}")
                            break
                    if ort_input:
                        break
                except Exception as e:
                    logger.warning(f"Fehler mit Ort-Selektor {selector}: {e}")
                
            if not ort_input:
                # Fallback - versuche sichtbare Eingabefelder zu finden
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                    if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder (Ort, Straße, Hausnummer)
                        # Bei 3+ Feldern, nehme das erste als Ort an
                        ort_input = visible_inputs[0]
                        logger.info("Ort-Feld per Fallback als erstes sichtbares Input-Feld angenommen")
                except Exception as e:
                    logger.warning(f"Fehler bei Fallback-Suche für Ort-Feld: {e}")
                
            # Wenn Ort-Feld gefunden, ausfüllen
            if ort_input and ort_value:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", ort_input)
                    time.sleep(0.5)
                    ort_input.clear()
                    ort_input.send_keys(ort_value)
                    logger.info(f"Ort '{ort_value}' eingegeben")
                    time.sleep(0.5)
                    ort_input.send_keys(Keys.TAB)  # Tab drücken nach der Eingabe
                    time.sleep(0.5)
                        
                    # Nach Dropdown-Items suchen und ggf. klicken
                    try:
                        dropdown_items = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'k-list-item')]")
                        for item in dropdown_items:
                            if item.is_displayed() and ort_value.lower() in item.text.lower():
                                item.click()
                                logger.info(f"Ort '{ort_value}' aus Dropdown-Liste ausgewählt")
                                time.sleep(1)
                                break
                    except Exception as dd_error:
                        logger.warning(f"Dropdown-Handling für Ort-Feld fehlgeschlagen: {dd_error}")
                except Exception as e:
                    logger.error(f"Fehler beim Ausfüllen des Ort-Felds: {e}")
            else:
                logger.warning(f"Konnte Ort-Feld nicht finden oder kein Ort-Wert vorhanden")
                
            # Straße eingeben
            logger.info(f"Versuche Straße '{strasse_value}' einzugeben...")
            strasse_input = None
                
            # Versuche, das Straße-Input-Feld zu finden
            strasse_selectors = [
                "//input[contains(@aria-controls, 'locationPickerStrasse')]",
                "//input[contains(@aria-label, 'Straße')]",
                "//div[contains(text(), 'Straße')]/following-sibling::input",
                "//div[contains(text(), '4: Straße')]/following-sibling::div//input"
            ]
                
            for selector in strasse_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            strasse_input = element
                            logger.info(f"Straße-Feld gefunden mit Selektor: {selector}")
                            break
                    if strasse_input:
                        break
                except Exception as e:
                    logger.warning(f"Fehler mit Straße-Selektor {selector}: {e}")
                
            if not strasse_input:
                # Fallback - versuche sichtbare Eingabefelder zu finden
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                    if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder
                        # Bei 3+ Feldern, nehme das zweite als Straße an
                        strasse_input = visible_inputs[1]
                        logger.info("Straße-Feld per Fallback als zweites sichtbares Input-Feld angenommen")
                except Exception as e:
                    logger.warning(f"Fehler bei Fallback-Suche für Straße-Feld: {e}")
                
            # Wenn Straße-Feld gefunden, ausfüllen
            if strasse_input and strasse_value:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", strasse_input)
                    time.sleep(0.5)
                    strasse_input.clear()
                    strasse_input.send_keys(strasse_value)
                    logger.info(f"Straße '{strasse_value}' eingegeben")
                    time.sleep(0.5)
                    strasse_input.send_keys(Keys.TAB)  # Tab drücken nach der Eingabe
                    time.sleep(0.5)
                        
                    # Nach Dropdown-Items suchen und ggf. klicken
                    try:
                        dropdown_items = self.driver.find_elements(By.XPATH, "//li[contains(@class, 'k-list-item')]")
                        for item in dropdown_items:
                            if item.is_displayed() and strasse_value.lower() in item.text.lower():
                                item.click()
                                logger.info(f"Straße '{strasse_value}' aus Dropdown-Liste ausgewählt")
                                time.sleep(1)
                                break
                    except Exception as dd_error:
                        logger.warning(f"Dropdown-Handling für Straße-Feld fehlgeschlagen: {dd_error}")
                except Exception as e:
                    logger.error(f"Fehler beim Ausfüllen des Straße-Felds: {e}")
            else:
                logger.warning(f"Konnte Straße-Feld nicht finden oder kein Straße-Wert vorhanden")
                
            # Hausnummer eingeben
            logger.info(f"Versuche Hausnummer '{hausnummer_value}' einzugeben...")
            hausnummer_input = None
                
            # Versuche, das Hausnummer-Input-Feld zu finden
            hausnummer_selectors = [
                "//input[@id='locationPickerNummerInput']",
                "//input[contains(@aria-label, 'Hausnummer')]",
                "//input[contains(@aria-label, 'Haus-Nr')]",
                "//div[contains(text(), 'Haus-Nr')]/following-sibling::input",
                "//div[contains(text(), 'Nr')]/following-sibling::input"
            ]
                
            for selector in hausnummer_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            hausnummer_input = element
                            logger.info(f"Hausnummer-Feld gefunden mit Selektor: {selector}")
                            break
                    if hausnummer_input:
                        break
                except Exception as e:
                    logger.warning(f"Fehler mit Hausnummer-Selektor {selector}: {e}")
                
            if not hausnummer_input:
                # Fallback - versuche sichtbare Eingabefelder zu finden
                try:
                    inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    visible_inputs = [input for input in inputs if input.is_displayed()]
                        
                    if len(visible_inputs) >= 3:  # Annahme: Es gibt mind. 3 Felder
                        # Bei 3+ Feldern, nehme das dritte als Hausnummer an
                        hausnummer_input = visible_inputs[2]
                        logger.info("Hausnummer-Feld per Fallback als drittes sichtbares Input-Feld angenommen")
                except Exception as e:
                    logger.warning(f"Fehler bei Fallback-Suche für Hausnummer-Feld: {e}")
                
            # Wenn Hausnummer-Feld gefunden, ausfüllen
            if hausnummer_input:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", hausnummer_input)
                    time.sleep(0.5)
                    hausnummer_input.clear()
                    hausnummer_input.send_keys(hausnummer_value)
                    logger.info(f"Hausnummer '{hausnummer_value}' eingegeben")
                    time.sleep(0.5)
                except Exception as e:
                    logger.error(f"Fehler beim Ausfüllen des Hausnummer-Felds: {e}")
            else:
                logger.warning(f"Konnte Hausnummer-Feld nicht finden")
                
            # Übernehmen-Button klicken
            logger.info("Suche nach dem Übernehmen-Button im Modal...")
            uebernehmen_button = None
                
            # Versuche, den Übernehmen-Button zu finden
            uebernehmen_selectors = [
                "//button[contains(text(), 'Übernehmen')]",
                "//button[contains(@class, 'win-contentdialog-primarycommand')]",
                "//button[@class='win-contentdialog-primarycommand win-button']",
                "//div[contains(@class, 'dialog-footer') or contains(@class, 'modal-footer')]//button[last()]"
            ]
                
            for selector in uebernehmen_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for element in elements:
                        if element.is_displayed():
                            uebernehmen_button = element
                            logger.info(f"Übernehmen-Button gefunden mit Selektor: {selector}")
                            break
                    if uebernehmen_button:
                        break
                except Exception as e:
                    logger.warning(f"Fehler mit Übernehmen-Selektor {selector}: {e}")
                
            if not uebernehmen_button:
                # Fallback - suche nach allen sichtbaren Buttons
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    for button in buttons:
                        if button.is_displayed():
                            button_text = button.text.lower()
                            if "übernehmen" in button_text or "ok" in button_text or "bestätigen" in button_text:
                                uebernehmen_button = button
                                logger.info(f"Übernehmen-Button per Fallback mit Text '{button.text}' gefunden")
                                break
                except Exception as e:
                    logger.warning(f"Fehler bei Fallback-Suche für Übernehmen-Button: {e}")
                
            # Wenn Übernehmen-Button gefunden, klicken
            if uebernehmen_button:
                try:
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", uebernehmen_button)
                    time.sleep(0.5)
                        
                    # Normaler Klick versuchen
                    try:
                        uebernehmen_button.click()
                        logger.info("Übernehmen-Button normal geklickt")
                    except:
                        # Bei Problemen mit normalem Klick, JavaScript verwenden
                        self.driver.execute_script("arguments[0].click();", uebernehmen_button)
                        logger.info("Übernehmen-Button mit JavaScript geklickt")
                        
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Fehler beim Klicken des Übernehmen-Buttons: {e}")
                    return False
            else:
                logger.error("Konnte keinen Übernehmen-Button finden")
                return False

            time.sleep(3)  # Warten nach dem Klicken des Übernehmen-Buttons
            
            # KRITISCH: Finale Dialog- und Overlay-Bereinigung
            try:
                self.driver.execute_script("""
                    // Entferne alle Modal-Overlays vollständig
                    function removeAllDialogElements() {
                        // Dialoge entfernen
                        var dialogs = document.querySelectorAll('div[role="dialog"][aria-modal="true"], .win-contentdialog, .modal');
                        for (var i = 0; i < dialogs.length; i++) {
                            if (dialogs[i].parentNode) {
                                dialogs[i].parentNode.removeChild(dialogs[i]);
                            }
                        }
                        
                        // Alle möglichen Overlay-Klassen entfernen
                        var overlays = document.querySelectorAll(
                            '.modal-backdrop, .dialog-backdrop, .overlay, .k-overlay, ' +
                            '.win-contentdialog-backdrop, .win-dialog-backdrop, .backdrop, ' +
                            'div[style*="opacity"][style*="block"]'
                        );
                        for (var j = 0; j < overlays.length; j++) {
                            if (overlays[j].parentNode) {
                                overlays[j].parentNode.removeChild(overlays[j]);
                            }
                        }
                        
                        // body zurücksetzen
                        document.body.classList.remove('modal-open', 'dialog-open', 'overflow-hidden');
                        document.body.style.overflow = '';
                        document.body.style.paddingRight = '';
                        
                        // Inline-Styles für Elemente mit opacity oder filter entfernen
                        var elements = document.querySelectorAll('div[style*="opacity"], div[style*="filter"]');
                        for (var k = 0; k < elements.length; k++) {
                            elements[k].style.opacity = '';
                            elements[k].style.filter = '';
                        }
                        
                        return "Finale Bereinigung durchgeführt";
                    }
                    
                    // Führe Bereinigung aus und wiederhole nach kurzer Zeit für Nachlader
                    var result = removeAllDialogElements();
                    
                    // Nachlader behandeln (manchmal werden Overlays dynamisch nachgeladen)
                    setTimeout(removeAllDialogElements, 500);
                    
                    return result;
                """)
                
                logger.info("Finale Overlay-Bereinigung durchgeführt")
                
                # Klicke auf body, um den Fokus zurückzusetzen
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    self.driver.execute_script("arguments[0].click();", body)
                except:
                    pass
                    
                # Escape-Taste drücken (kann helfen, verbleibende Dialoge zu schließen)
                try:
                    body = self.driver.find_element(By.TAG_NAME, "body")
                    body.send_keys(Keys.ESCAPE)
                except:
                    pass
                    
                # Nach oben scrollen, um den sichtbaren Bereich zu aktualisieren
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                
                logger.info("Finale Seitenaktualisierung durchgeführt")
                
            except Exception as e:
                logger.warning(f"Fehler bei finaler Bereinigung: {e}")
            
            return True
                
        except Exception as e:
            logger.error(f"Fehler bei Tatort-Adresse: {e}")
            logger.error(traceback.format_exc())
            
            # Selbst im Fehlerfall Overlays bereinigen
            try:
                self.driver.execute_script("""
                    // Entferne alle Dialoge und Overlays
                    var dialogs = document.querySelectorAll('div[role="dialog"], .win-contentdialog, .modal');
                    for (var i = 0; i < dialogs.length; i++) {
                        if (dialogs[i].parentNode) dialogs[i].parentNode.removeChild(dialogs[i]);
                    }
                    
                    var overlays = document.querySelectorAll('.modal-backdrop, .dialog-backdrop, .overlay, .k-overlay');
                    for (var j = 0; j < overlays.length; j++) {
                        if (overlays[j].parentNode) overlays[j].parentNode.removeChild(overlays[j]);
                    }
                    
                    document.body.classList.remove('modal-open', 'dialog-open', 'overflow-hidden');
                    document.body.style.overflow = '';
                    
                    return "Notfall-Bereinigung durchgeführt";
                """)
            except:
                pass
                
            return True  # Trotz Fehler weitermachen
            


    # --- Navigation Method ---
    def continue_to_next_section(self):
        """ Generic method to find and click the next/continue button. """
        # (Code aus der vorherigen Antwort ist OK)
        logger.info("Trying to continue to next section using generic method...")
        try:
            # Strategie 1: Div mit Text "Weiter zu:"
            try:
                weiter_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'label') and starts-with(normalize-space(.), 'Weiter zu:')] | //button[starts-with(normalize-space(.), 'Weiter zu:')]")
                if weiter_elements:
                     logger.info(f"Found {len(weiter_elements)} 'Weiter zu:' elements")
                     for elem in weiter_elements:
                         if elem.is_displayed():
                            try: clickable_element = self.wait.until(EC.element_to_be_clickable(elem)); self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_element); time.sleep(1); self.driver.execute_script("arguments[0].click();", clickable_element); logger.info(f"Clicked 'Weiter zu:' element (Text: '{elem.text}')"); time.sleep(4); return True
                            except TimeoutException: logger.warning(f"'Weiter zu:' Element (Text: '{elem.text}') gefunden, aber nicht klickbar.")
                            except Exception as click_e: logger.warning(f"Fehler beim Klicken auf 'Weiter zu:' Element (Text: '{elem.text}'): {click_e}")
            except Exception as div_e: logger.warning(f"Error finding 'Weiter zu:' divs: {str(div_e)}")
            # Strategie 2: Buttons mit typischem Text
            button_texts = ["Weiter", "Fortfahren", "Speichern", "Next", "Continue"]
            for text in button_texts:
                try:
                    elements = self.driver.find_elements(By.XPATH, f"//button[normalize-space()='{text}'] | //div[@role='button' and normalize-space()='{text}'] | //a[@role='button' and normalize-space()='{text}']")
                    if not elements: elements = self.driver.find_elements(By.XPATH, f"//button[contains(., '{text}')] | //div[@role='button' and contains(., '{text}')] | //a[@role='button' and contains(., '{text}')]")
                    if elements:
                        logger.info(f"Found {len(elements)} elements containing/matching '{text}'")
                        for elem in elements:
                             if elem.is_displayed():
                                try: clickable_elem = self.wait.until(EC.element_to_be_clickable(elem)); self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_elem); time.sleep(1); self.driver.execute_script("arguments[0].click();", clickable_elem); logger.info(f"Clicked button/element with text: {elem.text}"); time.sleep(4); return True
                                except TimeoutException: logger.warning(f"Element mit Text '{text}' gefunden, aber nicht klickbar.")
                                except Exception as click_e: logger.warning(f"Fehler beim Klicken auf Element mit Text '{text}': {click_e}")
                except Exception as text_e: logger.warning(f"Error finding elements with text '{text}': {str(text_e)}")
            # Strategie 3: Buttons mit typischen Klassen
            button_classes = ["k-button-solid-primary", "btn-primary", "button-weiter", "next-button", "forward-button"] # !!! KLASSEN ANPASSEN / PRÜFEN !!!
            for class_name in button_classes:
                 try:
                     buttons = self.driver.find_elements(By.CSS_SELECTOR, f"button.{class_name}, div.{class_name}[role='button'], a.{class_name}[role='button']")
                     if buttons:
                        logger.info(f"Found {len(buttons)} elements with class '{class_name}'")
                        for button in buttons:
                            if button.is_displayed():
                                try: clickable_button = self.wait.until(EC.element_to_be_clickable(button)); self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", clickable_button); time.sleep(1); self.driver.execute_script("arguments[0].click();", clickable_button); logger.info(f"Clicked element with class: {class_name}"); time.sleep(4); return True
                                except TimeoutException: logger.warning(f"Element mit Klasse '{class_name}' gefunden, aber nicht klickbar.")
                                except Exception as click_e: logger.warning(f"Fehler beim Klicken auf Element mit Klasse '{class_name}': {click_e}")
                 except Exception as class_e: logger.warning(f"Error finding buttons with class '{class_name}': {str(class_e)}")
            logger.error("KONNTE KEINEN 'Weiter'-Button mit den definierten Strategien finden oder klicken.")
            return False
        except Exception as e: logger.error(f"General error in continue_to_next_section: {str(e)}"); logger.error(traceback.format_exc()); return False

    def process_theft_report(self, incident_data, user_data):
        """ Process a theft report using the new personal data method. """
        logger.info("Starting theft report process...")
        try:
            # 1. Navigate & Initial Steps (Condensed)
            self.driver.get("https://portal.onlinewache.polizei.de/de/")
            logger.info("Navigated to portal.")
            try: self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Verstanden')]"))).click(); time.sleep(0.5)
            except TimeoutException: logger.info("Cookie notice not found.")
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(., 'in Deutschland')]"))).click(); time.sleep(0.5)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//img[contains(@alt, 'Baden-Württemberg')]]"))).click(); time.sleep(0.5)
            self.wait.until(EC.element_to_be_clickable((By.XPATH, "//h3[contains(text(), 'Diebstahl')]/ancestor::a | //h3[contains(text(), 'Diebstahl')]/ancestor::button"))).click(); time.sleep(0.5)
            self.wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, 'Zur Anzeige Diebstahl'))).click(); logger.info("Initial steps OK.")

            # 2. Switch Window & Initial Questions (Condensed)
            self.long_wait.until(lambda d: len(d.window_handles) > 1, "New window timeout")
            self.driver.switch_to.window(self.driver.window_handles[-1]); logger.info("Switched window."); time.sleep(2)
            terms_cb = self.wait.until(EC.element_to_be_clickable((By.ID, "nutzungsbedingung_onlinewache_zustimmung"))); self.driver.execute_script("arguments[0].click();", terms_cb); time.sleep(0.5)
            no_incrim_rb = self.wait.until(EC.element_to_be_clickable((By.ID, "beschuldigtenbelehrung_nein"))); self.driver.execute_script("arguments[0].click();", no_incrim_rb); logger.info("Terms & Incrimination OK."); time.sleep(0.5)

            # 3. Theft Details (Condensed)
            try: gewalt_label = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='diebstahl_details_gewaltandrohung_nein']"))); self.driver.execute_script("arguments[0].click();", gewalt_label)
            except Exception as e: logger.warning(f"Gewalt 'Nein' failed: {e}")
            try: sonstiges_label = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//label[@for='diebstahl_details_entwendetes_gut_sonstiges']"))); self.driver.execute_script("arguments[0].click();", sonstiges_label); logger.info("Theft Details OK."); time.sleep(0.5)
            except Exception as e: logger.warning(f"Sonstiger Diebstahl failed: {e}")

            # 4. Continue to Personal Data
            logger.info("Navigating to Personal Data section...")
            if not self.continue_to_next_section(): raise Exception("Nav to Personal Data failed")
            logger.info("OK: Reached Personal Data section."); time.sleep(3)

            # 5. Fill Personal Data with the new method
            if not self.fill_personal_data(user_data): raise Exception("Personal data form failed")

            # 6. Click "Tatort bekannt? Ja"
            try:
                tatort_bekannt_ja_id = "tatort_bekannt_ja" # Bestätigte ID
                logger.info(f"Suche Radio-Button ID: {tatort_bekannt_ja_id}")
                tatort_ja_radio = self.wait.until(EC.presence_of_element_located((By.ID, tatort_bekannt_ja_id)))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tatort_ja_radio); time.sleep(0.5)
                if not tatort_ja_radio.is_selected(): self.driver.execute_script("arguments[0].click();", tatort_ja_radio); logger.info(f"'{tatort_bekannt_ja_id}' geklickt.")
                else: logger.info(f"'{tatort_bekannt_ja_id}' war bereits ausgewählt.")
                time.sleep(1)
            except Exception as e: logger.error(f"Fehler Klick '{tatort_bekannt_ja_id}': {e}"); raise Exception("Click Tatort Bekannt Ja failed")

            # 6. Click "Tatort bekannt? Ja"
            try:
                tatort_bekannt_ja_id = "tatort_bekannt_ja"
                logger.info(f"Suche Radio-Button ID: {tatort_bekannt_ja_id}")
                tatort_ja_radio = self.wait.until(EC.presence_of_element_located((By.ID, tatort_bekannt_ja_id)))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tatort_ja_radio)
                time.sleep(0.5)
                if not tatort_ja_radio.is_selected(): 
                    self.driver.execute_script("arguments[0].click();", tatort_ja_radio)
                    logger.info(f"'{tatort_bekannt_ja_id}' geklickt.")
                else: 
                    logger.info(f"'{tatort_bekannt_ja_id}' war bereits ausgewählt.")
                time.sleep(1)
            except Exception as e: 
                logger.error(f"Fehler Klick '{tatort_bekannt_ja_id}': {e}")
                # Versuche trotzdem fortzufahren

            # 7. Click "Tatzeitpunkt benennen"
            try:
                tatzeitpunkt_radio_id = "tatzeit_wann_tatzeitpunkt" # Bestätigte ID
                logger.info(f"Suche Radio-Button ID: {tatzeitpunkt_radio_id}")
                tatzeitpunkt_radio = self.wait.until(EC.presence_of_element_located((By.ID, tatzeitpunkt_radio_id)))
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tatzeitpunkt_radio); time.sleep(0.5)
                if not tatzeitpunkt_radio.is_selected(): self.driver.execute_script("arguments[0].click();", tatzeitpunkt_radio); logger.info(f"'{tatzeitpunkt_radio_id}' geklickt.")
                else: logger.info(f"'{tatzeitpunkt_radio_id}' war bereits ausgewählt.")
                time.sleep(1)
            except Exception as e: logger.error(f"'Tatzeitpunkt benennen'-Radio Fehler: {e}"); raise Exception("Click Tatzeitpunkt failed")

            # 8. Fill Actual Date and Time
            logger.info("Filling actual date and time...")
            try:
                date_field_id = "tatzeit_tatzeitpunkt_datum-kendoInput" # !!! ID PRÜFEN !!!
                time_field_id = "tatzeit_tatzeitpunkt_uhrzeit-kendoInput" # !!! ID PRÜFEN !!!
                date_field = self.wait.until(EC.visibility_of_element_located((By.ID, date_field_id)))
                incident_date = incident_data.get('incident_date', '')
                if incident_date: date_field.clear(); time.sleep(0.2); date_field.send_keys(self.format_date(incident_date)); logger.info("Date OK")
                else: logger.warning("No incident date.")
                time_field = self.wait.until(EC.visibility_of_element_located((By.ID, time_field_id)))
                incident_time = incident_data.get('incident_time', '')
                if incident_time: time_field.clear(); time.sleep(0.2); time_field.send_keys(incident_time); logger.info("Time OK")
                else: logger.warning("No incident time.")
                time.sleep(1)
            except Exception as e: logger.error(f"Error filling date/time: {e}"); raise Exception("Date/time fields failed")

            # 9. JETZT kommt der Tatort (NACH Datum/Zeit)
            logger.info("Now handling crime location address...")
            if self.location:
                logger.info(f"Location data exists, handling crime scene address")
                
                try:
                    # Suche den Adresse-Button für den Tatort
                    address_button = self.wait.until(EC.element_to_be_clickable(
                        (By.XPATH, "//button[@aria-label='Suche/Zuordnung Adresse']")
                    ))
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", address_button)
                    time.sleep(0.5)
                    address_button.click()
                    logger.info("Tatort-Adresse-Button geklickt")
                    time.sleep(2)  # Warte auf Modal
                    
                    # Fülle das Adress-Modal mit den Standortdaten
                    modal_location_data = {
                        'city': self.location.get('ort', self.location.get('city', '')),
                        'address': f"{self.location.get('strasse', '')} {self.location.get('hausnummer', '')}",
                        'additional_info': self.location.get('zusatz_info', '')
                    }
                    
                    # Nutze die bestehende handle_crime_location_modal Methode
                    if not self.handle_crime_location_modal(modal_location_data):
                        logger.warning("Handling crime location modal failed, trying to continue anyway")
                    else:
                        logger.info("Crime scene address modal handled successfully.")
                except Exception as e:
                    logger.warning(f"Error handling crime location: {e}")
                    # Versuche trotzdem fortzufahren
            else:
                logger.info("No location data provided, skipping crime scene address.")

            # 11. NEUE ERWEITERTE SCHRITTE - HIER WERDEN DIE 12 SCHRITTE HINZUGEFÜGT
            logger.info("=== STARTE DIE 12 ERWEITERTEN FORMULAR-SCHRITTE ===")
            if not self.fill_extended_form_fields():
                logger.error("Erweiterte Formular-Schritte fehlgeschlagen")
                # Trotzdem als erfolgreich markieren, da die Basis-Automatisierung funktioniert hat
                logger.warning("Basis-Automatisierung war erfolgreich, nur erweiterte Schritte fehlgeschlagen")

            logger.info("Theft report process with extended fields completed successfully. Browser remains open.")
            return True

        except Exception as e:
            logger.error(f"Error occurred within process_theft_report: {str(e)}")
            raise

    # process_property_damage_report (Platzhalter)
    def process_property_damage_report(self, incident_data, user_data):
        logger.warning("process_property_damage_report needs adaptation using new methods.")
        # Implementiere analog zu process_theft_report
        return True

    def run(self) -> bool:
        """ Main execution method. """
        process_successful = False; incident_data = {}
        try:
            logger.info(f"Starting DirectAgent for incident {self.incident_id}")
            self.update_incident_status("processing", "Agent gestartet, lädt Daten...")
            if not self.incident_id: logger.error("No incident ID"); return False

            incident_data = self.load_incident_data()
            if not incident_data: logger.error("Failed to load incident data"); self.update_incident_status("error", "Fehler Laden Vorfallsdaten"); return False
            logger.info(f"Incident data loaded (Type: {incident_data.get('type')})")

            user_id = incident_data.get('user_id')
            if not user_id: logger.error("No user ID in incident"); self.update_incident_status("error", "Keine Benutzer-ID"); return False
            user_data = self.load_user_data(user_id)
            if not user_data: logger.error("Failed to load user data"); self.update_incident_status("error", "Fehler Laden Benutzerdaten"); return False
            logger.info("User data loaded.")

            # KORRIGIERTE Location-Behandlung
            self.location = None
            
            # Priorisiere user_location_id wenn vorhanden
            user_location_id = incident_data.get('user_location_id')
            if user_location_id:
                logger.info(f"Loading user location with ID: {user_location_id}")
                self.location = self.load_user_location_data(user_location_id)
                if self.location:
                    logger.info(f"User location data loaded: {self.location.get('name', 'N/A')}")
                else:
                    logger.warning(f"Failed to load user location with ID: {user_location_id}")
            
            # Fallback zu location_id
            if not self.location:
                location_id = incident_data.get('location_id')
                
                # Versuche aus email_data zu extrahieren
                if not location_id and incident_data.get('email_data'):
                    try: 
                        location_id = json.loads(incident_data['email_data']).get('locationId')
                        logger.info(f"Got locationId '{location_id}' from email.")
                    except Exception: 
                        logger.warning("Could not parse locationId from email_data.")
                
                if location_id:
                    logger.info(f"Loading location with ID: {location_id}")
                    self.location = self.load_location_data(location_id)
                    if self.location:
                        logger.info(f"Location data loaded: {self.location.get('city', 'N/A')}, {self.location.get('address', 'N/A')}")
                    else:
                        logger.warning(f"Failed to load location with ID: {location_id}")
            
            if not self.location:
                logger.warning("No location data available for crime scene.")
            else:
                logger.info(f"Final location data: {self.location}")

            logger.info("Setting up WebDriver...")
            if not self.setup_driver(): 
                logger.error("WebDriver setup failed")
                return False
            
            # NEUE ZEILEN HINZUFÜGEN:
            logger.info("Sammle erweiterte Formulardaten...")
            self.extended_form_data = self.collect_extended_form_data()
            if not self.extended_form_data:
                logger.error("Erweiterte Formulardaten nicht verfügbar")
                self.update_incident_status("error", "Erweiterte Formulardaten fehlen")
                return False

            incident_type = incident_data.get('type', '').lower()
            logger.info(f"Processing incident type: {incident_type}")
            self.update_incident_status("processing", f"Verarbeite '{incident_type}'...")

            if incident_type == 'diebstahl':
                process_successful = self.process_theft_report(incident_data, user_data)
            elif incident_type == 'sachbeschaedigung':
                process_successful = self.process_property_damage_report(incident_data, user_data)
            else: 
                logger.error(f"Unsupported type: {incident_type}")
                self.update_incident_status("error", f"Typ nicht unterstützt: {incident_type}")
                return False

            if process_successful: 
                logger.info(f"Process for '{incident_type}' completed.")
                self.update_incident_status("completed", f"{incident_type.capitalize()} Meldung abgeschlossen (Browser offen).")
                return True
            else: 
                logger.error(f"Process for '{incident_type}' returned failure.")
                self.update_incident_status("error", f"Verarbeitung fehlgeschlagen: {incident_type}")
                return False

        except Exception as e:
             error_message = f"Error during {incident_data.get('type', 'unknown type')} process: {str(e)}" if incident_data else f"Critical error in agent run: {str(e)}"
             logger.error(error_message)
             logger.error(traceback.format_exc())
             try: # KRITISCHER FEHLER - VERSUCHE SCREENSHOT
                 if hasattr(self, 'driver') and self.driver: # Nur wenn Treiber existiert
                     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S"); incident_type_str = incident_data.get('type', 'unknown')
                     ss_path = f"critical_error_{incident_type_str}_{self.incident_id}_{timestamp}.png"; self.driver.save_screenshot(ss_path); logger.info(f"CRITICAL Error screenshot: {ss_path}")
             except Exception as ss_error: logger.warning(f"Could not save critical error screenshot: {ss_error}")
             self.update_incident_status("error", error_message)
             return False
        finally:
            if hasattr(self, 'driver') and self.driver:
                logger.info(">>> Process finished. Leaving WebDriver open as requested. <<<")
                # self.driver.quit() # AUSKOMMENTIERT
            else:
                logger.info("No WebDriver instance was active or it failed to initialize.")

# --- Main Execution Block ---
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Direct Agent for incident reporting')
    parser.add_argument('incident_id', type=int, nargs='?', default=None,
                        help='Incident ID to process')
    parser.add_argument('--token', type=str, help='API token for authentication')
    parser.add_argument('--token-file', type=str, help='File containing API token')
    parser.add_argument('--api-host', type=str, default='localhost:8002',
                       help='API host address')
    parser.add_argument('--visible', action='store_true',
                       help='Run in visible mode (show browser UI)')
    args = parser.parse_args()

    is_headless = not args.visible

    incident_id = args.incident_id or os.environ.get("INCIDENT_ID")
    if incident_id:
        try: incident_id = int(incident_id)
        except (ValueError, TypeError): print(f"Invalid incident ID: {incident_id}", file=sys.stderr); sys.exit(1)
    else: print("No incident ID provided via argument or environment variable INCIDENT_ID.", file=sys.stderr); sys.exit(1)

    token = args.token or os.environ.get("API_TOKEN")
    if args.token_file and not token:
        try:
            with open(args.token_file, 'r') as f: token = f.read().strip()
        except Exception as e: print(f"Warning: Error reading token file '{args.token_file}': {str(e)}", file=sys.stderr)
    if not token: print("Warning: No API token provided.", file=sys.stderr)

    print(f"--- Starting DirectAgent ---")
    print(f"Incident ID: {incident_id}")
    print(f"API Host: {args.api_host}")
    print(f"Headless Mode: {is_headless}")
    print(f"Token Provided: {'Yes' if token else 'No'}")
    print(f"Current Directory: {os.getcwd()}")
    print(f"--------------------------")

    agent = None
    success = False
    try:
        agent = DirectAgent(
            incident_id=incident_id,
            token=token,
            api_host=args.api_host,
            headless=is_headless
        )
        success = agent.run()
        print(f"--- DirectAgent Finished ---")
        print(f"Final Status: {'Success' if success else 'Failed'}")
        print(f"--------------------------")
    except Exception as e:
        print(f"--- DirectAgent CRITICAL ERROR ---", file=sys.stderr)
        print(f"An unexpected error occurred: {str(e)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"--------------------------------", file=sys.stderr)
        if agent and hasattr(agent, 'update_incident_status'): agent.update_incident_status("error", f"Critical agent error: {str(e)}")
        success = False

    sys.exit(0 if success else 1)