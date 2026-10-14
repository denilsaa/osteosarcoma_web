import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { CloudUpload, KeyRound, LockKeyhole, RefreshCw } from "lucide-react";
import {
  subscribeClinicalQueue, unlockClinicalQueue, lockClinicalQueue,
  synchronizeClinicalQueue, startClinicalQueueSync, listPendingPatientLinks,
  type PendingPatientLink, type QueueStats,
} from "../../offline/clinicalQueue";
import { getPatientCatalogs } from "../../api/pacientes.api";
import { getClinicalCaseCatalogs } from "../../api/casos.api";
import "./OfflineClinicalQueuePanel.css";

const initial: QueueStats = {
  ready: false, pending: 0, patientPending: 0, casePending: 0,
  review: 0, syncing: false, lastError: null,
};

export function OfflineClinicalQueuePanel() {
  const navigate = useNavigate();
  const [state, setState] = useState(initial);
  const [pendingPatientLinks, setPendingPatientLinks] = useState<PendingPatientLink[]>([]);
  const [pin, setPin] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    startClinicalQueueSync();
    // Precargar catálogos sin información de pacientes para el modo contingencia.
    void getPatientCatalogs().catch(() => {});
    void getClinicalCaseCatalogs().catch(() => {});
    return subscribeClinicalQueue(setState);
  }, []);

  useEffect(() => {
    if (!state.ready) {
      setPendingPatientLinks([]);
      return;
    }
    let active = true;
    void listPendingPatientLinks()
      .then((links) => { if (active) setPendingPatientLinks(links); })
      .catch(() => { if (active) setPendingPatientLinks([]); });
    return () => { active = false; };
  }, [state.ready, state.patientPending, state.syncing]);

  async function unlock() {
    setBusy(true);
    setError("");
    try {
      await unlockClinicalQueue(pin);
      setPin("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo desbloquear.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="offline-clinical">
      <div className="offline-clinical__title">
        <LockKeyhole size={17} />
        <strong>Registros clínicos pendientes</strong>
        <span>{state.ready ? "Bandeja local desbloqueada" : "Protección cifrada"}</span>
      </div>

      {!state.ready ? (
        <div className="offline-clinical__unlock">
          <input
            type="password"
            value={pin}
            autoComplete="off"
            minLength={8}
            placeholder="Clave local (mín. 8 caracteres)"
            aria-label="Clave privada para registros offline"
            title="Conserva esta clave. Los registros no se sincronizan hasta confirmar el envío."
            onChange={(event) => setPin(event.target.value)}
          />
          <button type="button" disabled={busy || pin.length < 8} onClick={() => void unlock()}>
            <KeyRound size={15} />
            {busy ? "Comprobando..." : "Preparar bandeja cifrada"}
          </button>
          {error && <p className="offline-clinical__error" role="alert">{error}</p>}
        </div>
      ) : (
        <div className="offline-clinical__active">
          <span><strong>{state.patientPending}</strong> pacientes pendientes</span>
          <span><strong>{state.casePending}</strong> casos pendientes</span>
          <span><strong>{state.review}</strong> requieren revisión</span>
          <button type="button" onClick={() => void synchronizeClinicalQueue()} disabled={state.syncing}>
            {state.syncing ? <RefreshCw size={15} className="offline-panel__spin" /> : <CloudUpload size={15} />}
            {state.syncing ? "Sincronizando..." : "Sincronizar ahora"}
          </button>
          <button type="button" onClick={lockClinicalQueue}>Bloquear</button>
        </div>
      )}

      {state.ready && pendingPatientLinks.length > 0 && (
        <div className="offline-clinical__linked">
          <strong>Crear un caso de un paciente pendiente</strong>
          <div className="offline-clinical__linked-actions">
            {pendingPatientLinks.slice(0, 10).map((item, index) => (
              <button
                type="button"
                key={item.operationId}
                onClick={() => navigate(`/casos/nuevo?paciente=${encodeURIComponent(item.localReference)}`)}
              >
                Caso del paciente pendiente {index + 1}
              </button>
            ))}
          </div>
          {pendingPatientLinks.length > 10 && (
            <p>Mostrando 10 de {pendingPatientLinks.length} registros pendientes.</p>
          )}
        </div>
      )}

      {state.lastError && (
        <p className="offline-clinical__error" role="status">{state.lastError}</p>
      )}

      {/* Aviso crítico solo cuando existen registros que aún no llegaron a la clínica. */}
      {state.ready && state.pending > 0 && (
        <p className="offline-clinical__pending-note" role="status">
          {state.pending} registro(s) sin sincronizar. Aún no figuran en la clínica; conserva tu clave y los datos del navegador.
        </p>
      )}
    </div>
  );
}
