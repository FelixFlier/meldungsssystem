# agents/sachbeschaedigung_agent.py

# In diebstahl_agent.py und sachbeschaedigung_agent.py
import os
import sys
import traceback
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

# Systemübergreifender Import mit korrektem Pfad
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from agents.base_agent import BaseAgent
from config import get_settings

# Konfiguration laden
settings = get_settings()

# Logger für den Agenten
logger = logging.getLogger(f"{settings.APP_NAME}.sachbeschaedigung_agent")


class SachbeschaedigungAgent(BaseAgent):
    """Agent zur Meldung von Sachbeschädigungen."""
    
    def run(self) -> bool:
        """Führt den Sachbeschädigungs-Agenten aus."""
        try:
            logger.info("Starte Sachbeschädigungs-Agent...")
            
            # Aktualisiere Status
            self.update_incident_status("processing")
            
            # Driver einrichten
            if not self.setup_driver():
                return False
            
            # Lade Vorfallsdaten
            incident_data = self.load_incident_data()
            if not incident_data:
                logger.error("Keine Vorfallsdaten gefunden")
                return False
            
            # Lade Benutzerdaten
            user_data = self.load_user_data(incident_data.get("user_id"))
            if not user_data:
                logger.warning("Keine Benutzerdaten gefunden, verwende Standardwerte")
            
            # Website öffnen
            self.driver.get("https://portal.onlinewache.polizei.de/de/")
            logger.info("Website geöffnet")
            
            # Klicke "Verstanden"
            verstanden_button = self.wait_and_find_element(
                By.XPATH, "//button[contains(., 'Verstanden')]"
            )
            if not verstanden_button or not self.safe_click(verstanden_button):
                logger.error("'Verstanden'-Button nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("'Verstanden'-Button geklickt")
            time.sleep(1)
            
            # Wähle "in Deutschland"
            radio_label = self.wait_and_find_element(
                By.XPATH, "//label[contains(., 'in Deutschland')]"
            )
            if not radio_label or not self.safe_click(radio_label):
                logger.error("'in Deutschland'-Label nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("'in Deutschland' ausgewählt")
            time.sleep(1)
            
            # Wähle Baden-Württemberg
            state_element = self.wait_and_find_element(
                By.XPATH, "//div[contains(@class, 'MuiBox-root') and .//img[@alt='Wappen Baden-Württemberg mit drei Löwen']]"
            )
            if not state_element or not self.safe_click(state_element):
                logger.error("'Baden-Württemberg' nicht gefunden oder konnte nicht ausgewählt werden")
                return False
            logger.info("Baden-Württemberg ausgewählt")
            time.sleep(1)
            
            # Wähle Sachbeschädigung
            sachbeschaedigung_element = self.wait_and_find_element(
                By.XPATH, "//h3[contains(text(), 'Sachbeschädigung')]"
            )
            if not sachbeschaedigung_element or not self.safe_click(sachbeschaedigung_element):
                logger.error("'Sachbeschädigung' nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("'Sachbeschädigung' ausgewählt")
            time.sleep(1)
            
            # Klicke auf "Zur Anzeige Sachbeschädigung"
            display_link = self.wait_and_find_element(
                By.XPATH, "//a[contains(., 'Zur Anzeige Sachbeschädigung (ohne Anmeldung)')]"
            )
            if not display_link or not self.safe_click(display_link):
                logger.error("'Zur Anzeige Sachbeschädigung'-Link nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("'Zur Anzeige Sachbeschädigung' geklickt")
            
            # Wechsle zum neuen Fenster
            self.driver.switch_to.window(self.driver.window_handles[-1])
            logger.info("Zum neuen Fenster gewechselt")
            time.sleep(2)
            
            # Fülle die initialen Formulare aus
            if not self.fill_initial_forms():
                return False
            
            # Persönliche Daten ausfüllen
            if not self.fill_personal_data(user_data):
                return False
            
            # Geburtsland ausfüllen
            geburtsland = user_data.get("geburtsland", "Deutschland") if user_data else "Deutschland"
            if not self.fill_geburtsland(geburtsland):
                return False
            
            # Weitere Formularschritte für Sachbeschädigung
            # ...
            
            # Status aktualisieren
            self.update_incident_status("completed")
            
            logger.info("Sachbeschädigungs-Agent erfolgreich abgeschlossen")
            return True
        
        except Exception as e:
            logger.error(f"Fehler während der Agent-Ausführung: {str(e)}")
            traceback.print_exc()
            
            # Status aktualisieren
            self.update_incident_status("error")
            
            return False
        
        finally:
            # Im Debug-Modus Browser geöffnet lassen
            if settings.DEBUG:
                logger.info("DEBUG-Modus aktiv: Browser bleibt geöffnet")
                input("Drücken Sie Enter, um den Browser zu schließen...")
            else:
                self.cleanup()
    
    def fill_initial_forms(self) -> bool:
        """Füllt die initialen Formulare aus."""
        try:
            logger.info("Fülle initiale Formulare aus...")
            
            # Nutzungsbedingungen akzeptieren
            checkbox_zustimmung = self.wait_and_find_element(
                By.ID, "nutzungsbedingung_onlinewache_zustimmung"
            )
            if not checkbox_zustimmung or not self.safe_click(checkbox_zustimmung):
                logger.error("Nutzungsbedingungen-Checkbox nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("Nutzungsbedingungen akzeptiert")
            time.sleep(1)
            
            # 'Nein' für Selbstbelastung
            radio_nein_selbstbelastung = self.wait_and_find_element(
                By.ID, "beschuldigtenbelehrung_nein"
            )
            if not radio_nein_selbstbelastung or not self.safe_click(radio_nein_selbstbelastung):
                logger.error("'Nein'-Radio für Selbstbelastung nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("'Nein' für Selbstbelastung ausgewählt")
            time.sleep(1)
            
            # Weiter zu Personendaten
            weiter_personendaten_button = self.wait_and_find_element(
                By.XPATH, "//div[@class='label'][contains(text(), 'Weiter zu: Personendaten')]"
            )
            if not weiter_personendaten_button or not self.safe_click(weiter_personendaten_button):
                logger.error("'Weiter zu: Personendaten'-Button nicht gefunden oder konnte nicht geklickt werden")
                return False
            logger.info("Zu Personendaten weitergeleitet")
            time.sleep(2)
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Ausfüllen der initialen Formulare: {str(e)}")
            traceback.print_exc()
            return False
    
    def fill_personal_data(self, user_data=None) -> bool:
        """Füllt die persönlichen Daten aus."""
        try:
            logger.info("Fülle persönliche Daten aus...")
            
            # Wenn keine Benutzerdaten vorhanden sind, verwende Standardwerte
            if not user_data:
                user_data = {
                    "nachname": "Mustermann",
                    "vorname": "Max",
                    "geburtsdatum": "01.01.1990",
                    "geburtsort": "Musterstadt",
                    "telefonnr": "0123456789",
                    "email": "max.mustermann@example.com"
                }
            
            # Dictionary mit Feld-IDs und Werten
            fields = {
                "eigene_personalien_nachname": user_data.get("nachname", ""),
                "eigene_personalien_vorname": user_data.get("vorname", ""),
                "eigene_personalien_gebdat-kendoInput": user_data.get("geburtsdatum", ""),
                "eigene_personalien_geburtsort": user_data.get("geburtsort", ""),
                "eigene_personalien_telefonnr": user_data.get("telefonnr", ""),
                "eigene_personalien_email": user_data.get("email", "")
            }
            
            # Füllt alle Felder aus
            for field_id, value in fields.items():
                field = self.wait_and_find_element(By.ID, field_id)
                if not field or not self.safe_send_keys(field, value):
                    logger.warning(f"Feld '{field_id}' nicht gefunden oder konnte nicht ausgefüllt werden")
                    continue
                time.sleep(0.3)
            
            logger.info("Persönliche Daten wurden eingetragen")
            return True
        except Exception as e:
            logger.error(f"Fehler beim Ausfüllen der persönlichen Daten: {str(e)}")
            traceback.print_exc()
            return False
    
    def fill_geburtsland(self, geburtsland="Deutschland") -> bool:
        """Füllt das Geburtsland-Feld aus."""
        try:
            logger.info(f"Fülle Geburtsland: {geburtsland} ein...")
            birthcountry_input = self.wait_and_find_element(
                By.ID, "eigene_personalien_geburtsland-kendoInput"
            )
            if not birthcountry_input or not self.safe_send_keys(birthcountry_input, geburtsland):
                logger.error("Geburtsland-Feld nicht gefunden oder konnte nicht ausgefüllt werden")
                return False
            
            time.sleep(1)
            
            # Versuche, aus der Dropdown-Liste auszuwählen
            try:
                list_item = self.wait_and_find_element(
                    By.XPATH, f"//li[contains(@class, 'k-list-item') and .//span[contains(., '{geburtsland}')]]",
                    timeout=5
                )
                if list_item and self.safe_click(list_item):
                    logger.info(f"Geburtsland '{geburtsland}' wurde aus der Liste ausgewählt")
                    return True
            except Exception as e:
                logger.warning(f"Fehler beim Auswählen des Geburtslandes aus der Liste: {e}")
            
            # Fallback: Enter drücken
            logger.info("Versuche direktes Bestätigen mit Enter...")
            birthcountry_input.send_keys("\n")
            logger.info("Eingabe bestätigt")
            
            return True
        except Exception as e:
            logger.error(f"Fehler beim Ausfüllen des Geburtslandes: {str(e)}")
            traceback.print_exc()
            return False


# Wenn direkt ausgeführt, starte den Agenten
if __name__ == "__main__":
    # Für Debugging: Aus der Kommandozeile übergeben
    incident_id = os.environ.get("INCIDENT_ID")
    if len(sys.argv) > 1:
        incident_id = sys.argv[1]
    
    # Headless-Modus aus Umgebungsvariable oder Standard
    headless = os.environ.get("SELENIUM_HEADLESS", "True").lower() in ("true", "1", "t")
    
    # Widersprüchliche Debug-Einstellungen prüfen
    if settings.DEBUG and headless:
        print("DEBUG-Modus aktiv, aber SELENIUM_HEADLESS ist True. Setze Headless auf False.")
        headless = False
    
    # Agent erstellen und ausführen
    agent = SachbeschaedigungAgent(headless=headless, incident_id=incident_id)
    success = agent.run()
    
    # Exit-Code für Prozesssteuerung
    exit_code = 0 if success else 1
    sys.exit(exit_code)