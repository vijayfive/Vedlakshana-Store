// Vedlakshana Store — minimal offline app-shell cache.
// The app shell (HTML) is fetched network-first so updates show up right away
// the next time you're online; it only falls back to the cached copy when
// offline. Static icons/manifest stay cache-first since they rarely change.
// Data calls to the Google Apps Script backend always go straight to the network.
const CACHE = 'vedlakshana-shell-v1';
const SHELL = ['./', './index.html', './manifest.json', './favicon-32.png', './icon-180.png', './icon-192.png', './icon-512.png', './icon-192-maskable.png', './icon-512-maskable.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Never cache calls to the Apps Script backend — always go live.
  if (url.hostname.indexOf('script.google.com') > -1 || url.hostname.indexOf('script.googleusercontent.com') > -1) {
    return;
  }

  const isHTML = e.request.mode === 'navigate' || (e.request.headers.get('accept') || '').indexOf('text/html') > -1;
  if (isHTML) {
    // Network-first for the app shell so a new deploy is picked up immediately
    // instead of being stuck behind whatever was cached last time.
    e.respondWith(
      fetch(e.request)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request).then((cached) => cached || caches.match('./index.html')))
    );
    return;
  }

  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
