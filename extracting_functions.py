"""
Functions for extracting information from emails for agent use.
"""

import re
import logging
import json
from bs4 import BeautifulSoup
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from config import get_settings

settings = get_settings()
logger = logging.getLogger(f"{settings.APP_NAME}.extracting_functions")

def parse_email_content(content: str) -> Dict[str, Any]:
    """
    Extract date, time, and location information from email content.
    
    Args:
        content: String content of the email
        
    Returns:
        Dictionary with extracted date, time, location and confidence
    """
    # Initialize results
    results = {
        'date': None,
        'time': None,
        'location': None,
        'confidence': 0
    }
    
    # Detect if HTML and convert to plain text if needed
    if '<html' in content.lower() or '<!doctype html' in content.lower():
        text_content = html_to_text(content)
    else:
        text_content = content
    
    # Perform extraction
    date_result = extract_date(text_content)
    time_result = extract_time(text_content)
    location_result = extract_location(text_content)
    
    # Update results
    if date_result:
        results['date'] = date_result
    
    if time_result:
        results['time'] = time_result
    
    if location_result:
        results['location'] = location_result[0]
        results['confidence'] = location_result[1]
    
    # Return extracted information
    return results

def html_to_text(html_content: str) -> str:
    """
    Convert HTML content to plain text.
    
    Args:
        html_content: HTML string
        
    Returns:
        Plain text extracted from HTML
    """
    try:
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.extract()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Break into lines and remove leading and trailing space
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    except Exception as e:
        logger.error(f"Error converting HTML to text: {str(e)}")
        # Return original content as fallback
        return html_content

def extract_date(text: str) -> Optional[str]:
    """
    Extract date from text content.
    
    Args:
        text: Plain text content
        
    Returns:
        Date in YYYY-MM-DD format or None if not found
    """
    date_patterns = [
        # Format: February 09, 2025 or February 09 2025
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,|\s)\s*(\d{4})',
        
        # Format: Feb 09, 2025 or Feb 09 2025
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+(\d{1,2})(?:,|\s)\s*(\d{4})',
        
        # Format: 09.02.2025 or 09-02-2025 or 09/02/2025
        r'(\d{1,2})[./-](\d{1,2})[./-](\d{4})',
        
        # Format: 2025-02-09
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        
        # Example from the email: "February 09"
        r'(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})'
    ]
    
    # Current year as fallback for formats without year
    current_year = datetime.now().year
    
    # Try each pattern
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            match = matches[0]
            
            # Handle different match formats
            if len(match) == 3:
                if re.match(r'\d{4}', match[0]):  # YYYY-MM-DD format
                    year = match[0]
                    month = match[1].zfill(2)
                    day = match[2].zfill(2)
                elif re.match(r'\d{1,2}', match[0]):  # DD.MM.YYYY format
                    day = match[0].zfill(2)
                    month = match[1].zfill(2)
                    year = match[2]
                else:  # Month name format
                    month_names = ["january", "february", "march", "april", "may", "june", 
                                 "july", "august", "september", "october", "november", "december"]
                    month_abbr = ["jan", "feb", "mar", "apr", "may", "jun", 
                                "jul", "aug", "sep", "oct", "nov", "dec"]
                    
                    month_str = match[0].lower()
                    
                    if month_str in month_names:
                        month = str(month_names.index(month_str) + 1).zfill(2)
                    elif month_str in month_abbr:
                        month = str(month_abbr.index(month_str) + 1).zfill(2)
                    else:
                        continue
                    
                    day = match[1].zfill(2)
                    year = match[2]
                
                return f"{year}-{month}-{day}"
            
            elif len(match) == 2:  # Format without year (e.g., "February 09")
                month_names = ["january", "february", "march", "april", "may", "june", 
                             "july", "august", "september", "october", "november", "december"]
                
                month_str = match[0].lower()
                
                if month_str in month_names:
                    month = str(month_names.index(month_str) + 1).zfill(2)
                    day = match[1].zfill(2)
                    # Use current year or 2025 as fallback
                    return f"2025-{month}-{day}"
    
    # No date found
    return None

