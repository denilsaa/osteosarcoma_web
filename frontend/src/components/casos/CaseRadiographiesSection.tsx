import {
  AlertTriangle,
  CalendarDays,
  CheckCircle2,
  Clock3,
  FileImage,
  Image,
  Info,
  LoaderCircle,
  MapPin,
  Maximize2,
  Minus,
  Plus,
  RotateCcw,
  RotateCw,
  Save,
  Sun,
  ShieldAlert,
  Upload,
  UserRound,
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
    return "—";
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
    return "—";
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
    "No fue posible completar la operación."
  );
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


function getPrimaryRadiographicFile(
  study: RadiographicStudy,
): RadiographicFile | null {

  return (
    study.files.find(
      (file) =>
        file.active,
    )
    ??
    study.files[0]
    ??
    null
  );
}



const RADIOGRAPHY_FILE_EXTENSIONS =
  [
    "jpg",
    "jpeg",
    "png",
    "dcm",
  ] as const;


function getLocalRadiographyExtension(
  file?: File | null,
): string {

  if (!file) {
    return "";
  }

  return (
    file
      .name
      .split(".")
      .pop()
      ?.toLowerCase()
    ??
    ""
  );
}


function isAcceptedLocalRadiographyFile(
  file?: File | null,
): boolean {

  return RADIOGRAPHY_FILE_EXTENSIONS.includes(
    getLocalRadiographyExtension(
      file,
    ) as typeof RADIOGRAPHY_FILE_EXTENSIONS[number],
  );
}


function isLocalRadiographyPreviewable(
  file?: File | null,
): boolean {

  const extension =
    getLocalRadiographyExtension(
      file,
    );

  return [
    "jpg",
    "jpeg",
    "png",
  ].includes(
    extension,
  );
}


function getLocalRadiographyFormatLabel(
  file?: File | null,
): string {

  const extension =
    getLocalRadiographyExtension(
      file,
    );

  switch (extension) {
    case "jpg":
    case "jpeg":
      return "JPEG";

    case "png":
      return "PNG";

    case "dcm":
      return "DICOM";

    default:
      return extension
        ? extension.toUpperCase()
        : "Archivo";
  }
}


function isRadiographicFilePreviewable(
  file?: RadiographicFile | null,
): boolean {

  return Boolean(
    file
    &&
    file.validation_status === "VALIDA"
    &&
    file.mime.code !== "DICOM",
  );
}


