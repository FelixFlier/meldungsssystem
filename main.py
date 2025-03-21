"""
Main application entry point for the Meldungssystem API.
Sets up the FastAPI application, middleware, routes, and static serving.
"""
# uvicorn main:app --reload 

from fastapi import FastAPI, Depends, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pathlib import Path
from fastapi.exceptions import HTTPException
import logging
import os
   
# Internal imports
from database import engine, create_tables
from config import get_settings
from utils.log_config import setup_logging
from middleware import (
    SecurityHeadersMiddleware, 
    RequestLoggingMiddleware, 
    RateLimitMiddleware
)
from routes import router as api_router

# Load configuration
settings = get_settings()

# Setup logging
logger = setup_logging()

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    description="Ein modernes System zur Erfassung und Bearbeitung von Vorfällen",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    RateLimitMiddleware, 
    max_requests=100, 
    time_window=60
)

# Setup CORS
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths for static files
static_dir = Path(settings.BASE_DIR) / "static"

# Check if static directory exists
if not static_dir.exists():
    logger.warning(f"Static directory not found at {static_dir}, creating...")
    static_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include all API routes
app.include_router(api_router)

# --- Special Static File Handlers ---

@app.get("/sw.js")
async def get_service_worker():
    """Stellt den Service Worker für die Browser-Registrierung bereit"""
    sw_path = static_dir / "sw.js"
    if not sw_path.exists():
        logger.error(f"Service Worker not found at {sw_path}")
        raise HTTPException(status_code=404, detail="Service Worker not found")
    return FileResponse(sw_path, media_type="application/javascript")

@app.get("/favicon.ico")
async def get_favicon_ico():
    """Stellt das Favicon bereit"""
    favicon_path = static_dir / "img" / "favicon.png"
    if not favicon_path.exists():
        logger.error(f"Favicon.ico not found at {favicon_path}")
        return Response(status_code=404)
    return FileResponse(favicon_path)

@app.get("/favicon.svg")
async def get_favicon_svg():
    """Stellt das SVG-Favicon bereit"""
    favicon_path = static_dir / "img" / "favicon.svg"
    if not favicon_path.exists():
        logger.error(f"Favicon.svg not found at {favicon_path}")
        return Response(status_code=404)
    return FileResponse(favicon_path)

# --- Server Startup and Main Page ---

@app.on_event("startup")
async def startup_event():
    """Wird beim Serverstart ausgeführt."""
    logger.info("Initialisiere Datenbank...")
    await create_tables()  # Now properly awaited
    
    # Stelle sicher, dass alle benötigten Verzeichnisse existieren
    for dir_path in [
        static_dir, 
        static_dir / "css", 
        static_dir / "js", 
        static_dir / "img"
    ]:
        if not dir_path.exists():
            logger.warning(f"Creating missing directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Server-Startup abgeschlossen!") 

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Main page handler that serves the single-page application."""
    try:
        # Check for static index.html
        index_path = static_dir / "index.html"
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                logger.info("Serving index.html from static directory")
                return HTMLResponse(content=f.read())
          
        # Fallback to error page
        logger.error(f"index.html not found at {index_path}")
        return HTMLResponse(content=f"""
        <html>
        <head><title>Fehler beim Laden der Seite</title></head>
        <body style="font-family: sans-serif; background: #000; color: #fff; padding: 20px;">
            <h1 style="color: #00C389;">Fehler beim Laden der Seite</h1>
            <p>Die Anwendung konnte nicht geladen werden.</p>
            <p>Bitte stellen Sie sicher, dass die Datei index.html im static-Verzeichnis existiert.</p>
        </body>
        </html>
        """)
            
    except Exception as e:
        logger.error(f"Error rendering index page: {e}")
        return HTMLResponse(content=f"""
        <html>
        <head><title>Fehler beim Laden der Seite</title></head>
        <body style="font-family: sans-serif; background: #000; color: #fff; padding: 20px;">
            <h1 style="color: #00C389;">Fehler beim Laden der Seite</h1>
            <p>Es ist ein Fehler aufgetreten: {str(e)}</p>
        </body>
        </html>
        """)

@app.get("/api-docs", response_class=HTMLResponse)
async def api_docs_redirect():
    """Redirect to the API documentation."""
    return RedirectResponse(url="/docs")

# Run with Uvicorn if executed directly
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting server from directory: {settings.BASE_DIR}")
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8000, 
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )