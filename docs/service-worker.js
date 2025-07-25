const CACHE_NAME = 'usc-cache-v1';

const urlsToCache = [
  '/',                         // Root der GitHub Pages-Seite (wird als / angezeigt)
  '/index.html',               // Startseite
  '/manifest.webmanifest',     // Manifest
  '/icon-192.png',             // App-Icon klein
  '/icon-512.png'              // App-Icon groß
];

// Service Worker Installation → Cache initialisieren
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Aktivierung → Alte Caches entfernen
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      )
    )
  );
});

// Netzwerkabfragen → Aus dem Cache oder aus dem Netz
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      // Antwort aus dem Cache oder vom Server
      return response || fetch(event.request);
    }).catch(() => {
      // Optional: Offline-Fallback hier definieren
    })
  );
});