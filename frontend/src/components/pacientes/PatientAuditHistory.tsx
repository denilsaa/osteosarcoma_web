import {
  Activity,
  ChevronDown,
  ChevronUp,
  CircleAlert,
  Clock3,
  LoaderCircle,
  Monitor,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getPatientAuditEventDetail,
  getPatientAuditHistory,
  type PatientAuditChange,
  type PatientAuditEvent,
} from "../../api/pacienteAuditoria.api";

import "./PatientAuditHistory.css";


// ==========================================================
// PROPS
// ==========================================================

interface Props {

  patientId:
    string;

}


// ==========================================================
// FECHA
// ==========================================================

function formatDateTime(
  value: string,
): string {

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

      second:
        "2-digit",

    },
  ).format(
    date,
  );

}


// ==========================================================
// OBTENER NOMBRE DEL ACTOR
// ==========================================================

function getActorName(
  event:
    PatientAuditEvent,
): string {

  const detail =
    event.detalle_json;


  if (
    detail
    &&
    typeof detail[
      "actor_nombre"
    ] === "string"
  ) {

    return detail[
      "actor_nombre"
    ] as string;

  }


  if (
    event.actor_usuario_uuid
  ) {

    return event
      .actor_usuario_uuid;

  }


  return "Sistema";

}


// ==========================================================
// OBTENER ROL DEL ACTOR
// ==========================================================

function getActorRole(
  event:
    PatientAuditEvent,
): string | null {

  const detail =
    event.detalle_json;


  if (
    detail
    &&
    typeof detail[
      "actor_rol"
    ] === "string"
  ) {

    return detail[
      "actor_rol"
    ] as string;

  }


  return null;

}


// ==========================================================
// OBTENER MOTIVO
// ==========================================================

function getReason(
  event:
    PatientAuditEvent,
): string | null {

  const detail =
    event.detalle_json;


  if (
    detail
    &&
    typeof detail[
      "motivo"
    ] === "string"
  ) {

    return detail[
      "motivo"
    ] as string;

  }


  return null;

}


// ==========================================================
// OBTENER DESCRIPCIÓN
// ==========================================================

function getDescription(
  event:
    PatientAuditEvent,
): string | null {

  const detail =
    event.detalle_json;


  if (
    detail
    &&
    typeof detail[
      "descripcion"
    ] === "string"
  ) {

    return detail[
      "descripcion"
    ] as string;

  }


  return null;

}


// ==========================================================
// NOMBRE AMIGABLE DEL CAMPO
// ==========================================================

