import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  ClipboardPlus,
  LoaderCircle,
  Save,
  Stethoscope,
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
  useSearchParams,
} from "react-router-dom";

import {
  createClinicalCase,
  getClinicalCaseCatalogs,
  type ClinicalCaseCatalogs,
} from "../../api/casos.api";

import {
  listarOncologos,
  type OncologoResumen,
} from "../../api/oncologos.api";

import {
  getPatient,
  type PatientDetail,
} from "../../api/pacientes.api";

import "./NuevoCasoPage.css";


// ==========================================================
// FORM
// ==========================================================

type FormState = {
  priority_id:
    string;

  responsible_oncologist_uuid:
    string;

  consultation_reason:
    string;

  general_observation:
    string;
};


const initialForm:
  FormState = {

    priority_id:
      "",

    responsible_oncologist_uuid:
      "",

    consultation_reason:
      "",

    general_observation:
      "",

  };


// ==========================================================
// HELPERS
// ==========================================================

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
        ?.error ===
      "string"
    ) {

      return response.data.error;
    }


    if (
      typeof response
        ?.data
        ?.detail ===
      "string"
    ) {

      return response.data.detail;
    }

  }


  return (
    "No fue posible registrar el caso clínico."
  );
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function NuevoCasoPage() {

  const navigate =
    useNavigate();


  const [
    searchParams,
  ] =
    useSearchParams();


  const patientId =
    searchParams.get(
      "paciente",
    )
    ??
    "";

  // ========================================================
  // DATOS
  // ========================================================

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
    catalogs,
    setCatalogs,
  ] =
    useState<
      ClinicalCaseCatalogs | null
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
    form,
    setForm,
  ] =
    useState<FormState>(
      initialForm,
    );


  // ========================================================
  // ESTADOS
  // ========================================================

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
  // CARGA INICIAL
  // ========================================================

  useEffect(
    () => {

      if (
        !patientId
      ) {

        setError(
          "Debe registrar el caso desde la ficha de un paciente.",
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
            oncologistData,
          ] =
            await Promise.all(
              [
                getPatient(
                  patientId,
                ),

                getClinicalCaseCatalogs(),

                listarOncologos(
                  "",
                  "ACTIVO",
                  "",
                ),
              ],
            );


          if (
            !mounted
          ) {

            return;
          }


          setPatient(
            patientData,
          );


          setCatalogs(
            catalogData,
          );


          setOncologists(
            oncologistData
              .resultados,
          );


          const defaultPriority =
            catalogData
              .priorities
              .find(
                (
                  item,
                ) =>
                  item.code ===
                  "MEDIA",
              )
            ??
            catalogData
              .priorities[0];


          setForm(
            (
              current,
            ) => ({
              ...current,

              priority_id:
                defaultPriority
                  ? String(
                      defaultPriority.id,
                    )
                  : "",
            }),
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
      patientId,
    ],
  );


  // ========================================================
  // VALIDACIÓN
  // ========================================================

  const formValid =
    useMemo(
      () => {

        return Boolean(
          patientId
          &&
          form.priority_id
          &&
          normalizeText(
            form.consultation_reason,
          ).length >= 10
        );

      },
      [
        patientId,
        form.priority_id,
        form.consultation_reason,
      ],
    );


  // ========================================================
  // CAMPO
  // ========================================================

  function updateField(
    field:
      keyof FormState,

    value:
      string,
  ) {

    setForm(
      (
        current,
      ) => ({
        ...current,

        [field]:
          value,
      }),
    );


    setError(
      null,
    );


    setSuccess(
      null,
    );
  }


  // ========================================================
  // GUARDAR
  // ========================================================

  async function handleSubmit(
    event:
      React.FormEvent,
  ) {

    event.preventDefault();


    if (
      !patientId
    ) {

      setError(
        "No se identificó al paciente.",
      );


      return;
    }


    const consultationReason =
      normalizeText(
        form.consultation_reason,
      );


    if (
      !form.priority_id
    ) {

      setError(
        "Seleccione la prioridad del caso.",
      );


      return;
    }


    if (
      consultationReason.length <
      10
    ) {

      setError(
        "El motivo de consulta debe contener al menos 10 caracteres.",
      );


      return;
    }


    setSaving(
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
        await createClinicalCase(
          patientId,
          {
            priority_id:
              Number(
                form.priority_id,
              ),

            responsible_oncologist_uuid:
              form
                .responsible_oncologist_uuid
              ||
              null,

            consultation_reason:
              consultationReason,

            general_observation:
              normalizeText(
                form.general_observation,
              )
              ||
              null,
          },
        );


      setSuccess(
        response.message,
      );


      window.setTimeout(
        () => {

          navigate(
            `/casos/${response.data.id_case}`,
          );

        },
        500,
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
        className="new-case-loading"
      >

        <LoaderCircle
          size={30}
          className="new-case-spin"
        />

        <span>
          Cargando formulario...
        </span>

      </div>

    );
  }


  // ========================================================
  // SIN PACIENTE
  // ========================================================

  if (
    !patientId
    ||
    !patient
  ) {

    return (

      <section
        className="new-case-page"
      >

        <div
          className="new-case-message new-case-message--error"
        >

          <CircleAlert
            size={19}
          />

          <span>
            {
              error
              ??
              "Debe registrar el caso desde la ficha de un paciente."
            }
          </span>

        </div>


        <button
          type="button"
          className="new-case-back-list"
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
      className="new-case-page"
    >

      <header
        className="new-case-header"
      >

        <div
          className="new-case-header__main"
        >

          <button
            type="button"
            className="new-case-back"
            onClick={
              () =>
                navigate(
                  `/pacientes/${patient.id_patient}`,
                )
            }
          >
            <ArrowLeft
              size={18}
            />
          </button>


          <div>

            <span
              className="new-case-eyebrow"
            >
              Gestión clínica
            </span>


            <h1>
              Registrar caso clínico
            </h1>


            <p>
              Registre la información inicial
              para la evaluación clínica del paciente.
            </p>

          </div>

        </div>


        <div
          className="new-case-header__icon"
        >
          <ClipboardPlus
            size={26}
          />
        </div>

      </header>


      {
        error
        &&
        (

          <div
            className="new-case-message new-case-message--error"
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
            className="new-case-message new-case-message--success"
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


      <form
        className="new-case-form"
        onSubmit={
          handleSubmit
        }
      >

        {/* ================================================
            PACIENTE
            ================================================ */}

        <article
          className="new-case-card"
        >

          <div
            className="new-case-card__header"
          >

            <div
              className="new-case-card__icon"
            >
              <UserRound
                size={20}
              />
            </div>


            <div>
              <h2>
                Paciente
              </h2>

              <p>
                El caso quedará asociado permanentemente
                a esta ficha clínica.
              </p>
            </div>

          </div>


          <div
            className="new-case-patient"
          >

            <div
              className="new-case-patient__avatar"
            >
              {
                patient
                  .first_names
                  .charAt(
                    0,
                  )
                  .toUpperCase()
              }
            </div>


            <div>

              <strong>
                {patient.full_name}
              </strong>


              <span>
                {
                  patient
                    .documents[0]
                    ?.document_type_name
                  ??
                  "Documento"
                }
                {": "}
                {
                  patient
                    .documents[0]
                    ?.document_number
                  ??
                  "Sin registro"
                }
              </span>


              <small>
                UUID: {patient.id_patient}
              </small>

            </div>

          </div>

        </article>


        {/* ================================================
            INFORMACIÓN DEL CASO
            ================================================ */}

        <article
          className="new-case-card"
        >

          <div
            className="new-case-card__header"
          >

            <div
              className="new-case-card__icon"
            >
              <Stethoscope
                size={20}
              />
            </div>


            <div>
              <h2>
                Información inicial del caso
              </h2>

              <p>
                Defina prioridad, médico responsable
                y motivo de consulta.
              </p>
            </div>

          </div>


          <div
            className="new-case-grid new-case-grid--2"
          >

            <label>

              <span>
                Prioridad *
              </span>

              <select
                value={
                  form.priority_id
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "priority_id",
                      event.target.value,
                    )
                }
              >

                {
                  catalogs
                    ?.priorities
                    .map(
                      (
                        priority,
                      ) => (

                        <option
                          key={
                            priority.id
                          }
                          value={
                            priority.id
                          }
                        >
                          {priority.name}
                        </option>

                      ),
                    )
                }

              </select>

            </label>


            <label>

              <span>
                Médico responsable
              </span>

              <select
                value={
                  form.responsible_oncologist_uuid
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "responsible_oncologist_uuid",
                      event.target.value,
                    )
                }
              >

                <option
                  value=""
                >
                  Asignar al usuario actual
                </option>


                {
                  oncologists.map(
                    (
                      oncologist,
                    ) => (

                      <option
                        key={
                          oncologist.id_usuario
                        }
                        value={
                          oncologist.id_usuario
                        }
                      >
                        {
                          oncologist.nombre_completo
                        }
                        {" — "}
                        {
                          oncologist.rol
                        }
                      </option>

                    ),
                  )
                }

              </select>


              <small
                className="new-case-help"
              >
                Si no selecciona un profesional,
                el backend asignará al usuario autenticado.
              </small>

            </label>

          </div>


          <div
            className="new-case-grid new-case-grid--1"
          >

            <label>

              <span>
                Motivo de consulta *
              </span>

              <textarea
                value={
                  form.consultation_reason
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "consultation_reason",
                      event.target.value,
                    )
                }
                maxLength={1000}
                rows={4}
                placeholder="Ej. Dolor óseo persistente, aumento de volumen y limitación funcional."
              />

              <small
                className="new-case-counter"
              >
                {
                  form
                    .consultation_reason
                    .length
                }
                /1000
              </small>

            </label>


            <label>

              <span>
                Observación general
              </span>

              <textarea
                value={
                  form.general_observation
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "general_observation",
                      event.target.value,
                    )
                }
                maxLength={2000}
                rows={5}
                placeholder="Información complementaria relevante para la apertura del caso."
              />

              <small
                className="new-case-counter"
              >
                {
                  form
                    .general_observation
                    .length
                }
                /2000
              </small>

            </label>

          </div>

        </article>


        {/* ================================================
            ESTADO INICIAL
            ================================================ */}

        <article
          className="new-case-state-card"
        >

          <div>

            <span>
              Estado inicial
            </span>

            <strong>
              Registrado
            </strong>

          </div>


          <p>
            El sistema generará automáticamente
            el código del caso y registrará el primer
            evento del historial de estados.
          </p>

        </article>


        {/* ================================================
            ACCIONES
            ================================================ */}

        <footer
          className="new-case-footer"
        >

          <button
            type="button"
            className="new-case-cancel"
            disabled={
              saving
            }
            onClick={
              () =>
                navigate(
                  `/pacientes/${patient.id_patient}`,
                )
            }
          >

            <X
              size={17}
            />

            Cancelar

          </button>


          <button
            type="submit"
            className="new-case-save"
            disabled={
              saving
              ||
              !formValid
            }
          >

            {
              saving
                ? (
                    <LoaderCircle
                      size={18}
                      className="new-case-spin"
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
                ? "Registrando..."
                : "Registrar caso clínico"
            }

          </button>

        </footer>

      </form>

    </section>

  );
}