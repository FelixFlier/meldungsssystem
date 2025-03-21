"""
Base Agent class with common functionality for all agent types.
Updated for compatibility with new architecture.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import requests
import time
import traceback
import logging
import os
import json
import sys
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
# Standardized method for accessing base directory
import os
import sys
from pathlib import Path

# Get the base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Add base directory to path if needed
if __name__ == "__main__" and BASE_DIR not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Cross-platform import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import get_settings

# Load settings
settings = get_settings()

# Logger for agent
logger = logging.getLogger(f"{settings.APP_NAME}.agent")


class BaseAgent:
    """
    Base Agent class providing common functionality for all agents.
    """
    
    def __init__(self, headless: bool = None, incident_id: Optional[int] = None):
        """Initialize the base agent."""
        # Logger configuration
        self.setup_logging()
        
        # Configuration
        self.headless = headless if headless is not None else settings.SELENIUM_HEADLESS
        self.incident_id = incident_id or os.environ.get("INCIDENT_ID")
        
        # Driver and wait objects
        self.driver = None
        self.wait = None
        self.long_wait = None
        
        logger.info(f"Agent initialized (headless={self.headless}, incident_id={self.incident_id})")
    
    def setup_logging(self):
        """Configure logger for the agent."""
        # Add handlers if not already present
        if not logger.handlers:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            ))
            logger.addHandler(console_handler)
            
            # Set log level
            logger.setLevel(logging.INFO)
    
    def setup_driver(self) -> bool:
        """Set up Selenium WebDriver."""
        try:
            logger.info("Configuring Chrome options...")
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            if self.headless:
                chrome_options.add_argument('--headless')
            
            logger.info("Installing ChromeDriver...")
            service = Service(ChromeDriverManager().install())
            
            logger.info("Creating Chrome WebDriver...")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Wait objects for different timeout durations
            self.wait = WebDriverWait(self.driver, 30)
            self.long_wait = WebDriverWait(self.driver, 60)
            
            logger.info("WebDriver successfully initialized")
            return True
        
        except Exception as e:
            logger.error(f"Error setting up WebDriver: {str(e)}")
            traceback.print_exc()
            return False
    
    def load_incident_data(self) -> Dict[str, Any]:
        """Load current incident data."""
        if not self.incident_id:
            logger.warning("No incident ID provided")
            return {}
        
        try:
            api_host = os.environ.get("API_HOST", "localhost:8000")
            logger.info(f"Loading data for incident {self.incident_id}...")
            response = requests.get(
                f"http://{api_host}/incidents/{self.incident_id}",
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN', '')}"}
            )
            
            if response.status_code == 200:
                incident_data = response.json()
                logger.info(f"Incident data successfully loaded")
                return incident_data
            else:
                logger.error(f"Error loading incident data: {response.text}")
                return {}
        
        except Exception as e:
            logger.error(f"Error loading incident data: {str(e)}")
            return {}

    def load_user_data(self, user_id: int) -> Dict[str, Any]:
        """Load user data for given user ID."""
        if not user_id:
            logger.warning("No user ID provided")
            return {}
        
        try:
            api_host = os.environ.get("API_HOST", "localhost:8000")
            logger.info(f"Loading data for user {user_id}...")
            response = requests.get(
                f"http://{api_host}/users/{user_id}",
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN', '')}"}
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

    def update_incident_status(self, status: str) -> bool:
        """Update incident status."""
        if not self.incident_id:
            logger.warning("No incident ID to update status")
            return False
        
        try:
            api_host = os.environ.get("API_HOST", "localhost:8000")
            logger.info(f"Updating status for incident {self.incident_id} to '{status}'...")
            response = requests.patch(
                f"http://{api_host}/incidents/{self.incident_id}",
                json={"status": status},
                headers={"Authorization": f"Bearer {os.environ.get('API_TOKEN', '')}"}
            )
            
            if response.status_code == 200:
                logger.info(f"Status successfully updated")
                return True
            else:
                logger.error(f"Error updating status: {response.text}")
                return False
        
        except Exception as e:
            logger.error(f"Error updating status: {str(e)}")
            return False
    
    def format_date(self, date_str: str) -> str:
        """Format date from YYYY-MM-DD to DD.MM.YYYY."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj.strftime("%d.%m.%Y")
        except Exception as e:
            logger.error(f"Error formatting date: {str(e)}")
            return date_str
    
    def safe_click(self, element, scroll: bool = True, retry: int = 3) -> bool:
        """Click an element with error handling and optional scrolling."""
        for attempt in range(retry):
            try:
                if scroll:
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
                    time.sleep(0.5)
                
                element.click()
                return True
            except Exception as e:
                if attempt == retry - 1:
                    logger.error(f"Error clicking element: {str(e)}")
                    return False
                
                logger.warning(f"Click attempt {attempt + 1} failed, retrying...")
                time.sleep(1)
    
    def safe_send_keys(self, element, text: str, clear: bool = True) -> bool:
        """Enter text into an element with error handling."""
        try:
            if clear:
                element.clear()
            
            element.send_keys(text)
            return True
        except Exception as e:
            logger.error(f"Error entering text: {str(e)}")
            return False
    
    def wait_and_find_element(self, by, value, timeout: int = 30) -> Optional[Any]:
        """Wait for an element and return it if found."""
        try:
            wait = WebDriverWait(self.driver, timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            logger.warning(f"Element not found: {by}={value}")
            return None
        except Exception as e:
            logger.error(f"Error finding element: {str(e)}")
            return None
    
    def cleanup(self):
        """Clean up resources and close browser."""
        if self.driver:
            try:
                logger.info("Closing browser...")
                self.driver.quit()
                logger.info("Browser successfully closed")
            except Exception as e:
                logger.error(f"Error closing browser: {str(e)}")
    
    def run(self) -> bool:
        """
        Main method to be implemented by derived agent classes.
        """
        raise NotImplementedError("This method must be implemented by derived classes")