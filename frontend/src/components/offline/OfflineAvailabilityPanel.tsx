import { useEffect, useState } from "react";
import {
  CloudOff, CloudUpload, DownloadCloud, LockKeyhole, Monitor,
  Radio, RefreshCw,
} from "lucide-react";
import {
  retryOfflinePreparation,
  startOfflinePreparation,
  subscribeOffline,
  type OfflineSnapshot,
} from "../../offline/offlinePreparation";
import { OfflineClinicalQueuePanel } from "./OfflineClinicalQueuePanel";
import "./OfflineAvailabilityPanel.css";

const initialState: OfflineSnapshot = {
  status: "checking",
  connectivity: "checking",
  done: 0,
  total: 0,
  failed: 0,
  message: "Comprobando requisitos de funcionamiento sin conexión...",
};

export function OfflineAvailabilityPanel() {
  const [state, setState] = useState<OfflineSnapshot>(initialState);

  useEffect(() => {
    const unsubscribe = subscribeOffline(setState);
    void startOfflinePreparation();
    return unsubscribe;
  }, []);

  const percentage = state.total > 0
    ? Math.max(0, Math.min(100, Math.floor(((state.done - state.failed) * 100) / state.total)))
    : 0;
  const uiReady = state.status === "ready";
  const browserCompatible = state.status !== "unsupported";

  return (
    <section className="offline-panel" aria-labelledby="offline-panel-title">
      <div className="offline-panel__top">
        <div className="offline-panel__icon"><DownloadCloud size={22} /></div>
        <div className="offline-panel__heading">
          <h2 id="offline-panel-title">Disponibilidad sin conexión</h2>
        </div>
        <span className={`offline-panel__server offline-panel__server--${state.connectivity}`}>
          {state.connectivity === "disconnected" ? <CloudOff size={15} /> : <Radio size={15} />}
          {state.connectivity === "connected" ? "Servidor web disponible" :
            state.connectivity === "disconnected" ? "Servidor web sin respuesta" : "Comprobando conexión"}
        </span>
      </div>

      <div className="offline-panel__bar-head">
        <strong>Preparación de interfaz</strong>
        <span>{percentage} %</span>
      </div>
      <div
        className="offline-panel__progress"
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label="Recursos de interfaz verificados"
      >
        <div style={{ width: `${percentage}%` }} />
      </div>

      {/* Solo mostrar mensajes de error o preparación; no duplicar el estado 100 %. */}
      {!uiReady && (
        <div className="offline-panel__status-compact" role="status" aria-live="polite">
          {state.message}
        </div>
      )}

      <div className="offline-panel__capabilities">
        <div className="offline-panel__capability">
          <Monitor size={17} />
          <span>Archivos de la interfaz</span>
          <strong className={uiReady ? "offline-panel__ok" : "offline-panel__pending"}>
            {uiReady ? "Preparados" : browserCompatible ? "En preparación" : "No compatible"}
          </strong>
        </div>
        <div className="offline-panel__capability">
          <LockKeyhole size={17} />
          <span>Pacientes y casos pendientes</span>
          <strong className="offline-panel__pending">Disponible en fase de prueba</strong>
        </div>
        <div className="offline-panel__capability">
          <CloudUpload size={17} />
          <span>Radiografías y sincronización</span>
          <strong className="offline-panel__pending">Pendiente de implementar</strong>
        </div>
        <div className="offline-panel__capability">
          <RefreshCw size={17} />
          <span>Análisis de IA en esta computadora</span>
          <strong className="offline-panel__pending">Pendiente de validar</strong>
        </div>
      </div>

      {state.status === "partial" && (
        <button type="button" className="offline-panel__retry" onClick={() => void retryOfflinePreparation()}>
          <RefreshCw size={15} /> Reintentar preparación
        </button>
      )}
      <OfflineClinicalQueuePanel />
    </section>
  );
}
