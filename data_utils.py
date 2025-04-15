"""
Utilities for data management and import.
"""

import os
import pandas as pd
import logging
from pathlib import Path
import traceback
from sqlalchemy.orm import Session
from typing import List, Dict, Any

import models
import crud
from config import get_settings

settings = get_settings()
logger = logging.getLogger(f"{settings.APP_NAME}.data_utils")

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

def ensure_data_directory():
    """
    Ensure the data directory exists.
    Creates it if it doesn't exist.
    """
    if not DATA_DIR.exists():
        logger.info(f"Creating data directory at {DATA_DIR}")
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return True
    return False

def import_locations_from_excel(db: Session, excel_path: Path = None) -> int:
    """
    Import locations from the provided Excel file or from the default path.
    
    Args:
        db: Database session
        excel_path: Path to the Excel file (optional, defaults to data/polizei_standorte.xlsx)
        
    Returns:
        int: Number of imported locations
    """
    try:
        # Ensure data directory exists
        ensure_data_directory()
        
        # Default path
        if not excel_path:
            excel_path = DATA_DIR / "polizei_standorte.xlsx"
        
        # Check if file exists
        if not excel_path.exists():
            logger.warning(f"Excel file not found at {excel_path}")
            return 0
        
        # Read Excel file
        logger.info(f"Reading Excel file from {excel_path}")
        df = pd.read_excel(excel_path)
        
        # Convert DataFrame to list of dictionaries
        locations_data = df.fillna('').to_dict('records')
        
        # Import locations
        count = crud.import_locations_from_excel(db, locations_data)
        logger.info(f"Imported {count} locations from {excel_path}")
        
        return count
    
    except Exception as e:
        logger.error(f"Error importing locations from Excel: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def create_sample_locations(db: Session) -> int:
    """
    Create sample locations if no Excel file is available.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of created locations
    """
    try:
        # Sample location data
        sample_locations = [
            {"name": "Hessental", "city": "Schwäbisch Hall", "state": "Baden-Württemberg", "postal_code": "74523", "address": "Hessentaler Str. 25"},
            {"name": "Heilbronn", "city": "Heilbronn", "state": "Baden-Württemberg", "postal_code": "74072", "address": "Karlstraße 108"},
            {"name": "Stuttgart Mitte", "city": "Stuttgart", "state": "Baden-Württemberg", "postal_code": "70173", "address": "Hauptstätter Str. 70"},
            {"name": "Stuttgart Nord", "city": "Stuttgart", "state": "Baden-Württemberg", "postal_code": "70191", "address": "Wolframstraße 54"},
            {"name": "Stuttgart West", "city": "Stuttgart", "state": "Baden-Württemberg", "postal_code": "70197", "address": "Bebelstraße 22"},
            {"name": "Stuttgart Ost", "city": "Stuttgart", "state": "Baden-Württemberg", "postal_code": "70188", "address": "Landhausstraße 110"},
            {"name": "Stuttgart Süd", "city": "Stuttgart", "state": "Baden-Württemberg", "postal_code": "70178", "address": "Hohenheimer Str. 10"},
            {"name": "Mannheim", "city": "Mannheim", "state": "Baden-Württemberg", "postal_code": "68161", "address": "L4, 16"},
            {"name": "Karlsruhe", "city": "Karlsruhe", "state": "Baden-Württemberg", "postal_code": "76133", "address": "Beiertheimer Allee 16"},
            {"name": "Freiburg", "city": "Freiburg", "state": "Baden-Württemberg", "postal_code": "79098", "address": "Heinrich-von-Stephan-Str. 4"},
        ]
        
        # Import sample locations
        count = crud.import_locations_from_excel(db, sample_locations)
        logger.info(f"Created {count} sample locations")
        
        return count
    
    except Exception as e:
        logger.error(f"Error creating sample locations: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

def initialize_locations(db: Session) -> int:
    """
    Initialize locations from Excel file or create sample locations if file not found.
    
    Args:
        db: Database session
        
    Returns:
        int: Number of imported/created locations
    """
    try:
        # Check if locations already exist
        existing_count = db.query(models.Location).count()
        if existing_count > 0:
            logger.info(f"Found {existing_count} existing locations, skipping import")
            return existing_count
        
        # Try to import from Excel file first
        excel_path = DATA_DIR / "polizei_standorte.xlsx"
        if excel_path.exists():
            return import_locations_from_excel(db, excel_path)
        else:
            logger.warning(f"Excel file not found at {excel_path}, creating sample locations")
            return create_sample_locations(db)
    
    except Exception as e:
        logger.error(f"Error initializing locations: {str(e)}")
        logger.error(traceback.format_exc())
        return 0