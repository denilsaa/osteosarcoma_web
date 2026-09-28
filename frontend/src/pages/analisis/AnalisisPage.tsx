import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent, ReactNode } from "react";
import { AxiosError } from "axios";
import {
  Activity,
  BrainCircuit,
  CheckCircle2,
  FileImage,
  ImagePlus,
  LoaderCircle,
  LockKeyhole,
  RotateCcw,
  ScanLine,
  ShieldCheck,
  Upload,
  X,
  XCircle,
} from "lucide-react";

import {
  validateRadiography,
  type RadiographyValidationResponse,
} from "../../api/ia.api";

import "./AnalisisPage.css";

const MAX_FILE_SIZE = 20 * 1024 * 1024;
const ACCEPTED_EXTENSIONS = ["jpg", "jpeg", "png", "dcm"];

type StageState =
  | "waiting"
  | "processing"
  | "approved"
  | "rejected"
  | "completed"
  | "blocked";

interface PipelineStageProps {
  number: number;
  title: string;
  description: string;
  state: StageState;
  icon: ReactNode;
  detail?: string;
}

function getExtension(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() ?? "";
}

function formatPercentage(value?: number | null): string {
  if (
    value === undefined ||
    value === null ||
    !Number.isFinite(value)
  ) {
    return "—";
  }

  return `${(value * 100).toFixed(2)} %`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) {
    return `${bytes} B`;
  }

  if (bytes < 1024 * 1024) {
    return `${(bytes / 1024).toFixed(1)} KB`;
  }

  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function getErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    const data = error.response?.data as
      | {
          detail?: string;
          mensaje?: string;
          error?:
            | string
            | {
                code?: string;
                message?: string;
              };
        }
      | undefined;

    if (typeof data?.detail === "string") {
      return data.detail;
    }

    if (typeof data?.mensaje === "string") {
      return data.mensaje;
    }

    if (typeof data?.error === "string") {
      return data.error;
    }

    if (
      data?.error &&
      typeof data.error === "object" &&
      typeof data.error.message === "string"
    ) {
      return data.error.message;
    }

    return "No fue posible analizar la imagen.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "No fue posible analizar la imagen.";
}

function getStageLabel(state: StageState): string {
  switch (state) {
    case "processing":
      return "Analizando";

    case "approved":
      return "Aprobada";

    case "rejected":
      return "Rechazada";

    case "completed":
      return "Ejecutada";

    case "blocked":
      return "Bloqueada";

    default:
      return "Pendiente";
  }
}

function PipelineStage({
  number,
  title,
  description,
  state,
  icon,
  detail,
}: PipelineStageProps) {
  return (
    <div
      className={`ai-pipeline-stage ai-pipeline-stage-${state}`}
    >
      <div className="ai-pipeline-stage-top">
        <div className="ai-pipeline-stage-icon">
          {state === "processing" ? (
            <LoaderCircle
              size={22}
              className="ai-spinner"
            />
          ) : state === "approved" ||
            state === "completed" ? (
            <CheckCircle2 size={22} />
          ) : state === "rejected" ? (
            <XCircle size={22} />
          ) : state === "blocked" ? (
            <LockKeyhole size={21} />
          ) : (
            icon
          )}
        </div>

        <span className="ai-pipeline-stage-number">
          ETAPA {number}
        </span>
      </div>

      <strong className="ai-pipeline-stage-title">
        {title}
      </strong>

      <span className="ai-pipeline-stage-description">
        {description}
      </span>

      <div className="ai-pipeline-stage-status">
        {getStageLabel(state)}
      </div>

      {detail && (
        <small className="ai-pipeline-stage-detail">
          {detail}
        </small>
      )}
    </div>
  );
}

