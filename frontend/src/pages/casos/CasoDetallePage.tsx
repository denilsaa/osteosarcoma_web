import {
  Activity,
  ArrowLeft,
  CalendarDays,
  CheckCircle2,
  CircleAlert,
  ClipboardList,
  ContactRound,
  FileImage,
  HeartPulse,
  IdCard,
  Image,
  LoaderCircle,
  ShieldCheck,
  Stethoscope,
  UserRound,
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
  getClinicalCase,
  type ClinicalCase,
} from "../../api/casos.api";

import {
  listarOncologos,
  type OncologoResumen,
} from "../../api/oncologos.api";

import {
  getPatient,
  resolvePatientPhotoUrl,
  type PatientDetail,
} from "../../api/pacientes.api";

import "./CasoDetallePage.css";


// ==========================================================
// TIPOS
// ==========================================================

type CaseTab =
  | "clinical"
  | "radiographies"
  | "followup";


// ==========================================================
// ESTADOS DEL CASO
// ==========================================================

const CASE_STATUS_FLOW = [
  {
    code:
      "REGISTRADO",

    name:
      "Registrado",
  },
  {
    code:
      "PENDIENTE",

    name:
      "Pendiente",
  },
  {
    code:
      "EN_ANALISIS",

    name:
      "En análisis",
  },
  {
    code:
      "REVISADO",

    name:
      "Revisado",
  },
  {
    code:
      "CERRADO",

    name:
      "Cerrado",
  },
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


function calculateAge(
  birthDate:
    string,
): number {

  const birth =
    new Date(
      `${birthDate}T00:00:00`,
    );


  const today =
    new Date();


  let age =
    today.getFullYear()
    -
    birth.getFullYear();


  const monthDifference =
    today.getMonth()
    -
    birth.getMonth();


  if (
    monthDifference < 0
    ||
    (
      monthDifference === 0
      &&
      today.getDate()
      <
      birth.getDate()
    )
  ) {

    age -= 1;

  }


  return Math.max(
    age,
    0,
  );

}


function relationshipName(
  value:
    string,
): string {

  const normalized =
    value.toUpperCase();


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

      OTRO:
        "Otro",

    };


  return (
    names[
      normalized
    ]
    ??
    value
  );

}


function priorityClass(
  code:
    string,
): string {

  switch (
    code.toUpperCase()
  ) {

    case "URGENTE":
      return (
        "case-detail-priority case-detail-priority--urgent"
      );


    case "ALTA":
      return (
        "case-detail-priority case-detail-priority--high"
      );


    case "MEDIA":
      return (
        "case-detail-priority case-detail-priority--medium"
      );


    default:
      return (
        "case-detail-priority case-detail-priority--low"
      );

  }

}


