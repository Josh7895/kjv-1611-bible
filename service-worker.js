/* Service worker for The Holy Bible — Anno 1611.
   Stale-while-revalidate: serves from cache instantly when available
   (works fully offline once things have loaded once), while quietly
   refreshing the cache from the network in the background when online.

   IMPORTANT: service workers only register on https:// (or localhost).
   Opening this file directly (file://) skips this entirely — the app
   still works, it just won't be installable or offline-capable until
   it's hosted somewhere real. */

/* Bump CACHE_NAME whenever the app files or data/kjv.json change: data/ and
   icons/ are served cache-first, so a new cache name is how updates arrive. */
var CACHE_NAME = "kjv1611-v4";
var RUNTIME_CACHE = "kjv1611-runtime"; // fonts and illustrations seen while reading
var SAVED_CACHE = "kjv1611-saved";     // what the user saved with the download buttons
var RUNTIME_MAX_ENTRIES = 80;
var APP_SHELL = [
  "./",
  "./index.html",
  "./manifest.json",
  "./data/kjv.json",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./icons/apple-touch-icon.png"
];

/* The only other origins the app loads from and may cache at runtime. */
var RUNTIME_ORIGINS = [
  "https://commons.wikimedia.org",
  "https://upload.wikimedia.org",
  "https://thumb.wikimedia.org",
  "https://fonts.googleapis.com",
  "https://fonts.gstatic.com"
];

