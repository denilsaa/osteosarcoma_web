import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Eye,
  FileImage,
  Image,
  Info,
  LoaderCircle,
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
  RotateCw,
  Save,
  Sun,
  ShieldAlert,
  Upload,
  X,
  XCircle,
  ZoomIn,
  ZoomOut,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createRadiography,
  getCaseRadiographies,
  getRadiographicFileBlob,
  getRadiographyCatalogs,
  replaceRejectedRadiographicFile,
  type RadiographicFile,
  type RadiographicStudy,
  type RadiographyCatalogs,
} from "../../api/radiografias.api";

import "./CaseRadiographiesSection.css";


interface Props {
  caseId:
    string;

  resolveAuthorName:
    (
      userUuid:
        string,
    ) => string;
}


type ViewerPoint = {
  x: number;
  y: number;
};


function formatDate(
  value?:
    string | null,
): string {

  if (!value) {
    return "â€”";
  }

  const date =
    new Date(
      `${value.substring(0, 10)}T00:00:00`,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",
    },
  ).format(
    date,
  );
}


function formatDateTime(
  value?:
    string | null,
): string {

  if (!value) {
    return "â€”";
  }

  const date =
    new Date(
      value,
    );

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",

      hour:
        "2-digit",

      minute:
        "2-digit",
    },
  ).format(
    date,
  );
}


function formatBytes(
  value:
    number,
): string {

  if (
    value < 1024
  ) {
    return `${value} B`;
  }

  if (
    value
    <
    1024 * 1024
  ) {
    return (
      `${(
        value
        /
        1024
      ).toFixed(1)} KB`
    );
  }

  return (
    `${(
      value
      /
      (
        1024
        *
        1024
      )
    ).toFixed(2)} MB`
  );
}


function getErrorMessage(
  error:
    unknown,
): string {

  if (
    typeof error ===
    "object"
    &&
    error !== null
    &&
    "response" in error
  ) {

    const response =
      (
        error as {
          response?: {
            data?: {
              message?:
                string;

              error?:
                string
                |
                {
                  message?:
                    string;
                };

              errors?:
                Record<
                  string,
                  string[]
                >;
            };
          };
        }
      )
        .response;

    if (
      typeof response
        ?.data
        ?.error
      ===
      "object"
      &&
      response
        ?.data
        ?.error
        ?.message
    ) {

      return response
        .data
        .error
        .message;
    }

    if (
      typeof response
        ?.data
        ?.error
      ===
      "string"
    ) {

      return response
        .data
        .error;
    }

    if (
      response
        ?.data
        ?.message
    ) {

      return response
        .data
        .message;
    }

    const errors =
      response
        ?.data
        ?.errors;

    if (errors) {

      const first =
        Object
          .values(
            errors,
          )
          .flat()
          .find(
            Boolean,
          );

      if (first) {
        return first;
      }
    }
  }

  return (
    "No fue posible completar la operaciÃ³n."
  );
}


function getValidationStatusLabel(
  file:
    RadiographicFile,
): string {

  switch (
    file.validation_status
  ) {

    case "VALIDA":
      return "RadiografÃ­a vÃ¡lida";

    case "RECHAZADA":
      return "RadiografÃ­a rechazada";

    case "PENDIENTE":
      return "ValidaciÃ³n pendiente";

    default:
      return file.validation_status;
  }
}


function getValidationStatusClass(
  file:
    RadiographicFile,
): string {

  switch (
    file.validation_status
  ) {

    case "VALIDA":
      return "case-radiographies-status--valid";

    case "RECHAZADA":
      return "case-radiographies-status--rejected";

    default:
      return "case-radiographies-status--pending";
  }
}


