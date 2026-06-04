// Cathedral Network Service Worker v5 – No POST caching, self-destructs old caches

const CACHE_NAME = 'cathedral-v5';
const STATIC_URLS = [
  '/',
  '/index.html',
  '/about.html',
  '/archive.html',
  '/spotter.html',
  '/sources.html',
  '/constitution.html',
  '/wardens.html',
  '/hewd.html',
  '/threat-matrix.html',
  '/glossary.html',
  '/undp-demo.html',
    '/pra.html',
   '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      // Cache only GET requests for static assets – skip any that fail
      return Promise.allSettled(
        STATIC_URLS.map(url => fetch(url).then(res => {
          if (res.ok && res.method === 'GET') cache.put(url, res);
        }).catch(() => {}))
      );
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('fetch', event => {
  // For non-GET requests, never cache – just fetch directly
  if (event.request.method !== 'GET') {
    event.respondWith(fetch(event.request));
    return;
  }
  // For GET requests: network first, fallback to cache
  event.respondWith(
    fetch(event.request)
      .then(response => {
        const clone = response.clone();
        caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.map(key => {
        if (key !== CACHE_NAME) return caches.delete(key);
      })
    )).then(() => self.clients.claim())
  );
});
