import {
  CalendarDays,
  Download,
  Eye,
  FileImage,
  Image,
  LoaderCircle,
  Plus,
  Save,
  Upload,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import {
  createRadiography,
  downloadRadiographicFileBlob,
  getCaseRadiographies,
  getRadiographicFileBlob,
  getRadiographyCatalogs,
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


export function CaseRadiographiesSection({
  caseId,
  resolveAuthorName,
}: Props) {

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null,
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

    resetForm();

    setShowForm(
      false,
    );

    setError(
      null,
    );
  }


  async function handleSave() {

    if (
      !studyTypeId
    ) {
      setError(
        "Seleccione el tipo de estudio.",
      );
      return;
    }

    if (
      !anatomicalRegionId
    ) {
      setError(
        "Seleccione la región anatómica.",
      );
      return;
    }

    if (
      !lateralityId
    ) {
      setError(
        "Seleccione la lateralidad.",
      );
      return;
    }

    if (
      !selectedFile
    ) {
      setError(
        "Seleccione una radiografía.",
      );
      return;
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
      setError(
        "Solo se permiten archivos JPG, PNG o DICOM.",
      );
      return;
    }


    if (
      selectedFile.size
      >
      20 * 1024 * 1024
    ) {
      setError(
        "El archivo no puede superar los 20 MB.",
      );
      return;
    }


    setSaving(
      true,
    );

    setError(
      null,
    );


    try {

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
      );


      await loadStudies();

      resetForm();

      setShowForm(
        false,
      );

      setSuccess(
        "Radiografía registrada correctamente.",
      );


      window.setTimeout(
        () => {

          setSuccess(
            null,
          );

        },
        3500,
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

      setSaving(
        false,
      );

    }
  }


  async function handleView(
    fileId:
      string,
  ) {

    setWorkingFileId(
      fileId,
    );

    setError(
      null,
    );


    try {

      const blob =
        await getRadiographicFileBlob(
          fileId,
        );


      const url =
        URL.createObjectURL(
          blob,
        );


      const popup =
        window.open(
          url,
          "_blank",
          "noopener,noreferrer",
        );


      if (!popup) {

        const anchor =
          document.createElement(
            "a",
          );

        anchor.href =
          url;

        anchor.target =
          "_blank";

        anchor.rel =
          "noopener noreferrer";

        anchor.click();
      }


      window.setTimeout(
        () => {

          URL.revokeObjectURL(
            url,
          );

        },
        60_000,
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


  async function handleDownload(
    fileId:
      string,

    fileName:
      string,
  ) {

    setWorkingFileId(
      fileId,
    );

    setError(
      null,
    );


    try {

      const blob =
        await downloadRadiographicFileBlob(
          fileId,
        );


      const url =
        URL.createObjectURL(
          blob,
        );


      const anchor =
        document.createElement(
          "a",
        );

      anchor.href =
        url;

      anchor.download =
        fileName;

      document.body.appendChild(
        anchor,
      );

      anchor.click();

      anchor.remove();

      URL.revokeObjectURL(
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
          onClick={
            () => {

              setShowForm(
                (
                  current,
                ) =>
                  !current,
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
                  Complete los datos y seleccione
                  la radiografía correspondiente.
                </span>
              </div>
            </div>


            <div
              className="case-radiographies-form-grid"
            >

              <label>
                Tipo de estudio *

                <select
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
                              Tamaño máximo: 20 MB
                            </span>
                          </>
                        )
                  }
                </div>

              </label>

            </div>


            <div
              className="case-radiographies-form-actions"
            >

              <button
                type="button"
                className="case-radiographies-secondary"
                disabled={
                  saving
                }
                onClick={
                  closeForm
                }
              >
                Cancelar
              </button>


              <button
                type="button"
                className="case-radiographies-primary"
                disabled={
                  saving
                }
                onClick={
                  () =>
                    void handleSave()
                }
              >

                {
                  saving
                    ? (
                        <LoaderCircle
                          size={17}
                          className="case-radiographies-spin"
                        />
                      )
                    : (
                        <Save
                          size={17}
                        />
                      )
                }

                {
                  saving
                    ? "Guardando..."
                    : "Guardar radiografía"
                }

              </button>

            </div>

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
                  Sin radiografías registradas
                </strong>

                <span>
                  Registre el primer estudio radiográfico
                  asociado a este caso clínico.
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
                                  ) => (

                                    <div
                                      key={
                                        file.id_file
                                      }
                                      className="case-radiographies-file"
                                    >

                                      <div
                                        className="case-radiographies-file-info"
                                      >

                                        <strong>
                                          {
                                            file
                                              .original_name
                                          }
                                        </strong>


                                        <span>
                                          {
                                            file
                                              .mime
                                              .code
                                          }
                                          {" · "}
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
                                                    {" · "}
                                                    {
                                                      file.width_px
                                                    }
                                                    ×
                                                    {
                                                      file.height_px
                                                    }
                                                  </>
                                                )
                                              : null
                                          }
                                        </span>

                                      </div>


                                      <div
                                        className="case-radiographies-file-actions"
                                      >

                                        {
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

                                              Ver
                                            </button>

                                          )
                                        }


                                        <button
                                          type="button"
                                          disabled={
                                            workingFileId
                                            ===
                                            file.id_file
                                          }
                                          onClick={
                                            () =>
                                              void handleDownload(
                                                file.id_file,
                                                file.original_name,
                                              )
                                          }
                                        >
                                          <Download
                                            size={15}
                                          />

                                          Descargar
                                        </button>

                                      </div>

                                    </div>

                                  ),
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

  );
}
