// Service Worker - Disabled for debugging
// This service worker does nothing - just passes through all requests

self.addEventListener('install', (event) => {
  // Skip waiting and activate immediately
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  // Delete all caches
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          console.log('Deleting cache:', cacheName);
          return caches.delete(cacheName);
        })
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Pass through all requests - don't cache anything
self.addEventListener('fetch', (event) => {
  event.respondWith(fetch(event.request));
});
