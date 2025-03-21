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
        self.api_host = api_host or os.environ.get("API_HOST", "localhost:8000")
        
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
            
            # Prepare data
            payload = {"status": status}
            if message:
                payload["agent_log"] = message
            
            # Make the API call
            response = requests.patch(
                f"http://{self.api_host}/incidents/{self.incident_id}",
                json=payload,
                headers={"Authorization": f"Bearer {self.token}"},
                timeout=10  # 10 second timeout
            )
            
            if response.status_code == 200:
                logger.info(f"Status successfully updated to {status}")
                return True
            else:
                logger.error(f"Error updating status: {response.status_code} - {response.text}")
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
            
            # Update status to processing
            success = self.update_incident_status("processing", "Agent gestartet und verarbeitet den Vorfall...")
            logger.info(f"Status update result: {success}")
            
            # Load incident data
            incident_data = self.load_incident_data()
            if not incident_data:
                logger.error("Failed to load incident data")
                self.update_incident_status("error", "Fehler beim Laden der Vorfallsdaten")
                return False
            
            logger.info(f"Loaded incident data: {incident_data}")
            
            # Load user data
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
                
            logger.info(f"Loaded user data for user {user_id}")
            
            # Simulate successful processing (for demo purposes)
            self.simulate_processing(incident_data, user_data)
            
            # Update status to completed
            self.update_incident_status("completed", "Diebstahl erfolgreich gemeldet.")
            
            logger.info("Agent execution completed successfully")
            return True
            
        except Exception as e:
            error_message = f"Error in DiebstahlAgent: {str(e)}"
            logger.error(error_message)
            logger.error(traceback.format_exc())
            
            # Update status to error
            self.update_incident_status("error", error_message + "\n" + traceback.format_exc())
            
            return False
        finally:
            # Always clean up resources
            self.cleanup()
    
    def simulate_processing(self, incident_data, user_data):
        """Simulate the processing of a theft incident (for demo purposes)."""
        logger.info("Starting simulated processing...")
        
        # Show incident details
        logger.info(f"Processing theft on date {incident_data.get('incident_date')} "
                   f"at time {incident_data.get('incident_time')}")
        
        # Show user details (without sensitive info)
        user_name = f"{user_data.get('vorname', '')} {user_data.get('nachname', '')}"
        logger.info(f"Report for user: {user_name}")
        
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
    parser.add_argument('--api-host', type=str, default='localhost:8000', 
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