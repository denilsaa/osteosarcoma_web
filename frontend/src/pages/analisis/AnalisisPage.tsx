import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { AxiosError } from "axios";
import {
  BrainCircuit,
  CheckCircle2,
  FileImage,
  ImagePlus,
  LoaderCircle,
  RotateCcw,
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

function getExtension(filename: string): string {
  return filename.split(".").pop()?.toLowerCase() ?? "";
}

function formatPercentage(value: number): string {
  return `${(value * 100).toFixed(2)} %`;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
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

    return "No fue posible validar la imagen.";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "No fue posible validar la imagen.";
}

export function AnalisisPage() {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<RadiographyValidationResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
  }, [previewUrl]);

  function reset(): void {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(null);
    setFile(null);
    setResult(null);
    setError(null);
    setLoading(false);
    if (inputRef.current) inputRef.current.value = "";
  }

  function selectFile(selected: File): void {
    setResult(null);
    setError(null);
    const extension = getExtension(selected.name);
    if (!ACCEPTED_EXTENSIONS.includes(extension)) {
      setError("Formato no admitido. Seleccione JPG, JPEG, PNG o DICOM.");
      return;
    }
    if (selected.size > MAX_FILE_SIZE) {
      setError("El archivo supera el límite máximo de 20 MB.");
      return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setFile(selected);
    setPreviewUrl(extension === "dcm" ? null : URL.createObjectURL(selected));
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>): void {
    const selected = event.target.files?.[0];
    if (selected) selectFile(selected);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>): void {
    event.preventDefault();
    setDragging(false);
    const selected = event.dataTransfer.files?.[0];
    if (selected) selectFile(selected);
  }

  async function handleValidate(): Promise<void> {
    if (!file || loading) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      setResult(await validateRadiography(file));
    } catch (validationError) {
      setError(getErrorMessage(validationError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="ai-analysis-page">
      <header className="ai-analysis-header">
        <div className="ai-analysis-heading">
          <div className="ai-analysis-heading-icon"><BrainCircuit size={25} /></div>
          <div>
            <h1>Análisis con IA</h1>
            <p>Validación inicial de imágenes radiográficas mediante EfficientNet.</p>
          </div>
        </div>
        <div className="ai-analysis-model-badge"><ShieldCheck size={17} /> Validador radiográfico V2</div>
      </header>

      <div className="ai-analysis-grid">
        <section className="ai-upload-card">
          <div className="ai-card-heading">
            <span className="ai-step">ETAPA 1</span>
            <h2>Seleccionar imagen</h2>
            <p>Compruebe si el archivo corresponde a una radiografía antes de continuar con el análisis.</p>
          </div>

          {!file ? (
            <div
              className={`ai-drop-zone ${dragging ? "ai-drop-zone-active" : ""}`}
              onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
              onDragLeave={(event) => { event.preventDefault(); setDragging(false); }}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
            >
              <div className="ai-drop-icon"><Upload size={30} /></div>
              <h3>Cargar imagen</h3>
              <p>Arrastre una imagen aquí o selecciónela desde su equipo.</p>
              <button type="button" className="ai-select-button"><ImagePlus size={17} /> Seleccionar archivo</button>
              <span className="ai-file-help">JPG · JPEG · PNG · DICOM · máximo 20 MB</span>
            </div>
          ) : (
            <div className="ai-selected-file">
              <div className="ai-preview">
                {previewUrl ? (
                  <img src={previewUrl} alt="Vista previa de la imagen seleccionada" />
                ) : (
                  <div className="ai-dicom-preview">
                    <FileImage size={48} />
                    <strong>Archivo DICOM</strong>
                    <span>El archivo será enviado directamente al validador.</span>
                  </div>
                )}
              </div>
              <div className="ai-file-info">
                <div><span>Archivo seleccionado</span><strong>{file.name}</strong><small>{formatFileSize(file.size)}</small></div>
                <button type="button" className="ai-remove-file" onClick={reset} title="Quitar archivo"><X size={19} /></button>
              </div>
              <button type="button" className="ai-validate-button" onClick={handleValidate} disabled={loading}>
                {loading ? <><LoaderCircle className="ai-spinner" size={19} /> Analizando imagen...</> : <><BrainCircuit size={19} /> Validar radiografía</>}
              </button>
            </div>
          )}

          <input ref={inputRef} type="file" accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png,application/dicom" hidden onChange={handleFileChange} />
          {error && <div className="ai-error-message"><XCircle size={19} /><span>{error}</span></div>}
        </section>

        <section className="ai-result-card">
          {!result ? (
            <div className="ai-result-empty">
              <div className="ai-result-empty-icon"><BrainCircuit size={38} /></div>
              <h2>Resultado de validación</h2>
              <p>Seleccione una imagen y ejecute la validación para visualizar la respuesta real del modelo.</p>
            </div>
          ) : (
            <div className="ai-result-content">
              <div className={result.es_radiografia ? "ai-result-status ai-result-success" : "ai-result-status ai-result-rejected"}>
                {result.es_radiografia ? <CheckCircle2 size={27} /> : <XCircle size={27} />}
                <div><span>Resultado</span><strong>{result.es_radiografia ? "Radiografía identificada" : "Imagen no admitida"}</strong></div>
              </div>

              <div className="ai-probability-section">
                <div className="ai-probability-row">
                  <div className="ai-probability-label"><span>Probabilidad de radiografía</span><strong>{formatPercentage(result.probabilidad_radiografia)}</strong></div>
                  <div className="ai-progress"><div className="ai-progress-value" style={{ width: `${Math.min(100, Math.max(0, result.probabilidad_radiografia * 100))}%` }} /></div>
                </div>
                <div className="ai-probability-row">
                  <div className="ai-probability-label"><span>Probabilidad de no radiografía</span><strong>{formatPercentage(result.probabilidad_no_radiografia)}</strong></div>
                  <div className="ai-progress"><div className="ai-progress-value" style={{ width: `${Math.min(100, Math.max(0, result.probabilidad_no_radiografia * 100))}%` }} /></div>
                </div>
              </div>

              <div className="ai-model-details">
                <div><span>Confianza</span><strong>{formatPercentage(result.confianza)}</strong></div>
                <div><span>Umbral</span><strong>{formatPercentage(result.umbral)}</strong></div>
                <div><span>Arquitectura</span><strong>{result.arquitectura}</strong></div>
                <div><span>Familia</span><strong>{result.familia_modelo}</strong></div>
              </div>

              <div className="ai-result-message">{result.mensaje}</div>
              <button type="button" className="ai-reset-button" onClick={reset}><RotateCcw size={17} /> Probar otra imagen</button>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
