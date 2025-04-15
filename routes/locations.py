"""
Location management routes for the Meldungssystem API.
Handles location listing and details.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from typing import List, Optional
import pandas as pd
import io

import crud
import security
from database import get_db, get_db_sync
import models
from schemas import Location, LocationCreate

router = APIRouter()

@router.get("/", response_model=List[Location])
async def read_locations(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db_sync),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get all locations with pagination.
    """
    locations = crud.get_locations(db, skip=skip, limit=limit)
    return locations

@router.get("/{location_id}", response_model=Location)
async def read_location(
    location_id: int, 
    db: Session = Depends(get_db_sync),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Get a specific location by ID.
    """
    location = crud.get_location(db, location_id=location_id)
    if location is None:
        raise HTTPException(status_code=404, detail="Standort nicht gefunden")
    return location

@router.post("/import")
async def import_locations_from_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db_sync),
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Import locations from an Excel file.
    """
    try:
        # Read the Excel file
        content = await file.read()
        
        # Use pandas to read the Excel data
        df = pd.read_excel(io.BytesIO(content))
        
        # Check required columns
        required_columns = ['name', 'city', 'state']
        for column in required_columns:
            if column not in df.columns:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Die Excel-Datei muss eine '{column}'-Spalte enthalten"
                )
        
        # Convert DataFrame to list of dictionaries
        locations_data = df.fillna('').to_dict('records')
        
        # Import locations
        count = crud.import_locations_from_excel(db, locations_data)
        
        return {
            "success": True,
            "message": f"{count} Standorte erfolgreich importiert",
            "imported_count": count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Importieren der Standorte: {str(e)}"
        )