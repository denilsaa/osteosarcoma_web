import { useEffect, useState } from "react";
import { getClinicalCaseSupervision, type ClinicalCaseSupervision } from "../../api/casos.api";
import { tokenStorage } from "../../auth/tokenStorage";
import "./CaseSupervisionSummary.css";

export function CaseSupervisionSummary() {
  const isHead = Boolean(tokenStorage.obtenerUsuario()?.roles?.includes("JEFE_ONCOLOGIA"));
  const [summary, setSummary] = useState<ClinicalCaseSupervision | null>(null);
  useEffect(() => {
    if (!isHead) return;
    let active = true;
    void getClinicalCaseSupervision()
      .then((data) => { if (active) setSummary(data); })
      .catch(() => { if (active) setSummary(null); });
    return () => { active = false; };
  }, [isHead]);
  if (!isHead || !summary) return null;
  return <section className="case-supervision" aria-label="Resumen de supervisión clínica">
    <div><span>Supervisión · todos los casos</span><strong>{summary.total}</strong></div>
    <div><span>Sin asignar</span><strong>{summary.unassigned}</strong></div>
    <div className="case-supervision-breakdown"><span>Por estado</span><p>{summary.by_status.map((entry) =>
      <span key={entry.estado_caso__codigo}>{entry.estado_caso__nombre}: <b>{entry.total}</b></span>
    )}</p></div>
  </section>;
}