export function AnalisisPage() {
  const inputRef =
    useRef<HTMLInputElement | null>(null);

  const [file, setFile] =
    useState<File | null>(null);

  const [previewUrl, setPreviewUrl] =
    useState<string | null>(null);

  const [result, setResult] =
    useState<RadiographyValidationResponse | null>(
      null,
    );

  const [loading, setLoading] =
    useState(false);

  const [dragging, setDragging] =
    useState(false);

  const [error, setError] =
    useState<string | null>(null);

  useEffect(
    () => () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    },
    [previewUrl],
  );

  function reset(): void {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setPreviewUrl(null);
    setFile(null);
    setResult(null);
    setError(null);
    setLoading(false);

    if (inputRef.current) {
      inputRef.current.value = "";
    }
  }

  function selectFile(selected: File): void {
    setResult(null);
    setError(null);

    const extension =
      getExtension(selected.name);

    if (
      !ACCEPTED_EXTENSIONS.includes(
        extension,
      )
    ) {
      setError(
        "Formato no admitido. Seleccione JPG, JPEG, PNG o DICOM.",
      );

      return;
    }

    if (selected.size > MAX_FILE_SIZE) {
      setError(
        "El archivo supera el límite máximo de 20 MB.",
      );

      return;
    }

    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }

    setFile(selected);

    setPreviewUrl(
      extension === "dcm"
        ? null
        : URL.createObjectURL(selected),
    );
  }

  function handleFileChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {
    const selected =
      event.target.files?.[0];

    if (selected) {
      selectFile(selected);
    }
  }

  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ): void {
    event.preventDefault();
    setDragging(false);

    const selected =
      event.dataTransfer.files?.[0];

    if (selected) {
      selectFile(selected);
    }
  }

  async function handleValidate(): Promise<void> {
    if (!file || loading) {
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response =
        await validateRadiography(file);

      setResult(response);
    } catch (validationError) {
      setError(
        getErrorMessage(
          validationError,
        ),
      );
    } finally {
      setLoading(false);
    }
  }

  const radiography =
    result?.validacion_radiografia;

  const anatomy =
    result?.validacion_anatomica;

  const tumor =
    result?.analisis_osteosarcoma;

  const stage1State: StageState =
    loading
      ? "processing"
      : !result
        ? "waiting"
        : result.es_radiografia
          ? "approved"
          : "rejected";

  const stage2State: StageState =
    loading
      ? "waiting"
      : !result
        ? "waiting"
        : !result.es_radiografia
          ? "blocked"
          : !result.anatomia_evaluada
            ? "waiting"
            : result.anatomia_admitida
              ? "approved"
              : "rejected";

  const stage3State: StageState =
    loading
      ? "waiting"
      : !result
        ? "waiting"
        : !result.es_radiografia ||
            result.anatomia_admitida === false
          ? "blocked"
          : result.analisis_osteosarcoma_evaluado
            ? "completed"
            : "waiting";

  return (
    <div className="ai-analysis-page">
      <header className="ai-analysis-header">
        <div className="ai-analysis-heading">
          <div className="ai-analysis-heading-icon">
            <BrainCircuit size={25} />
          </div>

          <div>
            <h1>Análisis con IA</h1>

            <p>
              Evaluación progresiva de la imagen
              mediante un pipeline de redes
              neuronales convolucionales.
            </p>
          </div>
        </div>

        <div className="ai-analysis-model-badge">
          <ShieldCheck size={17} />
          EfficientNet · Pipeline IA
        </div>
      </header>

      <section className="ai-pipeline-card">
        <div className="ai-pipeline-heading">
          <div>
            <span>
              FLUJO DE PROCESAMIENTO
            </span>

            <h2>
              Progreso del análisis
            </h2>
          </div>

          {loading && (
            <div className="ai-processing-badge">
              <LoaderCircle
                size={16}
                className="ai-spinner"
              />
              Procesando imagen
            </div>
          )}
        </div>

        <div className="ai-pipeline">
          <PipelineStage
            number={1}
            title="Validación radiográfica"
            description="Verifica si la imagen corresponde a una radiografía."
            state={stage1State}
            icon={<FileImage size={22} />}
            detail={
              result
                ? formatPercentage(
                    radiography
                      ?.probabilidad_radiografia ??
                      result.probabilidad_radiografia,
                  )
                : undefined
            }
          />

          <div
            className={`ai-pipeline-connector ${
              stage1State === "approved"
                ? "ai-pipeline-connector-active"
                : ""
            }`}
          >
            <span />
            <strong>›</strong>
          </div>

          <PipelineStage
            number={2}
            title="Validación anatómica"
            description="Comprueba si la región pertenece al alcance admitido."
            state={stage2State}
            icon={<ScanLine size={22} />}
            detail={
              anatomy
                ? formatPercentage(
                    anatomy.probabilidad_admitida,
                  )
                : undefined
            }
          />

          <div
            className={`ai-pipeline-connector ${
              stage2State === "approved"
                ? "ai-pipeline-connector-active"
                : ""
            }`}
          >
            <span />
            <strong>›</strong>
          </div>

          <PipelineStage
            number={3}
            title="Análisis de osteosarcoma"
            description="Evalúa características radiográficas asociadas a osteosarcoma."
            state={stage3State}
            icon={<Activity size={22} />}
            detail={
              tumor
                ? formatPercentage(
                    tumor.probabilidad_osteosarcoma,
                  )
                : undefined
            }
          />
        </div>
      </section>

      <div className="ai-analysis-grid">
        <section className="ai-upload-card">
          <div className="ai-card-heading">
            <span className="ai-step">
              IMAGEN DE ESTUDIO
            </span>

            <h2>
              Seleccionar radiografía
            </h2>

            <p>
              Cargue una imagen para iniciar
              automáticamente las etapas de
              validación y análisis disponibles.
            </p>
          </div>

          {!file ? (
            <div
              className={`ai-drop-zone ${
                dragging
                  ? "ai-drop-zone-active"
                  : ""
              }`}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={(event) => {
                event.preventDefault();
                setDragging(false);
              }}
              onDrop={handleDrop}
              onClick={() =>
                inputRef.current?.click()
              }
            >
              <div className="ai-drop-icon">
                <Upload size={30} />
              </div>

              <h3>
                Cargar imagen
              </h3>

              <p>
                Arrastre una radiografía o
                selecciónela desde su equipo.
              </p>

              <button
                type="button"
                className="ai-select-button"
              >
                <ImagePlus size={17} />
                Seleccionar archivo
              </button>

              <span className="ai-file-help">
                JPG · JPEG · PNG · DICOM ·
                máximo 20 MB
              </span>
            </div>
          ) : (
            <div className="ai-selected-file">
              <div className="ai-preview">
                {previewUrl ? (
                  <img
                    src={previewUrl}
                    alt="Vista previa de la radiografía"
                  />
                ) : (
                  <div className="ai-dicom-preview">
                    <FileImage size={48} />

                    <strong>
                      Archivo DICOM
                    </strong>

                    <span>
                      El archivo será procesado
                      directamente por el sistema.
                    </span>
                  </div>
                )}
              </div>

              <div className="ai-file-info">
                <div>
                  <span>
                    Archivo seleccionado
                  </span>

                  <strong>
                    {file.name}
                  </strong>

                  <small>
                    {formatFileSize(
                      file.size,
                    )}
                  </small>
                </div>

                <button
                  type="button"
                  className="ai-remove-file"
                  onClick={reset}
                  title="Quitar archivo"
                >
                  <X size={19} />
                </button>
              </div>

              <button
                type="button"
                className="ai-validate-button"
                onClick={handleValidate}
                disabled={loading}
              >
                {loading ? (
                  <>
                    <LoaderCircle
                      className="ai-spinner"
                      size={19}
                    />

                    Analizando imagen...
                  </>
                ) : (
                  <>
                    <BrainCircuit size={19} />
                    Ejecutar análisis
                  </>
                )}
              </button>
            </div>
          )}

          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png,application/dicom"
            hidden
            onChange={
              handleFileChange
            }
          />

          {error && (
            <div className="ai-error-message">
              <XCircle size={19} />
              <span>{error}</span>
            </div>
          )}
        </section>

        <section className="ai-result-card">
          {!result ? (
            <div className="ai-result-empty">
              <div className="ai-result-empty-icon">
                {loading ? (
                  <LoaderCircle
                    size={38}
                    className="ai-spinner"
                  />
                ) : (
                  <BrainCircuit size={38} />
                )}
              </div>

              <h2>
                {loading
                  ? "Analizando imagen"
                  : "Resultado del análisis"}
              </h2>

              <p>
                {loading
                  ? "El pipeline está procesando las etapas de validación."
                  : "Seleccione una imagen y ejecute el análisis para visualizar los resultados."}
              </p>
            </div>
          ) : (
            <div className="ai-result-content">
              <div className="ai-result-title">
                <div>
                  <span>
                    RESULTADOS
                  </span>

                  <h2>
                    Detalle por etapa
                  </h2>
                </div>

                <div
                  className={`ai-final-state ${
                    result.puede_continuar
                      ? "ai-final-state-ok"
                      : "ai-final-state-stop"
                  }`}
                >
                  {result.puede_continuar
                    ? "Pipeline completado"
                    : "Pipeline detenido"}
                </div>
              </div>

              <section className="ai-stage-detail">
                <div className="ai-stage-detail-header">
                  <div
                    className={`ai-stage-detail-number ${
                      result.es_radiografia
                        ? "ai-stage-number-ok"
                        : "ai-stage-number-error"
                    }`}
                  >
                    1
                  </div>

                  <div>
                    <span>
                      ETAPA 1
                    </span>

                    <h3>
                      Validación radiográfica
                    </h3>
                  </div>

                  <div
                    className={`ai-detail-status ${
                      result.es_radiografia
                        ? "ai-detail-status-ok"
                        : "ai-detail-status-error"
                    }`}
                  >
                    {result.es_radiografia ? (
                      <CheckCircle2 size={16} />
                    ) : (
                      <XCircle size={16} />
                    )}

                    {result.es_radiografia
                      ? "Aprobada"
                      : "Rechazada"}
                  </div>
                </div>

                <div className="ai-metrics-grid">
                  <div>
                    <span>
                      Prob. radiografía
                    </span>

                    <strong>
                      {formatPercentage(
                        radiography
                          ?.probabilidad_radiografia ??
                          result.probabilidad_radiografia,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Prob. no radiografía
                    </span>

                    <strong>
                      {formatPercentage(
                        radiography
                          ?.probabilidad_no_radiografia ??
                          result.probabilidad_no_radiografia,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Confianza
                    </span>

                    <strong>
                      {formatPercentage(
                        radiography?.confianza ??
                          result.confianza,
                      )}
                    </strong>
                  </div>

                  <div>
                    <span>
                      Umbral
                    </span>

                    <strong>
                      {formatPercentage(
                        radiography?.umbral ??
                          result.umbral,
                      )}
                    </strong>
                  </div>
                </div>

                <div className="ai-progress">
                  <div
                    className="ai-progress-value"
                    style={{
                      width: `${Math.min(
                        100,
                        Math.max(
                          0,
                          (radiography
                            ?.probabilidad_radiografia ??
                            result.probabilidad_radiografia ??
                            0) * 100,
                        ),
                      )}%`,
                    }}
                  />
                </div>
              </section>

              <section
                className={`ai-stage-detail ${
                  !result.anatomia_evaluada
                    ? "ai-stage-detail-blocked"
                    : ""
                }`}
              >
                <div className="ai-stage-detail-header">
                  <div
                    className={`ai-stage-detail-number ${
                      result.anatomia_evaluada
                        ? result.anatomia_admitida
                          ? "ai-stage-number-ok"
                          : "ai-stage-number-error"
                        : "ai-stage-number-blocked"
                    }`}
                  >
                    {result.anatomia_evaluada
                      ? "2"
                      : (
                        <LockKeyhole
                          size={16}
                        />
                      )}
                  </div>

                  <div>
                    <span>
                      ETAPA 2
                    </span>

                    <h3>
                      Validación anatómica
                    </h3>
                  </div>

                  <div
                    className={`ai-detail-status ${
                      !result.anatomia_evaluada
                        ? "ai-detail-status-blocked"
                        : result.anatomia_admitida
                          ? "ai-detail-status-ok"
                          : "ai-detail-status-error"
                    }`}
                  >
                    {!result.anatomia_evaluada ? (
                      <>
                        <LockKeyhole
                          size={15}
                        />
                        Bloqueada
                      </>
                    ) : result.anatomia_admitida ? (
                      <>
                        <CheckCircle2
                          size={16}
                        />
                        Aprobada
                      </>
                    ) : (
                      <>
                        <XCircle
                          size={16}
                        />
                        Rechazada
                      </>
                    )}
                  </div>
                </div>

                {result.anatomia_evaluada &&
                anatomy ? (
                  <>
                    <div className="ai-metrics-grid">
                      <div>
                        <span>
                          Prob. admitida
                        </span>

                        <strong>
                          {formatPercentage(
                            anatomy.probabilidad_admitida,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Prob. no admitida
                        </span>

                        <strong>
                          {formatPercentage(
                            anatomy.probabilidad_no_admitida,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Confianza
                        </span>

                        <strong>
                          {formatPercentage(
                            anatomy.confianza,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Umbral
                        </span>

                        <strong>
                          {formatPercentage(
                            anatomy.umbral,
                          )}
                        </strong>
                      </div>
                    </div>

                    <div className="ai-progress">
                      <div
                        className="ai-progress-value"
                        style={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              0,
                              anatomy.probabilidad_admitida *
                                100,
                            ),
                          )}%`,
                        }}
                      />
                    </div>

                    <div className="ai-anatomy-scope">
                      <span>
                        REGIONES ANATÓMICAS
                        ADMITIDAS
                      </span>

                      <div>
                        {anatomy.huesos_admitidos.map(
                          (bone) => (
                            <strong
                              key={bone}
                            >
                              {bone}
                            </strong>
                          ),
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="ai-blocked-message">
                    <LockKeyhole
                      size={18}
                    />

                    <span>
                      Esta etapa no fue ejecutada
                      porque la imagen no superó
                      la validación radiográfica.
                    </span>
                  </div>
                )}
              </section>

              <section
                className={`ai-stage-detail ${
                  !result.analisis_osteosarcoma_evaluado
                    ? "ai-stage-detail-blocked"
                    : ""
                }`}
              >
                <div className="ai-stage-detail-header">
                  <div
                    className={`ai-stage-detail-number ${
                      result.analisis_osteosarcoma_evaluado
                        ? "ai-stage-number-ok"
                        : "ai-stage-number-blocked"
                    }`}
                  >
                    {result.analisis_osteosarcoma_evaluado ? (
                      "3"
                    ) : (
                      <LockKeyhole
                        size={16}
                      />
                    )}
                  </div>

                  <div>
                    <span>
                      ETAPA 3
                    </span>

                    <h3>
                      Análisis de osteosarcoma
                    </h3>
                  </div>

                  <div
                    className={`ai-detail-status ${
                      result.analisis_osteosarcoma_evaluado
                        ? "ai-detail-status-ok"
                        : "ai-detail-status-blocked"
                    }`}
                  >
                    {result.analisis_osteosarcoma_evaluado ? (
                      <>
                        <CheckCircle2
                          size={16}
                        />
                        Ejecutada
                      </>
                    ) : (
                      <>
                        <LockKeyhole
                          size={15}
                        />
                        Bloqueada
                      </>
                    )}
                  </div>
                </div>

                {result.analisis_osteosarcoma_evaluado &&
                tumor ? (
                  <>
                    <div className="ai-metrics-grid">
                      <div>
                        <span>
                          Prob. osteosarcoma
                        </span>

                        <strong>
                          {formatPercentage(
                            tumor.probabilidad_osteosarcoma,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Prob. no osteosarcoma
                        </span>

                        <strong>
                          {formatPercentage(
                            tumor.probabilidad_no_osteosarcoma,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Confianza
                        </span>

                        <strong>
                          {formatPercentage(
                            tumor.confianza,
                          )}
                        </strong>
                      </div>

                      <div>
                        <span>
                          Umbral
                        </span>

                        <strong>
                          {formatPercentage(
                            tumor.umbral,
                          )}
                        </strong>
                      </div>
                    </div>

                    <div
                      className={`ai-clinical-result ${
                        tumor.sospechoso
                          ? "ai-clinical-result-warning"
                          : "ai-clinical-result-normal"
                      }`}
                    >
                      <Activity size={21} />

                      <div>
                        <span>
                          RESULTADO DEL MODELO
                        </span>

                        <strong>
                          {tumor.sospechoso
                            ? "Características compatibles con resultado sospechoso"
                            : "Resultado no sospechoso"}
                        </strong>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="ai-blocked-message">
                    <LockKeyhole
                      size={18}
                    />

                    <span>
                      El análisis tumoral no se
                      ejecutó porque una etapa
                      anterior no fue superada.
                    </span>
                  </div>
                )}
              </section>

              <div className="ai-result-message">
                <ShieldCheck size={18} />

                <span>
                  {result.mensaje}
                </span>
              </div>

              <div className="ai-model-summary">
                <div>
                  <span>
                    Familia
                  </span>

                  <strong>
                    {result.familia_modelo}
                  </strong>
                </div>

                <div>
                  <span>
                    Radiografía
                  </span>

                  <strong>
                    {radiography?.version ??
                      "V3"}
                  </strong>
                </div>

                <div>
                  <span>
                    Anatomía
                  </span>

                  <strong>
                    {anatomy?.version ??
                      "No ejecutada"}
                  </strong>
                </div>

                <div>
                  <span>
                    Osteosarcoma
                  </span>

                  <strong>
                    {tumor?.version ??
                      "No ejecutado"}
                  </strong>
                </div>
              </div>

              <button
                type="button"
                className="ai-reset-button"
                onClick={reset}
              >
                <RotateCcw size={17} />
                Probar otra imagen
              </button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
