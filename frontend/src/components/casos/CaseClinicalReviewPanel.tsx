import { useCallback, useEffect, useMemo, useState, type FormEvent } from "react";
import { CheckCircle2, ClipboardCheck, LoaderCircle, ShieldAlert } from "lucide-react";
import {
  createClinicalValuation,
  getClinicalValuationCriteria,
  getClinicalValuations,
  type ClinicalValuation,
  type ClinicalValuationCriterion,
} from "../../api/casos.api";
import { tokenStorage } from "../../auth/tokenStorage";
import "./CaseClinicalReviewPanel.css";

interface Props {
  caseId: string;
  caseStatus: string;
  responsibleOncologistUuid: string | null;
}

function getErrorMessage(error: unknown): string {
  if (error && typeof error === "object" && "response" in error) {
    const response = (error as { response?: { data?: { error?: unknown; detail?: string } } }).response;
    const message = response?.data?.error;
    if (typeof message === "string") return message;
    if (message && typeof message === "object" && "message" in message) {
      return String((message as { message: unknown }).message);
    }
    if (response?.data?.detail) return response.data.detail;
  }
  return error instanceof Error ? error.message : "No se pudo registrar la valoración.";
}

export function CaseClinicalReviewPanel({ caseId, caseStatus, responsibleOncologistUuid }: Props) {
  const [criteria, setCriteria] = useState<ClinicalValuationCriterion[]>([]);
  const [history, setHistory] = useState<ClinicalValuation[]>([]);
  const [criterionId, setCriterionId] = useState("");
  const [observation, setObservation] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const viewer = tokenStorage.obtenerUsuario();

  const canRegister = useMemo(() => Boolean(
    viewer?.id_usuario &&
    responsibleOncologistUuid?.toLowerCase() === viewer.id_usuario.toLowerCase() &&
    ["EN_ANALISIS", "REVISADO"].includes(caseStatus),
  ), [viewer?.id_usuario, responsibleOncologistUuid, caseStatus]);

  const fetchData = useCallback(async () => {
    try {
      const [catalog, valuations] = await Promise.all([
        getClinicalValuationCriteria(), getClinicalValuations(caseId),
      ]);
      setCriteria(catalog);
      setHistory(valuations);
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    setLoading(true);
    setError(null);
    void fetchData();
  }, [fetchData]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canRegister || saving) return;
    setError(null);
    setNotice(null);
    if (!criterionId || observation.trim().length < 15) {
      setError("Selecciona un criterio y escribe al menos 15 caracteres de valoración.");
      return;
    }
    setSaving(true);
    try {
      await createClinicalValuation(caseId, {
        criterion_id: Number(criterionId), observation: observation.trim(),
      });
      setObservation("");
      setCriterionId("");
      await fetchData();
      setNotice("Valoración registrada con fecha, autor y criterio. El historial no se sobrescribe.");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setSaving(false);
    }
  }

  const currentValuation = history.find(
    (item) => item.oncologist_uuid.toLowerCase() === responsibleOncologistUuid?.toLowerCase(),
  );

  return (
    <section className="case-review-panel" aria-labelledby="case-review-title">
      <div className="case-review-header">
        <div className="case-review-heading">
          <ClipboardCheck size={20} aria-hidden="true" />
          <div>
            <h2 id="case-review-title">Valoración del oncólogo</h2>
            <p>Registro profesional independiente del resultado automatizado.</p>
          </div>
        </div>
        <span className={currentValuation ? "case-review-status is-ready" : "case-review-status"}>
          {currentValuation ? "Valoración registrada" : "Pendiente de valoración"}
        </span>
      </div>

      {loading ? <p className="case-review-muted">Cargando valoraciones…</p> : (
        <>
          {error && <div className="case-review-error" role="alert"><ShieldAlert size={16}/>{error}</div>}
          {notice && <div className="case-review-success" role="status"><CheckCircle2 size={16}/>{notice}</div>}
          {caseStatus === "REVISADO" && !currentValuation && (
            <p className="case-review-info">Antes de cerrar el caso debe registrar una valoración el médico responsable.</p>
          )}

          {canRegister && (
            <form className="case-review-form" onSubmit={(event) => void save(event)}>
              <label htmlFor="review-criterion">Criterio médico</label>
              <select id="review-criterion" value={criterionId}
                onChange={(event) => setCriterionId(event.target.value)} required>
                <option value="">Seleccionar criterio</option>
                {criteria.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}
              </select>
              <label htmlFor="review-observation">Fundamento de la valoración</label>
              <textarea id="review-observation" rows={3} maxLength={4000} minLength={15}
                placeholder="Describa hallazgos, correlación clínica y próximos pasos…"
                value={observation} onChange={(event) => setObservation(event.target.value)} required/>
              <div className="case-review-actions">
                <span>El resultado de IA es de apoyo; la decisión corresponde al profesional.</span>
                <button type="submit" disabled={saving || !criterionId || observation.trim().length < 15}>
                  {saving && <LoaderCircle size={15} className="case-review-spin"/>}
                  Registrar valoración
                </button>
              </div>
            </form>
          )}

          {!canRegister && caseStatus !== "CERRADO" && (
            <p className="case-review-muted">Solo el oncólogo responsable puede registrar una valoración, en las etapas En análisis o Revisado.</p>
          )}

          <div className="case-review-history">
            <h3>Historial de valoraciones ({history.length})</h3>
            {history.length === 0 ? <p className="case-review-muted">Todavía no se registraron valoraciones.</p> : (
              <div className="case-review-entries">
                {history.map(item => (
                  <article className="case-review-entry" key={item.id_valuation}>
                    <div className="case-review-entry-top">
                      <strong>{item.criterion.name}</strong>
                      <time dateTime={item.created_at}>
                        {new Date(item.created_at).toLocaleString("es-BO")}
                      </time>
                    </div>
                    <p>{item.observation}</p>
                    <small>Médico: {item.oncologist_uuid}</small>
                  </article>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </section>
  );
}
