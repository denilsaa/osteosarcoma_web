/* Fase 3A. Solo recursos PUBLICOS de interfaz; nunca datos de pacientes.
   La persistencia clínica y la inferencia offline NO están implementadas aún. */
export type PreparationStatus = "checking" | "preparing" | "ready" | "partial" | "unsupported";
export type Connectivity = "checking" | "connected" | "disconnected";

export interface OfflineSnapshot {
  status: PreparationStatus;
  connectivity: Connectivity;
  done: number;
  total: number;
  failed: number;
  message: string;
}

let snapshot: OfflineSnapshot = {
  status: "checking",
  connectivity: "checking",
  done: 0,
  total: 0,
  failed: 0,
  message: "Verificando compatibilidad del navegador...",
};

const listeners = new Set<(state: OfflineSnapshot) => void>();
let started = false;
let preparationInProgress = false;

function notify(patch: Partial<OfflineSnapshot>) {
  snapshot = { ...snapshot, ...patch };
  for (const listener of listeners) listener(snapshot);
}

export function subscribeOffline(listener: (state: OfflineSnapshot) => void) {
  listeners.add(listener);
  listener(snapshot);
  return () => { listeners.delete(listener); };
}

function publicAsset(pathname: string) {
  return pathname === "/" || pathname === "/index.html" ||
    pathname === "/favicon.svg" || pathname === "/manifest.webmanifest" ||
    pathname.startsWith("/assets/") || pathname.startsWith("/src/") ||
    pathname.startsWith("/node_modules/.vite/") ||
    pathname.startsWith("/@vite/") || pathname.startsWith("/@id/") ||
    pathname === "/@vite/client" || pathname === "/@react-refresh";
}

async function getAssets(): Promise<string[]> {
  // En producción Vite genera un listado real de los archivos compilados.
  try {
    const result = await fetch("/offline-assets.json", { cache: "no-store" });
    if (result.ok && result.headers.get("content-type")?.includes("json")) {
      const data: unknown = await result.json();
      if (typeof data === "object" && data !== null && "assets" in data &&
          Array.isArray(data.assets)) {
        return data.assets.filter((value): value is string => typeof value === "string");
      }
    }
  } catch { /* En desarrollo se inspeccionan los módulos públicos cargados. */ }

  const result = new Set<string>(["/", "/index.html", "/favicon.svg", "/manifest.webmanifest"]);
  for (const resource of performance.getEntriesByType("resource")) {
    try {
      const url = new URL(resource.name);
      if (url.origin === location.origin && publicAsset(url.pathname)) {
        result.add(url.pathname + url.search);
      }
    } catch { /* URL inválida */ }
  }
  return [...result];
}

async function checkConnection(): Promise<void> {
  if (!navigator.onLine) {
    notify({ connectivity: "disconnected" });
    return;
  }
  try {
    // No va al Service Worker/cache; comprueba al servidor web real.
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 5000);
    try {
      const response = await fetch(`/index.html?osteo_connectivity=${Date.now()}`, {
        cache: "no-store", method: "HEAD", signal: controller.signal,
      });
      const wasDisconnected = snapshot.connectivity === "disconnected";
      notify({ connectivity: response.ok ? "connected" : "disconnected" });
      if (response.ok && wasDisconnected && snapshot.status === "partial") {
        void retryOfflinePreparation();
      }
    } finally { window.clearTimeout(timer); }
  } catch {
    notify({ connectivity: "disconnected" });
  }
}

function prepareThroughWorker(worker: ServiceWorker, assets: string[]): Promise<void> {
  return new Promise((resolve) => {
    const channel = new MessageChannel();
    let finished = false;
    const timeout = window.setTimeout(() => {
      if (!finished) {
        notify({ status: "partial", message: "La preparación tardó demasiado. Se reintentará al ingresar nuevamente." });
        channel.port1.close(); resolve();
      }
    }, 120000);
    channel.port1.onmessage = ({ data }: MessageEvent) => {
      if (finished) return;
      if (data.type === "progress" || data.type === "complete") {
        const done = Number(data.done) || 0;
        const total = Number(data.total) || 0;
        const failed = Number(data.failed) || 0;
        notify({ done, total, failed, status: "preparing",
          message: `Preparando recursos públicos (${done}/${total})...` });
      }
      if (data.type === "complete" || data.type === "error") {
        finished = true;
        window.clearTimeout(timeout);
        channel.port1.close();
        if (data.type === "error") {
          notify({ status: "partial", message: "No se completó la caché de la interfaz." });
        } else {
          notify({ status: data.failed ? "partial" : "ready",
            message: data.failed
              ? `${data.failed} recursos no pudieron guardarse. Se reintentará al abrir de nuevo.`
              : "Interfaz descargada y comprobada. Las funciones clínicas offline aún están pendientes." });
        }
        resolve();
      }
    };
    worker.postMessage({ type: "OSTEO_PREPARE_UI", assets }, [channel.port2]);
  });
}

export async function startOfflinePreparation(): Promise<void> {
  if (started || typeof window === "undefined") return;
  started = true;
  void checkConnection();
  window.addEventListener("online", () => {
    void checkConnection();
    if (snapshot.status === "partial") void retryOfflinePreparation();
  });
  window.addEventListener("offline", () => void checkConnection());
  window.setInterval(() => void checkConnection(), 15000);

  if (!window.isSecureContext || !("serviceWorker" in navigator) || !("caches" in window)) {
    notify({ status: "unsupported", message: !window.isSecureContext
      ? "Se necesita HTTPS confiable en la red local (localhost está permitido para pruebas)."
      : "Este navegador no permite preparar recursos offline." });
    return;
  }
  try {
    notify({ status: "preparing", message: "Registrando la interfaz para uso sin conexión..." });
    const registration = await navigator.serviceWorker.register("/sw.js", { scope: "/" });
    await navigator.serviceWorker.ready;
    if (!registration.active) throw new Error("El Service Worker aún no está activo.");
    await retryOfflinePreparation();
  } catch {
    notify({ status: "partial", message: "No se pudo preparar la interfaz en este navegador." });
  }
}


export async function retryOfflinePreparation(): Promise<void> {
  if (preparationInProgress || !window.isSecureContext || !("serviceWorker" in navigator)) return;
  preparationInProgress = true;
  try {
    const registration = await navigator.serviceWorker.ready;
    if (!registration.active) throw new Error("Service Worker inactivo.");
    notify({ status: "preparing", message: "Verificando recursos disponibles..." });
    await prepareThroughWorker(registration.active, await getAssets());
  } catch {
    notify({ status: "partial", message: "No se pudo preparar la interfaz. Reintenta con el servidor disponible." });
  } finally {
    preparationInProgress = false;
  }
}
