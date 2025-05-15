# create_user_locations_table.py
from database import engine, Base
from models import UserLocation  # Stellen Sie sicher, dass das UserLocation Modell importiert wird

# Erstelle alle Tabellen
Base.metadata.create_all(engine)

print("User locations table created successfully!")