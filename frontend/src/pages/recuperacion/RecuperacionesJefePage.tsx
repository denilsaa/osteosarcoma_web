import {
  AlertCircle,
  Check,
  Clock3,
  LoaderCircle,
  LockKeyhole,
  Mail,
  RefreshCcw,
  RotateCcw,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  listarRecuperaciones,
  mensajeErrorRecuperacion,
  resolverRecuperacion,
  type DecisionRecuperacion,
  type EstadoRecuperacion,
  type RecuperacionJefatura,
} from "../../api/recuperaciones.api";

import "./RecuperacionesJefePage.css";


/* =========================================================
   TIPOS
   ========================================================= */

type FiltroEstado =
  | ""
  | EstadoRecuperacion;


/* =========================================================
   FECHA
   ========================================================= */

function fecha(
  valor?: string | null,
): string {

  if (
    !valor
  ) {

    return "—";

  }


  const date =
    new Date(
      valor
    );


  if (
    Number.isNaN(
      date.getTime()
    )
  ) {

    return valor;

  }


  return new Intl.DateTimeFormat(
    "es-BO",
    {

      dateStyle:
        "medium",

      timeStyle:
        "short",

    },
  ).format(
    date
  );

}


/* =========================================================
   TEXTO ESTADO
   ========================================================= */

function textoEstado(
  estado: string,
): string {

  switch (
    estado.toUpperCase()
  ) {

    case "PENDIENTE":

      return "Pendiente";


    case "APROBADA":

      return "Aprobada";


    case "RECHAZADA":

      return "Rechazada";


    case "UTILIZADA":

      return "Utilizada";


    case "EXPIRADA":

      return "Expirada";


    default:

      return estado;

  }

}


/* =========================================================
   CLASE ESTADO
   ========================================================= */

function claseEstado(
  estado: string,
): string {

  switch (
    estado.toUpperCase()
  ) {

    case "APROBADA":

      return (
        "recovery-request__status " +
        "recovery-request__status--approved"
      );


    case "RECHAZADA":

      return (
        "recovery-request__status " +
        "recovery-request__status--rejected"
      );


    case "UTILIZADA":

      return (
        "recovery-request__status " +
        "recovery-request__status--used"
      );


    case "EXPIRADA":

      return (
        "recovery-request__status " +
        "recovery-request__status--expired"
      );


    default:

      return (
        "recovery-request__status " +
        "recovery-request__status--pending"
      );

  }

}


/* =========================================================
   COMPONENTE
   ========================================================= */