export function CaseRadiographiesSection({
  caseId,
  resolveAuthorName,
}: Props) {

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );

  const viewerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const draggingRef =
    useRef(false);

  const dragStartRef =
    useRef<ViewerPoint>({
      x: 0,
      y: 0,
    });

  const panStartRef =
    useRef<ViewerPoint>({
      x: 0,
      y: 0,
    });

  const [
    catalogs,
    setCatalogs,
  ] =
    useState<RadiographyCatalogs | null>(
      null,
    );

  const [
    studies,
    setStudies,
  ] =
    useState<RadiographicStudy[]>(
      [],
    );

  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );

  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );

  const [
    uploadProgress,
    setUploadProgress,
  ] =
    useState(
      0,
    );

  const [
    confirming,
    setConfirming,
  ] =
    useState(
      false,
    );

  const [
    workingFileId,
    setWorkingFileId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    showForm,
    setShowForm,
  ] =
    useState(
      false,
    );

  const [
    error,
    setError,
  ] =
    useState<string | null>(
      null,
    );

  const [
    success,
    setSuccess,
  ] =
    useState<string | null>(
      null,
    );

  const [
    studyTypeId,
    setStudyTypeId,
  ] =
    useState(
      "",
    );

  const [
    anatomicalRegionId,
    setAnatomicalRegionId,
  ] =
    useState(
      "",
    );

  const [
    lateralityId,
    setLateralityId,
  ] =
    useState(
      "",
    );

  const [
    studyDate,
    setStudyDate,
  ] =
    useState(
      "",
    );

  const [
    observation,
    setObservation,
  ] =
    useState(
      "",
    );

  const [
    selectedFile,
    setSelectedFile,
  ] =
    useState<File | null>(
      null,
    );


  // ==========================================================
  // VISOR RADIOGRÁFICO
  // ==========================================================

  const [
    viewerUrl,
    setViewerUrl,
  ] =
    useState<string | null>(
      null,
    );

  const [
    viewerFileName,
    setViewerFileName,
  ] =
    useState("");

  const [
    viewerZoom,
    setViewerZoom,
  ] =
    useState(1);

  const [
    viewerRotation,
    setViewerRotation,
  ] =
    useState(0);

  const [
    viewerBrightness,
    setViewerBrightness,
  ] =
    useState(100);

  const [
    viewerContrast,
    setViewerContrast,
  ] =
    useState(100);

  const [
    viewerInvert,
    setViewerInvert,
  ] =
    useState(false);

  const [
    viewerPan,
    setViewerPan,
  ] =
    useState<ViewerPoint>({
      x: 0,
      y: 0,
    });



  const replacementFileInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );

  const [
    replacementTarget,
    setReplacementTarget,
  ] =
    useState<RadiographicFile | null>(
      null,
    );

  const [
    replacementFile,
    setReplacementFile,
  ] =
    useState<File | null>(
      null,
    );

  const [
    replacementReason,
    setReplacementReason,
  ] =
    useState(
      "",
    );

  const [
    replacing,
    setReplacing,
  ] =
    useState(
      false,
    );

  const [
    replacementProgress,
    setReplacementProgress,
  ] =
    useState(
      0,
    );


  const loadStudies =
    useCallback(
      async () => {

        const response =
          await getCaseRadiographies(
            caseId,
          );

        setStudies(
          response.data,
        );

      },
      [
        caseId,
      ],
    );


  const loadAll =
    useCallback(
      async () => {

        setLoading(
          true,
        );

        setError(
          null,
        );

        try {

          const [
            catalogData,
            radiographyData,
          ] =
            await Promise.all(
              [
                getRadiographyCatalogs(),

                getCaseRadiographies(
                  caseId,
                ),
              ],
            );

          setCatalogs(
            catalogData,
          );

          setStudies(
            radiographyData.data,
          );

        } catch (
          requestError
        ) {

          setError(
            getErrorMessage(
              requestError,
            ),
          );

        } finally {

          setLoading(
            false,
          );
        }

      },
      [
        caseId,
      ],
    );


  useEffect(
    () => {

      void loadAll();

    },
    [
      loadAll,
    ],
  );


  useEffect(
    () => {
      if (!viewerUrl) {
        return;
      }

      document.body.classList.add(
        "case-radiographies-viewer-open",
      );

      return () => {
        document.body.classList.remove(
          "case-radiographies-viewer-open",
        );
      };
    },
    [
      viewerUrl,
    ],
  );


  useEffect(
    () => {
      return () => {
        if (viewerUrl) {
          URL.revokeObjectURL(
            viewerUrl,
          );
        }
      };
    },
    [
      viewerUrl,
    ],
  );


  useEffect(
    () => {
      function handleKeyDown(
        event: KeyboardEvent,
      ) {
        if (
          event.key === "Escape"
          &&
          viewerUrl
        ) {
          closeViewer();
        }
      }

      window.addEventListener(
        "keydown",
        handleKeyDown,
      );

      return () => {
        window.removeEventListener(
          "keydown",
          handleKeyDown,
        );
      };
    },
    [
      viewerUrl,
    ],
  );


  function resetForm() {

    setStudyTypeId(
      "",
    );

    setAnatomicalRegionId(
      "",
    );

    setLateralityId(
      "",
    );

    setStudyDate(
      "",
    );

    setObservation(
      "",
    );

    setSelectedFile(
      null,
    );

    setUploadProgress(
      0,
    );

    setConfirming(
      false,
    );

    if (
      fileInputRef.current
    ) {

      fileInputRef
        .current
        .value =
          "";
    }
  }


  function closeForm() {

    if (saving) {
      return;
    }

    resetForm();

    setShowForm(
      false,
    );

    setError(
      null,
    );
  }


  function resetViewer() {
    setViewerZoom(1);
    setViewerRotation(0);
    setViewerBrightness(100);
    setViewerContrast(100);
    setViewerInvert(false);

    setViewerPan({
      x: 0,
      y: 0,
    });
  }


  function closeViewer() {
    if (viewerUrl) {
      URL.revokeObjectURL(
        viewerUrl,
      );
    }

    setViewerUrl(null);
    setViewerFileName("");

    resetViewer();
  }


  function zoomIn() {
    setViewerZoom(
      (
        current,
      ) =>
        Math.min(
          4,
          Number(
            (
              current
              +
              0.25
            ).toFixed(2),
          ),
        ),
    );
  }


  function zoomOut() {
    setViewerZoom(
      (
        current,
      ) =>
        Math.max(
          0.5,
          Number(
            (
              current
              -
              0.25
            ).toFixed(2),
          ),
        ),
    );
  }


  function rotateViewer() {
    setViewerRotation(
      (
        current,
      ) =>
        (
          current
          +
          90
        )
        %
        360,
    );
  }


  async function toggleFullscreen() {
    const element =
      viewerRef.current;

    if (!element) {
      return;
    }

    try {
      if (
        document.fullscreenElement
      ) {
        await document
          .exitFullscreen();

        return;
      }

      await element
        .requestFullscreen();
    } catch {
      // El visor sigue funcionando aunque
      // el navegador rechace pantalla completa.
    }
  }


  function handlePointerDown(
    event:
      React.PointerEvent<HTMLDivElement>,
  ) {
    if (!viewerUrl) {
      return;
    }

    draggingRef.current =
      true;

    dragStartRef.current = {
      x: event.clientX,
      y: event.clientY,
    };

    panStartRef.current = {
      ...viewerPan,
    };

    event.currentTarget
      .setPointerCapture(
        event.pointerId,
      );
  }


  function handlePointerMove(
    event:
      React.PointerEvent<HTMLDivElement>,
  ) {
    if (
      !draggingRef.current
    ) {
      return;
    }

    const deltaX =
      event.clientX
      -
      dragStartRef.current.x;

    const deltaY =
      event.clientY
      -
      dragStartRef.current.y;

    setViewerPan({
      x:
        panStartRef.current.x
        +
        deltaX,

      y:
        panStartRef.current.y
        +
        deltaY,
    });
  }


  function handlePointerEnd(
    event:
      React.PointerEvent<HTMLDivElement>,
  ) {
    draggingRef.current =
      false;

    if (
      event.currentTarget
        .hasPointerCapture(
          event.pointerId,
        )
    ) {
      event.currentTarget
        .releasePointerCapture(
          event.pointerId,
        );
    }
  }


  function handleViewerWheel(
    event:
      React.WheelEvent<HTMLDivElement>,
  ) {
    event.preventDefault();

    if (
      event.deltaY < 0
    ) {
      zoomIn();
    } else {
      zoomOut();
    }
  }


  function validateForm():
    string | null {

    if (
      !studyTypeId
    ) {

      return (
        "Seleccione el tipo de estudio."
      );
    }

    if (
      !anatomicalRegionId
    ) {

      return (
        "Seleccione la regiÃ³n anatÃ³mica."
      );
    }

    if (
      !lateralityId
    ) {

      return (
        "Seleccione la lateralidad."
      );
    }

    if (
      !selectedFile
    ) {

      return (
        "Seleccione una radiografÃ­a."
      );
    }

    const extension =
      selectedFile
        .name
        .split(".")
        .pop()
        ?.toLowerCase();

    if (
      !extension
      ||
      ![
        "jpg",
        "jpeg",
        "png",
        "dcm",
      ].includes(
        extension,
      )
    ) {

      return (
        "Solo se permiten archivos JPG, PNG o DICOM."
      );
    }

    if (
      selectedFile.size
      >
      20 * 1024 * 1024
    ) {

      return (
        "El archivo no puede superar los 20 MB."
      );
    }

    return null;
  }


  function handleRequestConfirmation() {

    const validationError =
      validateForm();

    if (
      validationError
    ) {

      setError(
        validationError,
      );

      setConfirming(
        false,
      );

      return;
    }

    setError(
      null,
    );

    setConfirming(
      true,
    );
  }


  async function handleConfirmedSave() {

    const validationError =
      validateForm();

    if (
      validationError
    ) {

      setError(
        validationError,
      );

      setConfirming(
        false,
      );

      return;
    }

    if (
      !selectedFile
    ) {
      return;
    }

    setSaving(
      true,
    );

    setConfirming(
      false,
    );

    setUploadProgress(
      0,
    );

    setError(
      null,
    );

    try {

      const response =
        await createRadiography(
          caseId,
          {
            study_type_id:
              Number(
                studyTypeId,
              ),

            anatomical_region_id:
              Number(
                anatomicalRegionId,
              ),

            laterality_id:
              Number(
                lateralityId,
              ),

            study_date:
              studyDate
              ||
              null,

            observation:
              observation
                .trim()
              ||
              null,

            file:
              selectedFile,
          },
          {
            onUploadProgress:
              (
                progress,
              ) => {

                setUploadProgress(
                  progress,
                );
              },
          },
        );

      setUploadProgress(
        100,
      );

      await loadStudies();

      const createdFile =
        response
          .data
          .files
          .find(
            (
              file,
            ) =>
              file.active,
          )
        ??
        response
          .data
          .files[0];

      resetForm();

      setShowForm(
        false,
      );

      if (
        createdFile
          ?.validation_status
        ===
        "RECHAZADA"
      ) {

        setSuccess(
          null,
        );

        setError(
          "La radiografÃ­a fue recibida, pero fue rechazada durante la validaciÃ³n. Revise el motivo y la correcciÃ³n necesaria antes de enviarla al anÃ¡lisis.",
        );

      } else {

        setError(
          null,
        );

        setSuccess(
          "RadiografÃ­a registrada y validada correctamente.",
        );

        window.setTimeout(
          () => {

            setSuccess(
              null,
            );

          },
          3500,
        );
      }

    } catch (
      requestError
    ) {

      setUploadProgress(
        0,
      );

      setError(
        getErrorMessage(
          requestError,
        ),
      );

    } finally {

      setSaving(
        false,
      );
    }
  }


  async function handleView(
    fileId: string,
    fileName: string,
  ) {
    setWorkingFileId(
      fileId,
    );

    setError(null);

    try {
      const blob =
        await getRadiographicFileBlob(
          fileId,
        );

      if (viewerUrl) {
        URL.revokeObjectURL(
          viewerUrl,
        );
      }

      const url =
        URL.createObjectURL(
          blob,
        );

      resetViewer();

      setViewerFileName(
        fileName,
      );

      setViewerUrl(
        url,
      );
    } catch (
      requestError
    ) {
      setError(
        getErrorMessage(
          requestError,
        ),
      );
    } finally {
      setWorkingFileId(
        null,
      );
    }
  }


  function resetReplacementForm() {

    setReplacementTarget(
      null,
    );

    setReplacementFile(
      null,
    );

    setReplacementReason(
      "",
    );

    setReplacementProgress(
      0,
    );

    if (
      replacementFileInputRef.current
    ) {

      replacementFileInputRef
        .current
        .value =
        "";
    }
  }


  function openReplacement(
    file: RadiographicFile,
  ) {

    setError(
      null,
    );

    setSuccess(
      null,
    );

    setReplacementTarget(
      file,
    );

    setReplacementFile(
      null,
    );

    setReplacementReason(
      "",
    );

    setReplacementProgress(
      0,
    );
  }


  function validateReplacement():
    string | null {

    if (
      !replacementTarget
    ) {
      return "Seleccione la radiografÃ­a rechazada que desea reemplazar.";
    }

    if (
      !replacementFile
    ) {
      return "Seleccione la nueva radiografÃ­a.";
    }

    const extension =
      replacementFile
        .name
        .split(".")
        .pop()
        ?.toLowerCase();

    if (
      !extension
      ||
      ![
        "jpg",
        "jpeg",
        "png",
        "dcm",
      ].includes(
        extension,
      )
    ) {
      return "Solo se permiten archivos JPG, PNG o DICOM.";
    }

    if (
      replacementFile.size
      >
      20 * 1024 * 1024
    ) {
      return "El archivo no puede superar los 20 MB.";
    }

    if (
      !replacementReason.trim()
    ) {
      return "Ingrese el motivo del reemplazo.";
    }

    return null;
  }


