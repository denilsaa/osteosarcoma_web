import { useCallback, useEffect, useMemo, useState } from "react";
import { listarOncologos, type OncologoResumen } from "../../api/oncologos.api";
import {
  asignarPaciente, listarAsignacionesPaciente, revocarPaciente,
  type AsignacionPaciente,
} from "../../api/asignacionesPacientes.api";
import "./PatientAssignmentManager.css";

export function PatientAssignmentManager({ patientId }: { patientId: string }) {
  const [doctors, setDoctors] = useState<OncologoResumen[]>([]);
  const [assignments, setAssignments] = useState<AsignacionPaciente[]>([]);
  const [doctorId, setDoctorId] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [revokeTarget, setRevokeTarget] = useState<AsignacionPaciente | null>(null);
  const [revokeReason, setRevokeReason] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const refresh = useCallback(async () => {
    const list = await listarAsignacionesPaciente(patientId);
    setAssignments(list);
  }, [patientId]);

  useEffect(() => {
    let alive = true;
    Promise.all([
      listarAsignacionesPaciente(patientId),
      listarOncologos("", "ACTIVO", ""),
    ]).then(([rows, users]) => {
      if (alive) {
        setAssignments(rows);
        setDoctors(users.resultados);
      }
    }).catch(() => {
      if (alive) setError("No se pudieron cargar las asignaciones.");
    });
    return () => { alive = false; };
  }, [patientId]);

  const doctorsById = useMemo(() => new Map(doctors.map(item => [item.id_usuario, item.nombre_completo])), [doctors]);
  const active = assignments.filter(item => item.activa);
  const available = doctors.filter(item => !active.some(grant => grant.oncologo_uuid === item.id_usuario));

  async function handleAssign() {
    setError(""); setSuccess("");
    if (!doctorId || reason.trim().length < 10) {
      setError("Seleccione un oncólogo y escriba un motivo de al menos 10 caracteres.");
      return;
    }
    setBusy(true);
    try {
      await asignarPaciente(patientId, doctorId, reason.trim());
      await refresh();
      setDoctorId(""); setReason("");
      setSuccess("Paciente asignado correctamente.");
    } catch {
      setError("No se pudo asignar el paciente. Compruebe que el oncólogo esté activo.");
    } finally { setBusy(false); }
  }

  async function handleRevoke() {
    setError(""); setSuccess("");
    if (!revokeTarget || revokeReason.trim().length < 10) {
      setError("El motivo debe contener al menos 10 caracteres.");
      return;
    }
    setBusy(true);
    try {
      await revocarPaciente(patientId, revokeTarget.oncologo_uuid, revokeReason.trim());
      await refresh();
      setRevokeTarget(null);
      setRevokeReason("");
      setSuccess("Asignación revocada; el historial se conserva.");
    } catch {
      setError("No se puede revocar. Verifique si el oncólogo tiene casos asignados.");
    } finally { setBusy(false); }
  }

  return (
    <section className="patient-assignment-card" aria-label="Asignaciones clínicas">
      <div className="patient-assignment-header">
        <h2>Asignación de pacientes</h2>
        <span>Solo jefatura</span>
      </div>
      <p>Los oncólogos asignados pueden atender a este paciente y crear nuevos casos clínicos.</p>
      {error && <p role="alert" className="patient-assignment-error">{error}</p>}
      {success && <p role="status" className="patient-assignment-success">{success}</p>}
      <div className="patient-assignment-form">
        <label>Oncólogo activo
          <select value={doctorId} onChange={event => setDoctorId(event.target.value)} disabled={busy}>
            <option value="">Seleccione un profesional</option>
            {available.map(item => <option key={item.id_usuario} value={item.id_usuario}>{item.nombre_completo}</option>)}
          </select>
        </label>
        <label>Motivo de asignación
          <input value={reason} maxLength={500} disabled={busy} onChange={event => setReason(event.target.value)} placeholder="Motivo de la asignación" />
        </label>
        <button type="button" disabled={busy || !doctorId || reason.trim().length < 10} onClick={() => void handleAssign()}>Asignar paciente</button>
      </div>
      <h3>Profesionales autorizados</h3>
      {active.length === 0 ? <p>Sin asignaciones explícitas. Pueden existir casos previamente asignados.</p> : (
        <ul className="patient-assignment-list">
          {active.map(item => <li key={item.id_asignacion}>
            <div><strong>{doctorsById.get(item.oncologo_uuid) ?? "Profesional asignado"}</strong><small>Asignado: {new Date(item.fecha_asignacion).toLocaleDateString("es-BO")}</small></div>
            <button type="button" disabled={busy} onClick={() => { setRevokeTarget(item); setRevokeReason(""); }}>Revocar</button>
          </li>)}
        </ul>
      )}
      {revokeTarget && (
        <div className="patient-assignment-revoke">
          <strong>Revocar acceso del profesional</strong>
          <p>Si tiene casos asignados, deberá reasignarlos previamente. El historial se conservará.</p>
          <label>Motivo de revocación
            <input value={revokeReason} maxLength={500} onChange={event => setRevokeReason(event.target.value)} placeholder="Escriba la justificación" />
          </label>
          <div>
            <button type="button" disabled={busy} onClick={() => setRevokeTarget(null)}>Cancelar</button>
            <button type="button" disabled={busy || revokeReason.trim().length < 10} onClick={() => void handleRevoke()}>Confirmar revocación</button>
          </div>
        </div>
      )}
    </section>
  );
}
