"""
CRUD operations for location management.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy import update, select
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

import models
import schemas

def get_location(db, location_id: int):
    """Get a location by ID."""
    return db.query(models.Location).filter(models.Location.id == location_id).first()

def get_location_by_name(db, name: str):
    """Get a location by name."""
    return db.query(models.Location).filter(models.Location.name == name).first()

def get_locations(db, skip: int = 0, limit: int = 100):
    """Get all locations with pagination."""
    return db.query(models.Location).offset(skip).limit(limit).all()

def create_location(db, location: schemas.LocationCreate):
    """Create a new location."""
    db_location = models.Location(**location.dict())
    db.add(db_location)
    db.commit()
    db.refresh(db_location)
    return db_location

def update_location(db, location_id: int, location_update: schemas.LocationCreate):
    """Update a location."""
    db_location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not db_location:
        return None
    
    update_data = location_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
    
    db.commit()
    db.refresh(db_location)
    return db_location

def delete_location(db, location_id: int):
    """Delete a location."""
    db_location = db.query(models.Location).filter(models.Location.id == location_id).first()
    if not db_location:
        return False
    
    db.delete(db_location)
    db.commit()
    return True

def find_location_by_fuzzy_name(db, name: str, threshold: float = 0.6):
    """
    Find location by fuzzy name matching.
    
    Args:
        db: Database session
        name: Location name to search for
        threshold: Similarity threshold (0-1)
        
    Returns:
        Best match location or None if not found
    """
    from difflib import SequenceMatcher
    
    # Get all locations
    locations = get_locations(db)
    
    best_match = None
    best_score = 0
    
    # Normalize input name
    normalized_name = name.lower().strip()
    
    for location in locations:
        # Check for exact match first
        if location.name.lower() == normalized_name:
            return location
        
        # Calculate similarity
        similarity = SequenceMatcher(None, location.name.lower(), normalized_name).ratio()
        
        # Check if partial match (contains)
        contains_score = 0
        if normalized_name in location.name.lower():
            contains_score = 0.8
        elif location.name.lower() in normalized_name:
            contains_score = 0.7
        
        # Use best of similarity or contains
        score = max(similarity, contains_score)
        
        # Also check city name for matches
        city_similarity = SequenceMatcher(None, location.city.lower(), normalized_name).ratio()
        if city_similarity > score:
            score = city_similarity * 0.9  # Slightly lower confidence for city matches
        
        # Update best match if better score found
        if score > best_score and score >= threshold:
            best_match = location
            best_score = score
    
    return best_match if best_score >= threshold else None

def get_or_create_location(db, location_name: str):
    """
    Get a location by name or create it if not found.
    
    Args:
        db: Database session
        location_name: Name of the location
        
    Returns:
        Location object
    """
    # First check for exact match
    location = get_location_by_name(db, location_name)
    
    if location:
        return location
    
    # Try fuzzy matching if exact match not found
    location = find_location_by_fuzzy_name(db, location_name)
    
    if location:
        return location
    
    # Create new location if not found
    location_data = schemas.LocationCreate(
        name=location_name,
        city="Unbekannt",
        state="Unbekannt"
    )
    
    return create_location(db, location_data)