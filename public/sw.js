// Контра: сервис-воркер. Запоминает игру, чтобы она открывалась без интернета.
const CACHE = 'kontra-v3';
const CORE = ['/', '/index.html', '/play', '/play.html', '/vendor/three.min.js', '/manifest.webmanifest', '/icon-192.png', '/icon-512.png'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(CORE)).catch(() => {}).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', e => {
  const req = e.request, url = new URL(req.url);
  if (req.method !== 'GET' || url.origin !== location.origin) return;
  if (url.pathname.startsWith('/ws') || url.pathname.startsWith('/auth') || url.pathname.endsWith('.apk')) return;
  // сначала сеть (чтобы обновления приходили сразу), без интернета — из памяти
  e.respondWith(fetch(req).then(res => {
    if (res && res.ok) { const copy = res.clone(); caches.open(CACHE).then(c => c.put(req, copy)); }
    return res;
  }).catch(() => caches.match(req, { ignoreSearch: true }).then(r => r || caches.match(url.pathname === '/' ? '/index.html' : '/play.html'))));
});
