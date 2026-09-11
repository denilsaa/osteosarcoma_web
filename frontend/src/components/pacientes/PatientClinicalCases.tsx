import {
  Activity,
  ArrowRight,
  CalendarDays,
  CircleAlert,
  ClipboardList,
  LoaderCircle,
  Plus,
  RefreshCw,
  Stethoscope,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  getPatientClinicalCases,
  type ClinicalCase,
} from "../../api/casos.api";

import "./PatientClinicalCases.css";


// ==========================================================
// PROPS
// ==========================================================

interface Props {
  patientId: string;
}


// ==========================================================
// FECHA
// ==========================================================

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


// ==========================================================
// CLASE DE PRIORIDAD
// ==========================================================

function getPriorityClass(
  clinicalCase: ClinicalCase,
): string {

  const code =
    clinicalCase
      .priority
      .code
      .toUpperCase();


  if (
    code.includes("ALTA")
    ||
    code.includes("URGENTE")
  ) {
    return (
      "patient-case-priority patient-case-priority--high"
    );
  }


  if (
    code.includes("MEDIA")
    ||
    code.includes("MODERADA")
  ) {
    return (
      "patient-case-priority patient-case-priority--medium"
    );
  }


  return (
    "patient-case-priority patient-case-priority--low"
  );
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function PatientClinicalCases(
  {
    patientId,
  }: Props,
) {

  const navigate =
    useNavigate();


  const [
    cases,
    setCases,
  ] = useState<
    ClinicalCase[]
  >(
    [],
  );


  const [
    total,
    setTotal,
  ] = useState(
    0,
  );


  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null,
  );


  // ========================================================
  // CARGAR CASOS
  // ========================================================

  const loadCases =
    useCallback(
      async () => {

        setLoading(
          true,
        );


        setError(
          null,
        );


        try {

          const response =
            await getPatientClinicalCases(
              patientId,
            );


          setCases(
            response.data,
          );


          setTotal(
            response.total,
          );

        } catch {

          setCases(
            [],
          );


          setTotal(
            0,
          );


          setError(
            "No fue posible cargar los casos clínicos del paciente.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        patientId,
      ],
    );


  // ========================================================
  // EFFECT
  // ========================================================

  useEffect(
    () => {

      void loadCases();

    },
    [
      loadCases,
    ],
  );


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <article
      className="patient-cases-card"
    >

      <header
        className="patient-cases-header"
      >

        <div
          className="patient-cases-header__left"
        >

          <div
            className="patient-cases-header__icon"
          >
            <Stethoscope
              size={21}
            />
          </div>


          <div>
            <h2>
              Casos clínicos
            </h2>

            <p>
              Casos clínicos relacionados con este paciente.
            </p>
          </div>

        </div>


        <div
          className="patient-cases-header__actions"
        >

          {!loading && (

            <span
              className="patient-cases-total"
            >
              {total} caso{total === 1 ? "" : "s"}
            </span>

          )}


          <button
            type="button"
            className="patient-cases-create"
            onClick={
              () =>
                navigate(
                  `/casos/nuevo?paciente=${patientId}`,
                )
            }
          >
            <Plus
              size={16}
            />

            Nuevo caso
          </button>


          <button
            type="button"
            className="patient-cases-refresh"
            onClick={
              () =>
                void loadCases()
            }
            title="Actualizar casos"
            aria-label="Actualizar casos"
          >
            <RefreshCw
              size={17}
            />
          </button>

        </div>

      </header>


      {loading ? (

        <div
          className="patient-cases-state"
        >

          <LoaderCircle
            size={26}
            className="patient-cases-spin"
          />

          <span>
            Cargando casos clínicos...
          </span>

        </div>

      ) : error ? (

        <div
          className="patient-cases-error"
        >

          <CircleAlert
            size={19}
          />

          <span>
            {error}
          </span>

        </div>

      ) : cases.length === 0 ? (

        <div
          className="patient-cases-empty"
        >

          <Activity
            size={31}
          />

          <strong>
            Sin casos clínicos
          </strong>

          <span>
            Este paciente todavía no tiene casos clínicos registrados.
          </span>

        </div>

      ) : (

        <div
          className="patient-cases-list"
        >

          {cases.map(
            (
              clinicalCase,
            ) => (

              <section
                key={
                  clinicalCase.id_case
                }
                className="patient-case"
              >

                <div
                  className="patient-case__main"
                >

                  <div
                    className="patient-case__top"
                  >

                    <div
                      className="patient-case-code"
                    >

                      <ClipboardList
                        size={17}
                      />

                      <strong>
                        {
                          clinicalCase
                            .code
                        }
                      </strong>

                    </div>


                    <div
                      className="patient-case-badges"
                    >

                      <span
                        className="patient-case-status"
                      >
                        {
                          clinicalCase
                            .status
                            .name
                        }
                      </span>


                      <span
                        className={
                          getPriorityClass(
                            clinicalCase,
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

                  </div>


                  <div
                    className="patient-case-meta"
                  >

                    <span>

                      <CalendarDays
                        size={14}
                      />

                      Apertura:{" "}
                      {
                        formatDateTime(
                          clinicalCase
                            .opening_date,
                        )
                      }

                    </span>


                    {clinicalCase
                      .closing_date && (

                      <span>

                        <CalendarDays
                          size={14}
                        />

                        Cierre:{" "}
                        {
                          formatDateTime(
                            clinicalCase
                              .closing_date,
                          )
                        }

                      </span>

                    )}

                  </div>


                  <div
                    className="patient-case-reason"
                  >

                    <span>
                      Motivo de consulta
                    </span>

                    <p>
                      {
                        clinicalCase
                          .consultation_reason
                      }
                    </p>

                  </div>


                  {clinicalCase
                    .general_observation && (

                    <div
                      className="patient-case-observation"
                    >

                      <span>
                        Observación
                      </span>

                      <p>
                        {
                          clinicalCase
                            .general_observation
                        }
                      </p>

                    </div>

                  )}

                </div>


                <button
                  type="button"
                  className="patient-case-open"
                  onClick={
                    () =>
                      navigate(
                        `/casos/${clinicalCase.id_case}`,
                      )
                  }
                >

                  Ver caso

                  <ArrowRight
                    size={16}
                  />

                </button>

              </section>

            ),
          )}

        </div>

      )}

    </article>

  );
}