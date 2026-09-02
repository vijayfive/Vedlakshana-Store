// Till — minimal offline app-shell cache.
// Static files are cached so the app opens instantly and works offline;
// data calls to the Google Apps Script backend always go to the network.
const CACHE = 'till-shell-v2';
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
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
