const CACHE_NAME = 'project-focus-v5';

const STATIC_ASSETS = [
  '/offline/',
  '/static/manifest.json',
  '/static/images/pf-logo-512.png',
  '/static/images/ori.jpg'
];

// Install: Cache critical shell assets and activate immediately
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: Purge obsolete cache stores from previous builds
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cache) => {
          if (cache !== CACHE_NAME) {
            return caches.delete(cache);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Engine: Always fetch live network first
self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // HTML page navigation: Always load live from network, never cache HTML snapshots
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request)
        .catch(() => {
          return caches.match('/offline/');
        })
    );
    return;
  }

  // Static Assets & Media: Network first, fall back to cache only when offline
  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200) {
          const responseToCache = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, responseToCache);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        return caches.match(event.request);
      })
  );
}); 