function statusClass(
  code:
    string,
): string {

  switch (
    code.toUpperCase()
  ) {

    case "REGISTRADO":
      return (
        "case-detail-status case-detail-status--registered"
      );


    case "PENDIENTE":
      return (
        "case-detail-status case-detail-status--pending"
      );


    case "EN_ANALISIS":
      return (
        "case-detail-status case-detail-status--analysis"
      );


    case "REVISADO":
      return (
        "case-detail-status case-detail-status--reviewed"
      );


    case "CERRADO":
      return (
        "case-detail-status case-detail-status--closed"
      );


    default:
      return (
        "case-detail-status"
      );

  }

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

    const response =
      (
        error as {
          response?: {
            data?: {
              error?: string;
              detail?: string;
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
      "string"
    ) {

      return (
        response
          .data
          .error
      );

    }


    if (
      typeof response
        ?.data
        ?.detail
      ===
      "string"
    ) {

      return (
        response
          .data
          .detail
      );

    }

  }


  return (
    "No fue posible cargar el detalle del caso clínico."
  );

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function CasoDetallePage() {

  const navigate =
    useNavigate();


  const {
    id,
  } = useParams<{
    id:
      string;
  }>();


  // ========================================================
  // DATOS
  // ========================================================

  const [
    clinicalCase,
    setClinicalCase,
  ] =
    useState<
      ClinicalCase | null
    >(
      null,
    );


  const [
    patient,
    setPatient,
  ] =
    useState<
      PatientDetail | null
    >(
      null,
    );


  const [
    oncologists,
    setOncologists,
  ] =
    useState<
      OncologoResumen[]
    >(
      [],
    );


  // ========================================================
  // UI
  // ========================================================

  const [
    activeTab,
    setActiveTab,
  ] =
    useState<CaseTab>(
      "clinical",
    );


  const [
    loading,
    setLoading,
  ] =
    useState(
      true,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(
      null,
    );


  // ========================================================
  // CARGAR
  // ========================================================

  useEffect(
    () => {

      if (!id) {

        setError(
          "No se recibió un identificador válido del caso.",
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

          const caseData =
            await getClinicalCase(
              id!,
            );


          const [
            patientData,
            oncologistData,
          ] =
            await Promise.all(
              [
                getPatient(
                  caseData.patient_id,
                ),

                listarOncologos(
                  "",
                  "ACTIVO",
                  "",
                ),
              ],
            );


          if (!mounted) {

            return;

          }


          setClinicalCase(
            caseData,
          );


          setPatient(
            patientData,
          );


          setOncologists(
            oncologistData
              .resultados,
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
  // MÉDICO RESPONSABLE
  // ========================================================

  const responsibleName =
    useMemo(
      () => {

        if (
          !clinicalCase
            ?.responsible_oncologist_uuid
        ) {

          return (
            "Sin asignar"
          );

        }


        const found =
          oncologists
            .find(
              (
                oncologist,
              ) =>
                oncologist.id_usuario
                ===
                clinicalCase
                  .responsible_oncologist_uuid,
            );


        return (
          found
            ?.nombre_completo
          ??
          "Profesional asignado"
        );

      },
      [
        clinicalCase,
        oncologists,
      ],
    );


  // ========================================================
  // DOCUMENTO
  // ========================================================

  const primaryDocument =
    useMemo(
      () =>
        patient
          ?.documents
          ?.[0]
        ??
        null,
      [
        patient,
      ],
    );


  // ========================================================
  // CONTACTO
  // ========================================================

  const primaryContact =
    useMemo(
      () =>
        patient
          ?.contacts
          .find(
            (
              item,
            ) =>
              item.primary,
          )
        ??
        patient
          ?.contacts
          ?.[0]
        ??
        null,
      [
        patient,
      ],
    );


  // ========================================================
  // EMERGENCIA
  // ========================================================

  const emergencyContact =
    useMemo(
      () =>
        patient
          ?.primary_emergency_contact
        ??
        patient
          ?.emergency_contacts
          .find(
            (
              item,
            ) =>
              item.primary,
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
  // FOTO
  // ========================================================

  const patientPhoto =
    useMemo(
      () =>
        resolvePatientPhotoUrl(
          patient
            ?.photo_url,
        ),
      [
        patient,
      ],
    );


  // ========================================================
  // ESTADO ACTUAL
  // ========================================================

  const currentStatusIndex =
    useMemo(
      () => {

        if (
          !clinicalCase
        ) {

          return 0;

        }


        const index =
          CASE_STATUS_FLOW
            .findIndex(
              (
                item,
              ) =>
                item.code
                ===
                clinicalCase
                  .status
                  .code,
            );


        return (
          index >= 0
            ? index
            : 0
        );

      },
      [
        clinicalCase,
      ],
    );


  // ========================================================
  // LOADING
  // ========================================================

  if (
    loading
  ) {

    return (

      <div
        className="case-detail-loading"
      >

        <LoaderCircle
          size={31}
          className="case-detail-spin"
        />


        <span>
          Cargando caso clínico...
        </span>

      </div>

    );

  }


  // ========================================================
  // ERROR
  // ========================================================

  if (
    !clinicalCase
    ||
    !patient
  ) {

    return (

      <section
        className="case-detail-page"
      >

        <div
          className="case-detail-error"
        >

          <CircleAlert
            size={20}
          />


          <span>
            {
              error
              ??
              "No fue posible cargar el caso clínico."
            }
          </span>

        </div>


        <button
          type="button"
          className="case-detail-return"
          onClick={
            () =>
              navigate(
                "/casos",
              )
          }
        >

          <ArrowLeft
            size={17}
          />

          Volver a casos clínicos

        </button>

      </section>

    );

  }


  const age =
    calculateAge(
      patient.birth_date,
    );


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="case-detail-page"
    >

      {/* ==================================================
          BREADCRUMB
          ================================================== */}

      <div
        className="case-detail-breadcrumb"
      >

        <button
          type="button"
          onClick={
            () =>
              navigate(
                "/casos",
              )
          }
        >
          Casos clínicos
        </button>


        <span>
          /
        </span>


        <strong>
          {clinicalCase.code}
        </strong>

      </div>


      {/* ==================================================
          PACIENTE
          ================================================== */}

      <article
        className="case-detail-patient-card"
      >

        <div
          className="case-detail-patient-main"
        >

          <button
            type="button"
            className="case-detail-back"
            onClick={
              () =>
                navigate(
                  "/casos",
                )
            }
          >
            <ArrowLeft
              size={18}
            />
          </button>


          <div
            className="case-detail-avatar"
          >

            {
              patientPhoto
                ? (

                    <img
                      src={
                        patientPhoto
                      }
                      alt={
                        patient.full_name
                      }
                    />

                  )
                : (

                    <UserRound
                      size={42}
                    />

                  )
            }

          </div>


          <div
            className="case-detail-patient-identity"
          >

            <span
              className="case-detail-eyebrow"
            >
              Paciente
            </span>


            <h1>
              {patient.full_name}
            </h1>


            <div
              className="case-detail-patient-document"
            >

              <strong>
                {
                  primaryDocument
                    ?.document_type_code
                  ??
                  "Documento"
                }
                {": "}
                {
                  primaryDocument
                    ?.document_number
                  ??
                  "Sin registro"
                }
              </strong>


              {
                primaryDocument
                  ?.complement
                &&
                (
                  <strong>
                    {
                      primaryDocument
                        .complement
                    }
                  </strong>
                )
              }

            </div>


            <div
              className="case-detail-patient-basic"
            >

              <span>
                {age} años
              </span>

              <i />

              <span>
                {patient.sex.name}
              </span>

              <i />

              <span>
                Nacimiento:{" "}
                {
                  formatDate(
                    patient.birth_date,
                  )
                }
              </span>

            </div>

          </div>

        </div>


        <div
          className="case-detail-patient-contact"
        >

          <div>

            <span>
              Teléfono
            </span>

            <strong>
              {
                primaryContact
                  ?.value
                ??
                "Sin registro"
              }
            </strong>

          </div>


          <div>

            <span>
              Contacto de emergencia
            </span>

            <strong>

              {
                emergencyContact
                  ? (
                      <>
                        {
                          emergencyContact
                            .full_name
                        }
                        {" · "}
                        {
                          relationshipName(
                            emergencyContact
                              .relationship,
                          )
                        }
                        {" · "}
                        {
                          emergencyContact
                            .phone
                        }
                      </>
                    )
                  : (
                      "Sin registro"
                    )
              }

            </strong>

          </div>


          <div>

            <span>
              Médico responsable
            </span>

            <strong>
              {responsibleName}
            </strong>

          </div>

        </div>


        <div
          className="case-detail-patient-actions"
        >

          <span
            className={
              patient.active
                ? "case-detail-patient-active"
                : "case-detail-patient-inactive"
            }
          >

            {
              patient.active
                ? "Paciente activo"
                : "Paciente inactivo"
            }

          </span>


          <button
            type="button"
            onClick={
              () =>
                navigate(
                  `/pacientes/${patient.id_patient}`,
                )
            }
          >

            <IdCard
              size={16}
            />

            Ver ficha completa

          </button>

        </div>

      </article>


      {/* ==================================================
          TABS
          ================================================== */}

      <nav
        className="case-detail-tabs"
      >

        <button
          type="button"
          className={
            activeTab ===
            "clinical"
              ? "case-detail-tab case-detail-tab--active"
              : "case-detail-tab"
          }
          onClick={
            () =>
              setActiveTab(
                "clinical",
              )
          }
        >

          <HeartPulse
            size={18}
          />

          Información clínica

        </button>


        <button
          type="button"
          className={
            activeTab ===
            "radiographies"
              ? "case-detail-tab case-detail-tab--active"
              : "case-detail-tab"
          }
          onClick={
            () =>
              setActiveTab(
                "radiographies",
              )
          }
        >

          <Image
            size={18}
          />

          Radiografías

        </button>


        <button
          type="button"
          className={
            activeTab ===
            "followup"
              ? "case-detail-tab case-detail-tab--active"
              : "case-detail-tab"
          }
          onClick={
            () =>
              setActiveTab(
                "followup",
              )
          }
        >

          <Activity
            size={18}
          />

          Seguimiento

        </button>

      </nav>


      {/* ==================================================
          INFORMACIÓN CLÍNICA
          ================================================== */}

      {
        activeTab ===
        "clinical"
        &&
        (

          <div
            className="case-detail-clinical-grid"
          >

            <div
              className="case-detail-clinical-column"
            >

              {/* DATOS DEL CASO */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <ClipboardList
                      size={20}
                    />
                  </div>


                  <h2>
                    1. Datos del caso
                  </h2>

                </header>


                <div
                  className="case-detail-data-grid"
                >

                  <div>

                    <span>
                      Código del caso
                    </span>

                    <strong>
                      {clinicalCase.code}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Fecha de registro
                    </span>

                    <strong>
                      {
                        formatDate(
                          clinicalCase
                            .opening_date,
                        )
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Médico responsable
                    </span>

                    <strong>
                      {responsibleName}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Prioridad
                    </span>

                    <strong>

                      <span
                        className={
                          priorityClass(
                            clinicalCase
                              .priority
                              .code,
                          )
                        }
                      >
                        {
                          clinicalCase
                            .priority
                            .name
                        }
                      </span>

                    </strong>

                  </div>


                  <div>

                    <span>
                      Estado
                    </span>

                    <strong>

                      <span
                        className={
                          statusClass(
                            clinicalCase
                              .status
                              .code,
                          )
                        }
                      >
                        {
                          clinicalCase
                            .status
                            .name
                        }
                      </span>

                    </strong>

                  </div>


                  <div>

                    <span>
                      Servicio / Área
                    </span>

                    <strong>
                      Oncología
                    </strong>

                  </div>

                </div>

              </article>


              {/* MOTIVO */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <Stethoscope
                      size={20}
                    />
                  </div>


                  <h2>
                    2. Motivo de consulta
                  </h2>

                </header>


                <div
                  className="case-detail-text-box"
                >
                  {
                    clinicalCase
                      .consultation_reason
                  }
                </div>

              </article>


              {/* ANTECEDENTES */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <ShieldCheck
                      size={20}
                    />
                  </div>


                  <h2>
                    3. Antecedentes relevantes
                  </h2>

                </header>


                <div
                  className="case-detail-coming"
                >

                  <ShieldCheck
                    size={27}
                  />


                  <div>

                    <strong>
                      Sin antecedentes registrados
                    </strong>


                    <span>
                      Aquí se mostrarán antecedentes
                      personales, familiares, quirúrgicos
                      y otros registros clínicos con
                      autor y fecha.
                    </span>

                  </div>

                </div>

              </article>


              {/* SIGNOS Y SÍNTOMAS */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <Activity
                      size={20}
                    />
                  </div>


                  <h2>
                    4. Signos y síntomas
                  </h2>

                </header>


                <div
                  className="case-detail-coming"
                >

                  <Activity
                    size={27}
                  />


                  <div>

                    <strong>
                      Sin signos o síntomas registrados
                    </strong>


                    <span>
                      Este apartado será conectado con
                      los registros clínicos del caso.
                    </span>

                  </div>

                </div>

              </article>

            </div>


            <div
              className="case-detail-clinical-column"
            >

              {/* OBSERVACIONES */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <FileImage
                      size={20}
                    />
                  </div>


                  <h2>
                    5. Observaciones iniciales
                  </h2>

                </header>


                <div
                  className="case-detail-text-box case-detail-text-box--large"
                >

                  {
                    clinicalCase
                      .general_observation
                    ??
                    "No se registraron observaciones generales en la apertura del caso."
                  }

                </div>


                <footer
                  className="case-detail-record-meta"
                >

                  <Stethoscope
                    size={15}
                  />

                  <span>
                    Registrado por{" "}
                    <strong>
                      {responsibleName}
                    </strong>
                  </span>


                  <CalendarDays
                    size={15}
                  />

                  <span>
                    {
                      formatDateTime(
                        clinicalCase
                          .opening_date,
                      )
                    }
                  </span>

                </footer>

              </article>


              {/* ESTADO */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <Activity
                      size={20}
                    />
                  </div>


                  <h2>
                    Estado actual
                  </h2>

                </header>


                <div
                  className="case-detail-current-state"
                >

                  <span
                    className={
                      statusClass(
                        clinicalCase
                          .status
                          .code,
                      )
                    }
                  >
                    {
                      clinicalCase
                        .status
                        .name
                    }
                  </span>


                  <p>
                    El caso se encuentra actualmente
                    en esta etapa del flujo clínico.
                  </p>

                </div>

              </article>


              {/* RESUMEN */}

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <ContactRound
                      size={20}
                    />
                  </div>


                  <h2>
                    Resumen de atención
                  </h2>

                </header>


                <div
                  className="case-detail-summary-list"
                >

                  <div>

                    <span>
                      Paciente
                    </span>

                    <strong>
                      {patient.full_name}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Médico
                    </span>

                    <strong>
                      {responsibleName}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Apertura
                    </span>

                    <strong>
                      {
                        formatDateTime(
                          clinicalCase
                            .opening_date,
                        )
                      }
                    </strong>

                  </div>


                  <div>

                    <span>
                      Cierre
                    </span>

                    <strong>
                      {
                        formatDateTime(
                          clinicalCase
                            .closing_date,
                        )
                      }
                    </strong>

                  </div>

                </div>

              </article>

            </div>

          </div>

        )
      }


      {/* ==================================================
          RADIOGRAFÍAS
          ================================================== */}

      {
        activeTab ===
        "radiographies"
        &&
        (

          <article
            className="case-detail-section case-detail-full-section"
          >

            <header
              className="case-detail-section-header-actions"
            >

              <div
                className="case-detail-section-header-title"
              >

                <div>
                  <Image
                    size={20}
                  />
                </div>


                <div>

                  <h2>
                    Radiografías del caso
                  </h2>


                  <p>
                    Estudios radiográficos asociados
                    exclusivamente a este caso clínico.
                  </p>

                </div>

              </div>


              <button
                type="button"
                className="case-detail-primary-button"
                disabled
              >

                Registrar radiografía

              </button>

            </header>


            <div
              className="case-detail-coming case-detail-coming--large"
            >

              <Image
                size={38}
              />


              <div>

                <strong>
                  Integración de radiografías pendiente
                </strong>


                <span>
                  En el siguiente paso conectaremos el
                  servicio de radiografías para mostrar
                  fecha, zona anatómica, lateralidad,
                  observaciones y archivo privado.
                </span>

              </div>

            </div>

          </article>

        )
      }


      {/* ==================================================
          SEGUIMIENTO
          ================================================== */}

      {
        activeTab ===
        "followup"
        &&
        (

          <div
            className="case-detail-followup"
          >

            <article
              className="case-detail-section"
            >

              <header>

                <div>
                  <Activity
                    size={20}
                  />
                </div>


                <h2>
                  Línea de tiempo del caso
                </h2>

              </header>


              <div
                className="case-detail-timeline"
              >

                {
                  CASE_STATUS_FLOW
                    .map(
                      (
                        item,
                        index,
                      ) => {

                        const completed =
                          index
                          <
                          currentStatusIndex;


                        const current =
                          index
                          ===
                          currentStatusIndex;


                        return (

                          <div
                            key={
                              item.code
                            }
                            className={
                              current
                                ? "case-detail-timeline-step case-detail-timeline-step--current"
                                : completed
                                  ? "case-detail-timeline-step case-detail-timeline-step--completed"
                                  : "case-detail-timeline-step"
                            }
                          >

                            <div
                              className="case-detail-timeline-marker"
                            >

                              {
                                completed
                                  ? (
                                      <CheckCircle2
                                        size={22}
                                      />
                                    )
                                  : (
                                      <span />
                                    )
                              }

                            </div>


                            <strong>
                              {item.name}
                            </strong>


                            <span>
                              {
                                item.code
                                ===
                                "REGISTRADO"
                                  ? formatDate(
                                      clinicalCase
                                        .opening_date,
                                    )
                                  : item.code
                                    ===
                                    "CERRADO"
                                    &&
                                    clinicalCase
                                      .closing_date
                                      ? formatDate(
                                          clinicalCase
                                            .closing_date,
                                        )
                                      : "—"
                              }
                            </span>

                          </div>

                        );

                      },
                    )
                }

              </div>

            </article>


            <div
              className="case-detail-followup-grid"
            >

              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <ClipboardList
                      size={20}
                    />
                  </div>


                  <h2>
                    Historial del caso
                  </h2>

                </header>


                <div
                  className="case-detail-history-row"
                >

                  <div
                    className="case-detail-history-dot"
                  />


                  <div>

                    <strong>
                      Caso clínico registrado
                    </strong>


                    <span>
                      {
                        formatDateTime(
                          clinicalCase
                            .opening_date,
                        )
                      }
                    </span>


                    <p>
                      Apertura del caso clínico.
                    </p>

                  </div>

                </div>

              </article>


              <article
                className="case-detail-section"
              >

                <header>

                  <div>
                    <ShieldCheck
                      size={20}
                    />
                  </div>


                  <h2>
                    Estado actual
                  </h2>

                </header>


                <div
                  className="case-detail-current-state"
                >

                  <span
                    className={
                      statusClass(
                        clinicalCase
                          .status
                          .code,
                      )
                    }
                  >
                    {
                      clinicalCase
                        .status
                        .name
                    }
                  </span>


                  <p>
                    Próximamente habilitaremos aquí
                    el avance controlado al siguiente
                    estado del flujo clínico.
                  </p>

                </div>

              </article>

            </div>

          </div>

        )
      }

    </section>

  );

}