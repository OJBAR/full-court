// Full Court - Service Worker (real site only, for now - see render.py's
// service_worker_script for why demos/comprehensive don't register this).
//
// Strategy: stale-while-revalidate for every same-origin GET. A repeat
// visit gets an instant response from cache while a fresh copy is fetched
// in the background and saved for next time - freshness itself is NOT this
// worker's job, it's already handled by each page's own checkForNewVersion()
// script (a no-store fetch that force-reloads once if a newer app-version
// is detected), so this worker is free to optimize purely for speed/offline
// without worrying about ever showing genuinely stale content for more than
// a moment.
const CACHE_NAME = "full-court-v1";

self.addEventListener("install", function (event) {
  self.skipWaiting();
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (names) {
      return Promise.all(
        names
          .filter(function (name) { return name !== CACHE_NAME; })
          .map(function (name) { return caches.delete(name); })
      );
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  const req = event.request;
  if (req.method !== "GET" || new URL(req.url).origin !== self.location.origin) return;

  event.respondWith(
    caches.open(CACHE_NAME).then(function (cache) {
      return cache.match(req).then(function (cached) {
        const networkFetch = fetch(req)
          .then(function (res) {
            if (res && res.ok) cache.put(req, res.clone());
            return res;
          })
          .catch(function () { return cached; });
        return cached || networkFetch;
      });
    })
  );
});
