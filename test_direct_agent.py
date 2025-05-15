# test_direct_agent.py

import os
import sys
import json
import time
import logging
import argparse
import traceback
from pathlib import Path
from selenium.webdriver.common.keys import Keys

# Add the parent directory to sys.path if needed
current_dir = Path(__file__).resolve().parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import the DirectAgent class
from direct_agent import DirectAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("direct_agent_test.log")
    ]
)
logger = logging.getLogger("direct_agent_test")

# Mock data for testing
MOCK_USER_DATA = {
    "username": "test_user",
    "nachname": "Musterfrau",
    "vorname": "Erika",
    "geburtsdatum": "01.05.1985",
    "geburtsort": "Berlin",
    "geburtsland": "Deutschland",
    "telefonnr": "01234567890",
    "email": "erika.musterfrau@example.com",
    "firma": "Test GmbH",
    "ort": "Stuttgart",
    "strasse": "Hauptstraße",
    "hausnummer": "123"
}

MOCK_INCIDENT_THEFT = {
    "id": 42,
    "type": "diebstahl",
    "incident_date": "2025-04-20",
    "incident_time": "14:30",
    "user_id": 1,
    "status": "pending",
    "location_id": 3,
    "email_data": '{"date": "2025-04-20", "time": "14:30", "location": "Stuttgart Mitte", "locationId": 3}'
}

MOCK_INCIDENT_DAMAGE = {
    "id": 43,
    "type": "sachbeschaedigung",
    "incident_date": "2025-04-22",
    "incident_time": "09:15",
    "user_id": 1,
    "status": "pending",
    "location_id": 5,
    "email_data": '{"date": "2025-04-22", "time": "09:15", "location": "Stuttgart West", "locationId": 5}'
}

MOCK_LOCATION_STUTTGART_MITTE = {
    "id": 3,
    "name": "Stuttgart Mitte", 
    "city": "Stuttgart",
    "state": "Baden-Württemberg", 
    "postal_code": "70173",
    "address": "Hauptstätter Str. 70"
}

MOCK_LOCATION_STUTTGART_WEST = {
    "id": 5,
    "name": "Stuttgart West",
    "city": "Stuttgart",
    "state": "Baden-Württemberg",
    "postal_code": "70197",
    "address": "Bebelstraße 22"
}

def run_test_suite():
    """Run the complete test suite."""
    try:
        logger.info("Starting DirectAgent test suite")
        
        # Test theft report
        test_theft_report()
        
        # Test property damage report
        test_property_damage_report()
        
        logger.info("All tests completed successfully")
        return True
    except Exception as e:
        logger.error(f"Test suite failed: {str(e)}")
        traceback.print_exc()
        return False

def test_theft_report():
    """Test the theft report process."""
    logger.info("=== Testing theft report process ===")
    
    # Create a DirectAgent for theft
    agent = create_mock_agent(
        incident_data=MOCK_INCIDENT_THEFT,
        user_data=MOCK_USER_DATA,
        location_data=MOCK_LOCATION_STUTTGART_MITTE
    )
    
    try:
        # Run the agent
        logger.info("Running theft report test")
        success = agent.run()
        
        # Check result
        if success:
            logger.info("✅ Theft report test passed")
        else:
            logger.error("❌ Theft report test failed")
        
        return success
    except Exception as e:
        logger.error(f"Theft report test error: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Ensure cleanup
        try:
            if agent.driver:
                agent.driver.quit()
        except:
            pass

def test_property_damage_report():
    """Test the property damage report process."""
    logger.info("=== Testing property damage report process ===")
    
    # Create a DirectAgent for property damage
    agent = create_mock_agent(
        incident_data=MOCK_INCIDENT_DAMAGE,
        user_data=MOCK_USER_DATA,
        location_data=MOCK_LOCATION_STUTTGART_WEST
    )
    
    try:
        # Run the agent
        logger.info("Running property damage report test")
        success = agent.run()
        
        # Check result
        if success:
            logger.info("✅ Property damage report test passed")
        else:
            logger.error("❌ Property damage report test failed")
        
        return success
    except Exception as e:
        logger.error(f"Property damage report test error: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        # Ensure cleanup
        try:
            if agent.driver:
                agent.driver.quit()
        except:
            pass

def create_mock_agent(incident_data, user_data, location_data):
    """Create a DirectAgent with mock data."""
    # Create agent
    agent = DirectAgent(
        incident_id=incident_data["id"],
        api_host="localhost:8002",
        headless=False
    )
    
    # Override load methods to return mock data
    def mock_load_incident_data(self):
        logger.info(f"Mock: Loading incident data {incident_data['id']}")
        return incident_data
    
    def mock_load_user_data(self, user_id):
        logger.info(f"Mock: Loading user data for user {user_id}")
        return user_data
    
    def mock_load_location_data(self, location_id):
        logger.info(f"Mock: Loading location data for location {location_id}")
        return location_data
    
    def mock_update_incident_status(self, status, message=None):
        logger.info(f"Mock: Updating incident status to {status}")
        if message:
            logger.info(f"Mock: Status message: {message}")
        return True
    
    # Apply mock methods to agent
    import types
    agent.load_incident_data = types.MethodType(mock_load_incident_data, agent)
    agent.load_user_data = types.MethodType(mock_load_user_data, agent)
    agent.load_location_data = types.MethodType(mock_load_location_data, agent)
    agent.update_incident_status = types.MethodType(mock_update_incident_status, agent)
    
    # Set location directly
    agent.location = location_data
    
    return agent

def test_incident_from_database(incident_id, headless=False):
    """Test a real incident from the database."""
    logger.info(f"Testing real incident #{incident_id} from database")
    
    agent = DirectAgent(
        incident_id=incident_id,
        api_host="localhost:8002",
        headless=headless
    )
    
    try:
        success = agent.run()
        if success:
            logger.info(f"✅ Test for incident #{incident_id} passed")
        else:
            logger.error(f"❌ Test for incident #{incident_id} failed")
        return success
    except Exception as e:
        logger.error(f"Error testing incident #{incident_id}: {str(e)}")
        traceback.print_exc()
        return False
    finally:
        try:
            if agent.driver:
                agent.driver.quit()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Test DirectAgent with mock data')
    parser.add_argument('--test-type', choices=['all', 'theft', 'damage', 'db'], default='all',
                       help='Which test to run (all, theft, damage, db)')
    parser.add_argument('--incident-id', type=int, help='Incident ID from database to test')
    parser.add_argument('--headless', action='store_true', help='Run tests in headless mode')
    
    args = parser.parse_args()
    
    if args.test_type == 'all':
        run_test_suite()
    elif args.test_type == 'theft':
        test_theft_report()
    elif args.test_type == 'damage':
        test_property_damage_report()
    elif args.test_type == 'db':
        if not args.incident_id:
            logger.error("You must provide --incident-id when using --test-type=db")
            sys.exit(1)
        test_incident_from_database(args.incident_id, args.headless)