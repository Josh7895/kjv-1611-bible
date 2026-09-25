/* Service worker for The Holy Bible — Anno 1611.
   Stale-while-revalidate: serves from cache instantly when available
   (works fully offline once things have loaded once), while quietly
   refreshing the cache from the network in the background when online.

   IMPORTANT: service workers only register on https:// (or localhost).
   Opening this file directly (file://) skips this entirely — the app
   still works, it just won't be installable or offline-capable until
   it's hosted somewhere real. */

var CACHE_NAME = "kjv1611-v3";
var APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./data/kjv.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png"
];

self.addEventListener("install", function(event){
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){ return cache.addAll(APP_SHELL); })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function(event){
  event.waitUntil(
    caches.keys().then(function(names){
      return Promise.all(names.filter(function(n){ return n !== CACHE_NAME; })
        .map(function(n){ return caches.delete(n); }));
    })
  );
  self.clients.claim();
});

/* Audio (narration, hymns) is large: never cache it just because it played.
   It is only served from cache if the user saved it with the download button. */
function isAudio(req){
  return req.destination === "audio" || req.destination === "video" ||
         req.headers.has("range") || /\.(mp3|ogg|m4a|wav)(\?|$)/i.test(req.url);
}

/* The page itself: navigations, and same-origin requests for index.html or
   "./" — so a new deploy reaches online visitors on their next visit, while
   offline visitors still get the cached copy. */
function isPageRequest(req){
  if (req.mode === "navigate") return true;
  try{
    var url = new URL(req.url);
    if (url.origin !== self.location.origin) return false;
    return /\/$/.test(url.pathname) || /(^|\/)index\.html$/.test(url.pathname);
  }catch(e){ return false; }
}

/* Network-first with a timeout: try the network, but don't wait forever —
   fall back to the cached copy if the network hasn't answered in time. A
   fresh response is cached whenever the network eventually succeeds, even
   if the timeout already won the race. */
function networkFirstWithTimeout(req, timeoutMs){
  var network = fetch(req).then(function(networkResp){
    if (networkResp && (networkResp.status === 200 || networkResp.type === "opaque")){
      var copy = networkResp.clone();
      caches.open(CACHE_NAME).then(function(cache){ cache.put(req, copy); });
    }
    return networkResp;
  });
  /* No cached copy yet (first visit): keep waiting for the network. */
  function fromCache(){
    return caches.match(req).then(function(cached){ return cached || network; });
  }
  return new Promise(function(resolve){
    var timer = setTimeout(function(){ resolve(fromCache()); }, timeoutMs);
    network.then(function(resp){ clearTimeout(timer); resolve(resp); },
                 function(){ clearTimeout(timer); resolve(fromCache()); });
  });
}

self.addEventListener("fetch", function(event){
  var req = event.request;
  if (req.method !== "GET") return;

  if (isAudio(req)){
    event.respondWith(
      caches.match(req.url).then(function(cached){ return cached || fetch(req); })
    );
    return;
  }

  if (isPageRequest(req)){
    event.respondWith(networkFirstWithTimeout(req, 3000));
    return;
  }

  event.respondWith(
    caches.match(req).then(function(cached){
      var fetchPromise = fetch(req).then(function(networkResp){
        if (networkResp && (networkResp.status === 200 || networkResp.type === "opaque")){
          var copy = networkResp.clone();
          caches.open(CACHE_NAME).then(function(cache){ cache.put(req, copy); });
        }
        return networkResp;
      }).catch(function(){ return cached; });
      return cached || fetchPromise;
    })
  );
});

/* Lets the page ask the service worker to eagerly pull specific URLs into
   the cache (used for the "download this book for offline" button). */
self.addEventListener("message", function(event){
  if (event.data && event.data.type === "CACHE_URLS" && Array.isArray(event.data.urls)){
    event.waitUntil(
      caches.open(CACHE_NAME).then(function(cache){
        return Promise.all(event.data.urls.map(function(url){
          return fetch(url, {mode:"cors"}).then(function(resp){
            if (resp && (resp.status===200 || resp.type==="opaque")) return cache.put(url, resp);
          }).catch(function(){ /* ignore individual failures */ });
        }));
      }).then(function(){
        if (event.source) event.source.postMessage({type:"CACHE_URLS_DONE"});
      })
    );
  }
});
