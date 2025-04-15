# tests/test_frontend_integration.py
import unittest
import sys
import os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class TestFrontendIntegration(unittest.TestCase):
    """Frontend-Integrationstests mit Selenium."""
    
    @classmethod
    def setUpClass(cls):
        """Initialisiert den WebDriver für die Tests."""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
        except:
            print("WebDriver konnte nicht initialisiert werden. Tests werden übersprungen.")
            cls.driver = None
    
    @classmethod
    def tearDownClass(cls):
        """Bereinigt den WebDriver nach den Tests."""
        if cls.driver:
            cls.driver.quit()
    
    def setUp(self):
        """Setup für jeden Test."""
        if not self.driver:
            self.skipTest("WebDriver nicht verfügbar")
    
    def test_email_upload_interface(self):
        """Testet, ob die E-Mail-Upload-Schnittstelle korrekt angezeigt wird."""
        self.driver.get("http://localhost:8000")
        
        # Auf Login-Schaltfläche klicken
        login_button = self.wait.until(EC.element_to_be_clickable((By.ID, "loginButton")))
        login_button.click()
        
        # Login-Modal sollte erscheinen
        login_modal = self.wait.until(EC.visibility_of_element_located((By.ID, "login-modal")))
        self.assertTrue(login_modal.is_displayed())
        
        # Anmelden
        username_input = self.driver.find_element(By.ID, "username")
        password_input = self.driver.find_element(By.ID, "password")
        
        username_input.send_keys("testuser")
        password_input.send_keys("testpassword")
        
        login_form = self.driver.find_element(By.ID, "login-form")
        login_form.submit()
        
        # Warten auf erfolgreiche Anmeldung
        time.sleep(2)
        
        # Jetzt auf Diebstahl-Schaltfläche klicken
        diebstahl_button = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-action='agent-click' and @data-type='diebstahl']")
        ))
        diebstahl_button.click()
        
        # Das DateTime-Modal sollte erscheinen
        datetime_modal = self.wait.until(EC.visibility_of_element_located((By.ID, "datetime-modal")))
        self.assertTrue(datetime_modal.is_displayed())
        
        # Der E-Mail-Upload-Bereich sollte vorhanden sein
        email_upload = self.driver.find_element(By.ID, "email-upload")
        self.assertTrue(email_upload is not None)
        
        # Der extrahierte Daten-Vorschaubereich sollte vorhanden sein
        preview_container = self.driver.find_element(By.ID, "extracted-data-preview")
        self.assertTrue(preview_container is not None)
    
    def test_full_incident_flow(self):
        """Testet den gesamten Vorfall-Erstellungsfluss."""
        self.driver.get("http://localhost:8000")
        
        # Auf Login-Schaltfläche klicken und anmelden (wie oben)
        # [...]
        
        # Auf Diebstahl-Schaltfläche klicken
        diebstahl_button = self.wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//button[@data-action='agent-click' and @data-type='diebstahl']")
        ))
        diebstahl_button.click()
        
        # Das DateTime-Modal ausfüllen
        incident_date = self.driver.find_element(By.ID, "incident-date")
        incident_time = self.driver.find_element(By.ID, "incident-time")
        
        incident_date.send_keys("2025-02-09")
        incident_time.send_keys("09:24")
        
        # Formular absenden
        datetime_form = self.driver.find_element(By.ID, "datetime-form")
        datetime_form.submit()
        
        # Warten auf Erfolgsbenachrichtigung
        success_toast = self.wait.until(EC.visibility_of_element_located(
            (By.XPATH, "//div[contains(@class, 'toast') and contains(., 'erfolgreich')]")
        ))
        self.assertTrue(success_toast.is_displayed())
        
        # Vorfälle sollten angezeigt werden
        incidents_container = self.wait.until(EC.visibility_of_element_located((By.ID, "incidents-container")))
        self.assertTrue(incidents_container.is_displayed())
        
        # Es sollte mindestens ein Vorfall in der Tabelle sein
        incident_rows = self.driver.find_elements(By.XPATH, "//table[@aria-labelledby='incidents-heading']//tbody/tr")
        self.assertGreater(len(incident_rows), 0)

if __name__ == '__main__':
    unittest.main()