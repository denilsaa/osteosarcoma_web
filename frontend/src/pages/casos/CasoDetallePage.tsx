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
  Plus,
  Save,
  ShieldCheck,
  Stethoscope,
  UserRound,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useParams,
} from "react-router-dom";

import {
  createClinicalAntecedent,
  createClinicalObservation,
  createClinicalSign,
  createClinicalSymptom,
  getClinicalAntecedents,
  getClinicalCase,
  getClinicalCaseCatalogs,
  getClinicalObservations,
  getClinicalSigns,
  getClinicalSymptoms,
  type ClinicalAntecedent,
  type ClinicalCase,
  type ClinicalCaseCatalogs,
  type ClinicalObservation,
  type ClinicalSign,
  type ClinicalSymptom,
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


type ClinicalForm =
  | "antecedent"
  | "symptom"
  | "sign"
  | "observation"
  | null;


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
      return response.data.error;
    }


    if (
      typeof response
        ?.data
        ?.detail
      ===
      "string"
    ) {
      return response.data.detail;
    }

  }


  return (
    "No fue posible completar la operación."
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
  // DATOS PRINCIPALES
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


  const [
    catalogs,
    setCatalogs,
  ] =
    useState<
      ClinicalCaseCatalogs | null
    >(
      null,
    );


  const [
    antecedents,
    setAntecedents,
  ] =
    useState<
      ClinicalAntecedent[]
    >(
      [],
    );


  const [
    symptoms,
    setSymptoms,
  ] =
    useState<
      ClinicalSymptom[]
    >(
      [],
    );


  const [
    signs,
    setSigns,
  ] =
    useState<
      ClinicalSign[]
    >(
      [],
    );


  const [
    observations,
    setObservations,
  ] =
    useState<
      ClinicalObservation[]
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
    activeForm,
    setActiveForm,
  ] =
    useState<ClinicalForm>(
      null,
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
    error,
    setError,
  ] =
    useState<
      string | null
    >(
      null,
    );


  const [
    success,
    setSuccess,
  ] =
    useState<
      string | null
    >(
      null,
    );


  // ========================================================
  // FORMULARIOS
  // ========================================================

  const [
    antecedentTypeId,
    setAntecedentTypeId,
  ] =
    useState(
      "",
    );


  const [
    antecedentDescription,
    setAntecedentDescription,
  ] =
    useState(
      "",
    );


  const [
    symptomId,
    setSymptomId,
  ] =
    useState(
      "",
    );


  const [
    intensityId,
    setIntensityId,
  ] =
    useState(
      "",
    );


  const [
    symptomStartDate,
    setSymptomStartDate,
  ] =
    useState(
      "",
    );


  const [
    symptomObservation,
    setSymptomObservation,
  ] =
    useState(
      "",
    );


  const [
    signId,
    setSignId,
  ] =
    useState(
      "",
    );


  const [
    signDescription,
    setSignDescription,
  ] =
    useState(
      "",
    );


  const [
    observationContent,
    setObservationContent,
  ] =
    useState(
      "",
    );


  // ========================================================
  // CARGAR INFORMACIÓN CLÍNICA
  // ========================================================

  const loadClinicalInformation =
    useCallback(
      async (
        caseId:
          string,
      ) => {

        const [
          antecedentResponse,
          symptomResponse,
          signResponse,
          observationResponse,
        ] =
          await Promise.all(
            [
              getClinicalAntecedents(
                caseId,
              ),

              getClinicalSymptoms(
                caseId,
              ),

              getClinicalSigns(
                caseId,
              ),

              getClinicalObservations(
                caseId,
              ),
            ],
          );


        setAntecedents(
          antecedentResponse.data,
        );


        setSymptoms(
          symptomResponse.data,
        );


        setSigns(
          signResponse.data,
        );


        setObservations(
          observationResponse.data,
        );

      },
      [],
    );


  // ========================================================
  // CARGAR TODO
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
            catalogData,
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

                getClinicalCaseCatalogs(),
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


          setCatalogs(
            catalogData,
          );


          await loadClinicalInformation(
            id!,
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
      loadClinicalInformation,
    ],
  );


  // ========================================================
  // AUTOR
  // ========================================================

  const getAuthorName =
    useCallback(
      (
        authorUuid?:
          string | null,
      ): string => {

        if (!authorUuid) {
          return "Autor no identificado";
        }


        const found =
          oncologists
            .find(
              (
                oncologist,
              ) =>
                oncologist.id_usuario
                ===
                authorUuid,
            );


        if (
          found
            ?.nombre_completo
        ) {

          return (
            found.nombre_completo
          );

        }


        return (
          `Usuario ${authorUuid.slice(0, 8)}`
        );

      },
      [
        oncologists,
      ],
    );


  // ========================================================
  // RESPONSABLE
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


        return (
          getAuthorName(
            clinicalCase
              .responsible_oncologist_uuid,
          )
        );

      },
      [
        clinicalCase,
        getAuthorName,
      ],
    );


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
  // MENSAJES
  // ========================================================

  function showSuccess(
    message:
      string,
  ) {

    setSuccess(
      message,
    );


    setError(
      null,
    );


    window.setTimeout(
      () => {

        setSuccess(
          null,
        );

      },
      3200,
    );

  }


  // ========================================================
  // GUARDAR ANTECEDENTE
  // ========================================================

  async function handleSaveAntecedent() {

    if (
      !id
      ||
      !antecedentTypeId
    ) {

      setError(
        "Seleccione el tipo de antecedente.",
      );

      return;

    }


    if (
      antecedentDescription
        .trim()
        .length
      <
      3
    ) {

      setError(
        "Ingrese una descripción válida.",
      );

      return;

    }


    setSaving(
      true,
    );


    try {

      await createClinicalAntecedent(
        id,
        {
          antecedent_type_id:
            Number(
              antecedentTypeId,
            ),

          description:
            antecedentDescription
              .trim(),
        },
      );


      setAntecedentTypeId(
        "",
      );


      setAntecedentDescription(
        "",
      );


      setActiveForm(
        null,
      );


      await loadClinicalInformation(
        id,
      );


      showSuccess(
        "Antecedente registrado correctamente.",
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
  // GUARDAR SÍNTOMA
  // ========================================================

  async function handleSaveSymptom() {

    if (
      !id
      ||
      !symptomId
    ) {

      setError(
        "Seleccione un síntoma.",
      );

      return;

    }


    setSaving(
      true,
    );


    try {

      await createClinicalSymptom(
        id,
        {
          symptom_id:
            Number(
              symptomId,
            ),

          intensity_id:
            intensityId
              ? Number(
                  intensityId,
                )
              : null,

          start_date:
            symptomStartDate
              ||
              null,

          observation:
            symptomObservation
              .trim()
              ||
              null,
        },
      );


      setSymptomId(
        "",
      );


      setIntensityId(
        "",
      );


      setSymptomStartDate(
        "",
      );


      setSymptomObservation(
        "",
      );


      setActiveForm(
        null,
      );


      await loadClinicalInformation(
        id,
      );


      showSuccess(
        "Síntoma registrado correctamente.",
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
  // GUARDAR SIGNO
  // ========================================================

  async function handleSaveSign() {

    if (
      !id
      ||
      !signId
    ) {

      setError(
        "Seleccione un signo clínico.",
      );

      return;

    }


    setSaving(
      true,
    );


    try {

      await createClinicalSign(
        id,
        {
          sign_id:
            Number(
              signId,
            ),

          finding_description:
            signDescription
              .trim()
              ||
              null,
        },
      );


      setSignId(
        "",
      );


      setSignDescription(
        "",
      );


      setActiveForm(
        null,
      );


      await loadClinicalInformation(
        id,
      );


      showSuccess(
        "Signo registrado correctamente.",
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
  // GUARDAR OBSERVACIÓN
  // ========================================================

  async function handleSaveObservation() {

    if (!id) {
      return;
    }


    if (
      observationContent
        .trim()
        .length
      <
      3
    ) {

      setError(
        "Ingrese una observación válida.",
      );

      return;

    }


    setSaving(
      true,
    );


    try {

      await createClinicalObservation(
        id,
        {
          content:
            observationContent
              .trim(),
        },
      );


      setObservationContent(
        "",
      );


      setActiveForm(
        null,
      );


      await loadClinicalInformation(
        id,
      );


      showSuccess(
        "Observación registrada correctamente.",
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
  // ERROR DE CARGA
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

      {
        error
        &&
        (

          <div
            className="case-detail-error"
          >

            <CircleAlert
              size={19}
            />

            <span>
              {error}
            </span>


            <button
              type="button"
              onClick={
                () =>
                  setError(
                    null,
                  )
              }
            >
              <X
                size={17}
              />
            </button>

          </div>

        )
      }


      {
        success
        &&
        (

          <div
            className="case-detail-success"
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
                  : "Sin registro"
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
                  </div>


                  <div>
                    <span>
                      Estado
                    </span>

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


              {/* ==================================================
                  ANTECEDENTES
                  ================================================== */}

              <article
                className="case-detail-section"
              >

                <header
                  className="case-detail-section-header-actions"
                >

                  <div
                    className="case-detail-section-header-title"
                  >
                    <div>
                      <ShieldCheck
                        size={20}
                      />
                    </div>

                    <div>
                      <h2>
                        3. Antecedentes relevantes
                      </h2>

                      <p>
                        {
                          antecedents.length
                        } registro(s)
                      </p>
                    </div>
                  </div>


                  <button
                    type="button"
                    className="case-detail-add-button"
                    onClick={
                      () =>
                        setActiveForm(
                          activeForm ===
                          "antecedent"
                            ? null
                            : "antecedent",
                        )
                    }
                  >
                    <Plus
                      size={16}
                    />

                    Registrar
                  </button>

                </header>


                {
                  activeForm ===
                  "antecedent"
                  &&
                  (

                    <div
                      className="case-detail-inline-form"
                    >

                      <label>
                        Tipo de antecedente *

                        <select
                          value={
                            antecedentTypeId
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setAntecedentTypeId(
                                event.target.value,
                              )
                          }
                        >
                          <option
                            value=""
                          >
                            Seleccione
                          </option>

                          {
                            catalogs
                              ?.antecedent_types
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


                      <label
                        className="case-detail-form-wide"
                      >
                        Descripción *

                        <textarea
                          rows={3}
                          value={
                            antecedentDescription
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setAntecedentDescription(
                                event.target.value,
                              )
                          }
                          placeholder="Detalle del antecedente clínico..."
                        />
                      </label>


                      <div
                        className="case-detail-form-actions"
                      >
                        <button
                          type="button"
                          className="case-detail-secondary-button"
                          onClick={
                            () =>
                              setActiveForm(
                                null,
                              )
                          }
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          className="case-detail-primary-button"
                          disabled={
                            saving
                          }
                          onClick={
                            () =>
                              void handleSaveAntecedent()
                          }
                        >
                          {
                            saving
                              ? (
                                  <LoaderCircle
                                    size={16}
                                    className="case-detail-spin"
                                  />
                                )
                              : (
                                  <Save
                                    size={16}
                                  />
                                )
                          }

                          Guardar
                        </button>
                      </div>

                    </div>

                  )
                }


                <div
                  className="case-detail-record-list"
                >

                  {
                    antecedents.length ===
                    0
                      ? (

                          <div
                            className="case-detail-empty"
                          >
                            <ShieldCheck
                              size={27}
                            />

                            <strong>
                              Sin antecedentes registrados
                            </strong>

                            <span>
                              Registre antecedentes personales,
                              familiares, quirúrgicos, alérgicos
                              u oncológicos.
                            </span>
                          </div>

                        )
                      : antecedents.map(
                          (
                            item,
                          ) => (

                            <div
                              key={
                                item.id_antecedent
                              }
                              className="case-detail-record"
                            >

                              <div
                                className="case-detail-record-top"
                              >
                                <strong>
                                  {item.type.name}
                                </strong>

                                <span>
                                  {
                                    formatDateTime(
                                      item.registered_at,
                                    )
                                  }
                                </span>
                              </div>


                              <p>
                                {item.description}
                              </p>


                              <div
                                className="case-detail-record-author"
                              >
                                <Stethoscope
                                  size={14}
                                />

                                {
                                  getAuthorName(
                                    item.author_uuid,
                                  )
                                }
                              </div>

                            </div>

                          ),
                        )
                  }

                </div>

              </article>


              {/* ==================================================
                  SÍNTOMAS
                  ================================================== */}

              <article
                className="case-detail-section"
              >

                <header
                  className="case-detail-section-header-actions"
                >

                  <div
                    className="case-detail-section-header-title"
                  >
                    <div>
                      <HeartPulse
                        size={20}
                      />
                    </div>

                    <div>
                      <h2>
                        4. Síntomas
                      </h2>

                      <p>
                        {
                          symptoms.length
                        } registro(s)
                      </p>
                    </div>
                  </div>


                  <button
                    type="button"
                    className="case-detail-add-button"
                    onClick={
                      () =>
                        setActiveForm(
                          activeForm ===
                          "symptom"
                            ? null
                            : "symptom",
                        )
                    }
                  >
                    <Plus
                      size={16}
                    />

                    Registrar
                  </button>

                </header>


                {
                  activeForm ===
                  "symptom"
                  &&
                  (

                    <div
                      className="case-detail-inline-form"
                    >

                      <label>
                        Síntoma *

                        <select
                          value={
                            symptomId
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setSymptomId(
                                event.target.value,
                              )
                          }
                        >
                          <option
                            value=""
                          >
                            Seleccione
                          </option>

                          {
                            catalogs
                              ?.symptoms
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
                        Intensidad

                        <select
                          value={
                            intensityId
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setIntensityId(
                                event.target.value,
                              )
                          }
                        >
                          <option
                            value=""
                          >
                            Sin especificar
                          </option>

                          {
                            catalogs
                              ?.intensity_levels
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
                        Fecha de inicio

                        <input
                          type="date"
                          value={
                            symptomStartDate
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setSymptomStartDate(
                                event.target.value,
                              )
                          }
                        />
                      </label>


                      <label
                        className="case-detail-form-wide"
                      >
                        Observación

                        <textarea
                          rows={3}
                          value={
                            symptomObservation
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setSymptomObservation(
                                event.target.value,
                              )
                          }
                          placeholder="Descripción adicional del síntoma..."
                        />
                      </label>


                      <div
                        className="case-detail-form-actions"
                      >
                        <button
                          type="button"
                          className="case-detail-secondary-button"
                          onClick={
                            () =>
                              setActiveForm(
                                null,
                              )
                          }
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          className="case-detail-primary-button"
                          disabled={
                            saving
                          }
                          onClick={
                            () =>
                              void handleSaveSymptom()
                          }
                        >
                          <Save
                            size={16}
                          />

                          Guardar
                        </button>
                      </div>

                    </div>

                  )
                }


                <div
                  className="case-detail-record-list"
                >

                  {
                    symptoms.length ===
                    0
                      ? (

                          <div
                            className="case-detail-empty"
                          >
                            <HeartPulse
                              size={27}
                            />

                            <strong>
                              Sin síntomas registrados
                            </strong>
                          </div>

                        )
                      : symptoms.map(
                          (
                            item,
                          ) => (

                            <div
                              key={
                                item.id_case_symptom
                              }
                              className="case-detail-record"
                            >

                              <div
                                className="case-detail-record-top"
                              >
                                <strong>
                                  {item.symptom.name}
                                </strong>

                                {
                                  item.intensity
                                  &&
                                  (
                                    <span
                                      className="case-detail-intensity"
                                    >
                                      {
                                        item.intensity.name
                                      }
                                    </span>
                                  )
                                }
                              </div>


                              {
                                item.observation
                                &&
                                (
                                  <p>
                                    {item.observation}
                                  </p>
                                )
                              }


                              <div
                                className="case-detail-record-details"
                              >
                                <span>
                                  Inicio:{" "}
                                  {
                                    formatDate(
                                      item.start_date,
                                    )
                                  }
                                </span>

                                <span>
                                  Registro:{" "}
                                  {
                                    formatDateTime(
                                      item.registered_at,
                                    )
                                  }
                                </span>
                              </div>


                              <div
                                className="case-detail-record-author"
                              >
                                <Stethoscope
                                  size={14}
                                />

                                {
                                  getAuthorName(
                                    item.author_uuid,
                                  )
                                }
                              </div>

                            </div>

                          ),
                        )
                  }

                </div>

              </article>


              {/* ==================================================
                  SIGNOS
                  ================================================== */}

              <article
                className="case-detail-section"
              >

                <header
                  className="case-detail-section-header-actions"
                >

                  <div
                    className="case-detail-section-header-title"
                  >
                    <div>
                      <Activity
                        size={20}
                      />
                    </div>

                    <div>
                      <h2>
                        5. Signos clínicos
                      </h2>

                      <p>
                        {
                          signs.length
                        } registro(s)
                      </p>
                    </div>
                  </div>


                  <button
                    type="button"
                    className="case-detail-add-button"
                    onClick={
                      () =>
                        setActiveForm(
                          activeForm ===
                          "sign"
                            ? null
                            : "sign",
                        )
                    }
                  >
                    <Plus
                      size={16}
                    />

                    Registrar
                  </button>

                </header>


                {
                  activeForm ===
                  "sign"
                  &&
                  (

                    <div
                      className="case-detail-inline-form"
                    >

                      <label>
                        Signo *

                        <select
                          value={
                            signId
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setSignId(
                                event.target.value,
                              )
                          }
                        >
                          <option
                            value=""
                          >
                            Seleccione
                          </option>

                          {
                            catalogs
                              ?.signs
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


                      <label
                        className="case-detail-form-wide"
                      >
                        Hallazgo / descripción

                        <textarea
                          rows={3}
                          value={
                            signDescription
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setSignDescription(
                                event.target.value,
                              )
                          }
                          placeholder="Detalle del hallazgo observado..."
                        />
                      </label>


                      <div
                        className="case-detail-form-actions"
                      >
                        <button
                          type="button"
                          className="case-detail-secondary-button"
                          onClick={
                            () =>
                              setActiveForm(
                                null,
                              )
                          }
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          className="case-detail-primary-button"
                          disabled={
                            saving
                          }
                          onClick={
                            () =>
                              void handleSaveSign()
                          }
                        >
                          <Save
                            size={16}
                          />

                          Guardar
                        </button>
                      </div>

                    </div>

                  )
                }


                <div
                  className="case-detail-record-list"
                >

                  {
                    signs.length ===
                    0
                      ? (

                          <div
                            className="case-detail-empty"
                          >
                            <Activity
                              size={27}
                            />

                            <strong>
                              Sin signos registrados
                            </strong>
                          </div>

                        )
                      : signs.map(
                          (
                            item,
                          ) => (

                            <div
                              key={
                                item.id_case_sign
                              }
                              className="case-detail-record"
                            >

                              <div
                                className="case-detail-record-top"
                              >
                                <strong>
                                  {item.sign.name}
                                </strong>

                                <span>
                                  {
                                    formatDateTime(
                                      item.observed_at,
                                    )
                                  }
                                </span>
                              </div>


                              {
                                item.finding_description
                                &&
                                (
                                  <p>
                                    {
                                      item.finding_description
                                    }
                                  </p>
                                )
                              }


                              <div
                                className="case-detail-record-author"
                              >
                                <Stethoscope
                                  size={14}
                                />

                                {
                                  getAuthorName(
                                    item.author_uuid,
                                  )
                                }
                              </div>

                            </div>

                          ),
                        )
                  }

                </div>

              </article>

            </div>


            <div
              className="case-detail-clinical-column"
            >

              {/* ==================================================
                  OBSERVACIONES
                  ================================================== */}

              <article
                className="case-detail-section"
              >

                <header
                  className="case-detail-section-header-actions"
                >

                  <div
                    className="case-detail-section-header-title"
                  >
                    <div>
                      <FileImage
                        size={20}
                      />
                    </div>

                    <div>
                      <h2>
                        6. Observaciones clínicas
                      </h2>

                      <p>
                        {
                          observations.length
                        } registro(s)
                      </p>
                    </div>
                  </div>


                  <button
                    type="button"
                    className="case-detail-add-button"
                    onClick={
                      () =>
                        setActiveForm(
                          activeForm ===
                          "observation"
                            ? null
                            : "observation",
                        )
                    }
                  >
                    <Plus
                      size={16}
                    />

                    Registrar
                  </button>

                </header>


                {
                  activeForm ===
                  "observation"
                  &&
                  (

                    <div
                      className="case-detail-inline-form"
                    >

                      <label
                        className="case-detail-form-wide"
                      >
                        Nueva observación *

                        <textarea
                          rows={4}
                          value={
                            observationContent
                          }
                          onChange={
                            (
                              event,
                            ) =>
                              setObservationContent(
                                event.target.value,
                              )
                          }
                          placeholder="Ingrese la evolución u observación clínica..."
                        />
                      </label>


                      <div
                        className="case-detail-form-actions"
                      >
                        <button
                          type="button"
                          className="case-detail-secondary-button"
                          onClick={
                            () =>
                              setActiveForm(
                                null,
                              )
                          }
                        >
                          Cancelar
                        </button>

                        <button
                          type="button"
                          className="case-detail-primary-button"
                          disabled={
                            saving
                          }
                          onClick={
                            () =>
                              void handleSaveObservation()
                          }
                        >
                          <Save
                            size={16}
                          />

                          Guardar
                        </button>
                      </div>

                    </div>

                  )
                }


                <div
                  className="case-detail-record-list"
                >

                  {
                    observations.length ===
                    0
                      ? (

                          <div
                            className="case-detail-empty"
                          >
                            <FileImage
                              size={27}
                            />

                            <strong>
                              Sin observaciones registradas
                            </strong>
                          </div>

                        )
                      : observations.map(
                          (
                            item,
                          ) => (

                            <div
                              key={
                                item.id_observation
                              }
                              className="case-detail-record"
                            >

                              <p>
                                {item.content}
                              </p>


                              <div
                                className="case-detail-record-author"
                              >
                                <Stethoscope
                                  size={14}
                                />

                                {
                                  getAuthorName(
                                    item.author_uuid,
                                  )
                                }

                                <span>
                                  ·
                                </span>

                                <CalendarDays
                                  size={14}
                                />

                                {
                                  formatDateTime(
                                    item.registered_at,
                                  )
                                }
                              </div>

                            </div>

                          ),
                        )
                  }

                </div>

              </article>


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
                    Observación inicial
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

              </article>


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
                    Estudios radiográficos asociados al caso.
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
                  Esta será la siguiente fase.
                </span>
              </div>

            </div>

          </article>

        )
      }


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
                                item.code ===
                                "REGISTRADO"
                                  ? formatDate(
                                      clinicalCase
                                        .opening_date,
                                    )
                                  : item.code ===
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
                    El cambio controlado de estado
                    se implementará en la siguiente fase.
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