import {
  Activity,
  ArrowRight,
  CheckCircle2,
  ClipboardList,
  Clock3,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
  Stethoscope,
  UserPlus,
  UserRound,
  UsersRound,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  listPatients,
  type PatientSummary,
} from "../../api/pacientes.api";

import {
  listarOncologos,
} from "../../api/oncologos.api";

import {
  listarRecuperaciones,
} from "../../api/recuperaciones.api";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./DashboardPage.css";


// ==========================================================
// FECHAS
// ==========================================================

function formatDateTime(
  value?: string | null,
): string {

  if (!value) {
    return "Sin registro";
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
      month: "short",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    date,
  );

}


// ==========================================================
// NOMBRE
// ==========================================================

function getVisibleName(
  nombres?: string,
  apellido?: string | null,
  usuario?: string,
): string {

  const parts = [
    nombres?.trim(),
    apellido?.trim(),
  ].filter(Boolean);


  if (
    parts.length > 0
  ) {
    return parts.join(
      " ",
    );
  }


  return (
    usuario?.trim()
    ||
    "Usuario"
  );

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function DashboardPage() {

  const navigate =
    useNavigate();


  const {
    usuario,
    tieneRol,
    infoSesion,
  } = useAuth();


  const esJefe =
    tieneRol(
      "JEFE_ONCOLOGIA",
    );


  const nombre =
    getVisibleName(
      usuario?.nombres,
      usuario?.apellido_paterno,
      usuario?.nombre_usuario,
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


  const [
    totalPacientes,
    setTotalPacientes,
  ] = useState(
    0,
  );


  const [
    pacientesRecientes,
    setPacientesRecientes,
  ] = useState<
    PatientSummary[]
  >(
    [],
  );


  const [
    totalOncologos,
    setTotalOncologos,
  ] = useState(
    0,
  );


  const [
    recuperacionesPendientes,
    setRecuperacionesPendientes,
  ] = useState(
    0,
  );


  // ========================================================
  // CARGAR
  // ========================================================

  const cargarDashboard =
    useCallback(
      async () => {

        setLoading(
          true,
        );


        setError(
          null,
        );


        try {

          const pacientesRequest =
            listPatients(
              {
                page: 1,
                page_size: 5,
              },
            );


          if (
            esJefe
          ) {

            const [
              pacientes,
              oncologos,
              recuperaciones,
            ] =
              await Promise.all(
                [
                  pacientesRequest,

                  listarOncologos(
                    "",
                    "",
                  ),

                  listarRecuperaciones(
                    "PENDIENTE",
                  ),
                ],
              );


            setTotalPacientes(
              pacientes
                .pagination
                .total,
            );


            setPacientesRecientes(
              pacientes.data,
            );


            setTotalOncologos(
              oncologos.total,
            );


            setRecuperacionesPendientes(
              recuperaciones.total,
            );

          } else {

            const pacientes =
              await pacientesRequest;


            setTotalPacientes(
              pacientes
                .pagination
                .total,
            );


            setPacientesRecientes(
              pacientes.data,
            );


            setTotalOncologos(
              0,
            );


            setRecuperacionesPendientes(
              0,
            );

          }

        } catch {

          setError(
            "No fue posible cargar todo el resumen del panel.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        esJefe,
      ],
    );


  useEffect(
    () => {

      void cargarDashboard();

    },
    [
      cargarDashboard,
    ],
  );


  // ========================================================
  // SALUDO
  // ========================================================

  const saludo =
    useMemo(
      () => {

        const hour =
          new Date()
            .getHours();


        if (
          hour < 12
        ) {
          return "Buenos días";
        }


        if (
          hour < 19
        ) {
          return "Buenas tardes";
        }


        return "Buenas noches";

      },
      [],
    );


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="dashboard-page"
    >

      {/* ==================================================
          HERO
          ================================================== */}

      <header
        className="dashboard-hero"
      >

        <div>

          <span
            className="dashboard-eyebrow"
          >
            Sistema de apoyo oncológico
          </span>


          <h1>
            {saludo}, {nombre}
          </h1>


          <p>
            {
              esJefe
                ? (
                    "Supervise la actividad clínica, pacientes, "
                    +
                    "personal y solicitudes administrativas."
                  )
                : (
                    "Consulte pacientes, casos clínicos "
                    +
                    "y actividad asistencial desde un solo lugar."
                  )
            }
          </p>

        </div>


        <div
          className="dashboard-hero__status"
        >

          <div
            className="dashboard-hero__status-icon"
          >

            <CheckCircle2
              size={22}
            />

          </div>


          <div>

            <span>
              Estado del sistema
            </span>

            <strong>
              Operativo
            </strong>

          </div>

        </div>

      </header>


      {/* ==================================================
          ERROR
          ================================================== */}

      {
        error
        &&
        (

          <div
            className="dashboard-error"
          >

            <Activity
              size={18}
            />

            {error}

          </div>

        )
      }


      {/* ==================================================
          LOADING
          ================================================== */}

      {
        loading
          ? (

              <div
                className="dashboard-loading"
              >

                <LoaderCircle
                  size={27}
                  className="dashboard-spin"
                />

                <span>
                  Cargando resumen clínico...
                </span>

              </div>

            )
          : (

              <>

                {/* ==========================================
                    KPIS
                    ========================================== */}

                <div
                  className="dashboard-kpis"
                >

                  <button
                    type="button"
                    className="dashboard-kpi"
                    onClick={
                      () =>
                        navigate(
                          "/pacientes",
                        )
                    }
                  >

                    <div
                      className="dashboard-kpi__icon"
                    >

                      <UsersRound
                        size={22}
                      />

                    </div>


                    <div
                      className="dashboard-kpi__content"
                    >

                      <span>
                        Pacientes registrados
                      </span>

                      <strong>
                        {totalPacientes}
                      </strong>

                      <small>
                        Abrir gestión de pacientes
                      </small>

                    </div>


                    <ArrowRight
                      size={18}
                      className="dashboard-kpi__arrow"
                    />

                  </button>


                  <button
                    type="button"
                    className="dashboard-kpi"
                    onClick={
                      () =>
                        navigate(
                          "/casos",
                        )
                    }
                  >

                    <div
                      className="dashboard-kpi__icon"
                    >

                      <ClipboardList
                        size={22}
                      />

                    </div>


                    <div
                      className="dashboard-kpi__content"
                    >

                      <span>
                        Casos clínicos
                      </span>

                      <strong>
                        —
                      </strong>

                      <small>
                        Gestión clínica
                      </small>

                    </div>


                    <ArrowRight
                      size={18}
                      className="dashboard-kpi__arrow"
                    />

                  </button>


                  {
                    esJefe
                      ? (

                          <>

                            <button
                              type="button"
                              className="dashboard-kpi"
                              onClick={
                                () =>
                                  navigate(
                                    "/usuarios",
                                  )
                              }
                            >

                              <div
                                className="dashboard-kpi__icon"
                              >

                                <Stethoscope
                                  size={22}
                                />

                              </div>


                              <div
                                className="dashboard-kpi__content"
                              >

                                <span>
                                  Personal oncológico
                                </span>

                                <strong>
                                  {totalOncologos}
                                </strong>

                                <small>
                                  Oncólogos y jefatura
                                </small>

                              </div>


                              <ArrowRight
                                size={18}
                                className="dashboard-kpi__arrow"
                              />

                            </button>


                            <button
                              type="button"
                              className={
                                recuperacionesPendientes > 0
                                  ? "dashboard-kpi dashboard-kpi--attention"
                                  : "dashboard-kpi"
                              }
                              onClick={
                                () =>
                                  navigate(
                                    "/recuperaciones",
                                  )
                              }
                            >

                              <div
                                className="dashboard-kpi__icon"
                              >

                                <KeyRound
                                  size={22}
                                />

                              </div>


                              <div
                                className="dashboard-kpi__content"
                              >

                                <span>
                                  Recuperaciones pendientes
                                </span>

                                <strong>
                                  {
                                    recuperacionesPendientes
                                  }
                                </strong>

                                <small>
                                  Solicitudes por revisar
                                </small>

                              </div>


                              <ArrowRight
                                size={18}
                                className="dashboard-kpi__arrow"
                              />

                            </button>

                          </>

                        )
                      : (

                          <button
                            type="button"
                            className="dashboard-kpi"
                            onClick={
                              () =>
                                navigate(
                                  "/radiografias/subir",
                                )
                            }
                          >

                            <div
                              className="dashboard-kpi__icon"
                            >

                              <Activity
                                size={22}
                              />

                            </div>


                            <div
                              className="dashboard-kpi__content"
                            >

                              <span>
                                Radiografías
                              </span>

                              <strong>
                                —
                              </strong>

                              <small>
                                Gestión radiológica
                              </small>

                            </div>


                            <ArrowRight
                              size={18}
                              className="dashboard-kpi__arrow"
                            />

                          </button>

                        )
                  }

                </div>


                {/* ==========================================
                    GRID PRINCIPAL
                    ========================================== */}

                <div
                  className="dashboard-grid"
                >

                  {/* ========================================
                      PACIENTES RECIENTES
                      ======================================== */}

                  <article
                    className="dashboard-card dashboard-card--large"
                  >

                    <header
                      className="dashboard-card__header"
                    >

                      <div>

                        <span
                          className="dashboard-card__icon"
                        >

                          <UsersRound
                            size={19}
                          />

                        </span>


                        <div>

                          <h2>
                            Pacientes recientes
                          </h2>

                          <p>
                            Últimos registros disponibles.
                          </p>

                        </div>

                      </div>


                      <button
                        type="button"
                        onClick={
                          () =>
                            navigate(
                              "/pacientes",
                            )
                        }
                      >
                        Ver todos
                      </button>

                    </header>


                    {
                      pacientesRecientes.length === 0
                        ? (

                            <div
                              className="dashboard-empty"
                            >

                              <UsersRound
                                size={27}
                              />

                              <strong>
                                Sin pacientes registrados
                              </strong>

                              <span>
                                Registre el primer paciente
                                para comenzar.
                              </span>

                            </div>

                          )
                        : (

                            <div
                              className="dashboard-patient-list"
                            >

                              {
                                pacientesRecientes.map(
                                  (
                                    patient,
                                  ) => (

                                    <button
                                      type="button"
                                      key={
                                        patient
                                          .id_patient
                                      }
                                      className="dashboard-patient"
                                      onClick={
                                        () =>
                                          navigate(
                                            `/pacientes/${patient.id_patient}`,
                                          )
                                      }
                                    >

                                      <div
                                        className="dashboard-patient__avatar"
                                      >

                                        {
                                          patient
                                            .full_name
                                            .charAt(
                                              0,
                                            )
                                            .toUpperCase()
                                        }

                                      </div>


                                      <div
                                        className="dashboard-patient__data"
                                      >

                                        <strong>
                                          {
                                            patient
                                              .full_name
                                          }
                                        </strong>


                                        <span>
                                          {
                                            patient
                                              .primary_document
                                              ?.document_number
                                            ??
                                            "Sin documento"
                                          }
                                        </span>

                                      </div>


                                      <div
                                        className="dashboard-patient__cases"
                                      >

                                        <strong>
                                          {
                                            patient
                                              .clinical_cases_count
                                          }
                                        </strong>

                                        <span>
                                          casos
                                        </span>

                                      </div>


                                      <ArrowRight
                                        size={17}
                                      />

                                    </button>

                                  ),
                                )
                              }

                            </div>

                          )
                    }

                  </article>


                  {/* ========================================
                      SESIÓN
                      ======================================== */}

                  <article
                    className="dashboard-card"
                  >

                    <header
                      className="dashboard-card__header dashboard-card__header--simple"
                    >

                      <div>

                        <span
                          className="dashboard-card__icon"
                        >

                          <ShieldCheck
                            size={19}
                          />

                        </span>


                        <div>

                          <h2>
                            Sesión segura
                          </h2>

                          <p>
                            Estado de autenticación.
                          </p>

                        </div>

                      </div>

                    </header>


                    <div
                      className="dashboard-session"
                    >

                      <div>

                        <span>
                          Estado
                        </span>

                        <strong
                          className="dashboard-session__active"
                        >
                          Activa
                        </strong>

                      </div>


                      <div>

                        <span>
                          Access token vence
                        </span>

                        <strong>
                          {
                            formatDateTime(
                              infoSesion
                                .accessExpiraEn,
                            )
                          }
                        </strong>

                      </div>


                      <div>

                        <span>
                          Refresh token vence
                        </span>

                        <strong>
                          {
                            formatDateTime(
                              infoSesion
                                .refreshExpiraEn,
                            )
                          }
                        </strong>

                      </div>


                      <div>

                        <span>
                          Última renovación
                        </span>

                        <strong>
                          {
                            formatDateTime(
                              infoSesion
                                .ultimaRenovacion,
                            )
                          }
                        </strong>

                      </div>

                    </div>

                  </article>


                  {/* ========================================
                      ACCESOS RÁPIDOS
                      ======================================== */}

                  <article
                    className="dashboard-card"
                  >

                    <header
                      className="dashboard-card__header dashboard-card__header--simple"
                    >

                      <div>

                        <span
                          className="dashboard-card__icon"
                        >

                          <Activity
                            size={19}
                          />

                        </span>


                        <div>

                          <h2>
                            Accesos rápidos
                          </h2>

                          <p>
                            Operaciones frecuentes.
                          </p>

                        </div>

                      </div>

                    </header>


                    <div
                      className="dashboard-shortcuts"
                    >

                      <button
                        type="button"
                        onClick={
                          () =>
                            navigate(
                              "/pacientes/nuevo",
                            )
                        }
                      >

                        <UserPlus
                          size={19}
                        />

                        <div>

                          <strong>
                            Registrar paciente
                          </strong>

                          <span>
                            Nueva ficha clínica
                          </span>

                        </div>

                      </button>


                      <button
                        type="button"
                        onClick={
                          () =>
                            navigate(
                              "/casos",
                            )
                        }
                      >

                        <ClipboardList
                          size={19}
                        />

                        <div>

                          <strong>
                            Casos clínicos
                          </strong>

                          <span>
                            Consultar casos
                          </span>

                        </div>

                      </button>


                      {
                        esJefe
                        &&
                        (

                          <>

                            <button
                              type="button"
                              onClick={
                                () =>
                                  navigate(
                                    "/usuarios/nuevo",
                                  )
                              }
                            >

                              <UserRound
                                size={19}
                              />

                              <div>

                                <strong>
                                  Registrar oncólogo
                                </strong>

                                <span>
                                  Nueva cuenta institucional
                                </span>

                              </div>

                            </button>


                            <button
                              type="button"
                              onClick={
                                () =>
                                  navigate(
                                    "/auditoria",
                                  )
                              }
                            >

                              <Clock3
                                size={19}
                              />

                              <div>

                                <strong>
                                  Auditoría
                                </strong>

                                <span>
                                  Revisar actividad
                                </span>

                              </div>

                            </button>

                          </>

                        )
                      }

                    </div>

                  </article>

                </div>

              </>

            )
      }

    </section>

  );

}