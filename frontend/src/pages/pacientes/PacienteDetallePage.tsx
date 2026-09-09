import {
  Activity,
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  ContactRound,
  Edit3,
  IdCard,
  LoaderCircle,
  Save,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  getPatient,
  getPatientCatalogs,
  updatePatient,
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
  Record<string, string> = {

    LP: "La Paz",

    CB: "Cochabamba",

    SC: "Santa Cruz",

    OR: "Oruro",

    PT: "Potosí",

    CH: "Chuquisaca",

    TJ: "Tarija",

    BE: "Beni",

    PD: "Pando",

  };


// ==========================================================
// HELPERS
// ==========================================================

function formatDate(
  value?: string | null,
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


  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day: "2-digit",

      month: "2-digit",

      year: "numeric",
    },
  ).format(
    date,
  );

}


function formatDateTime(
  value?: string | null,
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
      day: "2-digit",

      month: "2-digit",

      year: "numeric",

      hour: "2-digit",

      minute: "2-digit",
    },
  ).format(
    date,
  );

}


function normalizeText(
  value: string,
): string {

  return value
    .trim()
    .replace(
      /\s+/g,
      " ",
    );

}


function departmentName(
  code?: string | null,
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


function extractErrorMessage(
  error: unknown,
): string {

  if (
    typeof error === "object"
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

            detail?: string;
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


  const {
    id,
  } = useParams<{
    id: string;
  }>();


  // ========================================================
  // ESTADO
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
            catalogData,
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
  // CONTACTO EMERGENCIA PRINCIPAL
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


  // ========================================================
  // CANCELAR EDICIÓN
  // ========================================================

  function cancelEditing() {

    setEditing(
      false,
    );


    setError(
      null,
    );

  }


  // ========================================================
  // ACTUALIZAR INPUT
  // ========================================================

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


    // ======================================================
    // VALIDACIONES
    // ======================================================

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

  if (
    !patient
  ) {

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


      {/* ==================================================
          MENSAJE ERROR
          ================================================== */}

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


      {/* ==================================================
          MENSAJE ÉXITO
          ================================================== */}

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


      {/* ==================================================
          KPIS
          ================================================== */}

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
                patient
                  .registration_date,
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
                        editForm
                          .first_names
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "first_names",
                            event
                              .target
                              .value,
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
                        editForm
                          .paternal_surname
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "paternal_surname",
                            event
                              .target
                              .value,
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
                        editForm
                          .maternal_surname
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "maternal_surname",
                            event
                              .target
                              .value,
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
                        editForm
                          .birth_date
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "birth_date",
                            event
                              .target
                              .value,
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
                        editForm
                          .sex_id
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "sex_id",
                            event
                              .target
                              .value,
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

                                {
                                  item.name
                                }

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
                        editForm
                          .active
                          ? "true"
                          : "false"
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "active",
                            event
                              .target
                              .value
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
                        editForm
                          .reason
                      }
                      onChange={
                        (
                          event,
                        ) =>
                          updateField(
                            "reason",
                            event
                              .target
                              .value,
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

                {/* ==========================================
                    DATOS PERSONALES
                    ========================================== */}

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
                        {
                          patient
                            .first_names
                        }
                      </strong>

                    </div>


                    <div>

                      <span>
                        Apellido paterno
                      </span>


                      <strong>
                        {
                          patient
                            .paternal_surname
                        }
                      </strong>

                    </div>


                    <div>

                      <span>
                        Apellido materno
                      </span>


                      <strong>
                        {
                          patient
                            .maternal_surname
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
                            patient
                              .birth_date,
                          )
                        }
                      </strong>

                    </div>


                    <div>

                      <span>
                        Sexo
                      </span>


                      <strong>
                        {
                          patient
                            .sex
                            .name
                        }
                      </strong>

                    </div>


                    <div>

                      <span>
                        Identificador
                      </span>


                      <strong
                        className="patient-detail-uuid"
                      >

                        {
                          patient
                            .id_patient
                        }

                      </strong>

                    </div>

                  </div>

                </article>


                {/* ==========================================
                    DOCUMENTO + CONTACTOS
                    ========================================== */}

                <div
                  className="patient-detail-two-columns"
                >

                  {/* ========================================
                      DOCUMENTO
                      ======================================== */}

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


                  {/* ========================================
                      CONTACTOS DEL PACIENTE
                      ======================================== */}

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
                      patient
                        .contacts
                        .length > 0
                        ? (

                            <div
                              className="patient-detail-contact-list"
                            >

                              {
                                patient
                                  .contacts
                                  .map(
                                    (
                                      contact,
                                    ) => (

                                      <div
                                        key={
                                          contact
                                            .id_contact
                                          ??
                                          `${contact.contact_type_code}-${contact.value}`
                                        }
                                        className="patient-detail-contact-item"
                                      >

                                        <div>

                                          <span>
                                            {
                                              contact
                                                .contact_type_name
                                            }
                                          </span>


                                          <strong>
                                            {
                                              contact
                                                .value
                                            }
                                          </strong>

                                        </div>


                                        {
                                          contact
                                            .primary
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


                {/* ==========================================
                    CONTACTO EMERGENCIA
                    ========================================== */}

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
                        Contacto de emergencia
                      </h2>


                      <p>
                        Familiar, tutor o responsable del paciente.
                      </p>

                    </div>

                  </div>


                  {
                    patient
                      .emergency_contacts
                      .length > 0
                      ? (

                          <div
                            className="patient-detail-emergency-list"
                          >

                            {
                              patient
                                .emergency_contacts
                                .map(
                                  (
                                    contact,
                                  ) => (

                                    <div
                                      key={
                                        contact
                                          .id_emergency_contact
                                        ??
                                        `${contact.full_name}-${contact.phone}`
                                      }
                                      className={
                                        contact
                                          .primary
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
                                            contact
                                              .full_name
                                              .charAt(
                                                0,
                                              )
                                              .toUpperCase()
                                          }

                                        </div>


                                        <div>

                                          <strong>
                                            {
                                              contact
                                                .full_name
                                            }
                                          </strong>


                                          <span>
                                            {
                                              contact
                                                .relationship
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
                                            {
                                              contact
                                                .phone
                                            }
                                          </strong>

                                        </div>


                                        <div>

                                          <span>
                                            Correo
                                          </span>


                                          <strong>
                                            {
                                              contact
                                                .email
                                              ??
                                              "—"
                                            }
                                          </strong>

                                        </div>

                                      </div>


                                      {
                                        contact
                                          .primary
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
                              un familiar o responsable de emergencia registrado.
                            </span>

                          </div>

                        )
                  }

                </article>


                {/* ==========================================
                    RESUMEN CONTACTO PRINCIPAL
                    ========================================== */}

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
                                {
                                  primaryContact
                                    .value
                                }
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
                                {
                                  primaryEmergencyContact
                                    .full_name
                                }
                                {" · "}
                                {
                                  primaryEmergencyContact
                                    .phone
                                }
                              </strong>

                            </div>

                          </div>

                        )
                      }

                    </div>

                  )
                }


                {/* ==========================================
                    CASOS CLÍNICOS
                    ========================================== */}

                <PatientClinicalCases
                  patientId={
                    patient
                      .id_patient
                  }
                />


                {/* ==========================================
                    RADIOGRAFÍAS
                    ========================================== */}

                <PatientRadiographies
                  patientId={
                    patient
                      .id_patient
                  }
                />

              </>

            )
      }


      {/* ==================================================
          ÚLTIMO CAMBIO
          ================================================== */}

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

                        {
                          change.field
                        }

                      </span>


                      <div>

                        <span>
                          Anterior
                        </span>


                        <strong>
                          {
                            change
                              .old_value
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
                            change
                              .new_value
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


      {/* ==================================================
          AUDITORÍA
          ================================================== */}

      <PatientAuditHistory
        patientId={
          patient
            .id_patient
        }
      />

    </section>

  );

}