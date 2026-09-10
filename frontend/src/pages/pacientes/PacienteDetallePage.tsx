import {
  Activity,
  ArrowLeft,
  CalendarDays,
  Camera,
  CheckCircle2,
  CircleAlert,
  ContactRound,
  Edit3,
  IdCard,
  ImagePlus,
  LoaderCircle,
  Save,
  ShieldCheck,
  Trash2,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  deletePatientPhoto,
  getPatient,
  getPatientCatalogs,
  resolvePatientPhotoUrl,
  updatePatient,
  uploadPatientPhoto,
  type PatientCatalogs,
  type PatientChange,
  type PatientDetail,
} from "../../api/pacientes.api";

import {
  PatientAuditHistory,
} from "../../components/pacientes/PatientAuditHistory";

import {
  PatientClinicalCases,
} from "../../components/pacientes/PatientClinicalCases";

import {
  PatientRadiographies,
} from "../../components/pacientes/PatientRadiographies";

import "./PacienteDetallePage.css";


// ==========================================================
// DEPARTAMENTOS
// ==========================================================

const DEPARTAMENTOS:
  Record<
    string,
    string
  > = {

    LP:
      "La Paz",

    CB:
      "Cochabamba",

    SC:
      "Santa Cruz",

    OR:
      "Oruro",

    PT:
      "Potosí",

    CH:
      "Chuquisaca",

    TJ:
      "Tarija",

    BE:
      "Beni",

    PD:
      "Pando",

  };


// ==========================================================
// CONFIG FOTO
// ==========================================================

const MAX_PHOTO_SIZE =
  5
  *
  1024
  *
  1024;


const ALLOWED_PHOTO_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
];


// ==========================================================
// HELPERS
// ==========================================================

function formatDate(
  value?:
    string | null,
): string {

  if (!value) {

    return "—";

  }


  const date =
    new Date(
      `${value}T00:00:00`,
    );


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {

    return value;

  }


  return (
    new Intl.DateTimeFormat(
      "es-BO",
      {
        day:
          "2-digit",

        month:
          "2-digit",

        year:
          "numeric",
      },
    )
    .format(
      date,
    )
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


  return (
    new Intl.DateTimeFormat(
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
    )
    .format(
      date,
    )
  );

}


function normalizeText(
  value:
    string,
): string {

  return value
    .trim()
    .replace(
      /\s+/g,
      " ",
    );

}


function departmentName(
  code?:
    string | null,
): string {

  if (!code) {

    return "—";

  }


  return (
    DEPARTAMENTOS[
      code
    ]
    ??
    code
  );

}


function relationshipName(
  value:
    string,
): string {

  const names:
    Record<
      string,
      string
    > = {

      MADRE:
        "Madre",

      PADRE:
        "Padre",

      HERMANO:
        "Hermano",

      HERMANA:
        "Hermana",

      HIJO:
        "Hijo",

      HIJA:
        "Hija",

      ESPOSO:
        "Esposo",

      ESPOSA:
        "Esposa",

      TUTOR:
        "Tutor",

      TUTORA:
        "Tutora",

      ABUELO:
        "Abuelo",

      ABUELA:
        "Abuela",

      TIO:
        "Tío",

      TIA:
        "Tía",

      PRIMO:
        "Primo",

      PRIMA:
        "Prima",

      OTRO:
        "Otro",

    };


  return (
    names[
      value
    ]
    ??
    value
  );

}


function extractErrorMessage(
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

    const maybeAxios =
      error as {
        response?: {
          data?: {
            error?:
              | {
                  message?: string;
                }
              | string;

            detail?:
              string;
          };
        };
      };


    const data =
      maybeAxios
        .response
        ?.data;


    if (
      typeof data?.error ===
      "string"
    ) {

      return data.error;

    }


    if (
      data?.error
      &&
      typeof data.error ===
      "object"
      &&
      typeof data.error.message ===
      "string"
    ) {

      return data.error.message;

    }


    if (
      typeof data?.detail ===
      "string"
    ) {

      return data.detail;

    }

  }


  return (
    "No fue posible completar la operación."
  );

}


function patientInitials(
  patient:
    PatientDetail,
): string {

  const parts = [
    patient.first_names,
    patient.paternal_surname,
  ]
    .filter(
      Boolean,
    );


  return parts
    .map(
      (
        value,
      ) =>
        value
          .trim()
          .charAt(
            0,
          )
          .toUpperCase(),
    )
    .join(
      "",
    )
    .slice(
      0,
      2,
    )
    ||
    "P";

}