async function handleReplacement() {

  const validationError =
    validateReplacement();

  if (
    validationError
  ) {
    setError(
      validationError,
    );
    return;
  }

  if (
    !replacementTarget
    ||
    !replacementFile
  ) {
    return;
  }

  setReplacing(
    true,
  );

  setReplacementProgress(
    0,
  );

  setError(
    null,
  );

  setSuccess(
    null,
  );

  try {

    const response =
      await replaceRejectedRadiographicFile(
        caseId,
        replacementTarget.id_file,
        {
          file:
            replacementFile,

          replacement_reason:
            replacementReason.trim(),
        },
        {
          onUploadProgress:
            (progress) => {
              setReplacementProgress(
                progress,
              );
            },
        },
      );

    setReplacementProgress(
      100,
    );

    /*
     * El endpoint de reemplazo devuelve directamente
     * el nuevo archivo dentro de response.data.
     *
     * No devuelve un estudio completo con .files.
     */
    const newestFile =
      response.data;

    /*
     * Volvemos a consultar los estudios para que
     * la interfaz refleje:
     *
     * - V1 como inactiva.
     * - V2 como nueva versiÃ³n activa.
     * - sus validaciones actualizadas.
     */
    await loadStudies();

    resetReplacementForm();

    if (
      newestFile
        .validation_status
      ===
      "RECHAZADA"
    ) {
      setError(
        "La nueva versiÃ³n fue cargada, pero tambiÃ©n fue rechazada durante la validaciÃ³n. Revise las correcciones indicadas antes de intentar otro reemplazo.",
      );

      return;
    }

    setSuccess(
      `RadiografÃ­a reemplazada correctamente. Se registrÃ³ la versiÃ³n ${newestFile.version} y la versiÃ³n anterior se conserva para trazabilidad.`,
    );

    window.setTimeout(
      () => {
        setSuccess(
          null,
        );
      },
      4500,
    );

  } catch (
    requestError
  ) {

    setReplacementProgress(
      0,
    );

    setError(
      getErrorMessage(
        requestError,
      ),
    );

  } finally {

    setReplacing(
      false,
    );
  }
}

  const selectedStudyType =
    catalogs
      ?.study_types
      .find(
        (
          item,
        ) =>
          String(
            item.id,
          )
          ===
          studyTypeId,
      );


  const selectedRegion =
    catalogs
      ?.anatomical_regions
      .find(
        (
          item,
        ) =>
          String(
            item.id,
          )
          ===
          anatomicalRegionId,
      );


  const selectedLaterality =
    catalogs
      ?.lateralities
      .find(
        (
          item,
        ) =>
          String(
            item.id,
          )
          ===
          lateralityId,
      );


  if (
    loading
  ) {

    return (

      <div
        className="case-radiographies-loading"
      >

        <LoaderCircle
          size={28}
          className="case-radiographies-spin"
        />

        <span>
          Cargando radiografÃ­as...
        </span>

      </div>
    );
  }


  return (

    <>
      <article
      className="case-radiographies"
    >

      <header
        className="case-radiographies-header"
      >

        <div
          className="case-radiographies-title"
        >

          <div
            className="case-radiographies-title-icon"
          >
            <Image
              size={21}
            />
          </div>

          <div>
            <h2>
              RadiografÃ­as del caso
            </h2>

            <p>
              {
                studies.length
              } estudio(s) radiogrÃ¡fico(s)
            </p>
          </div>

        </div>

        <button
          type="button"
          className="case-radiographies-primary"
          disabled={
            saving
          }
          onClick={
            () => {

              if (
                showForm
              ) {

                closeForm();

              } else {

                setShowForm(
                  true,
                );

                setError(
                  null,
                );
              }
            }
          }
        >

          {
            showForm
              ? (
                  <X
                    size={17}
                  />
                )
              : (
                  <Plus
                    size={17}
                  />
                )
          }

          {
            showForm
              ? "Cerrar formulario"
              : "Registrar radiografÃ­a"
          }

        </button>

      </header>


      {
        error
        &&
        (

          <div
            className="case-radiographies-message case-radiographies-message--error"
          >
            {error}
          </div>
        )
      }


      {
        success
        &&
        (

          <div
            className="case-radiographies-message case-radiographies-message--success"
          >
            {success}
          </div>
        )
      }


      {
        showForm
        &&
        (

          <div
            className="case-radiographies-form"
          >

            <div
              className="case-radiographies-form-heading"
            >

              <Upload
                size={20}
              />

              <div>
                <strong>
                  Registrar nuevo estudio
                </strong>

                <span>
                  Complete los datos obligatorios
                  y seleccione la radiografÃ­a.
                </span>
              </div>

            </div>


            <div
              className="case-radiographies-form-grid"
            >

              <label>
                Tipo de estudio *

                <select
                  disabled={
                    saving
                  }
                  value={
                    studyTypeId
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setStudyTypeId(
                        event.target.value,
                      )
                  }
                >
                  <option value="">
                    Seleccione
                  </option>

                  {
                    catalogs
                      ?.study_types
                      .map(
                        (
                          item,
                        ) => (

                          <option
                            key={
                              item.id
                            }
                            value={
                              item.id
                            }
                          >
                            {item.name}
                          </option>
                        ),
                      )
                  }
                </select>
              </label>


              <label>
                Zona anatÃ³mica *

                <select
                  disabled={
                    saving
                  }
                  value={
                    anatomicalRegionId
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setAnatomicalRegionId(
                        event.target.value,
                      )
                  }
                >
                  <option value="">
                    Seleccione
                  </option>

                  {
                    catalogs
                      ?.anatomical_regions
                      .map(
                        (
                          item,
                        ) => (

                          <option
                            key={
                              item.id
                            }
                            value={
                              item.id
                            }
                          >
                            {item.name}
                          </option>
                        ),
                      )
                  }
                </select>
              </label>


              <label>
                Lateralidad *

                <select
                  disabled={
                    saving
                  }
                  value={
                    lateralityId
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setLateralityId(
                        event.target.value,
                      )
                  }
                >
                  <option value="">
                    Seleccione
                  </option>

                  {
                    catalogs
                      ?.lateralities
                      .map(
                        (
                          item,
                        ) => (

                          <option
                            key={
                              item.id
                            }
                            value={
                              item.id
                            }
                          >
                            {item.name}
                          </option>
                        ),
                      )
                  }
                </select>
              </label>


              <label>
                Fecha del estudio

                <input
                  type="date"
                  disabled={
                    saving
                  }
                  value={
                    studyDate
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setStudyDate(
                        event.target.value,
                      )
                  }
                />
              </label>


              <label
                className="case-radiographies-form-wide"
              >
                Observaciones

                <textarea
                  rows={3}
                  maxLength={4000}
                  disabled={
                    saving
                  }
                  value={
                    observation
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setObservation(
                        event.target.value,
                      )
                  }
                  placeholder="Ej.: lesiÃ³n localizada en regiÃ³n proximal..."
                />
              </label>


              <label
                className="case-radiographies-file-field case-radiographies-form-wide"
              >

                <span>
                  Archivo radiogrÃ¡fico *
                </span>

                <input
                  ref={
                    fileInputRef
                  }
                  type="file"
                  disabled={
                    saving
                  }
                  accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png,application/dicom"
                  onChange={
                    (
                      event,
                    ) => {

                      const file =
                        event
                          .target
                          .files
                          ?.[0]
                        ??
                        null;

                      setSelectedFile(
                        file,
                      );

                      setError(
                        null,
                      );

                      setConfirming(
                        false,
                      );

                      setUploadProgress(
                        0,
                      );
                    }
                  }
                />

                <div
                  className="case-radiographies-file-box"
                >

                  <FileImage
                    size={29}
                  />

                  {
                    selectedFile
                      ? (
                          <>
                            <strong>
                              {
                                selectedFile
                                  .name
                              }
                            </strong>

                            <span>
                              {
                                formatBytes(
                                  selectedFile
                                    .size,
                                )
                              }
                            </span>
                          </>
                        )
                      : (
                          <>
                            <strong>
                              Seleccione JPG, PNG o DICOM
                            </strong>

                            <span>
                              TamaÃ±o mÃ¡ximo: 20 MB
                            </span>
                          </>
                        )
                  }

                </div>

              </label>

            </div>


            {
              confirming
              &&
              selectedFile
              &&
              (

                <div
                  className="case-radiographies-confirmation"
                >

                  <div
                    className="case-radiographies-confirmation-heading"
                  >

                    <CheckCircle2
                      size={22}
                    />

                    <div>
                      <strong>
                        Confirme la carga
                      </strong>

                      <span>
                        Revise la informaciÃ³n antes de
                        enviar la radiografÃ­a.
                      </span>
                    </div>

                  </div>


                  <div
                    className="case-radiographies-confirmation-grid"
                  >

                    <div>
                      <span>
                        Tipo de estudio
                      </span>

                      <strong>
                        {
                          selectedStudyType
                            ?.name
                          ??
                          "â€”"
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        RegiÃ³n anatÃ³mica
                      </span>

                      <strong>
                        {
                          selectedRegion
                            ?.name
                          ??
                          "â€”"
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Lateralidad
                      </span>

                      <strong>
                        {
                          selectedLaterality
                            ?.name
                          ??
                          "â€”"
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Fecha del estudio
                      </span>

                      <strong>
                        {
                          studyDate
                            ? formatDate(
                                studyDate,
                              )
                            : "No especificada"
                        }
                      </strong>
                    </div>

                    <div
                      className="case-radiographies-confirmation-wide"
                    >
                      <span>
                        Archivo
                      </span>

                      <strong>
                        {
                          selectedFile.name
                        }
                      </strong>

                      <small>
                        {
                          formatBytes(
                            selectedFile.size,
                          )
                        }
                      </small>
                    </div>

                  </div>


                  <div
                    className="case-radiographies-confirmation-actions"
                  >

                    <button
                      type="button"
                      className="case-radiographies-secondary"
                      onClick={
                        () =>
                          setConfirming(
                            false,
                          )
                      }
                    >
                      Volver a editar
                    </button>

                    <button
                      type="button"
                      className="case-radiographies-primary"
                      onClick={
                        () =>
                          void handleConfirmedSave()
                      }
                    >
                      <Upload
                        size={17}
                      />

                      Confirmar y cargar
                    </button>

                  </div>

                </div>
              )
            }


            {
              saving
              &&
              (

                <div
                  className="case-radiographies-progress"
                  aria-live="polite"
                >

                  <div
                    className="case-radiographies-progress-header"
                  >

                    <div>
                      <LoaderCircle
                        size={18}
                        className="case-radiographies-spin"
                      />

                      <strong>
                        Cargando radiografÃ­a...
                      </strong>
                    </div>

                    <span>
                      {uploadProgress}%
                    </span>

                  </div>

                  <div
                    className="case-radiographies-progress-track"
                    role="progressbar"
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-valuenow={
                      uploadProgress
                    }
                  >
                    <div
                      className="case-radiographies-progress-bar"
                      style={{
                        width:
                          `${uploadProgress}%`,
                      }}
                    />
                  </div>

                  <p>
                    No cierre esta pantalla mientras
                    se completa la carga.
                  </p>

                </div>
              )
            }


            {
              !confirming
              &&
              !saving
              &&
              (

                <div
                  className="case-radiographies-form-actions"
                >

                  <button
                    type="button"
                    className="case-radiographies-secondary"
                    onClick={
                      closeForm
                    }
                  >
                    Cancelar
                  </button>

                  <button
                    type="button"
                    className="case-radiographies-primary"
                    onClick={
                      handleRequestConfirmation
                    }
                  >

                    <Save
                      size={17}
                    />

                    Revisar y continuar

                  </button>

                </div>
              )
            }

          </div>
        )
      }


      {
        studies.length ===
        0
          ? (

              <div
                className="case-radiographies-empty"
              >

                <Image
                  size={42}
                />

                <strong>
                  Sin radiografÃ­as registradas
                </strong>

                <span>
                  Registre el primer estudio radiogrÃ¡fico
                  asociado a este caso clÃ­nico.
                </span>

              </div>
            )
          : (

              <div
                className="case-radiographies-list"
              >

                {
                  studies.map(
                    (
                      study,
                    ) => (

                      <section
                        key={
                          study.id_study
                        }
                        className="case-radiographies-study"
                      >

                        <div
                          className="case-radiographies-study-main"
                        >

                          <div
                            className="case-radiographies-study-icon"
                          >
                            <FileImage
                              size={28}
                            />
                          </div>

                          <div
                            className="case-radiographies-study-data"
                          >

                            <div
                              className="case-radiographies-study-title"
                            >

                              <strong>
                                {
                                  study
                                    .study_type
                                    .name
                                }
                              </strong>

                              <span>
                                {
                                  study
                                    .anatomical_region
                                    .name
                                }
                              </span>

                            </div>


                            <div
                              className="case-radiographies-metadata"
                            >

                              <span>
                                <CalendarDays
                                  size={14}
                                />

                                Estudio:{" "}
                                {
                                  formatDate(
                                    study
                                      .study_date,
                                  )
                                }
                              </span>

                              <span>
                                Lateralidad:{" "}
                                {
                                  study
                                    .laterality
                                    ?.name
                                  ??
                                  "No especificada"
                                }
                              </span>

                              <span>
                                Registrado:{" "}
                                {
                                  formatDateTime(
                                    study
                                      .registered_at,
                                  )
                                }
                              </span>

                              <span>
                                Profesional:{" "}
                                {
                                  resolveAuthorName(
                                    study
                                      .registered_by_uuid,
                                  )
                                }
                              </span>

                            </div>


                            {
                              study.observation
                              &&
                              (

                                <p
                                  className="case-radiographies-observation"
                                >
                                  {
                                    study.observation
                                  }
                                </p>
                              )
                            }

                          </div>

                        </div>


                        <div
                          className="case-radiographies-files"
                        >

                          {
                            study.files.length ===
                            0
                              ? (

                                  <span
                                    className="case-radiographies-no-files"
                                  >
                                    Sin archivos disponibles.
                                  </span>
                                )
                              : study.files.map(
                                  (
                                    file,
                                  ) => {

                                    const isRejected =
                                      file
                                        .validation_status
                                      ===
                                      "RECHAZADA";

                                    const isValid =
                                      file
                                        .validation_status
                                      ===
                                      "VALIDA";

                                    const invalidValidations =
                                      file
                                        .validations
                                        .filter(
                                          (
                                            validation,
                                          ) =>
                                            validation
                                              .result_code
                                            ===
                                            "INVALIDO",
                                        );

                                    return (

                                      <div
                                        key={
                                          file.id_file
                                        }
                                        className={
                                          [
                                            "case-radiographies-file-card",

                                            isRejected
                                              ? "case-radiographies-file-card--rejected"
                                              : "",

                                            isValid
                                              ? "case-radiographies-file-card--valid"
                                              : "",
                                          ]
                                            .filter(
                                              Boolean,
                                            )
                                            .join(
                                              " ",
                                            )
                                        }
                                      >

                                        <div
                                          className="case-radiographies-file"
                                        >

                                          <div
                                            className="case-radiographies-file-info"
                                          >

                                            <div
                                              className="case-radiographies-file-name-row"
                                            >

                                              <strong>
                                                {
                                                  file
                                                    .original_name
                                                }
                                              </strong>

                                              <span
                                                className={
                                                  `case-radiographies-status ${getValidationStatusClass(
                                                    file,
                                                  )}`
                                                }
                                              >

                                                {
                                                  isValid
                                                    ? (
                                                        <CheckCircle2
                                                          size={13}
                                                        />
                                                      )
                                                    : isRejected
                                                      ? (
                                                          <XCircle
                                                            size={13}
                                                          />
                                                        )
                                                      : (
                                                          <LoaderCircle
                                                            size={13}
                                                          />
                                                        )
                                                }

                                                {
                                                  getValidationStatusLabel(
                                                    file,
                                                  )
                                                }

                                              </span>

                                            </div>


                                            <span>
                                              VersiÃ³n{" "}
                                              {
                                                file.version
                                              }

                                              {" Â· "}

                                              {
                                                file
                                                  .mime
                                                  .code
                                              }

                                              {" Â· "}

                                              {
                                                formatBytes(
                                                  file
                                                    .size_bytes,
                                                )
                                              }

                                              {
                                                file.width_px
                                                &&
                                                file.height_px
                                                  ? (
                                                      <>
                                                        {" Â· "}
                                                        {
                                                          file.width_px
                                                        }
                                                        Ã—
                                                        {
                                                          file.height_px
                                                        }
                                                      </>
                                                    )
                                                  : null
                                              }

                                              {" Â· "}

                                              Cargado:{" "}
                                              {
                                                formatDateTime(
                                                  file
                                                    .uploaded_at,
                                                )
                                              }
                                            </span>

                                          </div>


                                          <div
                                            className="case-radiographies-file-actions"
                                          >

                                            {
                                              isValid
                                              &&
                                              file
                                                .mime
                                                .code
                                              !==
                                              "DICOM"
                                              &&
                                              (

                                                <button
                                                  type="button"
                                                  disabled={
                                                    workingFileId
                                                    ===
                                                    file.id_file
                                                  }
                                                  onClick={
                                                    () =>
                                                      void handleView(
                                                        file.id_file,
                                                        file.original_name,
                                                      )
                                                  }
                                                >

                                                  {
                                                    workingFileId
                                                    ===
                                                    file.id_file
                                                      ? (
                                                          <LoaderCircle
                                                            size={15}
                                                            className="case-radiographies-spin"
                                                          />
                                                        )
                                                      : (
                                                          <Eye
                                                            size={15}
                                                          />
                                                        )
                                                  }

                                                  Ver radiografía

                                                </button>
                                              )
                                            }


                                            


                                            {
                                              isRejected
                                              &&
                                              file.active
                                              &&
                                              (

                                                <button
                                                  type="button"
                                                  disabled={
                                                    replacing
                                                  }
                                                  onClick={
                                                    () =>
                                                      openReplacement(
                                                        file,
                                                      )
                                                  }
                                                >
                                                  <Upload
                                                    size={15}
                                                  />

                                                  Reemplazar
                                                </button>
                                              )
                                            }

                                          </div>

                                        </div>


                                        {
                                          isValid
                                          &&
                                          (

                                            <div
                                              className="case-radiographies-valid-notice"
                                            >

                                              <CheckCircle2
                                                size={17}
                                              />

                                              <div>
                                                <strong>
                                                  Archivo validado
                                                </strong>

                                                <span>
                                                  La radiografÃ­a superÃ³ las validaciones
                                                  registradas y estÃ¡ disponible para
                                                  continuar con el flujo de anÃ¡lisis.
                                                </span>
                                              </div>

                                            </div>
                                          )
                                        }


                                        {
                                          isRejected
                                          &&
                                          (

                                            <div
                                              className="case-radiographies-rejection"
                                            >

                                              <div
                                                className="case-radiographies-rejection-header"
                                              >

                                                <div
                                                  className="case-radiographies-rejection-icon"
                                                >
                                                  <AlertTriangle
                                                    size={21}
                                                  />
                                                </div>

                                                <div>
                                                  <strong>
                                                    RadiografÃ­a rechazada
                                                  </strong>

                                                  <span>
                                                    El archivo no superÃ³ la validaciÃ³n.
                                                    Revise el motivo y realice la
                                                    correcciÃ³n indicada antes de
                                                    continuar con el anÃ¡lisis.
                                                  </span>
                                                </div>

                                              </div>


                                              {
                                                invalidValidations.length
                                                >
                                                0
                                                  ? (

                                                      <div
                                                        className="case-radiographies-validation-list"
                                                      >

                                                        {
                                                          invalidValidations.map(
                                                            (
                                                              validation,
                                                              validationIndex,
                                                            ) => (

                                                              <div
                                                                key={
                                                                  `${file.id_file}-${validation.type_code}-${validationIndex}`
                                                                }
                                                                className="case-radiographies-validation-item"
                                                              >

                                                                <div
                                                                  className="case-radiographies-validation-heading"
                                                                >

                                                                  <div>
                                                                    <XCircle
                                                                      size={16}
                                                                    />

                                                                    <strong>
                                                                      {
                                                                        validation
                                                                          .type_name
                                                                      }
                                                                    </strong>
                                                                  </div>

                                                                  <span>
                                                                    {
                                                                      validation
                                                                        .result_name
                                                                    }
                                                                  </span>

                                                                </div>


                                                                {
                                                                  validation.detail
                                                                  &&
                                                                  (

                                                                    <p
                                                                      className="case-radiographies-validation-detail"
                                                                    >
                                                                      {
                                                                        validation.detail
                                                                      }
                                                                    </p>
                                                                  )
                                                                }


                                                                {
                                                                  validation.reason
                                                                  &&
                                                                  (

                                                                    <div
                                                                      className="case-radiographies-validation-block case-radiographies-validation-block--reason"
                                                                    >

                                                                      <div>
                                                                        <Info
                                                                          size={15}
                                                                        />

                                                                        <strong>
                                                                          Motivo
                                                                        </strong>
                                                                      </div>

                                                                      <p>
                                                                        {
                                                                          validation.reason
                                                                        }
                                                                      </p>

                                                                    </div>
                                                                  )
                                                                }


                                                                {
                                                                  validation.correction
                                                                  &&
                                                                  (

                                                                    <div
                                                                      className="case-radiographies-validation-block case-radiographies-validation-block--correction"
                                                                    >

                                                                      <div>
                                                                        <CheckCircle2
                                                                          size={15}
                                                                        />

                                                                        <strong>
                                                                          CorrecciÃ³n necesaria
                                                                        </strong>
                                                                      </div>

                                                                      <p>
                                                                        {
                                                                          validation.correction
                                                                        }
                                                                      </p>

                                                                    </div>
                                                                  )
                                                                }


                                                                <span
                                                                  className="case-radiographies-validation-date"
                                                                >
                                                                  Validado:{" "}
                                                                  {
                                                                    formatDateTime(
                                                                      validation
                                                                        .validated_at,
                                                                    )
                                                                  }
                                                                </span>

                                                              </div>
                                                            ),
                                                          )
                                                        }

                                                      </div>
                                                    )
                                                  : (

                                                      <div
                                                        className="case-radiographies-validation-missing"
                                                      >
                                                        No se encontraron detalles
                                                        adicionales de la validaciÃ³n.
                                                      </div>
                                                    )
                                              }


                                              <div
                                                className="case-radiographies-analysis-blocked"
                                              >

                                                <ShieldAlert
                                                  size={18}
                                                />

                                                <div>
                                                  <strong>
                                                    No disponible para anÃ¡lisis
                                                  </strong>

                                                  <span>
                                                    Esta versiÃ³n se conserva para
                                                    trazabilidad, pero no puede
                                                    utilizarse en el anÃ¡lisis mientras
                                                    permanezca rechazada.
                                                  </span>
                                                </div>

                                              </div>


                                              {
                                                replacementTarget
                                                  ?.id_file
                                                ===
                                                file.id_file
                                                &&
                                                (

                                                  <div
                                                    className="case-radiographies-form"
                                                  >

                                                    <div
                                                      className="case-radiographies-form-heading"
                                                    >
                                                      <Upload
                                                        size={20}
                                                      />

                                                      <div>
                                                        <strong>
                                                          Reemplazar radiografÃ­a rechazada
                                                        </strong>
                                                        <span>
                                                          La versiÃ³n {file.version} se conservarÃ¡ para trazabilidad.
                                                        </span>
                                                      </div>
                                                    </div>


                                                    <label
                                                      className="case-radiographies-file-field case-radiographies-form-wide"
                                                    >
                                                      <span>
                                                        Nueva radiografÃ­a *
                                                      </span>

                                                      <input
                                                        ref={
                                                          replacementFileInputRef
                                                        }
                                                        type="file"
                                                        disabled={
                                                          replacing
                                                        }
                                                        accept=".jpg,.jpeg,.png,.dcm,image/jpeg,image/png,application/dicom"
                                                        onChange={
                                                          (event) => {
                                                            const nextFile =
                                                              event
                                                                .target
                                                                .files
                                                                ?.[0]
                                                              ??
                                                              null;

                                                            setReplacementFile(
                                                              nextFile,
                                                            );

                                                            setReplacementProgress(
                                                              0,
                                                            );

                                                            setError(
                                                              null,
                                                            );
                                                          }
                                                        }
                                                      />

                                                      <div
                                                        className="case-radiographies-file-box"
                                                      >
                                                        <FileImage
                                                          size={29}
                                                        />

                                                        {
                                                          replacementFile
                                                            ? (
                                                                <>
                                                                  <strong>
                                                                    {replacementFile.name}
                                                                  </strong>
                                                                  <span>
                                                                    {formatBytes(replacementFile.size)}
                                                                  </span>
                                                                </>
                                                              )
                                                            : (
                                                                <>
                                                                  <strong>
                                                                    Seleccione la radiografÃ­a corregida
                                                                  </strong>
                                                                  <span>
                                                                    JPG, PNG o DICOM Â· mÃ¡ximo 20 MB
                                                                  </span>
                                                                </>
                                                              )
                                                        }
                                                      </div>
                                                    </label>


                                                    <label
                                                      className="case-radiographies-form-wide"
                                                    >
                                                      Motivo del reemplazo *

                                                      <textarea
                                                        rows={3}
                                                        maxLength={1000}
                                                        disabled={
                                                          replacing
                                                        }
                                                        value={
                                                          replacementReason
                                                        }
                                                        onChange={
                                                          (event) =>
                                                            setReplacementReason(
                                                              event.target.value,
                                                            )
                                                        }
                                                        placeholder="Ej.: se reemplaza el archivo rechazado por la radiografÃ­a original correcta."
                                                      />
                                                    </label>


                                                    {
                                                      replacing
                                                      &&
                                                      (
                                                        <div
                                                          className="case-radiographies-progress"
                                                          aria-live="polite"
                                                        >
                                                          <div
                                                            className="case-radiographies-progress-header"
                                                          >
                                                            <div>
                                                              <LoaderCircle
                                                                size={18}
                                                                className="case-radiographies-spin"
                                                              />
                                                              <strong>
                                                                Reemplazando radiografÃ­a...
                                                              </strong>
                                                            </div>
                                                            <span>
                                                              {replacementProgress}%
                                                            </span>
                                                          </div>

                                                          <div
                                                            className="case-radiographies-progress-track"
                                                            role="progressbar"
                                                            aria-valuemin={0}
                                                            aria-valuemax={100}
                                                            aria-valuenow={
                                                              replacementProgress
                                                            }
                                                          >
                                                            <div
                                                              className="case-radiographies-progress-bar"
                                                              style={{
                                                                width:
                                                                  `${replacementProgress}%`,
                                                              }}
                                                            />
                                                          </div>
                                                        </div>
                                                      )
                                                    }


                                                    <div
                                                      className="case-radiographies-form-actions"
                                                    >
                                                      <button
                                                        type="button"
                                                        className="case-radiographies-secondary"
                                                        disabled={
                                                          replacing
                                                        }
                                                        onClick={
                                                          resetReplacementForm
                                                        }
                                                      >
                                                        Cancelar
                                                      </button>

                                                      <button
                                                        type="button"
                                                        className="case-radiographies-primary"
                                                        disabled={
                                                          replacing
                                                        }
                                                        onClick={
                                                          () =>
                                                            void handleReplacement()
                                                        }
                                                      >
                                                        {
                                                          replacing
                                                            ? (
                                                                <LoaderCircle
                                                                  size={17}
                                                                  className="case-radiographies-spin"
                                                                />
                                                              )
                                                            : (
                                                                <Upload
                                                                  size={17}
                                                                />
                                                              )
                                                        }

                                                        {
                                                          replacing
                                                            ? "Reemplazando..."
                                                            : "Confirmar reemplazo"
                                                        }
                                                      </button>
                                                    </div>

                                                  </div>
                                                )
                                              }

                                            </div>
                                          )
                                        }

                                      </div>
                                    );
                                  },
                                )
                          }

                        </div>

                      </section>
                    ),
                  )
                }

              </div>
            )
      }

      </article>


      {
        viewerUrl
        &&
        (
          <div
            className="case-radiography-viewer-overlay"
            role="dialog"
            aria-modal="true"
            aria-label="Visor radiográfico"
          >
            <div
              ref={
                viewerRef
              }
              className="case-radiography-viewer"
            >
              <header
                className="case-radiography-viewer-header"
              >
                <div>
                  <strong>
                    Visor radiográfico
                  </strong>

                  <span>
                    {viewerFileName}
                  </span>
                </div>

                <button
                  type="button"
                  title="Cerrar visor"
                  onClick={
                    closeViewer
                  }
                >
                  <X
                    size={20}
                  />
                </button>
              </header>


              <div
                className="case-radiography-viewer-toolbar"
              >
                <div
                  className="case-radiography-viewer-toolbar-group"
                >
                  <button
                    type="button"
                    title="Alejar"
                    onClick={
                      zoomOut
                    }
                  >
                    <ZoomOut
                      size={17}
                    />
                  </button>

                  <span
                    className="case-radiography-viewer-zoom"
                  >
                    {
                      Math.round(
                        viewerZoom
                        *
                        100,
                      )
                    }%
                  </span>

                  <button
                    type="button"
                    title="Acercar"
                    onClick={
                      zoomIn
                    }
                  >
                    <ZoomIn
                      size={17}
                    />
                  </button>

                  <button
                    type="button"
                    title="Rotar 90 grados"
                    onClick={
                      rotateViewer
                    }
                  >
                    <RotateCw
                      size={17}
                    />
                  </button>

                  <button
                    type="button"
                    title="Restablecer vista"
                    onClick={
                      resetViewer
                    }
                  >
                    <RotateCcw
                      size={17}
                    />
                  </button>

                  <button
                    type="button"
                    title="Pantalla completa"
                    onClick={
                      () =>
                        void toggleFullscreen()
                    }
                  >
                    <Maximize2
                      size={17}
                    />
                  </button>
                </div>


                <div
                  className="case-radiography-viewer-adjustments"
                >
                  <label>
                    <span>
                      <Sun
                        size={15}
                      />
                      Brillo
                    </span>

                    <input
                      type="range"
                      min="40"
                      max="200"
                      step="5"
                      value={
                        viewerBrightness
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          setViewerBrightness(
                            Number(
                              event.target.value,
                            ),
                          )
                      }
                    />

                    <strong>
                      {
                        viewerBrightness
                      }%
                    </strong>
                  </label>


                  <label>
                    <span>
                      <Minus
                        size={15}
                      />
                      Contraste
                    </span>

                    <input
                      type="range"
                      min="40"
                      max="250"
                      step="5"
                      value={
                        viewerContrast
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          setViewerContrast(
                            Number(
                              event.target.value,
                            ),
                          )
                      }
                    />

                    <strong>
                      {
                        viewerContrast
                      }%
                    </strong>
                  </label>


                  <button
                    type="button"
                    className={
                      viewerInvert
                        ? "case-radiography-viewer-invert case-radiography-viewer-invert--active"
                        : "case-radiography-viewer-invert"
                    }
                    onClick={
                      () =>
                        setViewerInvert(
                          (
                            current,
                          ) =>
                            !current,
                        )
                    }
                  >
                    Invertir
                  </button>
                </div>
              </div>


              <div
                className="case-radiography-viewer-help"
              >
                Use la rueda del mouse para acercar o alejar.
                Arrastre la radiografía para desplazarse.
                Los ajustes solo afectan la visualización.
              </div>


              <div
                className={
                  draggingRef.current
                    ? "case-radiography-viewer-stage case-radiography-viewer-stage--dragging"
                    : "case-radiography-viewer-stage"
                }
                onPointerDown={
                  handlePointerDown
                }
                onPointerMove={
                  handlePointerMove
                }
                onPointerUp={
                  handlePointerEnd
                }
                onPointerCancel={
                  handlePointerEnd
                }
                onWheel={
                  handleViewerWheel
                }
              >
                <img
                  src={
                    viewerUrl
                  }
                  alt={
                    `Radiografía ${viewerFileName}`
                  }
                  draggable={
                    false
                  }
                  style={{
                    transform:
                      `translate(${viewerPan.x}px, ${viewerPan.y}px) `
                      +
                      `rotate(${viewerRotation}deg) `
                      +
                      `scale(${viewerZoom})`,

                    filter:
                      `brightness(${viewerBrightness}%) `
                      +
                      `contrast(${viewerContrast}%) `
                      +
                      `invert(${viewerInvert ? 100 : 0}%)`,
                  }}
                />
              </div>


              <footer
                className="case-radiography-viewer-footer"
              >
                <span>
                  Imagen radiográfica privada ·
                  visualización dentro del sistema
                </span>

                <button
                  type="button"
                  onClick={
                    closeViewer
                  }
                >
                  Cerrar visor
                </button>
              </footer>
            </div>
          </div>
        )
      }
    </>
  );
}
