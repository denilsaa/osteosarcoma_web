import {
  AlertTriangle,
  FileImage,
  LoaderCircle,
  RotateCcw,
  X,
  XCircle,
} from "lucide-react";

import type {
  Dispatch,
  RefObject,
  SetStateAction,
} from "react";

import type { RadiographicFile } from "../../api/radiografias.api";

interface ReprocessDialogProps {
  reprocessTarget: RadiographicFile | null;
  reprocessReason: string;
  reprocessError: string | null;
  reprocessReasonRef: RefObject<HTMLTextAreaElement | null>;
  analyzingFileId: string | null;
  closeReprocessModal: () => void;
  setReprocessReason: Dispatch<SetStateAction<string>>;
  setReprocessError: Dispatch<SetStateAction<string | null>>;
  handleAnalyzeWithAi: (
    file: RadiographicFile,
    confirmedReason?: string,
  ) => Promise<void>;
}

export function RadiographyReprocessDialog({
  reprocessTarget,
  reprocessReason,
  reprocessError,
  reprocessReasonRef,
  analyzingFileId,
  closeReprocessModal,
  setReprocessReason,
  setReprocessError,
  handleAnalyzeWithAi,
}: ReprocessDialogProps) {
  return (
    <>
      {reprocessTarget && (
        <div className="case-radiographies-reprocess-overlay" role="presentation">
          <section
            className="case-radiographies-reprocess-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="radiography-reprocess-title"
            aria-describedby="radiography-reprocess-description"
          >
            <div className="case-radiographies-reprocess-header">
              <div className="case-radiographies-reprocess-icon" aria-hidden="true">
                <RotateCcw size={24} />
              </div>
              <button
                type="button"
                className="case-radiographies-reprocess-close"
                aria-label="Cancelar reprocesamiento"
                onClick={closeReprocessModal}
                disabled={analyzingFileId !== null}
              >
                <X size={19} />
              </button>
            </div>

            <h3 id="radiography-reprocess-title">Reprocesar análisis de IA</h3>
            <p id="radiography-reprocess-description">
              Esta radiografía ya tiene un resultado. Para iniciar un nuevo análisis,
              registra el motivo de forma que quede documentado.
            </p>

            <div className="case-radiographies-reprocess-file">
              <FileImage size={18} aria-hidden="true" />
              <span title={reprocessTarget.original_name}>
                {reprocessTarget.original_name}
              </span>
            </div>

            <form
              onSubmit={(event) => {
                event.preventDefault();
                void handleAnalyzeWithAi(reprocessTarget, reprocessReason);
              }}
            >
              <label htmlFor="radiography-reprocess-reason">
                Motivo del reprocesamiento <span aria-hidden="true">*</span>
              </label>
              <textarea
                ref={reprocessReasonRef}
                id="radiography-reprocess-reason"
                value={reprocessReason}
                minLength={8}
                maxLength={500}
                rows={4}
                placeholder="Ej.: Verificación técnica del análisis anterior"
                aria-required="true"
                aria-invalid={reprocessError !== null}
                aria-describedby="radiography-reprocess-help"
                disabled={analyzingFileId !== null}
                onChange={(event) => {
                  setReprocessReason(event.target.value);
                  setReprocessError(null);
                }}
              />
              <div id="radiography-reprocess-help" className="case-radiographies-reprocess-helper">
                <span>Mínimo 8 caracteres. Requiere autorización de jefatura.</span>
                <span>{reprocessReason.trim().length}/500</span>
              </div>
              {reprocessError && (
                <p className="case-radiographies-reprocess-error" role="alert">
                  <AlertTriangle size={16} aria-hidden="true" />
                  {reprocessError}
                </p>
              )}
              <footer className="case-radiographies-reprocess-actions">
                <button
                  type="button"
                  className="case-radiographies-reprocess-cancel"
                  onClick={closeReprocessModal}
                  disabled={analyzingFileId !== null}
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="case-radiographies-reprocess-confirm"
                  disabled={reprocessReason.trim().length < 8 || analyzingFileId !== null}
                >
                  {analyzingFileId === reprocessTarget.id_file ? (
                    <>
                      <LoaderCircle size={16} className="case-radiographies-spin" />
                      Enviando...
                    </>
                  ) : (
                    <>
                      <RotateCcw size={16} />
                      Confirmar reprocesamiento
                    </>
                  )}
                </button>
              </footer>
            </form>
          </section>
        </div>
      )}
    </>
  );
}

interface UploadErrorDialogProps {
  uploadErrorModal: string | null;
  closeUploadErrorModal: () => void;
}

export function RadiographyUploadErrorDialog({
  uploadErrorModal,
  closeUploadErrorModal,
}: UploadErrorDialogProps) {
  return (
    <>
      {
        uploadErrorModal
        &&
        (
          <div
            className="case-radiographies-upload-error-overlay"
            role="presentation"
          >
            <section
              className="case-radiographies-upload-error-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="radiography-upload-error-title"
              aria-describedby="radiography-upload-error-description"
            >
              <button
                type="button"
                className="case-radiographies-upload-error-close"
                aria-label="Cerrar mensaje"
                onClick={
                  closeUploadErrorModal
                }
              >
                <X
                  size={19}
                />
              </button>

              <div
                className="case-radiographies-upload-error-icon"
                aria-hidden="true"
              >
                <XCircle
                  size={31}
                />
              </div>

              <div
                className="case-radiographies-upload-error-content"
              >
                <span
                  className="case-radiographies-upload-error-eyebrow"
                >
                  Archivo rechazado
                </span>

                <h3
                  id="radiography-upload-error-title"
                >
                  La imagen seleccionada no es una radiografía válida
                </h3>

                <p
                  id="radiography-upload-error-description"
                  className="case-radiographies-upload-error-message"
                >
                  {
                    uploadErrorModal
                  }
                </p>

                <div
                  className="case-radiographies-upload-error-guidance"
                >
                  <FileImage
                    size={21}
                  />

                  <div>
                    <strong>
                      ¿Cómo corregirlo?
                    </strong>

                    <span>
                      Cierre este mensaje y seleccione otra imagen
                      JPG, JPEG, PNG o DICOM que corresponda a una
                      radiografía.
                    </span>
                  </div>
                </div>

                <button
                  type="button"
                  className="case-radiographies-upload-error-action"
                  onClick={
                    closeUploadErrorModal
                  }
                >
                  <X
                    size={17}
                  />
                  Cerrar y seleccionar otra imagen
                </button>
              </div>
            </section>
          </div>
        )
      }
    </>
  );
}