function getShortValidationLabel(
  file?: RadiographicFile | null,
): string {

  if (!file) {
    return "Sin archivo";
  }

  switch (file.validation_status) {
    case "VALIDA":
      return "Válida";

    case "RECHAZADA":
      return "Rechazada";

    default:
      return "Pendiente";
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

  const inlineViewerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const modalViewerRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const inlineStageRef =
    useRef<HTMLDivElement | null>(
      null,
    );

  const modalStageRef =
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

  const previewUrlsRef =
    useRef<Record<string, string>>(
      {},
    );

  const previewLoadingRef =
    useRef<Set<string>>(
      new Set(),
    );

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
    selectedStudyId,
    setSelectedStudyId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    selectedInlineFileId,
    setSelectedInlineFileId,
  ] =
    useState<string | null>(
      null,
    );

  const [
    previewUrls,
    setPreviewUrls,
  ] =
    useState<Record<string, string>>(
      {},
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
    uploadErrorModal,
    setUploadErrorModal,
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

  const [
    selectedFilePreviewUrl,
    setSelectedFilePreviewUrl,
  ] =
    useState<string | null>(
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
    replacementFilePreviewUrl,
    setReplacementFilePreviewUrl,
  ] =
    useState<string | null>(
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


  const selectedStudy =
    studies.find(
      (study) =>
        study.id_study === selectedStudyId,
    )
    ??
    null;

  const selectedInlineFile =
    selectedStudy
      ?.files
      .find(
        (file) =>
          file.id_file === selectedInlineFileId,
      )
    ??
    (
      selectedStudy
        ? getPrimaryRadiographicFile(
            selectedStudy,
          )
        : null
    );

  const inlineViewerUrl =
    selectedInlineFile
      ? previewUrls[
          selectedInlineFile.id_file
        ]
        ??
        null
      : null;

  const selectedInvalidValidations =
    selectedInlineFile
      ?.validations
      .filter(
        (validation) =>
          validation.result_code === "INVALIDO",
      )
    ??
    [];


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


  const ensurePreview =
    useCallback(
      async (
        file: RadiographicFile,
      ) => {

        if (
          !isRadiographicFilePreviewable(
            file,
          )
        ) {
          return;
        }

        if (
          previewUrlsRef.current[
            file.id_file
          ]
          ||
          previewLoadingRef.current.has(
            file.id_file,
          )
        ) {
          return;
        }

        previewLoadingRef.current.add(
          file.id_file,
        );

        try {
          const blob =
            await getRadiographicFileBlob(
              file.id_file,
            );

          const url =
            URL.createObjectURL(
              blob,
            );

          previewUrlsRef.current[
            file.id_file
          ] = url;

          setPreviewUrls(
            (current) => ({
              ...current,
              [file.id_file]: url,
            }),
          );

        } catch {
          // La ficha permanece usable aunque una miniatura
          // no pueda descargarse temporalmente.

        } finally {
          previewLoadingRef.current.delete(
            file.id_file,
          );
        }
      },
      [],
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

      if (
        studies.length === 0
      ) {
        setSelectedStudyId(
          null,
        );

        setSelectedInlineFileId(
          null,
        );

        return;
      }

      const studyStillExists =
        selectedStudyId
        &&
        studies.some(
          (study) =>
            study.id_study === selectedStudyId,
        );

      if (!studyStillExists) {
        const firstStudy =
          studies[0];

        const firstFile =
          getPrimaryRadiographicFile(
            firstStudy,
          );

        setSelectedStudyId(
          firstStudy.id_study,
        );

        setSelectedInlineFileId(
          firstFile?.id_file
          ??
          null,
        );
      }

    },
    [
      selectedStudyId,
      studies,
    ],
  );


  useEffect(
    () => {

      if (!selectedStudy) {
        return;
      }

      const selectedFileStillExists =
        selectedInlineFileId
        &&
        selectedStudy.files.some(
          (file) =>
            file.id_file === selectedInlineFileId,
        );

      if (!selectedFileStillExists) {
        const primaryFile =
          getPrimaryRadiographicFile(
            selectedStudy,
          );

        setSelectedInlineFileId(
          primaryFile?.id_file
          ??
          null,
        );
      }

    },
    [
      selectedInlineFileId,
      selectedStudy,
    ],
  );


  useEffect(
    () => {
      /*
       * Rendimiento:
       * no descargamos todas las radiografías originales al entrar.
       * Solo solicitamos el archivo que el usuario está visualizando.
       */
      if (selectedInlineFile) {
        void ensurePreview(
          selectedInlineFile,
        );
      }
    },
    [
      ensurePreview,
      selectedInlineFile,
    ],
  );


  useEffect(
    () => {
      return () => {
        Object.values(
          previewUrlsRef.current,
        ).forEach(
          (url) => {
            URL.revokeObjectURL(
              url,
            );
          },
        );
      };
    },
    [],
  );


  useEffect(
    () => {
      if (
        !selectedFile
        ||
        !isLocalRadiographyPreviewable(
          selectedFile,
        )
      ) {
        setSelectedFilePreviewUrl(
          null,
        );

        return;
      }

      const url =
        URL.createObjectURL(
          selectedFile,
        );

      setSelectedFilePreviewUrl(
        url,
      );

      return () => {
        URL.revokeObjectURL(
          url,
        );
      };
    },
    [
      selectedFile,
    ],
  );


  useEffect(
    () => {
      if (
        !replacementFile
        ||
        !isLocalRadiographyPreviewable(
          replacementFile,
        )
      ) {
        setReplacementFilePreviewUrl(
          null,
        );

        return;
      }

      const url =
        URL.createObjectURL(
          replacementFile,
        );

      setReplacementFilePreviewUrl(
        url,
      );

      return () => {
        URL.revokeObjectURL(
          url,
        );
      };
    },
    [
      replacementFile,
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


  function clearSelectedUploadFile() {

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


  function closeUploadErrorModal() {

    setUploadErrorModal(
      null,
    );

    setError(
      null,
    );

    clearSelectedUploadFile();

    window.setTimeout(
      () => {
        fileInputRef
          .current
          ?.focus();
      },
      0,
    );
  }


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

    setUploadErrorModal(
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


  function getActiveStage():
    HTMLDivElement | null {

    return viewerUrl
      ? modalStageRef.current
      : inlineStageRef.current;
  }


  function clampViewerPan(
    stage: HTMLDivElement,
    nextPan: ViewerPoint,
    zoom: number = viewerZoom,
    rotation: number = viewerRotation,
  ): ViewerPoint {

    const image =
      stage.querySelector<HTMLImageElement>(
        "img",
      );

    if (
      !image
      ||
      zoom <= 1
    ) {
      return {
        x: 0,
        y: 0,
      };
    }

    const normalizedRotation =
      (
        (rotation % 360)
        +
        360
      )
      %
      360;

    const swapsDimensions =
      normalizedRotation === 90
      ||
      normalizedRotation === 270;

    const baseWidth =
      swapsDimensions
        ? image.offsetHeight
        : image.offsetWidth;

    const baseHeight =
      swapsDimensions
        ? image.offsetWidth
        : image.offsetHeight;

    const scaledWidth =
      baseWidth * zoom;

    const scaledHeight =
      baseHeight * zoom;

    const maxX =
      Math.max(
        0,
        (
          scaledWidth
          -
          stage.clientWidth
        )
        /
        2,
      );

    const maxY =
      Math.max(
        0,
        (
          scaledHeight
          -
          stage.clientHeight
        )
        /
        2,
      );

    return {
      x: Math.max(
        -maxX,
        Math.min(
          maxX,
          nextPan.x,
        ),
      ),

      y: Math.max(
        -maxY,
        Math.min(
          maxY,
          nextPan.y,
        ),
      ),
    };
  }


  function reclampViewerPan(
    zoom: number = viewerZoom,
    rotation: number = viewerRotation,
  ) {
    if (zoom <= 1) {
      setViewerPan({
        x: 0,
        y: 0,
      });

      return;
    }

    window.requestAnimationFrame(
      () => {
        const stage =
          getActiveStage();

        if (!stage) {
          return;
        }

        setViewerPan(
          (current) =>
            clampViewerPan(
              stage,
              current,
              zoom,
              rotation,
            ),
        );
      },
    );
  }


  function changeViewerZoom(
    nextZoom: number,
  ) {
    const normalizedZoom =
      Math.min(
        4,
        Math.max(
          1,
          Number(
            nextZoom.toFixed(2),
          ),
        ),
      );

    setViewerZoom(
      normalizedZoom,
    );

    reclampViewerPan(
      normalizedZoom,
      viewerRotation,
    );
  }


  function zoomIn() {
    changeViewerZoom(
      viewerZoom + 0.25,
    );
  }


  function zoomOut() {
    changeViewerZoom(
      viewerZoom - 0.25,
    );
  }


  function rotateViewer() {
    const nextRotation =
      (
        viewerRotation
        +
        90
      )
      %
      360;

    setViewerRotation(
      nextRotation,
    );

    reclampViewerPan(
      viewerZoom,
      nextRotation,
    );
  }


  async function toggleFullscreen(
    element: HTMLDivElement | null,
  ) {
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
    if (
      (
        !viewerUrl
        &&
        !inlineViewerUrl
      )
      ||
      viewerZoom <= 1
      ||
      (
        event.pointerType === "mouse"
        &&
        event.button !== 0
      )
    ) {
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
      ||
      viewerZoom <= 1
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

    const nextPan = {
      x:
        panStartRef.current.x
        +
        deltaX,

      y:
        panStartRef.current.y
        +
        deltaY,
    };

    setViewerPan(
      clampViewerPan(
        event.currentTarget,
        nextPan,
      ),
    );
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

    const step =
      event.deltaY < 0
        ? 0.15
        : -0.15;

    changeViewerZoom(
      viewerZoom + step,
    );
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
        "Seleccione la región anatómica."
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
        "Seleccione una radiografía."
      );
    }

    if (
      !isAcceptedLocalRadiographyFile(
        selectedFile,
      )
    ) {

      return (
        "Solo se permiten archivos JPG, JPEG, PNG o DICOM (.dcm)."
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

    setUploadErrorModal(
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

      setSelectedStudyId(
        response.data.id_study,
      );

      setSelectedInlineFileId(
        createdFile?.id_file
        ??
        null,
      );

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
          "La radiografía fue recibida, pero fue rechazada durante la validación. Revise el motivo y la corrección necesaria antes de enviarla al análisis.",
        );

      } else {

        setError(
          null,
        );

        setSuccess(
          "Radiografía registrada y validada correctamente.",
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

      const message =
        getErrorMessage(
          requestError,
        );

      const normalizedMessage =
        message
          .toLocaleLowerCase(
            "es",
          );

      const isRadiographyRejectedByAi =
        normalizedMessage.includes(
          "no fue identificada como una radiografía",
        )
        ||
        normalizedMessage.includes(
          "no fue identificada como una radiografia",
        );

      if (
        isRadiographyRejectedByAi
      ) {

        setError(
          null,
        );

        setUploadErrorModal(
          message,
        );

      } else {

        setUploadErrorModal(
          null,
        );

        setError(
          message,
        );
      }

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
      return "Seleccione la radiografía rechazada que desea reemplazar.";
    }

    if (
      !replacementFile
    ) {
      return "Seleccione la nueva radiografía.";
    }

    if (
      !isAcceptedLocalRadiographyFile(
        replacementFile,
      )
    ) {
      return "Solo se permiten archivos JPG, JPEG, PNG o DICOM (.dcm).";
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
     * - V2 como nueva versión activa.
     * - sus validaciones actualizadas.
     */
    await loadStudies();

    setSelectedStudyId(
      newestFile.id_study,
    );

    setSelectedInlineFileId(
      newestFile.id_file,
    );

    resetReplacementForm();

    if (
      newestFile
        .validation_status
      ===
      "RECHAZADA"
    ) {
      setError(
        "La nueva versión fue cargada, pero también fue rechazada durante la validación. Revise las correcciones indicadas antes de intentar otro reemplazo.",
      );

      return;
    }

    setSuccess(
      `Radiografía reemplazada correctamente. Se registró la versión ${newestFile.version} y la versión anterior se conserva para trazabilidad.`,
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
          Cargando radiografías...
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
              Radiografías del caso
            </h2>

            <p>
              {
                studies.length
              } estudio(s) radiográfico(s)
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
              : "Registrar radiografía"
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
                  y seleccione la radiografía.
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
                Zona anatómica *

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
                  placeholder="Ej.: lesión localizada en región proximal..."
                />
              </label>


              <label
                className="case-radiographies-file-field case-radiographies-form-wide"
              >

                <span>
                  Archivo radiográfico *
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

                      setUploadErrorModal(
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
                  className={
                    selectedFile
                      ? "case-radiographies-file-box case-radiographies-file-box--selected"
                      : "case-radiographies-file-box"
                  }
                >

                  {
                    selectedFile
                      ? (
                          <>
                            <div
                              className="case-radiographies-local-preview"
                            >
                              {
                                selectedFilePreviewUrl
                                  ? (
                                      <img
                                        src={
                                          selectedFilePreviewUrl
                                        }
                                        alt="Vista previa del archivo radiográfico seleccionado"
                                      />
                                    )
                                  : (
                                      <div
                                        className="case-radiographies-local-preview-placeholder"
                                      >
                                        <FileImage
                                          size={36}
                                        />

                                        <strong>
                                          {
                                            getLocalRadiographyFormatLabel(
                                              selectedFile,
                                            )
                                          }
                                        </strong>

                                        <span>
                                          {
                                            getLocalRadiographyExtension(
                                              selectedFile,
                                            )
                                            ===
                                            "dcm"
                                              ? "Vista previa DICOM disponible después de la carga"
                                              : "Vista previa no disponible"
                                          }
                                        </span>
                                      </div>
                                    )
                              }

                              <span
                                className="case-radiographies-local-preview-badge"
                              >
                                Vista previa local
                              </span>
                            </div>

                            <div
                              className="case-radiographies-local-preview-info"
                            >
                              <strong>
                                {
                                  selectedFile
                                    .name
                                }
                              </strong>

                              <span>
                                {
                                  getLocalRadiographyFormatLabel(
                                    selectedFile,
                                  )
                                }
                                {" · "}
                                {
                                  formatBytes(
                                    selectedFile
                                      .size,
                                  )
                                }
                              </span>

                              <small>
                                {
                                  selectedFilePreviewUrl
                                    ? "La imagen se muestra sin subirla ni modificar el archivo original."
                                    : "El archivo será validado antes de registrarse."
                                }
                              </small>

                              <b>
                                Cambiar archivo
                              </b>
                            </div>
                          </>
                        )
                      : (
                          <>
                            <FileImage
                              size={29}
                            />

                            <strong>
                              Seleccione JPG, JPEG, PNG o DICOM
                            </strong>

                            <span>
                              Tamaño máximo: 20 MB · DICOM (.dcm)
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
                        Revise la información antes de
                        enviar la radiografía.
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
                          "—"
                        }
                      </strong>
                    </div>

                    <div>
                      <span>
                        Región anatómica
                      </span>

                      <strong>
                        {
                          selectedRegion
                            ?.name
                          ??
                          "—"
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
                          "—"
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
                        Cargando radiografía...
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
        studies.length === 0
          ? (
              <div
                className="case-radiographies-empty case-radiographies-empty--workspace"
              >
                <Image
                  size={42}
                />

                <strong>
                  Sin radiografías registradas
                </strong>

                <span>
                  Registre el primer estudio radiográfico
                  asociado a este caso clínico.
                </span>

                <button
                  type="button"
                  className="case-radiographies-primary"
                  onClick={
                    () => {
                      setShowForm(
                        true,
                      );

                      setError(
                        null,
                      );
                    }
                  }
                >
                  <Plus
                    size={16}
                  />

                  Registrar radiografía
                </button>
              </div>
            )
          : (
              <div
                className="case-radiographies-workspace"
              >
                <aside
                  className="case-radiographies-sidebar"
                >
                  <header
                    className="case-radiographies-sidebar-header"
                  >
                    <div>
                      <strong>
                        Radiografías del caso
                      </strong>

                      <span>
                        {studies.length} estudio(s) radiográfico(s)
                      </span>
                    </div>

                    <button
                      type="button"
                      className="case-radiographies-primary"
                      disabled={
                        saving
                      }
                      onClick={
                        () => {
                          if (showForm) {
                            closeForm();
                            return;
                          }

                          setShowForm(
                            true,
                          );

                          setConfirming(
                            false,
                          );

                          setError(
                            null,
                          );
                        }
                      }
                    >
                      {
                        showForm
                          ? (
                              <X
                                size={15}
                              />
                            )
                          : (
                              <Plus
                                size={15}
                              />
                            )
                      }

                      {
                        showForm
                          ? "Cerrar"
                          : "Registrar radiografía"
                      }
                    </button>
                  </header>


                  <div
                    className="case-radiographies-study-list"
                  >
                    {
                      studies.map(
                        (study) => {
                          const primaryFile =
                            getPrimaryRadiographicFile(
                              study,
                            );

                          const previewUrl =
                            primaryFile
                              ? previewUrls[
                                  primaryFile.id_file
                                ]
                              : undefined;

                          const isActive =
                            study.id_study === selectedStudyId;

                          return (
                            <button
                              key={
                                study.id_study
                              }
                              type="button"
                              className={
                                isActive
                                  ? "case-radiographies-study-item case-radiographies-study-item--active"
                                  : "case-radiographies-study-item"
                              }
                              onClick={
                                () => {
                                  const nextFile =
                                    getPrimaryRadiographicFile(
                                      study,
                                    );

                                  setSelectedStudyId(
                                    study.id_study,
                                  );

                                  setSelectedInlineFileId(
                                    nextFile?.id_file
                                    ??
                                    null,
                                  );

                                  setReplacementTarget(
                                    null,
                                  );

                                  resetViewer();
                                }
                              }
                            >
                              <div
                                className="case-radiographies-study-thumb"
                              >
                                {
                                  previewUrl
                                    ? (
                                        <img
                                          src={
                                            previewUrl
                                          }
                                          alt=""
                                          draggable={
                                            false
                                          }
                                        />
                                      )
                                    : (
                                        <FileImage
                                          size={26}
                                        />
                                      )
                                }
                              </div>


                              <div
                                className="case-radiographies-study-item-body"
                              >
                                <div
                                  className="case-radiographies-study-item-top"
                                >
                                  <strong>
                                    {study.study_type.name}
                                  </strong>

                                  <span
                                    className={
                                      primaryFile
                                        ? `case-radiographies-status ${getValidationStatusClass(primaryFile)}`
                                        : "case-radiographies-status case-radiographies-status--pending"
                                    }
                                  >
                                    {
                                      primaryFile?.validation_status === "VALIDA"
                                      &&
                                      <CheckCircle2
                                        size={12}
                                      />
                                    }

                                    {
                                      primaryFile?.validation_status === "RECHAZADA"
                                      &&
                                      <XCircle
                                        size={12}
                                      />
                                    }

                                    {getShortValidationLabel(primaryFile)}
                                  </span>
                                </div>


                                <div
                                  className="case-radiographies-study-tags"
                                >
                                  <span>
                                    {study.anatomical_region.name}
                                  </span>

                                  <span>
                                    {
                                      study.laterality?.name
                                      ??
                                      "Sin lateralidad"
                                    }
                                  </span>
                                </div>


                                <div
                                  className="case-radiographies-study-item-meta"
                                >
                                  <span>
                                    <CalendarDays
                                      size={13}
                                    />

                                    {formatDateTime(study.registered_at)}
                                  </span>

                                  <span>
                                    <UserRound
                                      size={13}
                                    />

                                    {
                                      resolveAuthorName(
                                        study.registered_by_uuid,
                                      )
                                    }
                                  </span>
                                </div>
                              </div>
                            </button>
                          );
                        },
                      )
                    }
                  </div>
                </aside>


                <section
                  className="case-radiographies-detail"
                >
                  {
                    selectedStudy
                    &&
                    (
                      <>
                        <header
                          className="case-radiographies-detail-header"
                        >
                          <div
                            className="case-radiographies-detail-heading"
                          >
                            <div
                              className="case-radiographies-detail-icon"
                            >
                              <Image
                                size={20}
                              />
                            </div>

                            <div
                              className="case-radiographies-detail-heading-content"
                            >
                              <div
                                className="case-radiographies-detail-title-row"
                              >
                                <h2>
                                  {selectedStudy.study_type.name}
                                </h2>

                                <span
                                  className="case-radiographies-detail-chip case-radiographies-detail-chip--region"
                                >
                                  {selectedStudy.anatomical_region.name}
                                </span>

                                <span
                                  className="case-radiographies-detail-chip"
                                >
                                  {
                                    selectedStudy.laterality?.name
                                    ??
                                    "Sin lateralidad"
                                  }
                                </span>
                              </div>
                            </div>
                          </div>


                          <div
                            className="case-radiographies-detail-actions"
                          >
                            {
                              selectedInlineFile
                              &&
                              (
                                <span
                                  className={
                                    `case-radiographies-status case-radiographies-detail-status ${getValidationStatusClass(selectedInlineFile)}`
                                  }
                                >
                                  {
                                    selectedInlineFile.validation_status === "VALIDA"
                                    &&
                                    <CheckCircle2
                                      size={13}
                                    />
                                  }

                                  {
                                    selectedInlineFile.validation_status === "RECHAZADA"
                                    &&
                                    <XCircle
                                      size={13}
                                    />
                                  }

                                  {
                                    selectedInlineFile.validation_status === "VALIDA"
                                      ? "Archivo válido"
                                      : getShortValidationLabel(
                                          selectedInlineFile,
                                        )
                                  }
                                </span>
                              )
                            }

                            {
                              selectedInlineFile
                              &&
                              isRadiographicFilePreviewable(
                                selectedInlineFile,
                              )
                              &&
                              (
                                <button
                                  type="button"
                                  className="case-radiographies-detail-more"
                                  title="Abrir visor avanzado"
                                  disabled={
                                    workingFileId === selectedInlineFile.id_file
                                  }
                                  onClick={
                                    () =>
                                      void handleView(
                                        selectedInlineFile.id_file,
                                        selectedInlineFile.original_name,
                                      )
                                  }
                                >
                                  {
                                    workingFileId === selectedInlineFile.id_file
                                      ? (
                                          <LoaderCircle
                                            size={16}
                                            className="case-radiographies-spin"
                                          />
                                        )
                                      : "⋮"
                                  }
                                </button>
                              )
                            }
                          </div>
                        </header>


                        <div
                          ref={
                            inlineViewerRef
                          }
                          className="case-radiographies-inline-viewer"
                        >
                          <div
                            className="case-radiographies-inline-thumbs"
                          >
                            {
                              selectedStudy.files.length > 0
                                ? selectedStudy.files.map(
                                    (
                                      file,
                                      index,
                                    ) => {
                                      const thumbUrl =
                                        previewUrls[
                                          file.id_file
                                        ];

                                      return (
                                        <button
                                          key={
                                            file.id_file
                                          }
                                          type="button"
                                          className={
                                            selectedInlineFile?.id_file === file.id_file
                                              ? "case-radiographies-inline-thumb case-radiographies-inline-thumb--active"
                                              : "case-radiographies-inline-thumb"
                                          }
                                          onClick={
                                            () => {
                                              setSelectedInlineFileId(
                                                file.id_file,
                                              );

                                              setReplacementTarget(
                                                null,
                                              );

                                              resetViewer();

                                              void ensurePreview(
                                                file,
                                              );
                                            }
                                          }
                                        >
                                          <div>
                                            {
                                              thumbUrl
                                                ? (
                                                    <img
                                                      src={
                                                        thumbUrl
                                                      }
                                                      alt=""
                                                      draggable={
                                                        false
                                                      }
                                                    />
                                                  )
                                                : (
                                                    <FileImage
                                                      size={22}
                                                    />
                                                  )
                                            }
                                          </div>

                                          <span>
                                            {
                                              selectedStudy.files.length > 1
                                                ? `Vista ${index + 1}`
                                                : selectedStudy.study_type.name
                                            }
                                          </span>
                                        </button>
                                      );
                                    },
                                  )
                                : (
                                    <div
                                      className="case-radiographies-inline-thumb-empty"
                                    >
                                      <FileImage
                                        size={22}
                                      />
                                    </div>
                                  )
                            }
                          </div>


                          <div
                            ref={
                              inlineStageRef
                            }
                            className={
                              draggingRef.current
                                ? "case-radiographies-inline-stage case-radiographies-inline-stage--dragging"
                                : "case-radiographies-inline-stage"
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
                            {
                              selectedInlineFile
                              &&
                              isRadiographicFilePreviewable(
                                selectedInlineFile,
                              )
                              &&
                              inlineViewerUrl
                                ? (
                                    <img
                                      src={
                                        inlineViewerUrl
                                      }
                                      alt={
                                        `Radiografía ${selectedInlineFile.original_name}`
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
                                  )
                                : (
                                    <div
                                      className="case-radiographies-inline-placeholder"
                                    >
                                      {
                                        selectedInlineFile?.validation_status === "RECHAZADA"
                                          ? (
                                              <>
                                                <ShieldAlert
                                                  size={42}
                                                />

                                                <strong>
                                                  Radiografía rechazada
                                                </strong>

                                                <span>
                                                  Revise el motivo y la corrección necesaria antes de continuar.
                                                </span>
                                              </>
                                            )
                                          : selectedInlineFile?.mime.code === "DICOM"
                                            ? (
                                                <>
                                                  <FileImage
                                                    size={42}
                                                  />

                                                  <strong>
                                                    Archivo DICOM registrado
                                                  </strong>

                                                  <span>
                                                    El archivo está almacenado de forma segura. La previsualización web para DICOM aún no está habilitada.
                                                  </span>
                                                </>
                                              )
                                            : (
                                                <>
                                                  <LoaderCircle
                                                    size={34}
                                                    className="case-radiographies-spin"
                                                  />

                                                  <strong>
                                                    Preparando vista previa...
                                                  </strong>
                                                </>
                                              )
                                      }
                                    </div>
                                  )
                            }


                            <div
                              className="case-radiographies-inline-toolbar"
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
                                title="Pantalla completa"
                                onClick={
                                  () =>
                                    void toggleFullscreen(
                                      inlineViewerRef.current,
                                    )
                                }
                              >
                                <Maximize2
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
                                title="Invertir imagen"
                                className={
                                  viewerInvert
                                    ? "case-radiographies-inline-toolbar-active"
                                    : undefined
                                }
                                onClick={
                                  () =>
                                    setViewerInvert(
                                      (current) =>
                                        !current,
                                    )
                                }
                              >
                                <Sun
                                  size={17}
                                />
                              </button>
                            </div>


                            <div
                              className="case-radiographies-inline-zoom"
                            >
                              <button
                                type="button"
                                onClick={
                                  zoomIn
                                }
                                title="Acercar"
                              >
                                <Plus
                                  size={14}
                                />
                              </button>

                              <input
                                type="range"
                                min="1"
                                max="4"
                                step="0.05"
                                value={
                                  viewerZoom
                                }
                                onChange={
                                  (event) =>
                                    changeViewerZoom(
                                      Number(
                                        event.target.value,
                                      ),
                                    )
                                }
                                aria-label="Nivel de zoom"
                              />

                              <button
                                type="button"
                                onClick={
                                  zoomOut
                                }
                                title="Alejar"
                              >
                                <Minus
                                  size={14}
                                />
                              </button>

                              <strong>
                                {
                                  Math.round(
                                    viewerZoom * 100,
                                  )
                                }%
                              </strong>
                            </div>


                            <div
                              className="case-radiographies-inline-adjustments"
                            >
                              <label>
                                <span>
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
                                    (event) =>
                                      setViewerBrightness(
                                        Number(
                                          event.target.value,
                                        ),
                                      )
                                  }
                                />
                              </label>

                              <label>
                                <span>
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
                                    (event) =>
                                      setViewerContrast(
                                        Number(
                                          event.target.value,
                                        ),
                                      )
                                  }
                                />
                              </label>
                            </div>
                          </div>
                        </div>


                        <div
                          className="case-radiographies-detail-information"
                        >
                          <section
                            className="case-radiographies-study-information"
                          >
                            <header>
                              <div
                                className="case-radiographies-detail-small-icon"
                              >
                                <Info
                                  size={15}
                                />
                              </div>

                              <strong>
                                Información del estudio
                              </strong>
                            </header>

                            <div
                              className="case-radiographies-study-information-grid"
                            >
                              <div>
                                <span>
                                  <CalendarDays
                                    size={14}
                                  />

                                  Fecha de estudio
                                </span>

                                <strong>
                                  {formatDate(selectedStudy.study_date)}
                                </strong>
                              </div>

                              <div>
                                <span>
                                  <FileImage
                                    size={14}
                                  />

                                  Tipo de estudio
                                </span>

                                <strong>
                                  {selectedStudy.study_type.name}
                                </strong>
                              </div>

                              <div>
                                <span>
                                  <Clock3
                                    size={14}
                                  />

                                  Fecha de registro
                                </span>

                                <strong>
                                  {formatDateTime(selectedStudy.registered_at)}
                                </strong>
                              </div>

                              <div>
                                <span>
                                  <MapPin
                                    size={14}
                                  />

                                  Región anatómica
                                </span>

                                <strong>
                                  {selectedStudy.anatomical_region.name}
                                </strong>
                              </div>

                              <div>
                                <span>
                                  <UserRound
                                    size={14}
                                  />

                                  Profesional
                                </span>

                                <strong>
                                  {
                                    resolveAuthorName(
                                      selectedStudy.registered_by_uuid,
                                    )
                                  }
                                </strong>
                              </div>

                              <div>
                                <span>
                                  <MapPin
                                    size={14}
                                  />

                                  Lateralidad
                                </span>

                                <strong>
                                  {
                                    selectedStudy.laterality?.name
                                    ??
                                    "No especificada"
                                  }
                                </strong>
                              </div>
                            </div>
                          </section>


                          <section
                            className="case-radiographies-study-observations"
                          >
                            <header>
                              <div
                                className="case-radiographies-detail-small-icon"
                              >
                                <FileImage
                                  size={15}
                                />
                              </div>

                              <strong>
                                Observaciones
                              </strong>
                            </header>

                            <div>
                              {
                                selectedStudy.observation
                                ||
                                "Sin observaciones registradas."
                              }
                            </div>
                          </section>
                        </div>


                        {
                          selectedInlineFile?.validation_status === "RECHAZADA"
                          &&
                          (
                            <section
                              className="case-radiographies-selected-rejection"
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
                                    Radiografía rechazada
                                  </strong>

                                  <span>
                                    El archivo no superó la validación. Revise el motivo y realice la corrección indicada antes de continuar con el análisis.
                                  </span>
                                </div>
                              </div>


                              {
                                selectedInvalidValidations.length > 0
                                  ? (
                                      <div
                                        className="case-radiographies-validation-list"
                                      >
                                        {
                                          selectedInvalidValidations.map(
                                            (
                                              validation,
                                              validationIndex,
                                            ) => (
                                              <div
                                                key={
                                                  `${selectedInlineFile.id_file}-${validation.type_code}-${validationIndex}`
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
                                                      {validation.type_name}
                                                    </strong>
                                                  </div>

                                                  <span>
                                                    {validation.result_name}
                                                  </span>
                                                </div>

                                                {
                                                  validation.detail
                                                  &&
                                                  (
                                                    <p
                                                      className="case-radiographies-validation-detail"
                                                    >
                                                      {validation.detail}
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
                                                        {validation.reason}
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
                                                          Corrección necesaria
                                                        </strong>
                                                      </div>

                                                      <p>
                                                        {validation.correction}
                                                      </p>
                                                    </div>
                                                  )
                                                }
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
                                        No se encontraron detalles adicionales de la validación.
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
                                    No disponible para análisis
                                  </strong>

                                  <span>
                                    Esta versión se conserva para trazabilidad, pero no puede utilizarse en el análisis mientras permanezca rechazada.
                                  </span>
                                </div>
                              </div>


                              {
                                selectedInlineFile.active
                                &&
                                (
                                  replacementTarget?.id_file === selectedInlineFile.id_file
                                    ? (
                                        <div
                                          className="case-radiographies-replacement-inline"
                                        >
                                          <div
                                            className="case-radiographies-form-heading"
                                          >
                                            <Upload
                                              size={20}
                                            />

                                            <div>
                                              <strong>
                                                Reemplazar radiografía rechazada
                                              </strong>

                                              <span>
                                                La versión {selectedInlineFile.version} se conservará para trazabilidad.
                                              </span>
                                            </div>
                                          </div>


                                          <label
                                            className="case-radiographies-file-field case-radiographies-form-wide"
                                          >
                                            <span>
                                              Nueva radiografía *
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
                                                    event.target.files?.[0]
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
                                              className={
                                                replacementFile
                                                  ? "case-radiographies-file-box case-radiographies-file-box--replacement case-radiographies-file-box--selected"
                                                  : "case-radiographies-file-box case-radiographies-file-box--replacement"
                                              }
                                            >
                                              {
                                                replacementFile
                                                  ? (
                                                      <>
                                                        <div
                                                          className="case-radiographies-local-preview case-radiographies-local-preview--replacement"
                                                        >
                                                          {
                                                            replacementFilePreviewUrl
                                                              ? (
                                                                  <img
                                                                    src={
                                                                      replacementFilePreviewUrl
                                                                    }
                                                                    alt="Vista previa del archivo de reemplazo"
                                                                  />
                                                                )
                                                              : (
                                                                  <div
                                                                    className="case-radiographies-local-preview-placeholder"
                                                                  >
                                                                    <FileImage
                                                                      size={32}
                                                                    />

                                                                    <strong>
                                                                      {
                                                                        getLocalRadiographyFormatLabel(
                                                                          replacementFile,
                                                                        )
                                                                      }
                                                                    </strong>

                                                                    <span>
                                                                      {
                                                                        getLocalRadiographyExtension(
                                                                          replacementFile,
                                                                        )
                                                                        ===
                                                                        "dcm"
                                                                          ? "Vista previa DICOM disponible después de la carga"
                                                                          : "Vista previa no disponible"
                                                                      }
                                                                    </span>
                                                                  </div>
                                                                )
                                                          }

                                                          <span
                                                            className="case-radiographies-local-preview-badge"
                                                          >
                                                            Vista previa
                                                          </span>
                                                        </div>

                                                        <div
                                                          className="case-radiographies-local-preview-info"
                                                        >
                                                          <strong>
                                                            {
                                                              replacementFile
                                                                .name
                                                            }
                                                          </strong>

                                                          <span>
                                                            {
                                                              getLocalRadiographyFormatLabel(
                                                                replacementFile,
                                                              )
                                                            }
                                                            {" · "}
                                                            {
                                                              formatBytes(
                                                                replacementFile
                                                                  .size,
                                                              )
                                                            }
                                                          </span>

                                                          <small>
                                                            El archivo original no se modifica.
                                                          </small>

                                                          <b>
                                                            Cambiar archivo
                                                          </b>
                                                        </div>
                                                      </>
                                                    )
                                                  : (
                                                      <>
                                                        <FileImage
                                                          size={29}
                                                        />

                                                        <strong>
                                                          Seleccione la radiografía corregida
                                                        </strong>

                                                        <span>
                                                          JPG, JPEG, PNG o DICOM (.dcm) · máximo 20 MB
                                                        </span>
                                                      </>
                                                    )
                                              }
                                            </div>
                                          </label>


                                          <label
                                            className="case-radiographies-replacement-reason"
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
                                              placeholder="Ej.: se reemplaza el archivo rechazado por la radiografía original correcta."
                                            />
                                          </label>


                                          {
                                            replacing
                                            &&
                                            (
                                              <div
                                                className="case-radiographies-progress"
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
                                                      Reemplazando radiografía...
                                                    </strong>
                                                  </div>

                                                  <span>
                                                    {replacementProgress}%
                                                  </span>
                                                </div>

                                                <div
                                                  className="case-radiographies-progress-track"
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
                                    : (
                                        <button
                                          type="button"
                                          className="case-radiographies-replace-inline-button"
                                          disabled={
                                            replacing
                                          }
                                          onClick={
                                            () =>
                                              openReplacement(
                                                selectedInlineFile,
                                              )
                                          }
                                        >
                                          <Upload
                                            size={15}
                                          />

                                          Reemplazar radiografía
                                        </button>
                                      )
                                )
                              }
                            </section>
                          )
                        }


                        {
                          selectedInlineFile
                          &&
                          (
                            <footer
                              className="case-radiographies-selected-file-footer"
                            >
                              <span>
                                <strong>
                                  Archivo:
                                </strong>{" "}
                                {selectedInlineFile.original_name}
                              </span>

                              <span>
                                Versión {selectedInlineFile.version}
                                {" · "}
                                {selectedInlineFile.mime.code}
                                {" · "}
                                {formatBytes(selectedInlineFile.size_bytes)}
                              </span>
                            </footer>
                          )
                        }
                      </>
                    )
                  }
                </section>
              </div>
            )
      }

      </article>


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
                modalViewerRef
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
                        void toggleFullscreen(
                          modalViewerRef.current,
                        )
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
                ref={
                  modalStageRef
                }
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
