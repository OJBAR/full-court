// Full Court - Service Worker. Identical copy lives in output/demos/ and
// output/comprehensive/ too (a SW's scope defaults to the directory it's
// served from, so each product needs its own file) - see render.py's
// register_service_worker flag for which pages register it.
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
  // Cache-busting requests (checkForNewVersion()'s periodic check, and both
  // its own and manualRefresh()'s "?_r=" reload) carry a unique timestamp
  // query param every time - caching those would just grow the cache
  // forever with entries that can never be matched again. Let the browser
  // handle these directly instead of intercepting them.
  if (/[?&](_v|_r)=/.test(req.url)) return;

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
