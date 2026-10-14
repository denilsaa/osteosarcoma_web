import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { ClipboardList, LoaderCircle, ShieldCheck } from "lucide-react";
import { getClinicalCaseManagementHistory, updateClinicalCaseManagement,
  type ClinicalCase, type ClinicalCaseCatalogs, type ClinicalCaseManagementEntry } from "../../api/casos.api";
import type { OncologoResumen } from "../../api/oncologos.api";
import { tokenStorage } from "../../auth/tokenStorage";
import "./CaseManagementPanel.css";

interface Props {
  clinicalCase: ClinicalCase;
  catalogs: ClinicalCaseCatalogs;
  oncologists: OncologoResumen[];
  onChanged: (updated: ClinicalCase) => void;
}

function errorText(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as { response?: { data?: { error?: unknown } } }).response;
    if (typeof response?.data?.error === "string") return response.data.error;
    if (response?.data?.error) return JSON.stringify(response.data.error);
  }
  return error instanceof Error ? error.message : "No fue posible actualizar la gestión del caso.";
}

export function CaseManagementPanel({ clinicalCase, catalogs, oncologists, onChanged }: Props) {
  const viewer = tokenStorage.obtenerUsuario();
  const isHead = Boolean(viewer?.roles?.includes("JEFE_ONCOLOGIA"));
  const [doctorId, setDoctorId] = useState(clinicalCase.responsible_oncologist_uuid ?? "");
  const [priorityId, setPriorityId] = useState(String(clinicalCase.priority.id));
  const [reason, setReason] = useState("");
  const [history, setHistory] = useState<ClinicalCaseManagementEntry[]>([]);
  const [saving, setSaving] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    setDoctorId(clinicalCase.responsible_oncologist_uuid ?? "");
    setPriorityId(String(clinicalCase.priority.id));
  }, [clinicalCase.responsible_oncologist_uuid, clinicalCase.priority.id]);

  const refresh = useCallback(async () => {
    setLoading(true);
    try { setHistory(await getClinicalCaseManagementHistory(clinicalCase.id_case)); }
    catch (exc) { setError(errorText(exc)); }
    finally { setLoading(false); }
  }, [clinicalCase.id_case]);

  useEffect(() => { if (isHead) void refresh(); }, [isHead, refresh]);

  const availableDoctors = useMemo(() => oncologists.filter((doctor) =>
    doctor.estado?.toUpperCase() === "ACTIVO" &&
    ["ONCOLOGO", "JEFE_ONCOLOGIA"].includes(doctor.rol_codigo)
  ), [oncologists]);

  const hasDoctorChanged = doctorId !== (clinicalCase.responsible_oncologist_uuid ?? "");
  const hasPriorityChanged = priorityId !== String(clinicalCase.priority.id);
  const disabled = clinicalCase.status.code === "CERRADO";

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving || disabled || (!hasDoctorChanged && !hasPriorityChanged)) return;
    if (reason.trim().length < 10) { setError("Indica un motivo de al menos 10 caracteres."); return; }
    if (hasDoctorChanged && !doctorId) { setError("Selecciona un médico responsable."); return; }
    setSaving(true); setError(null); setNotice(null);
    try {
      const updated = await updateClinicalCaseManagement(clinicalCase.id_case, {
        ...(hasDoctorChanged ? { responsible_oncologist_uuid: doctorId } : {}),
        ...(hasPriorityChanged ? { priority_id: Number(priorityId) } : {}),
        reason: reason.trim(),
      });
      onChanged(updated);
      setReason("");
      setNotice("Cambios registrados. La nueva asignación exige una valoración del responsable actual antes del cierre.");
      await refresh();
    } catch (exc) { setError(errorText(exc)); }
    finally { setSaving(false); }
  }

  function valueLabel(type: ClinicalCaseManagementEntry["type"], value: string | null): string {
    if (!value) return "Sin asignar";
    if (type === "PRIORIDAD") return catalogs.priorities.find((p) => String(p.id) === value)?.name ?? value;
    return oncologists.find((p) => p.id_usuario.toLowerCase() === value.toLowerCase())?.nombre_completo ?? `Médico ${value.slice(0, 8)}`;
  }

  if (!isHead) return null;
  return (
    <section className="case-manage" aria-labelledby="case-manage-title">
      <div className="case-manage-heading">
        <ShieldCheck size={19} aria-hidden="true" />
        <div><h2 id="case-manage-title">Gestión de jefatura</h2>
          <p>Asignación y prioridad del caso clínico</p></div>
        <span className="case-manage-tag">Jefe de oncología</span>
      </div>
      {error && <p className="case-manage-error" role="alert">{error}</p>}
      {notice && <p className="case-manage-notice" role="status">{notice}</p>}
      {disabled ? <p className="case-manage-muted">Este caso está cerrado. No se permiten cambios de responsable ni prioridad.</p> : (
        <form onSubmit={(event) => void save(event)}>
          <div className="case-manage-fields">
            <label>Médico responsable
              <select value={doctorId} onChange={(event) => setDoctorId(event.target.value)}>
                <option value="">Sin asignar</option>
                {availableDoctors.map((doctor) => <option key={doctor.id_usuario} value={doctor.id_usuario}>
                  {doctor.nombre_completo}
                </option>)}
              </select>
            </label>
            <label>Prioridad
              <select value={priorityId} onChange={(event) => setPriorityId(event.target.value)}>
                {catalogs.priorities.map((priority) => <option key={priority.id} value={priority.id}>
                  {priority.name}
                </option>)}
              </select>
            </label>
          </div>
          <label>Motivo del cambio
            <textarea value={reason} onChange={(event) => setReason(event.target.value)}
              maxLength={1000} rows={2} placeholder="Justificación de la reasignación o cambio de prioridad…" />
          </label>
          <div className="case-manage-actions"><span>Las modificaciones quedan registradas en el historial.</span>
            <button type="submit" disabled={saving || (!hasDoctorChanged && !hasPriorityChanged) || reason.trim().length < 10}>
              {saving && <LoaderCircle size={15} />} Guardar cambios
            </button>
          </div>
        </form>
      )}
      <div className="case-manage-history">
        <h3><ClipboardList size={16} aria-hidden="true" /> Historial de gestión</h3>
        {loading ? <p>Cargando…</p> : history.length === 0 ? <p>Sin cambios administrativos registrados.</p> : (
          <ol>{history.map((entry) => <li key={entry.id}>
            <strong>{entry.type === "RESPONSABLE" ? "Reasignación" : "Prioridad"}</strong>
            <span>{valueLabel(entry.type, entry.previous)} → {valueLabel(entry.type, entry.current)}</span>
            <small>{new Date(entry.changed_at).toLocaleString("es-BO")} · {entry.reason}</small>
          </li>)}</ol>
        )}
      </div>
    </section>
  );
}
