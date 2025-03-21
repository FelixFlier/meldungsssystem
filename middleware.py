# middleware.py

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import time
import logging
from config import get_settings

settings = get_settings()
logger = logging.getLogger(settings.APP_NAME)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware zum Hinzufügen von Sicherheits-HTTP-Headers.
    Diese Header helfen, die Anwendung gegen verschiedene Arten von Angriffen zu schützen.
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Content-Security-Policy
        # Hier beschränken wir, von welchen Quellen Ressourcen geladen werden dürfen
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' https://cdn.tailwindcss.com https://cdnjs.cloudflare.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data:;"
        
        # XSS-Protection
        # Moderne Browser haben diesen Header größtenteils durch CSP ersetzt
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Type-Options
        # Verhindert MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Frame-Options
        # Verhindert, dass die Seite in einem Frame eingebettet wird (Clickjacking-Schutz)
        response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer-Policy
        # Kontrolliert, wie viel Referrer-Information gesendet wird
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions-Policy (ehemals Feature-Policy)
        # Beschränkt, welche Browser-Features verwendet werden dürfen
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        
        # Strict-Transport-Security
        # Erzwingt HTTPS (nur im Produktionsmodus aktivieren)
        if not settings.DEBUG:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware zum Logging von HTTP-Anfragen und -Antworten.
    """
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Request-Informationen loggen
        logger.info(f"Request: {request.method} {request.url.path}")
        
        # Anfrage weiterleiten
        response = await call_next(request)
        
        # Antwortzeit berechnen
        process_time = time.time() - start_time
        
        # Response-Informationen loggen
        logger.info(f"Response: {response.status_code} ({process_time:.4f}s)")
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Einfache Rate-Limiting-Middleware zum Schutz vor DoS-Angriffen.
    In einer Produktionsumgebung sollte eine robustere Lösung verwendet werden.
    """
    
    def __init__(self, app: ASGIApp, max_requests: int = 100, time_window: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.time_window = time_window
        self.request_log = {}
    
    async def dispatch(self, request: Request, call_next):
        # IP-Adresse des Clients ermitteln
        client_ip = request.client.host if request.client else "unknown"
        
        # Aktuelle Zeit
        current_time = time.time()
        
        # Alte Einträge entfernen
        self.cleanup_old_requests(current_time)
        
        # Anfrage protokollieren
        if client_ip not in self.request_log:
            self.request_log[client_ip] = []
        
        self.request_log[client_ip].append(current_time)
        
        # Prüfen, ob Rate-Limit überschritten wurde
        if len(self.request_log[client_ip]) > self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return Response(
                content="Rate limit exceeded. Please try again later.",
                status_code=429
            )
        
        return await call_next(request)
    
    def cleanup_old_requests(self, current_time):
        """Entfernt alte Anfragen aus dem Log."""
        for ip, timestamps in list(self.request_log.items()):
            # Behalte nur Zeitstempel innerhalb des Zeitfensters
            valid_timestamps = [ts for ts in timestamps if current_time - ts < self.time_window]
            
            if valid_timestamps:
                self.request_log[ip] = valid_timestamps
            else:
                del self.request_log[ip]