export function RecuperacionesJefePage() {

  /* =======================================================
     LISTADO
     ======================================================= */

  const [
    solicitudes,
    setSolicitudes,
  ] = useState<
    RecuperacionJefatura[]
  >(
    []
  );


  const [
    filtro,
    setFiltro,
  ] = useState<FiltroEstado>(
    "PENDIENTE"
  );


  const [
    cargando,
    setCargando,
  ] = useState(
    true
  );


  const [
    error,
    setError,
  ] = useState(
    ""
  );


  const [
    mensaje,
    setMensaje,
  ] = useState(
    ""
  );


  /* =======================================================
     MODAL
     ======================================================= */

  const [
    seleccionada,
    setSeleccionada,
  ] = useState<
    RecuperacionJefatura
    | null
  >(
    null
  );


  const [
    decision,
    setDecision,
  ] = useState<
    DecisionRecuperacion
    | null
  >(
    null
  );


  const [
    observacion,
    setObservacion,
  ] = useState(
    ""
  );


  const [
    procesando,
    setProcesando,
  ] = useState(
    false
  );


  /* =======================================================
     CARGAR SOLICITUDES
     ======================================================= */

  const cargarSolicitudes =
    useCallback(
      async (
        estadoActual:
          FiltroEstado = filtro,
      ) => {

        try {

          setCargando(
            true
          );

          setError(
            ""
          );


          const response =
            await listarRecuperaciones(
              estadoActual
            );


          setSolicitudes(
            Array.isArray(
              response.resultados
            )
              ? response.resultados
              : []
          );

        } catch (
          err
        ) {

          setSolicitudes(
            []
          );


          setError(
            mensajeErrorRecuperacion(
              err
            )
          );

        } finally {

          setCargando(
            false
          );

        }

      },
      [
        filtro,
      ],
    );


  /* =======================================================
     CARGA INICIAL
     ======================================================= */

  useEffect(
    () => {

      void cargarSolicitudes(
        filtro
      );

    },
    [
      filtro,
      cargarSolicitudes,
    ],
  );


  /* =======================================================
     ABRIR RESOLUCIÓN
     ======================================================= */

  const abrirResolucion = (
    solicitud:
      RecuperacionJefatura,

    nuevaDecision:
      DecisionRecuperacion,
  ) => {

    /*
     * Protección visual adicional.
     *
     * El backend ya bloquea realmente
     * cualquier autoresolución.
     */

    if (
      solicitud.es_solicitud_propia
      ||
      !solicitud.puede_resolver
    ) {

      setError(
        "Esta solicitud no puede ser resuelta por el usuario actual."
      );

      return;

    }


    setSeleccionada(
      solicitud
    );


    setDecision(
      nuevaDecision
    );


    setObservacion(
      ""
    );


    setError(
      ""
    );


    setMensaje(
      ""
    );

  };


  /* =======================================================
     CERRAR MODAL
     ======================================================= */

  const cerrarResolucion =
    () => {

      if (
        procesando
      ) {

        return;

      }


      setSeleccionada(
        null
      );


      setDecision(
        null
      );


      setObservacion(
        ""
      );


      setError(
        ""
      );

    };


  /* =======================================================
     RESOLVER
     ======================================================= */

  const resolver =
    async () => {

      if (
        !seleccionada
        ||
        !decision
        ||
        procesando
      ) {

        return;

      }


      /* ---------------------------------------------------
         SEGUNDA PROTECCIÓN VISUAL
         --------------------------------------------------- */

      if (
        seleccionada
          .es_solicitud_propia
        ||
        !seleccionada
          .puede_resolver
      ) {

        setError(
          "No puede resolver su propia solicitud de recuperación."
        );

        return;

      }


      /* ---------------------------------------------------
         MOTIVO OBLIGATORIO EN RECHAZO
         --------------------------------------------------- */

      if (
        decision ===
        "RECHAZADA"
        &&
        !observacion.trim()
      ) {

        setError(
          "Debe indicar el motivo del rechazo."
        );

        return;

      }


      try {

        setProcesando(
          true
        );


        setError(
          ""
        );


        setMensaje(
          ""
        );


        const response =
          await resolverRecuperacion(

            seleccionada
              .id_solicitud,

            decision,

            observacion,

          );


        /* ================================================
           MENSAJE
           ================================================ */

        if (
          decision ===
          "APROBADA"
        ) {

          setMensaje(
            response.correo_enviado
              ? (
                  "La recuperación fue aprobada correctamente " +
                  "y el enlace seguro fue enviado al correo institucional."
                )
              : (
                  response.mensaje
                  ||
                  "La recuperación fue aprobada correctamente."
                )
          );

        } else {

          setMensaje(
            response.correo_enviado
              ? (
                  "La recuperación fue rechazada correctamente " +
                  "y el usuario fue notificado por correo."
                )
              : (
                  response.mensaje
                  ||
                  "La recuperación fue rechazada correctamente."
                )
          );

        }


        /* ================================================
           CERRAR MODAL
           ================================================ */

        setSeleccionada(
          null
        );


        setDecision(
          null
        );


        setObservacion(
          ""
        );


        /* ================================================
           RECARGAR
           ================================================ */

        await cargarSolicitudes(
          filtro
        );

      } catch (
        err
      ) {

        setError(
          mensajeErrorRecuperacion(
            err
          )
        );

      } finally {

        setProcesando(
          false
        );

      }

    };


  /* =======================================================
     REFRESCAR
     ======================================================= */

  const refrescar =
    async () => {

      setMensaje(
        ""
      );


      setError(
        ""
      );


      await cargarSolicitudes(
        filtro
      );

    };


  /* =======================================================
     CONTADOR DE SOLICITUDES PROPIAS
     ======================================================= */

  const propiasPendientes =
    solicitudes.filter(
      (
        solicitud
      ) =>
        solicitud.estado ===
        "PENDIENTE"
        &&
        solicitud
          .es_solicitud_propia
    ).length;


  /* =======================================================
     RENDER
     ======================================================= */

  return (

    <div
      className="recovery-admin-page"
    >

      {/* =================================================
          CABECERA
          ================================================= */}

      <section
        className="recovery-admin-header"
      >

        <div>

          <div
            className="recovery-admin-eyebrow"
          >

            <ShieldCheck
              size={17}
            />

            JEFATURA DE ONCOLOGÍA

          </div>


          <h1>
            Recuperaciones de contraseña
          </h1>


          <p>
            Revise las solicitudes de recuperación.
            Por seguridad, una solicitud realizada por
            un Jefe de Oncología debe ser resuelta por
            otro Jefe autorizado.
          </p>

        </div>


        <div
          className="recovery-admin-header__counter"
        >

          <strong>
            {solicitudes.length}
          </strong>

          <span>

            {
              filtro ===
              "PENDIENTE"
                ? "pendientes"
                : "solicitudes"
            }

          </span>

        </div>

      </section>


      {/* =================================================
          AVISO DE SOLICITUD PROPIA
          ================================================= */}

      {
        propiasPendientes > 0
        &&
        (
          <div
            className="recovery-admin-self-alert"
          >

            <LockKeyhole
              size={18}
            />

            <div>

              <strong>
                Tiene una solicitud propia pendiente
              </strong>

              <span>
                Por seguridad debe ser revisada por otro Jefe de Oncología.
              </span>

            </div>

          </div>
        )
      }


      {/* =================================================
          MENSAJES
          ================================================= */}

      {
        error
        &&
        (
          <div
            className="recovery-admin-alert recovery-admin-alert--error"
          >

            <AlertCircle
              size={18}
            />

            <span>
              {error}
            </span>

          </div>
        )
      }


      {
        mensaje
        &&
        (
          <div
            className="recovery-admin-alert recovery-admin-alert--success"
          >

            <Check
              size={18}
            />

            <span>
              {mensaje}
            </span>

          </div>
        )
      }


      {/* =================================================
          HERRAMIENTAS
          ================================================= */}

      <section
        className="recovery-admin-toolbar"
      >

        <div
          className="recovery-admin-toolbar__filter"
        >

          <label
            htmlFor="recovery-filter"
          >
            Estado
          </label>


          <select
            id="recovery-filter"
            value={filtro}
            onChange={(event) => {
              const nuevoFiltro = event.target.value as FiltroEstado;

              setMensaje("");
              setError("");
              setFiltro(nuevoFiltro);
            }}
            disabled={
              cargando ||
              procesando
            }
          >
            <option value="PENDIENTE">
              Pendientes
            </option>

            <option value="APROBADA">
              Aprobadas
            </option>

            <option value="RECHAZADA">
              Rechazadas
            </option>

            <option value="UTILIZADA">
              Utilizadas
            </option>

            <option value="EXPIRADA">
              Expiradas
            </option>

            <option value="">
              Todas
            </option>
          </select>
        </div>


        <button
          type="button"
          className="recovery-admin-refresh"
          onClick={
            () =>
              void refrescar()
          }
          disabled={
            cargando
            ||
            procesando
          }
        >

          {
            cargando
              ? (
                  <LoaderCircle
                    size={17}
                    className="recovery-admin-spin"
                  />
                )
              : (
                  <RefreshCcw
                    size={17}
                  />
                )
          }

          Actualizar

        </button>

      </section>


      {/* =================================================
          CARGANDO
          ================================================= */}

      {
        cargando
        &&
        (
          <section
            className="recovery-admin-loading"
          >

            <LoaderCircle
              size={28}
              className="recovery-admin-spin"
            />

            <div>

              <strong>
                Cargando solicitudes
              </strong>

              <span>
                Espere un momento...
              </span>

            </div>

          </section>
        )
      }


      {/* =================================================
          VACÍO
          ================================================= */}

      {
        !cargando
        &&
        solicitudes.length === 0
        &&
        (
          <section
            className="recovery-admin-empty"
          >

            <RotateCcw
              size={32}
            />

            <h2>
              No existen solicitudes
            </h2>

            <p>
              No se encontraron recuperaciones
              para el filtro seleccionado.
            </p>

          </section>
        )
      }


      {/* =================================================
          LISTADO
          ================================================= */}

      {
        !cargando
        &&
        solicitudes.length > 0
        &&
        (
          <section
            className="recovery-admin-list"
          >

            {
              solicitudes.map(
                (
                  solicitud
                ) => (

                  <article
                    key={
                      solicitud
                        .id_solicitud
                    }
                    className={
                      solicitud
                        .es_solicitud_propia
                        ? (
                            "recovery-request recovery-request--self"
                          )
                        : (
                            "recovery-request"
                          )
                    }
                  >

                    {/* =====================================
                        CABECERA
                        ===================================== */}

                    <header
                      className="recovery-request__header"
                    >

                      <div
                        className="recovery-request__user"
                      >

                        <div
                          className="recovery-request__avatar"
                        >

                          <UserRound
                            size={22}
                          />

                        </div>


                        <div>

                          <div
                            className="recovery-request__identity"
                          >

                            <h2>

                              {
                                solicitud
                                  .usuario
                                  .nombre_completo
                              }

                            </h2>


                            {
                              solicitud
                                .es_solicitud_propia
                              &&
                              (
                                <span
                                  className="recovery-request__self-badge"
                                >
                                  Tu solicitud
                                </span>
                              )
                            }

                          </div>


                          <span>

                            @
                            {
                              solicitud
                                .usuario
                                .nombre_usuario
                            }

                          </span>

                        </div>

                      </div>


                      <span
                        className={
                          claseEstado(
                            solicitud.estado
                          )
                        }
                      >

                        {
                          textoEstado(
                            solicitud.estado
                          )
                        }

                      </span>

                    </header>


                    {/* =====================================
                        INFORMACIÓN
                        ===================================== */}

                    <div
                      className="recovery-request__information"
                    >

                      <div
                        className="recovery-request__information-item"
                      >

                        <Mail
                          size={17}
                        />

                        <div>

                          <span>
                            Correo institucional
                          </span>

                          <strong>

                            {
                              solicitud
                                .usuario
                                .correo
                            }

                          </strong>

                        </div>

                      </div>


                      <div
                        className="recovery-request__information-item"
                      >

                        <Clock3
                          size={17}
                        />

                        <div>

                          <span>
                            Solicitud realizada
                          </span>

                          <strong>

                            {
                              fecha(
                                solicitud
                                  .fecha_solicitud
                              )
                            }

                          </strong>

                        </div>

                      </div>


                      <div
                        className="recovery-request__information-item"
                      >

                        <Clock3
                          size={17}
                        />

                        <div>

                          <span>
                            Vigencia
                          </span>

                          <strong>

                            {
                              fecha(
                                solicitud
                                  .fecha_expiracion
                              )
                            }

                          </strong>

                        </div>

                      </div>

                    </div>


                    {/* =====================================
                        ID
                        ===================================== */}

                    <div
                      className="recovery-request__id"
                    >

                      <span>
                        ID de solicitud
                      </span>

                      <code>

                        {
                          solicitud
                            .id_solicitud
                        }

                      </code>

                    </div>


                    {/* =====================================
                        SOLICITUD PROPIA
                        ===================================== */}

                    {
                      solicitud.estado ===
                      "PENDIENTE"
                      &&
                      solicitud
                        .es_solicitud_propia
                      &&
                      (
                        <div
                          className="recovery-request__self-notice"
                        >

                          <LockKeyhole
                            size={19}
                          />

                          <div>

                            <strong>
                              Esta es su solicitud
                            </strong>

                            <span>
                              No puede aprobarla ni rechazarla usted mismo. Debe ser revisada por otro Jefe de Oncología.
                            </span>

                          </div>

                        </div>
                      )
                    }


                    {/* =====================================
                        ACCIONES
                        ===================================== */}

                    {
                      solicitud.estado ===
                      "PENDIENTE"
                      &&
                      solicitud.puede_resolver
                      &&
                      !solicitud
                        .es_solicitud_propia
                      &&
                      (
                        <div
                          className="recovery-request__actions"
                        >

                          <button
                            type="button"
                            className="recovery-request__approve"
                            onClick={
                              () =>
                                abrirResolucion(
                                  solicitud,
                                  "APROBADA",
                                )
                            }
                          >

                            <Check
                              size={16}
                            />

                            Aprobar

                          </button>


                          <button
                            type="button"
                            className="recovery-request__reject"
                            onClick={
                              () =>
                                abrirResolucion(
                                  solicitud,
                                  "RECHAZADA",
                                )
                            }
                          >

                            <X
                              size={16}
                            />

                            Rechazar

                          </button>

                        </div>
                      )
                    }


                    {/* =====================================
                        RESOLUCIÓN
                        ===================================== */}

                    {
                      solicitud.resolucion
                      &&
                      (
                        <div
                          className="recovery-request__resolution"
                        >

                          <RotateCcw
                            size={16}
                          />


                          <div>

                            <strong>

                              {
                                solicitud
                                  .resolucion
                                  .decision ===
                                "APROBADA"
                                  ? (
                                      "Solicitud aprobada"
                                    )
                                  : (
                                      "Solicitud rechazada"
                                    )
                              }

                            </strong>


                            <span>

                              Resuelto por:
                              {" "}

                              {
                                solicitud
                                  .resolucion
                                  .resuelto_por
                                ||
                                "Jefatura"
                              }

                            </span>


                            <span>

                              {
                                fecha(
                                  solicitud
                                    .resolucion
                                    .fecha_resolucion
                                )
                              }

                            </span>


                            {
                              solicitud
                                .resolucion
                                .observacion
                              &&
                              (
                                <p>

                                  {
                                    solicitud
                                      .resolucion
                                      .observacion
                                  }

                                </p>
                              )
                            }

                          </div>

                        </div>
                      )
                    }

                  </article>

                )
              )
            }

          </section>
        )
      }


      {/* =================================================
          MODAL
          ================================================= */}

      {
        seleccionada
        &&
        decision
        &&
        (
          <div
            className="recovery-decision-modal__overlay"
            role="presentation"
            onMouseDown={
              (
                event
              ) => {

                if (
                  event.target ===
                  event.currentTarget
                ) {

                  cerrarResolucion();

                }

              }
            }
          >

            <section
              className="recovery-decision-modal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="recovery-decision-title"
            >

              <button
                type="button"
                className="recovery-decision-modal__close"
                onClick={
                  cerrarResolucion
                }
                disabled={
                  procesando
                }
                aria-label="Cerrar"
              >

                <X
                  size={19}
                />

              </button>


              <div
                className={`
                  recovery-decision-modal__icon
                  ${
                    decision ===
                    "APROBADA"
                      ? "recovery-decision-modal__icon--approve"
                      : "recovery-decision-modal__icon--reject"
                  }
                `}
              >

                {
                  decision ===
                  "APROBADA"
                    ? (
                        <Check
                          size={27}
                        />
                      )
                    : (
                        <X
                          size={27}
                        />
                      )
                }

              </div>


              <h2
                id="recovery-decision-title"
              >

                {
                  decision ===
                  "APROBADA"
                    ? "Aprobar recuperación"
                    : "Rechazar recuperación"
                }

              </h2>


              <p>

                Solicitud de
                {" "}

                <strong>

                  {
                    seleccionada
                      .usuario
                      .nombre_completo
                  }

                </strong>

              </p>


              <div
                className="recovery-decision-modal__email"
              >

                <Mail
                  size={16}
                />

                {
                  seleccionada
                    .usuario
                    .correo
                }

              </div>


              {
                decision ===
                "APROBADA"
                  ? (
                      <div
                        className="recovery-decision-modal__notice recovery-decision-modal__notice--approve"
                      >

                        <ShieldCheck
                          size={18}
                        />

                        <p>
                          Al aprobar, el sistema generará un enlace seguro y temporal que será enviado al correo institucional.
                        </p>

                      </div>
                    )
                  : (
                      <div
                        className="recovery-decision-modal__notice recovery-decision-modal__notice--reject"
                      >

                        <AlertCircle
                          size={18}
                        />

                        <p>
                          Al rechazar, esta solicitud quedará invalidada y el usuario será notificado por correo.
                        </p>

                      </div>
                    )
              }


              <label
                className="recovery-decision-modal__field"
              >

                <span>

                  {
                    decision ===
                    "APROBADA"
                      ? "Observación"
                      : "Motivo del rechazo"
                  }

                  {
                    decision ===
                    "RECHAZADA"
                    &&
                    (
                      <strong>
                        {" "}*
                      </strong>
                    )
                  }

                </span>


                <textarea
                  value={
                    observacion
                  }
                  onChange={
                    (
                      event
                    ) =>
                      setObservacion(
                        event.target.value
                      )
                  }
                  rows={4}
                  maxLength={500}
                  disabled={
                    procesando
                  }
                  placeholder={
                    decision ===
                    "APROBADA"
                      ? (
                          "Ej.: Solicitud verificada por Jefatura."
                        )
                      : (
                          "Indique el motivo del rechazo..."
                        )
                  }
                />


                <small>

                  {
                    observacion.length
                  }
                  /500

                </small>

              </label>


              {
                error
                &&
                (
                  <div
                    className="recovery-decision-modal__error"
                  >

                    <AlertCircle
                      size={16}
                    />

                    {error}

                  </div>
                )
              }


              <div
                className="recovery-decision-modal__actions"
              >

                <button
                  type="button"
                  className="recovery-admin-cancel"
                  onClick={
                    cerrarResolucion
                  }
                  disabled={
                    procesando
                  }
                >
                  Cancelar
                </button>


                <button
                  type="button"
                  className={
                    decision ===
                    "APROBADA"
                      ? (
                          "recovery-admin-confirm recovery-admin-confirm--approve"
                        )
                      : (
                          "recovery-admin-confirm recovery-admin-confirm--reject"
                        )
                  }
                  onClick={
                    () =>
                      void resolver()
                  }
                  disabled={
                    procesando
                    ||
                    (
                      decision ===
                      "RECHAZADA"
                      &&
                      !observacion.trim()
                    )
                  }
                >

                  {
                    procesando
                      ? (
                          <LoaderCircle
                            size={17}
                            className="recovery-admin-spin"
                          />
                        )
                      : decision ===
                        "APROBADA"
                        ? (
                            <Check
                              size={17}
                            />
                          )
                        : (
                            <X
                              size={17}
                            />
                          )
                  }


                  {
                    procesando
                      ? "Procesando..."
                      : decision ===
                        "APROBADA"
                        ? "Sí, aprobar"
                        : "Sí, rechazar"
                  }

                </button>

              </div>

            </section>

          </div>
        )
      }

    </div>

  );

}