// ==========================================================
// FORMULARIO EDICIÓN
// ==========================================================

type EditForm = {

  first_names:
    string;

  paternal_surname:
    string;

  maternal_surname:
    string;

  birth_date:
    string;

  sex_id:
    string;

  active:
    boolean;

  reason:
    string;

};


const emptyForm:
  EditForm = {

    first_names:
      "",

    paternal_surname:
      "",

    maternal_surname:
      "",

    birth_date:
      "",

    sex_id:
      "",

    active:
      true,

    reason:
      "",

  };


// ==========================================================
// COMPONENTE
// ==========================================================

export function PacienteDetallePage() {

  const navigate =
    useNavigate();


  const fileInputRef =
    useRef<HTMLInputElement>(
      null,
    );


  const {
    id,
  } = useParams<{
    id: string;
  }>();


  // ========================================================
  // ESTADO PRINCIPAL
  // ========================================================

  const [
    patient,
    setPatient,
  ] = useState<
    PatientDetail | null
  >(
    null,
  );


  const [
    catalogs,
    setCatalogs,
  ] = useState<
    PatientCatalogs | null
  >(
    null,
  );


  const [
    editForm,
    setEditForm,
  ] = useState<
    EditForm
  >(
    emptyForm,
  );


  const [
    editing,
    setEditing,
  ] = useState(
    false,
  );


  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );


  const [
    saving,
    setSaving,
  ] = useState(
    false,
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null,
  );


  const [
    success,
    setSuccess,
  ] = useState<
    string | null
  >(
    null,
  );


  const [
    lastChanges,
    setLastChanges,
  ] = useState<
    PatientChange[]
  >(
    [],
  );


  // ========================================================
  // FOTO
  // ========================================================

  const [
    selectedPhoto,
    setSelectedPhoto,
  ] = useState<
    File | null
  >(
    null,
  );


  const [
    photoPreview,
    setPhotoPreview,
  ] = useState<
    string | null
  >(
    null,
  );


  const [
    uploadingPhoto,
    setUploadingPhoto,
  ] = useState(
    false,
  );


  const [
    deletingPhoto,
    setDeletingPhoto,
  ] = useState(
    false,
  );


  // ========================================================
  // CARGAR PACIENTE
  // ========================================================

  useEffect(
    () => {

      if (!id) {

        setError(
          "No se recibió un identificador de paciente válido.",
        );


        setLoading(
          false,
        );


        return;

      }


      let mounted =
        true;


      async function load() {

        setLoading(
          true,
        );


        setError(
          null,
        );


        try {

          const [
            patientData,
            catalogData,
          ] =
            await Promise.all(
              [
                getPatient(
                  id!,
                ),

                getPatientCatalogs(),
              ],
            );


          if (!mounted) {

            return;

          }


          setPatient(
            patientData,
          );


          setCatalogs(
            {
              ...catalogData,

              sexes:
                catalogData
                  .sexes
                  .filter(
                    (
                      item,
                    ) =>
                      item.code ===
                      "M"
                      ||
                      item.code ===
                      "F",
                  ),
            },
          );


          setEditForm(
            {

              first_names:
                patientData
                  .first_names,

              paternal_surname:
                patientData
                  .paternal_surname,

              maternal_surname:
                patientData
                  .maternal_surname
                ??
                "",

              birth_date:
                patientData
                  .birth_date,

              sex_id:
                String(
                  patientData
                    .sex
                    .id
                  ??
                  "",
                ),

              active:
                patientData
                  .active,

              reason:
                "",

            },
          );

        } catch (
          requestError
        ) {

          if (
            mounted
          ) {

            setError(
              extractErrorMessage(
                requestError,
              ),
            );

          }

        } finally {

          if (
            mounted
          ) {

            setLoading(
              false,
            );

          }

        }

      }


      void load();


      return () => {

        mounted =
          false;

      };

    },
    [
      id,
    ],
  );


  // ========================================================
  // LIMPIAR PREVIEW
  // ========================================================

  useEffect(
    () => {

      return () => {

        if (
          photoPreview
        ) {

          URL.revokeObjectURL(
            photoPreview,
          );

        }

      };

    },
    [
      photoPreview,
    ],
  );


  // ========================================================
  // DOCUMENTO PRINCIPAL
  // ========================================================

  const primaryDocument =
    useMemo(
      () =>
        patient
          ?.documents[0]
        ??
        null,
      [
        patient,
      ],
    );


  // ========================================================
  // CONTACTO PRINCIPAL
  // ========================================================

  const primaryContact =
    useMemo(
      () =>
        patient
          ?.contacts
          .find(
            (
              contact,
            ) =>
              contact.primary,
          )
        ??
        patient
          ?.contacts[0]
        ??
        null,
      [
        patient,
      ],
    );


  // ========================================================
  // EMERGENCIA PRINCIPAL
  // ========================================================

  const primaryEmergencyContact =
    useMemo(
      () =>
        patient
          ?.primary_emergency_contact
        ??
        patient
          ?.emergency_contacts
          ?.find(
            (
              contact,
            ) =>
              contact.primary,
          )
        ??
        patient
          ?.emergency_contacts
          ?.[0]
        ??
        null,
      [
        patient,
      ],
    );


  // ========================================================
  // FOTO ACTUAL
  // ========================================================

  const currentPhoto =
    useMemo(
      () => {

        if (
          photoPreview
        ) {

          return photoPreview;

        }


        return (
          resolvePatientPhotoUrl(
            patient
              ?.photo_url,
          )
        );

      },
      [
        patient,
        photoPreview,
      ],
    );


  // ========================================================
  // SELECCIONAR FOTO
  // ========================================================

  function handlePhotoSelected(
    event:
      React.ChangeEvent<HTMLInputElement>,
  ) {

    const file =
      event
        .target
        .files
        ?.[0];


    if (!file) {

      return;

    }


    setError(
      null,
    );


    setSuccess(
      null,
    );


    if (
      !ALLOWED_PHOTO_TYPES
        .includes(
          file.type,
        )
    ) {

      setError(
        "Solo se permiten imágenes JPG, JPEG, PNG o WEBP.",
      );


      event.target.value =
        "";


      return;

    }


    if (
      file.size >
      MAX_PHOTO_SIZE
    ) {

      setError(
        "La imagen no puede superar los 5 MB.",
      );


      event.target.value =
        "";


      return;

    }


    if (
      photoPreview
    ) {

      URL.revokeObjectURL(
        photoPreview,
      );

    }


    const preview =
      URL.createObjectURL(
        file,
      );


    setSelectedPhoto(
      file,
    );


    setPhotoPreview(
      preview,
    );


    event.target.value =
      "";

  }


  // ========================================================
  // CANCELAR FOTO SELECCIONADA
  // ========================================================

  function cancelPhotoSelection() {

    if (
      photoPreview
    ) {

      URL.revokeObjectURL(
        photoPreview,
      );

    }


    setSelectedPhoto(
      null,
    );


    setPhotoPreview(
      null,
    );

  }


  // ========================================================
  // SUBIR FOTO
  // ========================================================

  async function handleUploadPhoto() {

    if (
      !id
      ||
      !patient
      ||
      !selectedPhoto
    ) {

      return;

    }


    setUploadingPhoto(
      true,
    );


    setError(
      null,
    );


    setSuccess(
      null,
    );


    try {

      const response =
        await uploadPatientPhoto(
          id,
          selectedPhoto,
        );


      if (
        photoPreview
      ) {

        URL.revokeObjectURL(
          photoPreview,
        );

      }


      setPatient(
        {
          ...patient,

          photo_url:
            response.photo_url,
        },
      );


      setSelectedPhoto(
        null,
      );


      setPhotoPreview(
        null,
      );


      setSuccess(
        response.message,
      );

    } catch (
      requestError
    ) {

      setError(
        extractErrorMessage(
          requestError,
        ),
      );

    } finally {

      setUploadingPhoto(
        false,
      );

    }

  }


  // ========================================================
  // ELIMINAR FOTO
  // ========================================================

  async function handleDeletePhoto() {

    if (
      !id
      ||
      !patient
    ) {

      return;

    }


    const confirmed =
      window.confirm(
        "¿Desea eliminar la foto del paciente?",
      );


    if (!confirmed) {

      return;

    }


    setDeletingPhoto(
      true,
    );


    setError(
      null,
    );


    setSuccess(
      null,
    );


    try {

      const response =
        await deletePatientPhoto(
          id,
        );


      cancelPhotoSelection();


      setPatient(
        {
          ...patient,

          photo_url:
            null,
        },
      );


      setSuccess(
        response.message,
      );

    } catch (
      requestError
    ) {

      setError(
        extractErrorMessage(
          requestError,
        ),
      );

    } finally {

      setDeletingPhoto(
        false,
      );

    }

  }


  // ========================================================
  // INICIAR EDICIÓN
  // ========================================================

  function startEditing() {

    if (!patient) {

      return;

    }


    setEditForm(
      {

        first_names:
          patient
            .first_names,

        paternal_surname:
          patient
            .paternal_surname,

        maternal_surname:
          patient
            .maternal_surname
          ??
          "",

        birth_date:
          patient
            .birth_date,

        sex_id:
          String(
            patient
              .sex
              .id
            ??
            "",
          ),

        active:
          patient
            .active,

        reason:
          "",

      },
    );


    setLastChanges(
      [],
    );


    setSuccess(
      null,
    );


    setError(
      null,
    );


    setEditing(
      true,
    );

  }


  function cancelEditing() {

    setEditing(
      false,
    );


    setError(
      null,
    );

  }


  function updateField(
    field:
      keyof EditForm,

    value:
      string | boolean,
  ) {

    setEditForm(
      (
        current,
      ) => ({
        ...current,

        [field]:
          value,
      }),
    );

  }


  // ========================================================
  // GUARDAR EDICIÓN
  // ========================================================

  async function handleSave(
    event:
      React.FormEvent,
  ) {

    event.preventDefault();


    if (
      !id
      ||
      !patient
    ) {

      return;

    }


    setError(
      null,
    );


    setSuccess(
      null,
    );


    if (
      normalizeText(
        editForm.first_names,
      ).length < 2
    ) {

      setError(
        "Los nombres deben contener al menos 2 caracteres.",
      );


      return;

    }


    if (
      normalizeText(
        editForm.paternal_surname,
      ).length < 2
    ) {

      setError(
        "El apellido paterno debe contener al menos 2 caracteres.",
      );


      return;

    }


    if (
      !editForm.birth_date
    ) {

      setError(
        "Debe seleccionar una fecha de nacimiento.",
      );


      return;

    }


    if (
      !editForm.sex_id
    ) {

      setError(
        "Debe seleccionar el sexo del paciente.",
      );


      return;

    }


    if (
      normalizeText(
        editForm.reason,
      ).length < 5
    ) {

      setError(
        "Debe indicar un motivo de edición de al menos 5 caracteres.",
      );


      return;

    }


    setSaving(
      true,
    );


    try {

      const response =
        await updatePatient(
          id,
          {
            first_names:
              normalizeText(
                editForm
                  .first_names,
              ),

            paternal_surname:
              normalizeText(
                editForm
                  .paternal_surname,
              ),

            maternal_surname:
              normalizeText(
                editForm
                  .maternal_surname,
              )
              ||
              null,

            birth_date:
              editForm
                .birth_date,

            sex_id:
              Number(
                editForm
                  .sex_id,
              ),

            active:
              editForm
                .active,

            reason:
              normalizeText(
                editForm
                  .reason,
              ),
          },
        );


      setPatient(
        response.data,
      );


      setLastChanges(
        response.changes,
      );


      setSuccess(
        response.message,
      );


      setEditing(
        false,
      );

    } catch (
      requestError
    ) {

      setError(
        extractErrorMessage(
          requestError,
        ),
      );

    } finally {

      setSaving(
        false,
      );

    }

  }


  // ========================================================
  // LOADING
  // ========================================================

  if (loading) {

    return (

      <div
        className="patient-detail-loading"
      >

        <LoaderCircle
          size={30}
          className="patient-detail-spin"
        />


        <span>
          Cargando ficha del paciente...
        </span>

      </div>

    );

  }


  // ========================================================
  // ERROR SIN PACIENTE
  // ========================================================

  if (!patient) {

    return (

      <section
        className="patient-detail-page"
      >

        <div
          className="patient-detail-message patient-detail-message--error"
        >

          <CircleAlert
            size={20}
          />


          <span>
            {
              error
              ??
              "No fue posible cargar la ficha del paciente."
            }
          </span>

        </div>


        <button
          type="button"
          className="patient-detail-back-list"
          onClick={
            () =>
              navigate(
                "/pacientes",
              )
          }
        >

          <ArrowLeft
            size={17}
          />

          Volver a pacientes

        </button>

      </section>

    );

  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="patient-detail-page"
    >

      {/* ==================================================
          HEADER
          ================================================== */}

      <header
        className="patient-detail-header"
      >

        <div
          className="patient-detail-header__main"
        >

          <button
            type="button"
            className="patient-detail-back"
            onClick={
              () =>
                navigate(
                  "/pacientes",
                )
            }
          >

            <ArrowLeft
              size={18}
            />

          </button>


          {/* FOTO */}

          <div
            className="patient-detail-photo-area"
          >

            <div
              className={
                currentPhoto
                  ? "patient-detail-photo patient-detail-photo--image"
                  : "patient-detail-photo"
              }
            >

              {
                currentPhoto
                  ? (

                      <img
                        src={
                          currentPhoto
                        }
                        alt={
                          `Foto de ${patient.full_name}`
                        }
                      />

                    )
                  : (

                      <span>
                        {
                          patientInitials(
                            patient,
                          )
                        }
                      </span>

                    )
              }


              {
                uploadingPhoto
                &&
                (

                  <div
                    className="patient-detail-photo-loading"
                  >
                    <LoaderCircle
                      size={24}
                      className="patient-detail-spin"
                    />
                  </div>

                )
              }

            </div>


            <input
              ref={
                fileInputRef
              }
              type="file"
              accept=".jpg,.jpeg,.png,.webp,image/jpeg,image/png,image/webp"
              className="patient-detail-photo-input"
              onChange={
                handlePhotoSelected
              }
            />


            <div
              className="patient-detail-photo-actions"
            >

              <button
                type="button"
                className="patient-detail-photo-select"
                disabled={
                  uploadingPhoto
                  ||
                  deletingPhoto
                }
                onClick={
                  () =>
                    fileInputRef
                      .current
                      ?.click()
                }
              >

                {
                  patient.photo_url
                    ? (
                        <Camera
                          size={14}
                        />
                      )
                    : (
                        <ImagePlus
                          size={14}
                        />
                      )
                }

                {
                  patient.photo_url
                    ? "Cambiar"
                    : "Subir foto"
                }

              </button>


              {
                selectedPhoto
                &&
                (

                  <>
                    <button
                      type="button"
                      className="patient-detail-photo-save"
                      disabled={
                        uploadingPhoto
                      }
                      onClick={
                        () =>
                          void handleUploadPhoto()
                      }
                    >

                      {
                        uploadingPhoto
                          ? (
                              <LoaderCircle
                                size={14}
                                className="patient-detail-spin"
                              />
                            )
                          : (
                              <Save
                                size={14}
                              />
                            )
                      }

                      Guardar

                    </button>


                    <button
                      type="button"
                      className="patient-detail-photo-cancel"
                      disabled={
                        uploadingPhoto
                      }
                      onClick={
                        cancelPhotoSelection
                      }
                      title="Cancelar"
                    >

                      <X
                        size={14}
                      />

                    </button>
                  </>

                )
              }


              {
                patient.photo_url
                &&
                !selectedPhoto
                &&
                (

                  <button
                    type="button"
                    className="patient-detail-photo-delete"
                    disabled={
                      deletingPhoto
                      ||
                      uploadingPhoto
                    }
                    onClick={
                      () =>
                        void handleDeletePhoto()
                    }
                    title="Eliminar foto"
                  >

                    {
                      deletingPhoto
                        ? (
                            <LoaderCircle
                              size={14}
                              className="patient-detail-spin"
                            />
                          )
                        : (
                            <Trash2
                              size={14}
                            />
                          )
                    }

                  </button>

                )
              }

            </div>

          </div>


          <div>

            <span
              className="patient-detail-eyebrow"
            >
              Ficha clínica
            </span>


            <div
              className="patient-detail-title-row"
            >

              <h1>
                {
                  patient
                    .full_name
                }
              </h1>


              <span
                className={
                  patient.active
                    ? "patient-detail-status patient-detail-status--active"
                    : "patient-detail-status patient-detail-status--inactive"
                }
              >

                {
                  patient.active
                    ? "Activo"
                    : "Inactivo"
                }

              </span>

            </div>


            <p>
              Información general, contactos,
              casos clínicos, radiografías e historial.
            </p>

          </div>

        </div>


        {
          !editing
          &&
          (

            <button
              type="button"
              className="patient-detail-edit-button"
              onClick={
                startEditing
              }
            >

              <Edit3
                size={17}
              />

              Editar paciente

            </button>

          )
        }

      </header>


      {
        error
        &&
        (

          <div
            className="patient-detail-message patient-detail-message--error"
          >

            <CircleAlert
              size={19}
            />

            <span>
              {error}
            </span>

          </div>

        )
      }


      {
        success
        &&
        (

          <div
            className="patient-detail-message patient-detail-message--success"
          >

            <CheckCircle2
              size={19}
            />

            <span>
              {success}
            </span>

          </div>

        )
      }


      {/* KPIS */}

      <div
        className="patient-detail-kpis"
      >

        <article>

          <div>
            <Activity
              size={21}
            />
          </div>

          <span>
            Casos clínicos
          </span>

          <strong>
            {
              patient
                .clinical_cases_count
            }
          </strong>

        </article>


        <article>

          <div>
            <CalendarDays
              size={21}
            />
          </div>

          <span>
            Registrado
          </span>

          <strong
            className="patient-detail-kpi-date"
          >
            {
              formatDateTime(
                patient.registration_date,
              )
            }
          </strong>

        </article>


        <article>

          <div>
            <ShieldCheck
              size={21}
            />
          </div>

          <span>
            Estado
          </span>

          <strong>
            {
              patient.active
                ? "Activo"
                : "Inactivo"
            }
          </strong>

        </article>

      </div>


      {/* ==================================================
          EDICIÓN
          ================================================== */}

      {
        editing
          ? (

              <form
                className="patient-detail-edit-card"
                onSubmit={
                  handleSave
                }
              >

                <div
                  className="patient-detail-section-header"
                >

                  <div
                    className="patient-detail-section-icon"
                  >
                    <Edit3
                      size={20}
                    />
                  </div>


                  <div>
                    <h2>
                      Editar datos personales
                    </h2>

                    <p>
                      Toda modificación requiere un motivo
                      y será enviada al historial de auditoría.
                    </p>
                  </div>

                </div>


                <div
                  className="patient-detail-edit-grid"
                >

                  <label>

                    <span>
                      Nombres *
                    </span>

                    <input
                      type="text"
                      value={
                        editForm.first_names
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "first_names",
                            event.target.value,
                          )
                      }
                      maxLength={100}
                    />

                  </label>


                  <label>

                    <span>
                      Apellido paterno *
                    </span>

                    <input
                      type="text"
                      value={
                        editForm.paternal_surname
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "paternal_surname",
                            event.target.value,
                          )
                      }
                      maxLength={80}
                    />

                  </label>


                  <label>

                    <span>
                      Apellido materno
                    </span>

                    <input
                      type="text"
                      value={
                        editForm.maternal_surname
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "maternal_surname",
                            event.target.value,
                          )
                      }
                      maxLength={80}
                    />

                  </label>


                  <label>

                    <span>
                      Fecha de nacimiento *
                    </span>

                    <input
                      type="date"
                      value={
                        editForm.birth_date
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "birth_date",
                            event.target.value,
                          )
                      }
                    />

                  </label>


                  <label>

                    <span>
                      Sexo *
                    </span>

                    <select
                      value={
                        editForm.sex_id
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "sex_id",
                            event.target.value,
                          )
                      }
                    >

                      {
                        catalogs
                          ?.sexes
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

                    <span>
                      Estado
                    </span>

                    <select
                      value={
                        editForm.active
                          ? "true"
                          : "false"
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "active",
                            event.target.value
                            ===
                            "true",
                          )
                      }
                    >

                      <option
                        value="true"
                      >
                        Activo
                      </option>

                      <option
                        value="false"
                      >
                        Inactivo
                      </option>

                    </select>

                  </label>


                  <label
                    className="patient-detail-reason"
                  >

                    <span>
                      Motivo de la modificación *
                    </span>

                    <textarea
                      value={
                        editForm.reason
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "reason",
                            event.target.value,
                          )
                      }
                      rows={3}
                      maxLength={500}
                      placeholder="Ej. Corrección de nombres solicitada por actualización de datos."
                    />

                  </label>

                </div>


                <footer
                  className="patient-detail-edit-actions"
                >

                  <button
                    type="button"
                    className="patient-detail-cancel"
                    disabled={
                      saving
                    }
                    onClick={
                      cancelEditing
                    }
                  >

                    <X
                      size={17}
                    />

                    Cancelar

                  </button>


                  <button
                    type="submit"
                    className="patient-detail-save"
                    disabled={
                      saving
                    }
                  >

                    {
                      saving
                        ? (
                            <LoaderCircle
                              size={18}
                              className="patient-detail-spin"
                            />
                          )
                        : (
                            <Save
                              size={18}
                            />
                          )
                    }

                    {
                      saving
                        ? "Guardando..."
                        : "Guardar cambios"
                    }

                  </button>

                </footer>

              </form>

            )
          : (

              <>

                {/* DATOS PERSONALES */}

                <article
                  className="patient-detail-card"
                >

                  <div
                    className="patient-detail-section-header"
                  >

                    <div
                      className="patient-detail-section-icon"
                    >
                      <UserRound
                        size={20}
                      />
                    </div>


                    <div>
                      <h2>
                        Datos personales
                      </h2>

                      <p>
                        Información principal del paciente.
                      </p>
                    </div>

                  </div>


                  <div
                    className="patient-detail-info-grid"
                  >

                    <div>
                      <span>
                        Nombres
                      </span>

                      <strong>
                        {patient.first_names}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Apellido paterno
                      </span>

                      <strong>
                        {patient.paternal_surname}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Apellido materno
                      </span>

                      <strong>
                        {
                          patient.maternal_surname
                          ||
                          "—"
                        }
                      </strong>
                    </div>


                    <div>
                      <span>
                        Fecha de nacimiento
                      </span>

                      <strong>
                        {
                          formatDate(
                            patient.birth_date,
                          )
                        }
                      </strong>
                    </div>


                    <div>
                      <span>
                        Sexo
                      </span>

                      <strong>
                        {patient.sex.name}
                      </strong>
                    </div>


                    <div>
                      <span>
                        Identificador
                      </span>

                      <strong
                        className="patient-detail-uuid"
                      >
                        {patient.id_patient}
                      </strong>
                    </div>

                  </div>

                </article>


                {/* DOCUMENTO + CONTACTOS */}

                <div
                  className="patient-detail-two-columns"
                >

                  <article
                    className="patient-detail-card"
                  >

                    <div
                      className="patient-detail-section-header"
                    >

                      <div
                        className="patient-detail-section-icon"
                      >
                        <IdCard
                          size={20}
                        />
                      </div>


                      <div>
                        <h2>
                          Documento
                        </h2>

                        <p>
                          Documento principal registrado.
                        </p>
                      </div>

                    </div>


                    {
                      primaryDocument
                        ? (

                            <div
                              className="patient-detail-info-grid patient-detail-info-grid--compact"
                            >

                              <div>
                                <span>
                                  Tipo
                                </span>

                                <strong>
                                  {
                                    primaryDocument
                                      .document_type_name
                                  }
                                </strong>
                              </div>


                              <div>
                                <span>
                                  Número
                                </span>

                                <strong>
                                  {
                                    primaryDocument
                                      .document_number
                                  }
                                </strong>
                              </div>


                              <div>
                                <span>
                                  Complemento
                                </span>

                                <strong>
                                  {
                                    primaryDocument
                                      .complement
                                    ||
                                    "—"
                                  }
                                </strong>
                              </div>


                              <div>
                                <span>
                                  Expedido en
                                </span>

                                <strong>
                                  {
                                    departmentName(
                                      primaryDocument
                                        .issued_in,
                                    )
                                  }
                                </strong>
                              </div>

                            </div>

                          )
                        : (

                            <div
                              className="patient-detail-empty-small"
                            >
                              Sin documento registrado.
                            </div>

                          )
                    }

                  </article>


                  <article
                    className="patient-detail-card"
                  >

                    <div
                      className="patient-detail-section-header"
                    >

                      <div
                        className="patient-detail-section-icon"
                      >
                        <ContactRound
                          size={20}
                        />
                      </div>


                      <div>
                        <h2>
                          Contactos del paciente
                        </h2>

                        <p>
                          Medios disponibles para comunicación.
                        </p>
                      </div>

                    </div>


                    {
                      patient.contacts.length > 0
                        ? (

                            <div
                              className="patient-detail-contact-list"
                            >

                              {
                                patient.contacts.map(
                                  (
                                    contact,
                                  ) => (

                                    <div
                                      key={
                                        contact.id_contact
                                        ??
                                        `${contact.contact_type_code}-${contact.value}`
                                      }
                                      className="patient-detail-contact-item"
                                    >

                                      <div>
                                        <span>
                                          {contact.contact_type_name}
                                        </span>

                                        <strong>
                                          {contact.value}
                                        </strong>
                                      </div>


                                      {
                                        contact.primary
                                        &&
                                        (
                                          <span
                                            className="patient-detail-primary-badge"
                                          >
                                            Principal
                                          </span>
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
                              className="patient-detail-empty-small"
                            >
                              Sin contactos registrados.
                            </div>

                          )
                    }

                  </article>

                </div>


                {/* EMERGENCIAS */}

                <article
                  className="patient-detail-card patient-detail-emergency-card"
                >

                  <div
                    className="patient-detail-section-header"
                  >

                    <div
                      className="patient-detail-section-icon"
                    >
                      <ShieldCheck
                        size={20}
                      />
                    </div>


                    <div>
                      <h2>
                        Contactos de emergencia
                      </h2>

                      <p>
                        Familiares, tutores o responsables del paciente.
                      </p>
                    </div>

                  </div>


                  {
                    patient.emergency_contacts.length > 0
                      ? (

                          <div
                            className="patient-detail-emergency-list"
                          >

                            {
                              patient.emergency_contacts.map(
                                (
                                  contact,
                                ) => (

                                  <div
                                    key={
                                      contact.id_emergency_contact
                                      ??
                                      `${contact.full_name}-${contact.phone}`
                                    }
                                    className={
                                      contact.primary
                                        ? "patient-detail-emergency-item patient-detail-emergency-item--primary"
                                        : "patient-detail-emergency-item"
                                    }
                                  >

                                    <div
                                      className="patient-detail-emergency-item__main"
                                    >

                                      <div
                                        className="patient-detail-emergency-avatar"
                                      >
                                        {
                                          contact.full_name
                                            .charAt(
                                              0,
                                            )
                                            .toUpperCase()
                                        }
                                      </div>


                                      <div>
                                        <strong>
                                          {contact.full_name}
                                        </strong>

                                        <span>
                                          {
                                            relationshipName(
                                              contact.relationship,
                                            )
                                          }
                                        </span>
                                      </div>

                                    </div>


                                    <div
                                      className="patient-detail-emergency-data"
                                    >

                                      <div>
                                        <span>
                                          Teléfono
                                        </span>

                                        <strong>
                                          {contact.phone}
                                        </strong>
                                      </div>


                                      <div>
                                        <span>
                                          Correo
                                        </span>

                                        <strong>
                                          {
                                            contact.email
                                            ??
                                            "—"
                                          }
                                        </strong>
                                      </div>

                                    </div>


                                    {
                                      contact.primary
                                      &&
                                      (
                                        <span
                                          className="patient-detail-primary-badge"
                                        >
                                          Principal
                                        </span>
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
                            className="patient-detail-empty"
                          >

                            <ContactRound
                              size={28}
                            />

                            <strong>
                              Sin contacto de emergencia
                            </strong>

                            <span>
                              Este paciente todavía no tiene
                              un familiar o responsable registrado.
                            </span>

                          </div>

                        )
                  }

                </article>


                {
                  (
                    primaryContact
                    ||
                    primaryEmergencyContact
                  )
                  &&
                  (

                    <div
                      className="patient-detail-contact-summary"
                    >

                      {
                        primaryContact
                        &&
                        (
                          <div>

                            <ContactRound
                              size={18}
                            />

                            <div>
                              <span>
                                Contacto principal
                              </span>

                              <strong>
                                {primaryContact.value}
                              </strong>
                            </div>

                          </div>
                        )
                      }


                      {
                        primaryEmergencyContact
                        &&
                        (
                          <div>

                            <ShieldCheck
                              size={18}
                            />

                            <div>
                              <span>
                                Emergencia principal
                              </span>

                              <strong>
                                {primaryEmergencyContact.full_name}
                                {" · "}
                                {primaryEmergencyContact.phone}
                              </strong>
                            </div>

                          </div>
                        )
                      }

                    </div>

                  )
                }


                <PatientClinicalCases
                  patientId={
                    patient.id_patient
                  }
                />


                <PatientRadiographies
                  patientId={
                    patient.id_patient
                  }
                />

              </>

            )
      }


      {
        lastChanges.length > 0
        &&
        (

          <article
            className="patient-detail-card patient-detail-changes-card"
          >

            <div
              className="patient-detail-section-header"
            >

              <div
                className="patient-detail-section-icon"
              >
                <ShieldCheck
                  size={20}
                />
              </div>


              <div>
                <h2>
                  Cambios registrados
                </h2>

                <p>
                  Resumen de la última modificación realizada.
                </p>
              </div>

            </div>


            <div
              className="patient-detail-changes"
            >

              {
                lastChanges.map(
                  (
                    change,
                    index,
                  ) => (

                    <div
                      key={
                        `${change.field}-${index}`
                      }
                      className="patient-detail-change"
                    >

                      <span
                        className="patient-detail-change__field"
                      >
                        {change.field}
                      </span>


                      <div>
                        <span>
                          Anterior
                        </span>

                        <strong>
                          {
                            change.old_value
                            ??
                            "—"
                          }
                        </strong>
                      </div>


                      <div>
                        <span>
                          Nuevo
                        </span>

                        <strong>
                          {
                            change.new_value
                            ??
                            "—"
                          }
                        </strong>
                      </div>

                    </div>

                  ),
                )
              }

            </div>

          </article>

        )
      }


      <PatientAuditHistory
        patientId={
          patient.id_patient
        }
      />

    </section>

  );

}