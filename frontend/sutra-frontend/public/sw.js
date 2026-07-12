const CACHE_NAME = 'sutra-go-v5'; // Bumped version to force cache wipe
const APP_SHELL = ['/', '/manifest.webmanifest', '/favicon.svg'];

self.addEventListener('install', (event) => {
  self.skipWaiting(); // Force instant activation
});

self.addEventListener('activate', (event) => {
  // Nuke ALL old caches to clear corrupted routing
  event.waitUntil(
    caches.keys().then((keys) => Promise.all(
      keys.map((key) => caches.delete(key))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  // 1. Bypass Service Worker entirely for WebSockets and Vite HMR
  if (event.request.url.includes('ws://') || event.request.url.includes('__vite')) {
    return;
  }

  // 2. API Calls: Try network, fail gracefully without throwing console errors
  if (event.request.url.includes(':8000')) {
    event.respondWith(
      fetch(event.request).catch(() => {
        return new Response(JSON.stringify({ status: "offline", message: "Backend unreachable" }), {
          status: 503, 
          headers: { 'Content-Type': 'application/json' }
        });
      })
    );
    return;
  }

  // 3. Static Assets & SPA Routing
  if (event.request.mode === 'navigate') {
    event.respondWith(
      fetch(event.request).catch(() => caches.match('/'))
    );
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      return cachedResponse || fetch(event.request).catch(() => {
        console.warn('Asset fetch failed:', event.request.url);
      });
    })
  );
});