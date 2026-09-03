import {
  AlertCircle,
  Check,
  Clock3,
  LoaderCircle,
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
  type RecuperacionJefatura,
} from "../../api/recuperaciones.api";

import "./RecuperacionesJefePage.css";


// ==========================================================
// TIPOS
// ==========================================================

type Decision =
  | "APROBADA"
  | "RECHAZADA";


type FiltroEstado =
  | ""
  | "PENDIENTE"
  | "APROBADA"
  | "RECHAZADA"
  | "UTILIZADA"
  | "EXPIRADA";


// ==========================================================
// UTILIDADES
// ==========================================================

function fecha(
  valor?: string | null,
): string {

  if (!valor) {
    return "—";
  }

  const date =
    new Date(valor);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return valor;
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


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


function claseEstado(
  estado: string,
): string {

  switch (
    estado.toUpperCase()
  ) {

    case "APROBADA":
      return "recovery-request__status recovery-request__status--approved";

    case "RECHAZADA":
      return "recovery-request__status recovery-request__status--rejected";

    case "UTILIZADA":
      return "recovery-request__status recovery-request__status--used";

    case "EXPIRADA":
      return "recovery-request__status recovery-request__status--expired";

    default:
      return "recovery-request__status recovery-request__status--pending";
  }
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function RecuperacionesJefePage() {

  // ========================================================
  // LISTADO
  // ========================================================

  const [
    solicitudes,
    setSolicitudes,
  ] =
    useState<
      RecuperacionJefatura[]
    >([]);


  const [
    filtro,
    setFiltro,
  ] =
    useState<FiltroEstado>(
      "PENDIENTE",
    );


  const [
    cargando,
    setCargando,
  ] =
    useState(true);


  const [
    error,
    setError,
  ] =
    useState("");


  const [
    mensaje,
    setMensaje,
  ] =
    useState("");


  // ========================================================
  // MODAL
  // ========================================================

  const [
    seleccionada,
    setSeleccionada,
  ] =
    useState<
      RecuperacionJefatura | null
    >(null);


  const [
    decision,
    setDecision,
  ] =
    useState<
      Decision | null
    >(null);


  const [
    observacion,
    setObservacion,
  ] =
    useState("");


  const [
    procesando,
    setProcesando,
  ] =
    useState(false);


  // ========================================================
  // CARGAR SOLICITUDES
  // ========================================================

  const cargarSolicitudes =
    useCallback(
      async (
        estadoActual:
          FiltroEstado = filtro,
      ) => {

        try {

          setCargando(true);

          setError("");

          const response =
            await listarRecuperaciones(
              estadoActual,
            );

          setSolicitudes(
            Array.isArray(
              response.resultados,
            )
              ? response.resultados
              : [],
          );

        } catch (err) {

          setSolicitudes([]);

          setError(
            mensajeErrorRecuperacion(
              err,
            ),
          );

        } finally {

          setCargando(false);
        }
      },
      [
        filtro,
      ],
    );


  // ========================================================
  // CARGA INICIAL / CAMBIO DE FILTRO
  // ========================================================

  useEffect(
    () => {

      void cargarSolicitudes(
        filtro,
      );

    },
    [
      filtro,
      cargarSolicitudes,
    ],
  );


  // ========================================================
  // ABRIR MODAL
  // ========================================================

  const abrirResolucion =
    (
      solicitud:
        RecuperacionJefatura,

      nuevaDecision:
        Decision,
    ) => {

      setSeleccionada(
        solicitud,
      );

      setDecision(
        nuevaDecision,
      );

      setObservacion("");

      setError("");

      setMensaje("");
    };


  // ========================================================
  // CERRAR MODAL
  // ========================================================

  const cerrarResolucion =
    () => {

      if (
        procesando
      ) {
        return;
      }

      setSeleccionada(null);

      setDecision(null);

      setObservacion("");
    };


  // ========================================================
  // RESOLVER
  // ========================================================

  const resolver =
    async () => {

      if (
        !seleccionada ||
        !decision ||
        procesando
      ) {
        return;
      }


      // ----------------------------------------------------
      // PARA RECHAZO EXIGIMOS MOTIVO
      // ----------------------------------------------------

      if (
        decision ===
          "RECHAZADA" &&
        !observacion.trim()
      ) {

        setError(
          "Debe indicar el motivo del rechazo.",
        );

        return;
      }


      try {

        setProcesando(true);

        setError("");

        setMensaje("");


        // ==================================================
        // AQUÍ OCURRE EL POST REAL AL BACKEND
        // ==================================================

        const response =
          await resolverRecuperacion(

            seleccionada
              .id_solicitud,

            decision,

            observacion,

          );


        // ==================================================
        // MENSAJE DE ÉXITO
        // ==================================================

        if (
          decision ===
          "APROBADA"
        ) {

          setMensaje(
            response.correo_enviado
              ? (
                  "La recuperación fue aprobada correctamente " +
                  "y el enlace seguro fue enviado al correo del oncólogo."
                )
              : (
                  response.mensaje ||
                  "La recuperación fue aprobada correctamente."
                ),
          );

        } else {

          setMensaje(
            response.correo_enviado
              ? (
                  "La recuperación fue rechazada correctamente " +
                  "y se notificó al oncólogo por correo."
                )
              : (
                  response.mensaje ||
                  "La recuperación fue rechazada correctamente."
                ),
          );
        }


        // ==================================================
        // CERRAR MODAL
        // ==================================================

        setSeleccionada(null);

        setDecision(null);

        setObservacion("");


        // ==================================================
        // RECARGAR LISTADO DESDE BACKEND
        // ==================================================

        await cargarSolicitudes(
          filtro,
        );


      } catch (err) {

        setError(
          mensajeErrorRecuperacion(
            err,
          ),
        );

      } finally {

        setProcesando(false);
      }
    };


  // ========================================================
  // REFRESCAR
  // ========================================================

  const refrescar =
    async () => {

      setMensaje("");

      await cargarSolicitudes(
        filtro,
      );
    };


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="recovery-admin-page">


      {/* ====================================================
          CABECERA
          ==================================================== */}

      <section className="recovery-admin-header">

        <div>

          <div className="recovery-admin-eyebrow">

            <ShieldCheck
              size={17}
            />

            JEFATURA DE ONCOLOGÍA

          </div>


          <h1>
            Recuperaciones de contraseña
          </h1>


          <p>
            Revise las solicitudes realizadas
            por los oncólogos y autorice o
            rechace el restablecimiento de
            credenciales.
          </p>

        </div>


        <div className="recovery-admin-header__counter">

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


      {/* ====================================================
          MENSAJES
          ==================================================== */}

      {
        error && (

          <div className="recovery-admin-alert recovery-admin-alert--error">

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
        mensaje && (

          <div className="recovery-admin-alert recovery-admin-alert--success">

            <Check
              size={18}
            />

            <span>
              {mensaje}
            </span>

          </div>
        )
      }


      {/* ====================================================
          HERRAMIENTAS
          ==================================================== */}

      <section className="recovery-admin-toolbar">

        <div className="recovery-admin-toolbar__filter">

          <label
            htmlFor="recovery-filter"
          >
            Estado
          </label>


          <select
            id="recovery-filter"
            value={filtro}
            onChange={(event) => {
              const nuevoFiltro =
                event.target.value as FiltroEstado;

              setMensaje("");

              setFiltro(
                nuevoFiltro,
              );
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
            cargando ||
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


      {/* ====================================================
          CARGANDO
          ==================================================== */}

      {
        cargando && (

          <section className="recovery-admin-loading">

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


      {/* ====================================================
          SIN RESULTADOS
          ==================================================== */}

      {
        !cargando &&
        solicitudes.length === 0 && (

          <section className="recovery-admin-empty">

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


      {/* ====================================================
          LISTADO
          ==================================================== */}

      {
        !cargando &&
        solicitudes.length > 0 && (

          <section className="recovery-admin-list">

            {
              solicitudes.map(
                (
                  solicitud,
                ) => (

                  <article

                    key={
                      solicitud
                        .id_solicitud
                    }

                    className="recovery-request"

                  >


                    {/* ========================================
                        CABECERA TARJETA
                        ======================================== */}

                    <header className="recovery-request__header">

                      <div className="recovery-request__user">

                        <div className="recovery-request__avatar">

                          <UserRound
                            size={22}
                          />

                        </div>


                        <div>

                          <h2>

                            {
                              solicitud
                                .usuario
                                .nombre_completo
                            }

                          </h2>


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
                            solicitud.estado,
                          )
                        }
                      >

                        {
                          textoEstado(
                            solicitud.estado,
                          )
                        }

                      </span>

                    </header>


                    {/* ========================================
                        INFORMACIÓN
                        ======================================== */}

                    <div className="recovery-request__information">


                      <div className="recovery-request__information-item">

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


                      <div className="recovery-request__information-item">

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
                                  .fecha_solicitud,
                              )
                            }
                          </strong>

                        </div>

                      </div>


                      <div className="recovery-request__information-item">

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
                                  .fecha_expiracion,
                              )
                            }
                          </strong>

                        </div>

                      </div>

                    </div>


                    {/* ========================================
                        ID
                        ======================================== */}

                    <div className="recovery-request__id">

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


                    {/* ========================================
                        BOTONES PENDIENTE
                        ======================================== */}

                    {
                      solicitud.estado ===
                        "PENDIENTE" && (

                        <div className="recovery-request__actions">


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


                    {/* ========================================
                        RESOLUCIÓN
                        ======================================== */}

                    {
                      solicitud.resolucion && (

                        <div className="recovery-request__resolution">

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

                              Resuelto por:{" "}

                              {
                                solicitud
                                  .resolucion
                                  .resuelto_por ||
                                "Jefatura"
                              }

                            </span>


                            <span>

                              {
                                fecha(
                                  solicitud
                                    .resolucion
                                    .fecha_resolucion,
                                )
                              }

                            </span>


                            {
                              solicitud
                                .resolucion
                                .observacion && (

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
                ),
              )
            }

          </section>
        )
      }


      {/* ====================================================
          MODAL DE CONFIRMACIÓN
          ==================================================== */}

      {
        seleccionada &&
        decision && (

          <div

            className="recovery-decision-modal__overlay"

            role="presentation"

            onMouseDown={
              (
                event,
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


              {/* ==============================================
                  CERRAR
                  ============================================== */}

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


              {/* ==============================================
                  ICONO
                  ============================================== */}

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


              {/* ==============================================
                  TÍTULO
                  ============================================== */}

              <h2
                id="recovery-decision-title"
              >

                {
                  decision ===
                    "APROBADA"
                    ? (
                        "Aprobar recuperación"
                      )
                    : (
                        "Rechazar recuperación"
                      )
                }

              </h2>


              <p>

                Solicitud de{" "}

                <strong>

                  {
                    seleccionada
                      .usuario
                      .nombre_completo
                  }

                </strong>

              </p>


              <div className="recovery-decision-modal__email">

                <Mail
                  size={16}
                />

                {
                  seleccionada
                    .usuario
                    .correo
                }

              </div>


              {/* ==============================================
                  INFORMACIÓN SEGÚN DECISIÓN
                  ============================================== */}

              {
                decision ===
                  "APROBADA"
                  ? (

                      <div className="recovery-decision-modal__notice recovery-decision-modal__notice--approve">

                        <ShieldCheck
                          size={18}
                        />

                        <p>

                          Al aprobar la solicitud,
                          el sistema generará un
                          enlace seguro y temporal
                          para cambiar la contraseña
                          y lo enviará al correo
                          institucional del oncólogo.

                        </p>

                      </div>

                    )
                  : (

                      <div className="recovery-decision-modal__notice recovery-decision-modal__notice--reject">

                        <AlertCircle
                          size={18}
                        />

                        <p>

                          Al rechazar la solicitud,
                          el usuario no podrá cambiar
                          su contraseña mediante esta
                          recuperación y será
                          notificado por correo.

                        </p>

                      </div>

                    )
              }


              {/* ==============================================
                  OBSERVACIÓN
                  ============================================== */}

              <label className="recovery-decision-modal__field">

                <span>

                  {
                    decision ===
                      "APROBADA"
                      ? (
                          "Observación"
                        )
                      : (
                          "Motivo del rechazo"
                        )
                  }

                  {
                    decision ===
                      "RECHAZADA" && (
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
                      event,
                    ) =>

                      setObservacion(
                        event
                          .target
                          .value,
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
                          "Ej.: Solicitud verificada y aprobada por Jefatura."
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


              {/* ==============================================
                  ERROR DENTRO DEL MODAL
                  ============================================== */}

              {
                error && (

                  <div className="recovery-decision-modal__error">

                    <AlertCircle
                      size={16}
                    />

                    {error}

                  </div>
                )
              }


              {/* ==============================================
                  BOTONES
                  ============================================== */}

              <div className="recovery-decision-modal__actions">


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


                {/* ============================================
                    ESTE ES EL BOTÓN QUE HACE EL POST REAL
                    ============================================ */}

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
                    procesando ||
                    (
                      decision ===
                        "RECHAZADA" &&
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
                      ? (
                          "Procesando..."
                        )
                      : decision ===
                          "APROBADA"
                        ? (
                            "Sí, aprobar"
                          )
                        : (
                            "Sí, rechazar"
                          )
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