self.addEventListener("install", function(event){
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache){
      /* cache:"reload" skips the HTTP cache, so install never stores stale copies. */
      return cache.addAll(APP_SHELL.map(function(u){ return new Request(u, {cache:"reload"}); }));
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", function(event){
  event.waitUntil(
    caches.keys().then(function(names){
      return Promise.all(names.filter(function(n){
        return n !== CACHE_NAME && n !== RUNTIME_CACHE && n !== SAVED_CACHE;
      }).map(function(n){ return caches.delete(n); }));
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

/* A response worth keeping: a full 200, never an error or a 206 partial.
   Cross-origin <img>/<link> loads are opaque, so their status can't be read;
   those are kept only from the known runtime origins. */
function isCacheable(resp, url){
  if (!resp) return false;
  if (resp.type === "opaque") return RUNTIME_ORIGINS.indexOf(new URL(url).origin) !== -1;
  return resp.status === 200;
}

/* Keep the runtime cache from growing forever: drop the oldest entries. */
function trimCache(cache, max){
  return cache.keys().then(function(keys){
    return Promise.all(keys.slice(0, Math.max(0, keys.length - max))
      .map(function(k){ return cache.delete(k); }));
  });
}

/* Safari and iOS only play and seek audio that answers Range requests with a
   206, so slice the saved file to the requested bytes. */
function rangeResponse(req, resp){
  var m = /^bytes=(\d*)-(\d*)$/.exec((req.headers.get("range") || "").trim());
  if (!m || (m[1] === "" && m[2] === "") || resp.type === "opaque") return resp;
  return resp.arrayBuffer().then(function(buf){
    var size = buf.byteLength, start, end;
    if (m[1] === ""){ start = Math.max(0, size - Number(m[2])); end = size - 1; }
    else { start = Number(m[1]); end = m[2] === "" ? size - 1 : Math.min(Number(m[2]), size - 1); }
    if (start >= size || start > end){
      return new Response(null, {status:416, statusText:"Range Not Satisfiable",
        headers:{"Content-Range":"bytes */" + size}});
    }
    return new Response(buf.slice(start, end + 1), {status:206, statusText:"Partial Content", headers:{
      "Content-Type": resp.headers.get("Content-Type") || "audio/mpeg",
      "Content-Range": "bytes " + start + "-" + end + "/" + size,
      "Content-Length": String(end - start + 1),
      "Accept-Ranges": "bytes"
    }});
  });
}

/* Network-first with a timeout: try the network, but don't wait forever —
   fall back to the cached copy if the network hasn't answered in time. A
   fresh response is cached whenever the network eventually succeeds, even
   if the timeout already won the race. The query string is ignored, so
   "?utm=x" links still open offline. */
function networkFirstWithTimeout(req, timeoutMs){
  var url = new URL(req.url); url.search = "";
  var network = fetch(req).then(function(networkResp){
    if (isCacheable(networkResp, req.url)){
      var copy = networkResp.clone();
      caches.open(CACHE_NAME).then(function(cache){ cache.put(url.href, copy); });
    }
    return networkResp;
  });
  /* No cached copy yet (first visit): keep waiting for the network. */
  function fromCache(){
    return caches.open(CACHE_NAME).then(function(cache){ return cache.match(url.href); })
      .then(function(cached){ return cached || network; });
  }
  return new Promise(function(resolve){
    var timer = setTimeout(function(){ resolve(fromCache()); }, timeoutMs);
    network.then(function(resp){ clearTimeout(timer); resolve(resp); },
                 function(){ clearTimeout(timer); resolve(fromCache()); });
  });
}

/* data/ (the KJV text) and icons/ only change with a new CACHE_NAME, so
   serve them straight from this version's cache. */
function isVersionedAsset(url){
  return url.origin === self.location.origin && /\/(data|icons)\//.test(url.pathname);
}
function cacheFirst(req){
  return caches.open(CACHE_NAME).then(function(cache){
    return cache.match(req).then(function(cached){
      return cached || fetch(req).then(function(networkResp){
        if (isCacheable(networkResp, req.url)) cache.put(req, networkResp.clone());
        return networkResp;
      });
    });
  });
}

self.addEventListener("fetch", function(event){
  var req = event.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);

  if (isAudio(req)){
    event.respondWith(
      caches.match(req.url).then(function(cached){
        return cached ? rangeResponse(req, cached) : fetch(req);
      })
    );
    return;
  }

  if (isPageRequest(req)){
    event.respondWith(networkFirstWithTimeout(req, 3000));
    return;
  }

  if (isVersionedAsset(url)){
    event.respondWith(cacheFirst(req));
    return;
  }

  var sameOrigin = url.origin === self.location.origin;
  if (!sameOrigin && RUNTIME_ORIGINS.indexOf(url.origin) === -1) return; // not ours: plain network

  event.respondWith(
    caches.match(req).then(function(cached){
      var fetchPromise = fetch(req).then(function(networkResp){
        if (isCacheable(networkResp, req.url)){
          var copy = networkResp.clone();
          caches.open(sameOrigin ? CACHE_NAME : RUNTIME_CACHE).then(function(cache){
            return cache.put(req, copy).then(function(){
              if (!sameOrigin) return trimCache(cache, RUNTIME_MAX_ENTRIES);
            });
          });
        }
        return networkResp;
      }).catch(function(){ return cached; });
      return cached || fetchPromise;
    })
  );
});

/* Lets the page ask the service worker to eagerly pull specific URLs into
   the cache (used for the "download this book for offline" buttons). Replies
   with the request's id and whether each URL was actually saved. */
function saveUrl(cache, url){
  return fetch(url, {mode:"cors"}).catch(function(err){
    /* Illustrations may lack CORS headers; an opaque copy still displays. */
    if (/\.wikimedia\.org$/.test(new URL(url).hostname)) return fetch(url, {mode:"no-cors"});
    throw err;
  }).then(function(resp){
    if (!isCacheable(resp, url)) return {url:url, ok:false, error:"HTTP " + resp.status};
    return cache.put(url, resp).then(function(){ return {url:url, ok:true}; });
  }).catch(function(err){
    return {url:url, ok:false, error:String(err && err.message || err)};
  });
}

self.addEventListener("message", function(event){
  if (event.data && event.data.type === "CACHE_URLS" && Array.isArray(event.data.urls)){
    var id = event.data.id;
    event.waitUntil(
      caches.open(SAVED_CACHE).then(function(cache){
        return Promise.all(event.data.urls.map(function(url){ return saveUrl(cache, url); }));
      }).then(function(results){
        if (event.source) event.source.postMessage({type:"CACHE_URLS_DONE", id:id, results:results});
      })
    );
  }
});
