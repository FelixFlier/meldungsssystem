"""
Diagnose script to help identify agent execution issues.
"""

import os
import sys
import time
import requests
import logging
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("agent-diagnose")

def test_environment():
    """Test environment variables and setup."""
    logger.info("Checking environment variables...")
    
    # Check API Token
    token = os.environ.get("API_TOKEN")
    if not token:
        logger.error("API_TOKEN environment variable not set")
    else:
        logger.info("API_TOKEN found, length: %d", len(token))
    
    # Check Incident ID
    incident_id = os.environ.get("INCIDENT_ID")
    if not incident_id:
        logger.error("INCIDENT_ID environment variable not set")
    else:
        logger.info("INCIDENT_ID: %s", incident_id)
    
    # Check API Host
    api_host = os.environ.get("API_HOST", "localhost:8000")
    logger.info("API_HOST: %s", api_host)
    
    # Check Python path
    logger.info("PYTHONPATH: %s", os.environ.get("PYTHONPATH", "Not set"))
    
    # Check working directory
    logger.info("Current working directory: %s", os.getcwd())
    
    # Check Python executable
    logger.info("Python executable: %s", sys.executable)
    
    # Check Python version
    logger.info("Python version: %s", sys.version)
    
    return True

def test_api_connection():
    """Test connection to the API."""
    logger.info("Testing API connection...")
    
    token = os.environ.get("API_TOKEN")
    api_host = os.environ.get("API_HOST", "localhost:8000")
    
    if not token:
        logger.error("Cannot test API: No API token")
        return False
    
    try:
        # Try to get auth status
        logger.info("Testing auth status endpoint...")
        response = requests.get(
            f"http://{api_host}/api/auth-status",
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.ok:
            logger.info("API connection successful: %s", response.json())
            return True
        else:
            logger.error("API connection failed: %s - %s", response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("Error connecting to API: %s", str(e))
        logger.error(traceback.format_exc())
        return False

def test_update_status():
    """Test updating an incident status."""
    logger.info("Testing incident status update...")
    
    token = os.environ.get("API_TOKEN")
    api_host = os.environ.get("API_HOST", "localhost:8000")
    incident_id = os.environ.get("INCIDENT_ID")
    
    if not token:
        logger.error("Cannot test status update: No API token")
        return False
    
    if not incident_id:
        logger.error("Cannot test status update: No incident ID")
        return False
    
    try:
        # Try a simple status update
        payload = {
            "status": "processing",
            "agent_log": "Diagnostic test update"
        }
        
        logger.info("Sending status update to incident %s...", incident_id)
        response = requests.patch(
            f"http://{api_host}/incidents/{incident_id}",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
            timeout=5
        )
        
        if response.ok:
            logger.info("Status update successful: %s", response.json())
            return True
        else:
            logger.error("Status update failed: %s - %s", response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("Error updating status: %s", str(e))
        logger.error(traceback.format_exc())
        return False

def test_selenium():
    """Test Selenium WebDriver."""
    logger.info("Testing Selenium WebDriver...")
    
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        logger.info("Selenium imports successful")
        
        # Try to setup WebDriver
        logger.info("Setting up Chrome options...")
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--headless')
        
        logger.info("Installing ChromeDriver...")
        service = Service(ChromeDriverManager().install())
        
        logger.info("Creating Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info("Loading test page...")
        driver.get("https://www.google.com")
        
        title = driver.title
        logger.info("Page title: %s", title)
        
        logger.info("Closing WebDriver...")
        driver.quit()
        
        logger.info("Selenium test successful")
        return True
    except Exception as e:
        logger.error("Error testing Selenium: %s", str(e))
        logger.error(traceback.format_exc())
        return False

def main():
    """Run all diagnostic tests."""
    logger.info("Starting agent diagnostics...")
    
    test_results = {
        "environment": test_environment(),
        "api_connection": test_api_connection(),
        "update_status": test_update_status()
    }
    
    # Only test Selenium if requested (can be slow)
    if "--selenium" in sys.argv:
        test_results["selenium"] = test_selenium()
    
    # Print summary
    logger.info("Diagnostic test results:")
    for test, result in test_results.items():
        logger.info("  %s: %s", test, "PASS" if result else "FAIL")
    
    # Overall result
    overall = all(test_results.values())
    logger.info("Overall result: %s", "PASS" if overall else "FAIL")
    
    return 0 if overall else 1

if __name__ == "__main__":
    sys.exit(main())