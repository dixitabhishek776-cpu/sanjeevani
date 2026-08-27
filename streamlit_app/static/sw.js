// Minimal service worker — required for "Add to Home Screen" installability
// on some browsers. Does not attempt aggressive offline caching (Streamlit's
// app is a live, database-backed, session-based app, not a static site —
// caching pages would show stale/broken state). It only enables the
// install prompt and lets network requests pass through normally.
self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", (event) => {
  // Pass-through — no caching. Keeps the app always fresh/live.
  event.respondWith(fetch(event.request));
});