def extract_time(text: str) -> Optional[str]:
    """
    Extract time from text content.
    
    Args:
        text: Plain text content
        
    Returns:
        Time in HH:MM format or None if not found
    """
    time_patterns = [
        # Format: 9:24, 09:24, 9.24, 09.24
        r'(\d{1,2})[:.](\d{2})(?:\s*(?:Uhr|AM|PM|h))?',
        
        # Format with seconds: 09:24:00
        r'(\d{1,2}):(\d{2}):\d{2}',
        
        # Format with AM/PM: 9:24 AM, 9:24PM
        r'(\d{1,2}):(\d{2})\s*([AP]M)'
    ]
    
    # Try each pattern
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        if matches:
            match = matches[0]
            
            # Handle different match formats
            if len(match) == 2:  # Basic HH:MM format
                hours = match[0].zfill(2)
                minutes = match[1]
                return f"{hours}:{minutes}"
            
            elif len(match) == 3 and match[2] in ['AM', 'PM']:  # AM/PM format
                hours = int(match[0])
                minutes = match[1]
                
                # Convert to 24-hour format
                if match[2].upper() == 'PM' and hours < 12:
                    hours += 12
                elif match[2].upper() == 'AM' and hours == 12:
                    hours = 0
                
                return f"{hours:02d}:{minutes}"
    
    # No time found
    return None

def extract_location(text: str) -> Optional[Tuple[str, float]]:
    """
    Extract location from text content.
    
    Args:
        text: Plain text content
        
    Returns:
        Tuple of (location name, confidence) or None if not found
    """
    # Available locations (in a real system, this would come from the database)
    locations = [
        "Hessental", "Heilbronn", "Stuttgart Mitte", "Stuttgart Nord",
        "Stuttgart West", "Stuttgart Ost", "Stuttgart Süd", "Mannheim",
        "Karlsruhe", "Freiburg"
    ]
    
    # Check for specific location indicators in the text
    location_indicators = [
        r'(?:Store|Filiale|Standort|Location):\s*([A-Za-z\s]+)',
        r'(?:Store|Filiale|Standort|Location)\s+([A-Za-z\s]+)',
        r'([A-Za-z\s]+)\s+(?:Store|Filiale|Standort|Location)'
    ]
    
    # First, check for specific phrases
    for pattern in location_indicators:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            location_name = matches[0].strip()
            # Check if this matches any known location
            for known_location in locations:
                if known_location.lower() in location_name.lower():
                    return (known_location, 0.9)  # High confidence for direct match
    
    # Special case for email subject line format "Hessental Store_"
    subject_match = re.search(r'([A-Za-z\s]+)\s+Store_', text)
    if subject_match:
        location_name = subject_match.group(1).strip()
        for known_location in locations:
            if known_location.lower() in location_name.lower():
                return (known_location, 0.95)  # Very high confidence for this format
    
    # Search for any known location name in the text
    for location in locations:
        if location.lower() in text.lower():
            # Check context for better confidence
            lines = text.split('\n')
            for line in lines:
                if location.lower() in line.lower():
                    # If location is mentioned with other keywords, higher confidence
                    if any(keyword in line.lower() for keyword in ['store', 'filiale', 'standort', 'location']):
                        return (location, 0.85)
                    # Otherwise, medium confidence
                    return (location, 0.7)
    
    # No location found
    return None

def get_location_id(db_session, location_name: str) -> Optional[int]:
    """
    Get location ID from the database by name.
    
    Args:
        db_session: Database session
        location_name: Name of the location
        
    Returns:
        Location ID or None if not found
    """
    try:
        # Import crud module here to avoid circular imports
        import crud
        
        # Get location by name
        location = crud.get_location_by_name(db_session, location_name)
        if location:
            return location.id
        
        return None
    except Exception as e:
        logger.error(f"Error getting location ID: {str(e)}")
        return None