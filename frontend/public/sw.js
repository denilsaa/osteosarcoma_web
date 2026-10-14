/* Osteosarcoma - cache exclusiva de recursos publicos de interfaz.
 * NUNCA almacenar respuestas API, tokens, historias clinicas, imagenes del usuario.
 */
const CACHE_NAME = "osteo-ui-shell-v1";
const CACHE_PREFIX = "osteo-ui-shell-";
const APP_SHELL = ["/", "/index.html"];

function isStaticPath(pathname) {
  return pathname === "/" || pathname === "/index.html" ||
    pathname === "/favicon.svg" || pathname === "/manifest.webmanifest" ||
    pathname.startsWith("/assets/") ||
    pathname.startsWith("/src/") ||
    pathname.startsWith("/node_modules/.vite/") ||
    pathname.startsWith("/@vite/") ||
    pathname.startsWith("/@id/") ||
    pathname === "/@vite/client" || pathname === "/@react-refresh";
}

function safeStaticUrl(value) {
  try {
    const url = new URL(value, self.location.origin);
    return url.origin === self.location.origin && isStaticPath(url.pathname);
  } catch {
    return false;
  }
}

async function putStatic(cache, urlValue) {
  if (!safeStaticUrl(urlValue)) return false;
  const url = new URL(urlValue, self.location.origin);
  const response = await fetch(url.href, {
    credentials: "omit",
    cache: "no-store",
    redirect: "error",
  });
  if (!response.ok || response.type === "opaque") return false;
  const type = response.headers.get("content-type") || "";
  // Impide almacenar HTML de respuestas de API o el fallback SPA de archivos inexistentes.
  if (url.pathname !== "/" && url.pathname !== "/index.html" &&
      (url.pathname.endsWith(".js") || url.pathname.endsWith(".ts") ||
       url.pathname.endsWith(".tsx") || url.pathname.endsWith(".css")) &&
      type.includes("text/html")) return false;
  await cache.put(url.href, response);
  return true;
}

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    // Los recursos publicos minimos permiten cargar la pagina offline.
    for (const path of APP_SHELL) {
      try { await putStatic(cache, path); } catch { /* reintentar desde la app */ }
    }
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((n) => n.startsWith(CACHE_PREFIX) && n !== CACHE_NAME)
      .map((n) => caches.delete(n)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET" || request.cache === "no-store" ||
      request.headers.has("authorization")) return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  // Las APIs, radiografias privadas, descargas y medios clinicos no se cachean.
  if (!isStaticPath(url.pathname) && request.mode !== "navigate") return;

  if (request.mode === "navigate") {
    event.respondWith((async () => {
      try {
        const response = await fetch(request);
        if (response.ok && response.headers.get("content-type")?.includes("text/html")) {
          const cache = await caches.open(CACHE_NAME);
          try { await cache.put(new URL("/index.html", self.location.origin).href, response.clone()); }
          catch { /* Caché llena: la respuesta en línea sigue disponible. */ }
        }
        return response;
      } catch {
        const cache = await caches.open(CACHE_NAME);
        return (await cache.match("/index.html")) || Response.error();
      }
    })());
    return;
  }
  if (!isStaticPath(url.pathname)) return;

  event.respondWith((async () => {
    const cache = await caches.open(CACHE_NAME);
    try {
      const response = await fetch(request);
      if (response.ok && response.type !== "opaque") {
        try { await cache.put(request, response.clone()); }
        catch { /* No romper la aplicación conectada si se agota la caché. */ }
      }
      return response;
    } catch {
      return (await cache.match(request)) || Response.error();
    }
  })());
});

self.addEventListener("message", (event) => {
  if (event.data?.type !== "OSTEO_PREPARE_UI") return;
  const port = event.ports[0];
  if (!port) return;
  const input = Array.isArray(event.data.assets) ? event.data.assets : [];
  const valid = [...new Set([...APP_SHELL, ...input].filter(safeStaticUrl))].slice(0, 2000);
  event.waitUntil((async () => {
    try {
      const cache = await caches.open(CACHE_NAME);
      let done = 0;
      let failed = 0;
      let index = 0;
      port.postMessage({ type: "progress", done, total: valid.length, failed });
      const run = async () => {
        while (index < valid.length) {
          const path = valid[index++];
          try {
            const cached = await cache.match(new URL(path, self.location.origin).href);
            if (!cached && !(await putStatic(cache, path))) failed++;
          } catch { failed++; }
          done++;
          if (done % 4 === 0 || done === valid.length) {
            port.postMessage({ type: "progress", done, total: valid.length, failed });
          }
        }
      };
      await Promise.all(Array.from({ length: Math.min(4, valid.length) }, () => run()));
      port.postMessage({ type: "complete", done, total: valid.length, failed });
    } catch (error) {
      port.postMessage({ type: "error", message: String(error) });
    } finally { port.close(); }
  })());
});
