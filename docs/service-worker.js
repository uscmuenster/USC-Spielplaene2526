const CACHE_NAME = 'usc-cache-v1';
const urlsToCache = [
  '/',
  '/USC-Spielplaene2526/',
  '/USC-Spielplaene2526/index.html',
  '/USC-Spielplaene2526/manifest.webmanifest',
  '/USC-Spielplaene2526/icon-192.png',
  '/USC-Spielplaene2526/icon-512.png'
];

// Installations-Event: Cache initialisieren
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(urlsToCache);
    })
  );
});

// Aktivierungs-Event: Alte Caches bereinigen
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

// Fetch-Event: Seiten aus dem Cache liefern (Fallback)
self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});