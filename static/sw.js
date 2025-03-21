// static/sw.js
// Service Worker für Offline-Unterstützung und bessere Performance

// Eindeutige Kennung für den Cache
const CACHE_NAME = 'meldungssystem-cache-v1';

// Dateien, die für das Basis-Erlebnis im Cache gespeichert werden sollen
const STATIC_ASSETS = [
  '/',
  '/static/css/animations.css',
  '/static/css/components.css',
  '/static/js/main.js',
  '/static/img/favicon.svg',
  '/static/img/favicon.png'
];

// Installation des Service Workers
self.addEventListener('install', (event) => {
  // Skip waiting, damit der neue Service Worker sofort aktiviert wird
  self.skipWaiting();
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('Cache geöffnet');
        return cache.addAll(STATIC_ASSETS);
      })
      .catch(err => {
        console.error('Fehler beim Cachen von statischen Assets:', err);
      })
  );
});

// Aktivierung des Service Workers
self.addEventListener('activate', (event) => {
  // Alte Caches löschen
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('Lösche alten Cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Claim clients, um den Service Worker sofort zu verwenden
  return self.clients.claim();
});

// Netzwerkanfragen abfangen
self.addEventListener('fetch', (event) => {
  // API-Anfragen nicht cachen (nur online)
  if (event.request.url.includes('/api/') || 
      event.request.url.includes('/token') || 
      event.request.url.includes('/users/') ||
      event.request.url.includes('/incidents/')) {
    return;
  }
  
  // Stale-while-revalidate Strategie für statische Assets
  if (event.request.method === 'GET' && 
      (event.request.url.includes('/static/') || 
       event.request.url === self.location.origin + '/')) {
    
    event.respondWith(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.match(event.request).then((cachedResponse) => {
          // Parallele Netzwerkanfrage
          const fetchPromise = fetch(event.request)
            .then((networkResponse) => {
              // Cache aktualisieren
              if (networkResponse && networkResponse.ok && networkResponse.type === 'basic') {
                cache.put(event.request, networkResponse.clone());
              }
              return networkResponse;
            })
            .catch(() => {
              // Bei Netzwerkfehler: Fallback für HTML-Anfragen
              if (event.request.headers.get('accept').includes('text/html')) {
                return caches.match('/');
              }
              return null;
            });
          
          // Cache-First: Gecachte Antwort oder Netzwerkanfrage
          return cachedResponse || fetchPromise;
        });
      })
    );
  }
});

// Fehlermeldung, wenn die Anwendung offline ist
const OFFLINE_HTML = `
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Offline - Meldungssystem</title>
  <style>
    body {
      font-family: 'Inter', sans-serif;
      background-color: #000000;
      color: #fff;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100vh;
      margin: 0;
      padding: 20px;
      text-align: center;
    }
    .container {
      background: rgba(15, 28, 33, 0.7);
      border: 1px solid rgba(0, 195, 137, 0.1);
      padding: 2rem;
      border-radius: 1rem;
      max-width: 500px;
    }
    h1 {
      color: #00C389;
      margin-bottom: 1rem;
    }
    button {
      background: transparent;
      border: 1px solid #00C389;
      padding: 0.5rem 1.5rem;
      border-radius: 9999px;
      color: white;
      cursor: pointer;
      margin-top: 1rem;
    }
    button:hover {
      background: rgba(0, 195, 137, 0.8);
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Sie sind offline</h1>
    <p>Das Meldungssystem benötigt eine Internetverbindung, um Vorfälle zu erfassen.</p>
    <p>Bitte stellen Sie Ihre Verbindung wieder her und versuchen Sie es erneut.</p>
    <button onclick="window.location.reload()">Erneut versuchen</button>
  </div>
</body>
</html>
`;

// Netzwerkfehlerbehandlung für HTML-Anfragen
self.addEventListener('fetch', (event) => {
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return new Response(OFFLINE_HTML, {
            headers: { 'Content-Type': 'text/html' }
          });
        })
    );
  }
});