function getFieldLabel(
  field: string,
): string {

  const labels:
    Record<
      string,
      string
    > = {

    first_names:
      "Nombres",

    paternal_surname:
      "Apellido paterno",

    maternal_surname:
      "Apellido materno",

    birth_date:
      "Fecha de nacimiento",

    sex_id:
      "Sexo",

    active:
      "Estado",

  };


  return labels[
    field
  ] ?? field;

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function PatientAuditHistory(
  {
    patientId,
  }: Props,
) {

  // ========================================================
  // ESTADO
  // ========================================================

  const [
    events,
    setEvents,
  ] = useState<
    PatientAuditEvent[]
  >([]);


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
  >(null);


  const [
    expandedId,
    setExpandedId,
  ] = useState<
    string | null
  >(null);


  const [
    loadingDetail,
    setLoadingDetail,
  ] = useState<
    string | null
  >(null);


  const [
    changesByEvent,
    setChangesByEvent,
  ] = useState<
    Record<
      string,
      PatientAuditChange[]
    >
  >({});


  // ========================================================
  // CARGAR HISTORIAL
  // ========================================================

  const loadHistory =
    useCallback(
      async () => {

        setLoading(
          true,
        );


        setError(
          null,
        );


        try {

          const data =
            await getPatientAuditHistory(
              patientId,
              15,
            );


          setEvents(
            data,
          );

        } catch {

          setEvents(
            [],
          );


          setError(
            "No fue posible cargar el historial de acciones.",
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
  // CARGAR AL MONTAR / CAMBIAR PACIENTE
  // ========================================================

  useEffect(
    () => {

      void loadHistory();

    },
    [
      loadHistory,
    ],
  );


  // ========================================================
  // EXPANDIR EVENTO
  // ========================================================

  async function toggleEvent(
    event:
      PatientAuditEvent,
  ) {

    if (
      expandedId ===
        event.id_evento
    ) {

      setExpandedId(
        null,
      );


      return;

    }


    setExpandedId(
      event.id_evento,
    );


    if (
      changesByEvent[
        event.id_evento
      ]
    ) {

      return;

    }


    setLoadingDetail(
      event.id_evento,
    );


    try {

      const detail =
        await getPatientAuditEventDetail(
          event.id_evento,
        );


      setChangesByEvent(
        (
          current,
        ) => ({

          ...current,

          [
            event.id_evento
          ]:
            detail.cambios,

        }),
      );

    } catch {

      setChangesByEvent(
        (
          current,
        ) => ({

          ...current,

          [
            event.id_evento
          ]:
            [],

        }),
      );

    } finally {

      setLoadingDetail(
        null,
      );

    }

  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <article
      className="patient-audit-card"
    >

      {/* ==================================================
          HEADER
          ================================================== */}

      <header
        className="patient-audit-header"
      >

        <div
          className="patient-audit-header__left"
        >

          <div
            className="patient-audit-header__icon"
          >

            <ShieldCheck
              size={21}
            />

          </div>


          <div>

            <h2>
              Historial de acciones
            </h2>


            <p>
              Registro de las últimas acciones realizadas sobre este paciente.
            </p>

          </div>

        </div>


        <button
          type="button"
          className="patient-audit-refresh"
          onClick={
            () =>
              void loadHistory()
          }
          title="Actualizar historial"
          aria-label="Actualizar historial"
        >

          <RefreshCw
            size={17}
          />

        </button>

      </header>


      {/* ==================================================
          LOADING
          ================================================== */}

      {loading ? (

        <div
          className="patient-audit-state"
        >

          <LoaderCircle
            size={25}
            className="patient-audit-spin"
          />


          <span>
            Cargando historial...
          </span>

        </div>

      ) : error ? (

        /* =================================================
           ERROR
           ================================================= */

        <div
          className="patient-audit-error"
        >

          <CircleAlert
            size={18}
          />


          <span>
            {error}
          </span>

        </div>

      ) : events.length === 0 ? (

        /* =================================================
           SIN EVENTOS
           ================================================= */

        <div
          className="patient-audit-state"
        >

          <Activity
            size={28}
          />


          <strong>
            Sin acciones registradas
          </strong>


          <span>
            Todavía no existen eventos de auditoría para este paciente.
          </span>

        </div>

      ) : (

        /* =================================================
           LISTADO
           ================================================= */

        <div
          className="patient-audit-list"
        >

          {events.map(
            (
              event,
            ) => {

              const expanded =
                expandedId ===
                  event.id_evento;


              const changes =
                changesByEvent[
                  event.id_evento
                ]
                ?? [];


              const reason =
                getReason(
                  event,
                );


              const description =
                getDescription(
                  event,
                );


              const actorRole =
                getActorRole(
                  event,
                );


              return (

                <section
                  key={
                    event.id_evento
                  }
                  className="patient-audit-event"
                >

                  {/* ========================================
                      RESUMEN DEL EVENTO
                      ======================================== */}

                  <button
                    type="button"
                    className="patient-audit-event__summary"
                    onClick={
                      () =>
                        void toggleEvent(
                          event,
                        )
                    }
                  >

                    <div
                      className="patient-audit-event__main"
                    >

                      <div
                        className="patient-audit-event__top"
                      >

                        <span
                          className="patient-audit-action"
                        >
                          {
                            event
                              .accion_nombre
                          }
                        </span>


                        <span
                          className={
                            event.resultado ===
                              "EXITOSO"

                              ? (
                                "patient-audit-result "
                                +
                                "patient-audit-result--success"
                              )

                              : event.resultado ===
                                  "DENEGADO"

                                ? (
                                  "patient-audit-result "
                                  +
                                  "patient-audit-result--denied"
                                )

                                : (
                                  "patient-audit-result "
                                  +
                                  "patient-audit-result--failed"
                                )
                          }
                        >
                          {
                            event
                              .resultado_nombre
                          }
                        </span>

                      </div>


                      {/* ====================================
                          METADATOS
                          ==================================== */}

                      <div
                        className="patient-audit-meta"
                      >

                        <span>

                          <UserRound
                            size={14}
                          />


                          {
                            getActorName(
                              event,
                            )
                          }

                        </span>


                        {actorRole && (

                          <span>
                            {actorRole}
                          </span>

                        )}


                        <span>

                          <Clock3
                            size={14}
                          />


                          {
                            formatDateTime(
                              event
                                .fecha_evento,
                            )
                          }

                        </span>


                        {event
                          .direccion_ip && (

                          <span>

                            <Monitor
                              size={14}
                            />


                            {
                              event
                                .direccion_ip
                            }

                          </span>

                        )}

                      </div>

                    </div>


                    {
                      expanded
                        ? (
                          <ChevronUp
                            size={18}
                          />
                        )
                        : (
                          <ChevronDown
                            size={18}
                          />
                        )
                    }

                  </button>


                  {/* ========================================
                      DETALLE EXPANDIDO
                      ======================================== */}

                  {expanded && (

                    <div
                      className="patient-audit-event__detail"
                    >

                      {/* ====================================
                          DESCRIPCIÓN
                          ==================================== */}

                      {description && (

                        <div
                          className="patient-audit-reason"
                        >

                          <span>
                            Descripción
                          </span>


                          <strong>
                            {description}
                          </strong>

                        </div>

                      )}


                      {/* ====================================
                          MOTIVO
                          ==================================== */}

                      {reason && (

                        <div
                          className="patient-audit-reason"
                        >

                          <span>
                            Motivo
                          </span>


                          <strong>
                            {reason}
                          </strong>

                        </div>

                      )}


                      {/* ====================================
                          CAMBIOS
                          ==================================== */}

                      {
                        loadingDetail ===
                          event.id_evento

                          ? (

                            <div
                              className="patient-audit-loading-detail"
                            >

                              <LoaderCircle
                                size={20}
                                className="patient-audit-spin"
                              />

                              Cargando cambios...

                            </div>

                          )

                          : changes.length > 0

                            ? (

                              <div
                                className="patient-audit-changes"
                              >

                                {changes.map(
                                  (
                                    change,
                                  ) => (

                                    <div
                                      key={
                                        change.id_cambio
                                      }
                                      className="patient-audit-change"
                                    >

                                      <strong>
                                        {
                                          getFieldLabel(
                                            change
                                              .campo,
                                          )
                                        }
                                      </strong>


                                      <div>

                                        <span>
                                          Valor anterior
                                        </span>


                                        <p>
                                          {
                                            change
                                              .valor_anterior
                                            ??
                                            "—"
                                          }
                                        </p>

                                      </div>


                                      <div>

                                        <span>
                                          Valor nuevo
                                        </span>


                                        <p>
                                          {
                                            change
                                              .valor_nuevo
                                            ??
                                            "—"
                                          }
                                        </p>

                                      </div>

                                    </div>

                                  ),
                                )}

                              </div>

                            )

                            : (

                              <div
                                className="patient-audit-no-changes"
                              >
                                Esta acción no contiene cambios de campos.
                              </div>

                            )
                      }


                      {/* ====================================
                          USER AGENT
                          ==================================== */}

                      {event.user_agent && (

                        <div
                          className="patient-audit-agent"
                        >

                          <span>
                            Dispositivo / navegador
                          </span>


                          <p>
                            {
                              event
                                .user_agent
                            }
                          </p>

                        </div>

                      )}

                    </div>

                  )}

                </section>

              );

            },
          )}

        </div>

      )}

    </article>

  );

}