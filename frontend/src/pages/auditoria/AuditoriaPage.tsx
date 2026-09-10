import {
  Activity,
  AlertCircle,
  ArrowRight,
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  ChevronUp,
  Clock3,
  Database,
  Eye,
  FileClock,
  Filter,
  Layers3,
  LoaderCircle,
  LockKeyhole,
  RefreshCcw,
  Search,
  ShieldCheck,
  ShieldX,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
  type FormEvent,
} from "react";

import {
  listarEventosAuditoria,
  mensajeErrorAuditoria,
  obtenerCatalogosAuditoria,
  obtenerEventoAuditoria,
  type CatalogosAuditoria,
  type DetalleEventoAuditoria,
  type EventoAuditoria,
  type FiltrosAuditoria,
  type RespuestaPaginadaAuditoria,
} from "../../api/auditoria.api";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./AuditoriaPage.css";


// ==========================================================
// CONFIGURACIÓN
// ==========================================================

const POR_PAGINA = 10;


// ==========================================================
// FILTROS
// ==========================================================

type FiltrosPantalla = {
  servicio: string;

  modulo: string;

  accion: string;

  resultado: string;

  entidad: string;
};


const FILTROS_INICIALES:
  FiltrosPantalla = {

    servicio: "",

    modulo: "",

    accion: "",

    resultado: "",

    entidad: "",

  };


// ==========================================================
// UTILIDADES
// ==========================================================

function normalizarFecha(
  valor: string,
): string {

  if (
    valor.includes(
      "T",
    )
  ) {
    return valor;
  }


  return valor.replace(
    " ",
    "T",
  );

}


function formatearFecha(
  valor?: string | null,
): string {

  if (!valor) {

    return "—";

  }


  const fecha =
    new Date(
      normalizarFecha(
        valor,
      ),
    );


  if (
    Number.isNaN(
      fecha.getTime(),
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
  ).format(
    fecha,
  );

}


function nombreActor(
  evento: EventoAuditoria,
): string {

  const nombre =
    evento.detalle_json
      ?.actor_nombre;


  if (
    typeof nombre === "string"
    &&
    nombre.trim()
  ) {

    return nombre.trim();

  }


  if (
    evento.actor_usuario_uuid
  ) {

    return (
      "Usuario " +
      evento
        .actor_usuario_uuid
        .slice(
          0,
          8,
        )
    );

  }


  return "Sistema";

}


function rolActor(
  evento: EventoAuditoria,
): string {

  const rol =
    evento.detalle_json
      ?.actor_rol;


  if (
    typeof rol === "string"
    &&
    rol.trim()
  ) {

    return rol.trim();

  }


  return (
    evento.actor_usuario_uuid
      ? "Usuario autenticado"
      : "Proceso del sistema"
  );

}


function descripcionEvento(
  evento: EventoAuditoria,
): string {

  const descripcion =
    evento.detalle_json
      ?.descripcion;


  if (
    typeof descripcion === "string"
    &&
    descripcion.trim()
  ) {

    return descripcion.trim();

  }


  return (
    `${evento.accion_nombre || evento.accion} ` +
    `en ${evento.modulo_nombre || evento.modulo}.`
  );

}


function motivoEvento(
  evento: EventoAuditoria,
): string | null {

  const motivo =
    evento.detalle_json
      ?.motivo;


  if (
    typeof motivo === "string"
    &&
    motivo.trim()
  ) {

    return motivo.trim();

  }


  return null;

}


function nombreCampo(
  campo: string,
): string {

  const limpio =
    campo
      .replace(
        /^permiso:/i,
        "",
      )
      .replaceAll(
        "_",
        " ",
      );


  return limpio
    .toLowerCase()
    .replace(
      /\b\w/g,
      (
        letra,
      ) =>
        letra.toUpperCase(),
    );

}


function valorVisible(
  valor: unknown,
): string {

  if (
    valor === null
    ||
    valor === undefined
    ||
    valor === ""
  ) {

    return "—";

  }


  if (
    typeof valor === "boolean"
  ) {

    return (
      valor
        ? "Sí"
        : "No"
    );

  }


  if (
    Array.isArray(
      valor,
    )
  ) {

    return (
      valor.length > 0
        ? valor
            .map(
              (
                item,
              ) =>
                String(
                  item,
                ),
            )
            .join(
              ", ",
            )
        : "Ninguno"
    );

  }


  if (
    typeof valor === "object"
  ) {

    return JSON.stringify(
      valor,
      null,
      2,
    );

  }


  return String(
    valor,
  );

}


function claseResultado(
  resultado: string,
): string {

  switch (
    resultado.toUpperCase()
  ) {

    case "EXITOSO":

      return (
        "audit-result " +
        "audit-result--success"
      );


    case "DENEGADO":

      return (
        "audit-result " +
        "audit-result--denied"
      );


    case "FALLIDO":

      return (
        "audit-result " +
        "audit-result--failed"
      );


    default:

      return "audit-result";

  }

}


function textoResultado(
  evento: EventoAuditoria,
): string {

  return (
    evento.resultado_nombre
    ||
    evento.resultado
  );

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function AuditoriaPage() {

  const {
    tieneRol,
  } = useAuth();


  const esJefe =
    tieneRol(
      "JEFE_ONCOLOGIA",
    );


  // ========================================================
  // CATÁLOGOS
  // ========================================================

  const [
    catalogos,
    setCatalogos,
  ] =
    useState<CatalogosAuditoria>(
      {
        servicios: [],

        modulos: [],

        acciones: [],

        resultados: [],
      },
    );


  // ========================================================
  // FILTROS
  // ========================================================

  const [
    filtrosFormulario,
    setFiltrosFormulario,
  ] =
    useState<FiltrosPantalla>(
      FILTROS_INICIALES,
    );


  const [
    filtrosAplicados,
    setFiltrosAplicados,
  ] =
    useState<FiltrosPantalla>(
      FILTROS_INICIALES,
    );


  const [
    filtrosVisibles,
    setFiltrosVisibles,
  ] =
    useState(
      false,
    );


  // ========================================================
  // PAGINACIÓN
  // ========================================================

  const [
    pagina,
    setPagina,
  ] =
    useState(
      1,
    );


  // ========================================================
  // EVENTOS
  // ========================================================

  const [
    respuesta,
    setRespuesta,
  ] =
    useState<
      RespuestaPaginadaAuditoria | null
    >(
      null,
    );


  const [
    cargando,
    setCargando,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState(
      "",
    );


  const [
    recarga,
    setRecarga,
  ] =
    useState(
      0,
    );


  // ========================================================
  // DETALLE
  // ========================================================

  const [
    detalle,
    setDetalle,
  ] =
    useState<
      DetalleEventoAuditoria | null
    >(
      null,
    );


  const [
    detalleVisible,
    setDetalleVisible,
  ] =
    useState(
      false,
    );


  const [
    cargandoDetalle,
    setCargandoDetalle,
  ] =
    useState(
      false,
    );


  const [
    errorDetalle,
    setErrorDetalle,
  ] =
    useState(
      "",
    );


  // ========================================================
  // CARGAR CATÁLOGOS
  // ========================================================

  useEffect(
    () => {

      if (!esJefe) {

        return;

      }


      const controller =
        new AbortController();


      async function cargar() {

        try {

          const data =
            await obtenerCatalogosAuditoria(
              controller.signal,
            );


          setCatalogos(
            data,
          );

        } catch (
          requestError
        ) {

          const mensaje =
            mensajeErrorAuditoria(
              requestError,
            );


          if (mensaje) {

            setError(
              mensaje,
            );

          }

        }

      }


      void cargar();


      return () =>
        controller.abort();

    },
    [
      esJefe,
    ],
  );


  // ========================================================
  // CARGAR EVENTOS
  // ========================================================

  useEffect(
    () => {

      if (!esJefe) {

        return;

      }


      const controller =
        new AbortController();


      async function cargar() {

        setCargando(
          true,
        );


        setError(
          "",
        );


        try {

          const filtros:
            FiltrosAuditoria = {

              page:
                pagina,

              per_page:
                POR_PAGINA,

              servicio:
                filtrosAplicados
                  .servicio,

              modulo:
                filtrosAplicados
                  .modulo,

              accion:
                filtrosAplicados
                  .accion,

              resultado:
                filtrosAplicados
                  .resultado,

              entidad:
                filtrosAplicados
                  .entidad,

            };


          const data =
            await listarEventosAuditoria(
              filtros,
              controller.signal,
            );


          setRespuesta(
            data,
          );

        } catch (
          requestError
        ) {

          const mensaje =
            mensajeErrorAuditoria(
              requestError,
            );


          if (mensaje) {

            setError(
              mensaje,
            );

          }

        } finally {

          if (
            !controller
              .signal
              .aborted
          ) {

            setCargando(
              false,
            );

          }

        }

      }


      void cargar();


      return () =>
        controller.abort();

    },
    [
      esJefe,
      filtrosAplicados,
      pagina,
      recarga,
    ],
  );


  // ========================================================
  // CERRAR MODAL CON ESC
  // ========================================================

  useEffect(
    () => {

      if (!detalleVisible) {

        return;

      }


      const cerrar =
        (
          event:
            KeyboardEvent,
        ) => {

          if (
            event.key ===
            "Escape"
          ) {

            setDetalleVisible(
              false,
            );

          }

        };


      window.addEventListener(
        "keydown",
        cerrar,
      );


      return () =>
        window.removeEventListener(
          "keydown",
          cerrar,
        );

    },
    [
      detalleVisible,
    ],
  );


  // ========================================================
  // MÓDULOS DISPONIBLES
  // ========================================================

  const modulosDisponibles =
    useMemo(
      () => {

        if (
          !filtrosFormulario
            .servicio
        ) {

          return catalogos.modulos;

        }


        return (
          catalogos
            .modulos
            .filter(
              (
                modulo,
              ) =>
                modulo.servicio
                ===
                filtrosFormulario
                  .servicio,
            )
        );

      },
      [
        catalogos.modulos,
        filtrosFormulario.servicio,
      ],
    );


  // ========================================================
  // EVENTOS DE PÁGINA
  // ========================================================

  const eventos =
    respuesta?.data
    ??
    [];


  const exitososPagina =
    eventos.filter(
      (
        evento,
      ) =>
        evento.resultado
        ===
        "EXITOSO",
    ).length;


  const problemasPagina =
    eventos.filter(
      (
        evento,
      ) =>
        (
          evento.resultado
          ===
          "DENEGADO"
        )
        ||
        (
          evento.resultado
          ===
          "FALLIDO"
        ),
    ).length;


  const cambiosPagina =
    eventos.filter(
      (
        evento,
      ) =>
        evento
          .cantidad_cambios
        >
        0,
    ).length;


  // ========================================================
  // CANTIDAD FILTROS
  // ========================================================

  const filtrosActivos =
    Object.values(
      filtrosAplicados,
    ).filter(
      (
        value,
      ) =>
        value.trim() !== "",
    ).length;


  // ========================================================
  // APLICAR
  // ========================================================

  function aplicarFiltros(
    event:
      FormEvent<HTMLFormElement>,
  ) {

    event.preventDefault();


    setPagina(
      1,
    );


    setFiltrosAplicados(
      {
        ...filtrosFormulario,

        entidad:
          filtrosFormulario
            .entidad
            .trim(),
      },
    );

  }


  // ========================================================
  // LIMPIAR
  // ========================================================

  function limpiarFiltros() {

    setFiltrosFormulario(
      FILTROS_INICIALES,
    );


    setFiltrosAplicados(
      FILTROS_INICIALES,
    );


    setPagina(
      1,
    );

  }


  // ========================================================
  // DETALLE
  // ========================================================

  async function abrirDetalle(
    idEvento:
      string,
  ) {

    setDetalleVisible(
      true,
    );


    setDetalle(
      null,
    );


    setErrorDetalle(
      "",
    );


    setCargandoDetalle(
      true,
    );


    try {

      const data =
        await obtenerEventoAuditoria(
          idEvento,
        );


      setDetalle(
        data,
      );

    } catch (
      requestError
    ) {

      setErrorDetalle(
        mensajeErrorAuditoria(
          requestError,
        ),
      );

    } finally {

      setCargandoDetalle(
        false,
      );

    }

  }


  // ========================================================
  // ACCESO
  // ========================================================

  if (!esJefe) {

    return (

      <section
        className="audit-access-denied"
      >

        <div
          className="audit-access-denied__icon"
        >

          <ShieldX
            size={31}
          />

        </div>


        <h1>
          Acceso restringido
        </h1>


        <p>
          El historial de auditoría está disponible
          únicamente para Jefatura de Oncología.
        </p>

      </section>

    );

  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="audit-page"
    >

      {/* ==================================================
          HEADER
          ================================================== */}

      <header
        className="audit-page__heading"
      >

        <div>

          <div
            className="audit-page__eyebrow"
          >

            <ShieldCheck
              size={16}
            />

            CONTROL Y TRAZABILIDAD

          </div>


          <h1>
            Auditoría
          </h1>


          <p>
            Revise las acciones más recientes del sistema
            y consulte el detalle solo cuando sea necesario.
          </p>

        </div>


        <div
          className="audit-page__readonly"
        >

          <LockKeyhole
            size={17}
          />


          <div>

            <strong>
              Historial protegido
            </strong>

            <span>
              Solo lectura
            </span>

          </div>

        </div>

      </header>


      {/* ==================================================
          RESUMEN
          ================================================== */}

      <div
        className="audit-summary"
      >

        <article>

          <div
            className="audit-summary__icon"
          >

            <Database
              size={20}
            />

          </div>


          <div>

            <span>
              Eventos
            </span>

            <strong>
              {
                respuesta?.total
                ??
                0
              }
            </strong>

            <small>
              Total encontrado
            </small>

          </div>

        </article>


        <article>

          <div
            className="audit-summary__icon audit-summary__icon--success"
          >

            <CheckCircle2
              size={20}
            />

          </div>


          <div>

            <span>
              Exitosos
            </span>

            <strong>
              {exitososPagina}
            </strong>

            <small>
              Página actual
            </small>

          </div>

        </article>


        <article>

          <div
            className="audit-summary__icon audit-summary__icon--danger"
          >

            <AlertCircle
              size={20}
            />

          </div>


          <div>

            <span>
              Alertas
            </span>

            <strong>
              {problemasPagina}
            </strong>

            <small>
              Fallidos o denegados
            </small>

          </div>

        </article>


        <article>

          <div
            className="audit-summary__icon audit-summary__icon--changes"
          >

            <FileClock
              size={20}
            />

          </div>


          <div>

            <span>
              Con cambios
            </span>

            <strong>
              {cambiosPagina}
            </strong>

            <small>
              Página actual
            </small>

          </div>

        </article>

      </div>


      {/* ==================================================
          BARRA DE CONTROL
          ================================================== */}

      <div
        className="audit-controlbar"
      >

        <div>

          <div
            className="audit-controlbar__icon"
          >

            <Clock3
              size={18}
            />

          </div>


          <div>

            <strong>
              Actividad reciente
            </strong>

            <span>
              Los últimos eventos aparecen primero.
            </span>

          </div>

        </div>


        <div
          className="audit-controlbar__actions"
        >

          <button
            type="button"
            className="audit-button audit-button--ghost"
            onClick={
              () =>
                setRecarga(
                  (
                    value,
                  ) =>
                    value + 1,
                )
            }
            disabled={
              cargando
            }
          >

            <RefreshCcw
              size={16}
              className={
                cargando
                  ? "audit-spin"
                  : ""
              }
            />

            Actualizar

          </button>


          <button
            type="button"
            className={
              filtrosActivos > 0
                ? "audit-filter-toggle audit-filter-toggle--active"
                : "audit-filter-toggle"
            }
            onClick={
              () =>
                setFiltrosVisibles(
                  (
                    value,
                  ) =>
                    !value,
                )
            }
          >

            <Filter
              size={16}
            />


            Filtros


            {
              filtrosActivos > 0
              &&
              (

                <span
                  className="audit-filter-toggle__count"
                >
                  {filtrosActivos}
                </span>

              )
            }


            {
              filtrosVisibles
                ? (
                    <ChevronUp
                      size={15}
                    />
                  )
                : (
                    <ChevronDown
                      size={15}
                    />
                  )
            }

          </button>

        </div>

      </div>


      {/* ==================================================
          FILTROS AVANZADOS
          ================================================== */}

      {
        filtrosVisibles
        &&
        (

          <form
            className="audit-filters"
            onSubmit={
              aplicarFiltros
            }
          >

            <div
              className="audit-filters__heading"
            >

              <div>

                <Filter
                  size={17}
                />


                <div>

                  <strong>
                    Filtros avanzados
                  </strong>

                  <span>
                    Combine criterios únicamente cuando necesite
                    localizar un evento específico.
                  </span>

                </div>

              </div>

            </div>


            <div
              className="audit-filters__grid"
            >

              <label>

                <span>
                  Servicio
                </span>


                <select
                  value={
                    filtrosFormulario.servicio
                  }
                  onChange={
                    (
                      event,
                    ) => {

                      const servicio =
                        event
                          .target
                          .value;


                      setFiltrosFormulario(
                        (
                          current,
                        ) => ({
                          ...current,

                          servicio,

                          modulo: "",
                        }),
                      );

                    }
                  }
                >

                  <option
                    value=""
                  >
                    Todos los servicios
                  </option>


                  {
                    catalogos
                      .servicios
                      .map(
                        (
                          servicio,
                        ) => (

                          <option
                            key={
                              servicio.codigo
                            }
                            value={
                              servicio.codigo
                            }
                          >

                            {
                              servicio.nombre
                            }

                          </option>

                        ),
                      )
                  }

                </select>

              </label>


              <label>

                <span>
                  Módulo
                </span>


                <select
                  value={
                    filtrosFormulario.modulo
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setFiltrosFormulario(
                        (
                          current,
                        ) => ({
                          ...current,

                          modulo:
                            event
                              .target
                              .value,
                        }),
                      )
                  }
                >

                  <option
                    value=""
                  >
                    Todos los módulos
                  </option>


                  {
                    modulosDisponibles.map(
                      (
                        modulo,
                      ) => (

                        <option
                          key={
                            `${modulo.servicio}-${modulo.codigo}`
                          }
                          value={
                            modulo.codigo
                          }
                        >

                          {
                            modulo.nombre
                          }

                        </option>

                      ),
                    )
                  }

                </select>

              </label>


              <label>

                <span>
                  Acción
                </span>


                <select
                  value={
                    filtrosFormulario.accion
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setFiltrosFormulario(
                        (
                          current,
                        ) => ({
                          ...current,

                          accion:
                            event
                              .target
                              .value,
                        }),
                      )
                  }
                >

                  <option
                    value=""
                  >
                    Todas las acciones
                  </option>


                  {
                    catalogos
                      .acciones
                      .map(
                        (
                          accion,
                        ) => (

                          <option
                            key={
                              accion.codigo
                            }
                            value={
                              accion.codigo
                            }
                          >

                            {
                              accion.nombre
                            }

                          </option>

                        ),
                      )
                  }

                </select>

              </label>


              <label>

                <span>
                  Resultado
                </span>


                <select
                  value={
                    filtrosFormulario.resultado
                  }
                  onChange={
                    (
                      event,
                    ) =>
                      setFiltrosFormulario(
                        (
                          current,
                        ) => ({
                          ...current,

                          resultado:
                            event
                              .target
                              .value,
                        }),
                      )
                  }
                >

                  <option
                    value=""
                  >
                    Todos los resultados
                  </option>


                  {
                    catalogos
                      .resultados
                      .map(
                        (
                          resultado,
                        ) => (

                          <option
                            key={
                              resultado.codigo
                            }
                            value={
                              resultado.codigo
                            }
                          >

                            {
                              resultado.nombre
                            }

                          </option>

                        ),
                      )
                  }

                </select>

              </label>


              <label
                className="audit-filters__entity"
              >

                <span>
                  Entidad o identificador
                </span>


                <div
                  className="audit-filters__search"
                >

                  <Search
                    size={16}
                  />


                  <input
                    type="search"
                    value={
                      filtrosFormulario.entidad
                    }
                    onChange={
                      (
                        event,
                      ) =>
                        setFiltrosFormulario(
                          (
                            current,
                          ) => ({
                            ...current,

                            entidad:
                              event
                                .target
                                .value,
                          }),
                        )
                    }
                    placeholder="UUID, paciente, sesión, entidad..."
                  />

                </div>

              </label>

            </div>


            <div
              className="audit-filters__actions"
            >

              <button
                type="button"
                className="audit-button audit-button--secondary"
                onClick={
                  limpiarFiltros
                }
              >

                Limpiar

              </button>


              <button
                type="submit"
                className="audit-button audit-button--primary"
              >

                <Search
                  size={16}
                />

                Aplicar filtros

              </button>

            </div>

          </form>

        )
      }


      {/* ==================================================
          FILTROS ACTIVOS
          ================================================== */}

      {
        filtrosActivos > 0
        &&
        (

          <div
            className="audit-active-filters"
          >

            <div>

              <Filter
                size={15}
              />

              <strong>
                {
                  filtrosActivos
                }
              </strong>

              <span>
                filtros aplicados
              </span>

            </div>


            <button
              type="button"
              onClick={
                limpiarFiltros
              }
            >

              Limpiar filtros

              <X
                size={14}
              />

            </button>

          </div>

        )
      }


      {/* ==================================================
          ERROR
          ================================================== */}

      {
        error
        &&
        (

          <div
            className="audit-error"
          >

            <AlertCircle
              size={19}
            />

            <span>
              {error}
            </span>

          </div>

        )
      }


      {/* ==================================================
          LISTADO
          ================================================== */}

      <article
        className="audit-events-card"
      >

        <header
          className="audit-events-card__header"
        >

          <div>

            <Activity
              size={19}
            />


            <div>

              <h2>
                Últimos eventos
              </h2>

              <p>
                Seleccione un registro para consultar todos sus detalles.
              </p>

            </div>

          </div>


          {
            respuesta
            &&
            (

              <span
                className="audit-events-card__range"
              >
                {
                  respuesta.from
                  ??
                  0
                }
                {" - "}
                {
                  respuesta.to
                  ??
                  0
                }
                {" de "}
                {
                  respuesta.total
                }
              </span>

            )
          }

        </header>


        {
          cargando
            ? (

                <div
                  className="audit-loading"
                >

                  <LoaderCircle
                    size={27}
                    className="audit-spin"
                  />

                  <span>
                    Cargando eventos...
                  </span>

                </div>

              )
            : eventos.length === 0
              ? (

                  <div
                    className="audit-empty"
                  >

                    <FileClock
                      size={30}
                    />


                    <strong>
                      No se encontraron eventos
                    </strong>


                    <span>
                      Modifique los filtros o actualice el historial.
                    </span>

                  </div>

                )
              : (

                  <div
                    className="audit-events"
                  >

                    {
                      eventos.map(
                        (
                          evento,
                        ) => (

                          <button
                            key={
                              evento.id_evento
                            }
                            type="button"
                            className="audit-event"
                            onClick={
                              () =>
                                void abrirDetalle(
                                  evento.id_evento,
                                )
                            }
                          >

                            <div
                              className="audit-event__actor"
                            >

                              <div
                                className="audit-event__avatar"
                              >

                                <UserRound
                                  size={17}
                                />

                              </div>


                              <div>

                                <strong>
                                  {
                                    nombreActor(
                                      evento,
                                    )
                                  }
                                </strong>


                                <span>
                                  {
                                    rolActor(
                                      evento,
                                    )
                                  }
                                </span>

                              </div>

                            </div>


                            <div
                              className="audit-event__action"
                            >

                              <strong>
                                {
                                  evento.accion_nombre
                                  ||
                                  evento.accion
                                }
                              </strong>


                              <span>
                                {
                                  descripcionEvento(
                                    evento,
                                  )
                                }
                              </span>

                            </div>


                            <div
                              className="audit-event__module"
                            >

                              <span>
                                {
                                  evento.modulo_nombre
                                  ||
                                  evento.modulo
                                }
                              </span>


                              <small>
                                {
                                  evento.servicio_nombre
                                  ||
                                  evento.servicio
                                }
                              </small>

                            </div>


                            <div
                              className="audit-event__result"
                            >

                              <span
                                className={
                                  claseResultado(
                                    evento.resultado,
                                  )
                                }
                              >

                                {
                                  textoResultado(
                                    evento,
                                  )
                                }

                              </span>


                              {
                                evento.cantidad_cambios > 0
                                &&
                                (

                                  <small>
                                    {
                                      evento.cantidad_cambios
                                    }
                                    {" "}
                                    cambio
                                    {
                                      evento.cantidad_cambios === 1
                                        ? ""
                                        : "s"
                                    }
                                  </small>

                                )
                              }

                            </div>


                            <div
                              className="audit-event__date"
                            >

                              <Clock3
                                size={14}
                              />

                              <span>
                                {
                                  formatearFecha(
                                    evento.fecha_evento,
                                  )
                                }
                              </span>

                            </div>


                            <div
                              className="audit-event__open"
                            >

                              <Eye
                                size={17}
                              />

                              <ArrowRight
                                size={15}
                              />

                            </div>

                          </button>

                        ),
                      )
                    }

                  </div>

                )
        }


        {/* ==================================================
            PAGINACIÓN
            ================================================== */}

        {
          respuesta
          &&
          respuesta.last_page > 1
          &&
          (

            <footer
              className="audit-pagination"
            >

              <span>
                Página
                {" "}
                <strong>
                  {
                    respuesta.current_page
                  }
                </strong>
                {" de "}
                <strong>
                  {
                    respuesta.last_page
                  }
                </strong>
              </span>


              <div>

                <button
                  type="button"
                  disabled={
                    pagina <= 1
                    ||
                    cargando
                  }
                  onClick={
                    () =>
                      setPagina(
                        (
                          current,
                        ) =>
                          Math.max(
                            1,
                            current - 1,
                          ),
                      )
                  }
                >

                  <ChevronLeft
                    size={17}
                  />

                  Anterior

                </button>


                <button
                  type="button"
                  disabled={
                    pagina
                    >=
                    respuesta.last_page
                    ||
                    cargando
                  }
                  onClick={
                    () =>
                      setPagina(
                        (
                          current,
                        ) =>
                          Math.min(
                            respuesta.last_page,
                            current + 1,
                          ),
                      )
                  }
                >

                  Siguiente

                  <ChevronRight
                    size={17}
                  />

                </button>

              </div>

            </footer>

          )
        }

      </article>


      {/* ==================================================
          MODAL DETALLE
          ================================================== */}

      {
        detalleVisible
        &&
        (

          <div
            className="audit-modal"
            role="presentation"
            onMouseDown={
              (
                event,
              ) => {

                if (
                  event.target
                  ===
                  event.currentTarget
                ) {

                  setDetalleVisible(
                    false,
                  );

                }

              }
            }
          >

            <article
              className="audit-modal__panel"
              role="dialog"
              aria-modal="true"
              aria-label="Detalle del evento de auditoría"
            >

              <header
                className="audit-modal__header"
              >

                <div>

                  <div
                    className="audit-modal__icon"
                  >

                    <FileClock
                      size={20}
                    />

                  </div>


                  <div>

                    <span>
                      Evento de auditoría
                    </span>

                    <h2>
                      Detalle de la acción
                    </h2>

                  </div>

                </div>


                <button
                  type="button"
                  aria-label="Cerrar"
                  onClick={
                    () =>
                      setDetalleVisible(
                        false,
                      )
                  }
                >

                  <X
                    size={20}
                  />

                </button>

              </header>


              {
                cargandoDetalle
                  ? (

                      <div
                        className="audit-modal__loading"
                      >

                        <LoaderCircle
                          size={27}
                          className="audit-spin"
                        />

                        Cargando detalle...

                      </div>

                    )
                  : errorDetalle
                    ? (

                        <div
                          className="audit-error"
                        >

                          <AlertCircle
                            size={19}
                          />

                          {errorDetalle}

                        </div>

                      )
                    : detalle
                      ? (

                          <div
                            className="audit-modal__content"
                          >

                            {/* ==============================
                                RESUMEN
                                ============================== */}

                            <div
                              className="audit-detail-summary"
                            >

                              <div>

                                <span>
                                  Acción
                                </span>

                                <strong>
                                  {
                                    detalle
                                      .evento
                                      .accion_nombre
                                    ||
                                    detalle
                                      .evento
                                      .accion
                                  }
                                </strong>

                              </div>


                              <div>

                                <span>
                                  Resultado
                                </span>

                                <strong
                                  className={
                                    claseResultado(
                                      detalle
                                        .evento
                                        .resultado,
                                    )
                                  }
                                >
                                  {
                                    textoResultado(
                                      detalle.evento,
                                    )
                                  }
                                </strong>

                              </div>


                              <div>

                                <span>
                                  Fecha
                                </span>

                                <strong>
                                  {
                                    formatearFecha(
                                      detalle
                                        .evento
                                        .fecha_evento,
                                    )
                                  }
                                </strong>

                              </div>

                            </div>


                            {/* ==============================
                                INFORMACIÓN
                                ============================== */}

                            <section
                              className="audit-detail-section"
                            >

                              <header>

                                <Activity
                                  size={17}
                                />

                                <h3>
                                  Información del evento
                                </h3>

                              </header>


                              <div
                                className="audit-detail-grid"
                              >

                                <div>

                                  <span>
                                    Usuario
                                  </span>

                                  <strong>
                                    {
                                      nombreActor(
                                        detalle.evento,
                                      )
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Rol
                                  </span>

                                  <strong>
                                    {
                                      rolActor(
                                        detalle.evento,
                                      )
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Servicio
                                  </span>

                                  <strong>
                                    {
                                      detalle
                                        .evento
                                        .servicio_nombre
                                      ||
                                      detalle
                                        .evento
                                        .servicio
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Módulo
                                  </span>

                                  <strong>
                                    {
                                      detalle
                                        .evento
                                        .modulo_nombre
                                      ||
                                      detalle
                                        .evento
                                        .modulo
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Entidad
                                  </span>

                                  <strong>
                                    {
                                      detalle
                                        .evento
                                        .entidad_tipo
                                      ||
                                      "—"
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Identificador
                                  </span>

                                  <strong
                                    className="audit-code"
                                  >
                                    {
                                      detalle
                                        .evento
                                        .entidad_id
                                      ||
                                      "—"
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Dirección IP
                                  </span>

                                  <strong>
                                    {
                                      detalle
                                        .evento
                                        .direccion_ip
                                      ||
                                      "—"
                                    }
                                  </strong>

                                </div>


                                <div>

                                  <span>
                                    Correlation ID
                                  </span>

                                  <strong
                                    className="audit-code"
                                  >
                                    {
                                      detalle
                                        .evento
                                        .correlation_id
                                      ||
                                      "—"
                                    }
                                  </strong>

                                </div>

                              </div>

                            </section>


                            {/* ==============================
                                DESCRIPCIÓN
                                ============================== */}

                            <section
                              className="audit-detail-section"
                            >

                              <header>

                                <Layers3
                                  size={17}
                                />

                                <h3>
                                  Acción realizada
                                </h3>

                              </header>


                              <div
                                className="audit-description"
                              >

                                <p>
                                  {
                                    descripcionEvento(
                                      detalle.evento,
                                    )
                                  }
                                </p>


                                {
                                  motivoEvento(
                                    detalle.evento,
                                  )
                                  &&
                                  (

                                    <div
                                      className="audit-description__reason"
                                    >

                                      <span>
                                        Motivo
                                      </span>

                                      <strong>
                                        {
                                          motivoEvento(
                                            detalle.evento,
                                          )
                                        }
                                      </strong>

                                    </div>

                                  )
                                }

                              </div>

                            </section>


                            {/* ==============================
                                CAMBIOS
                                ============================== */}

                            <section
                              className="audit-detail-section"
                            >

                              <header>

                                <FileClock
                                  size={17}
                                />

                                <h3>
                                  Cambios registrados
                                </h3>


                                <span
                                  className="audit-detail-section__count"
                                >
                                  {
                                    detalle.cambios.length
                                  }
                                </span>

                              </header>


                              {
                                detalle.cambios.length === 0
                                  ? (

                                      <div
                                        className="audit-no-changes"
                                      >

                                        <CheckCircle2
                                          size={19}
                                        />

                                        Este evento no modificó información.

                                      </div>

                                    )
                                  : (

                                      <div
                                        className="audit-changes"
                                      >

                                        {
                                          detalle
                                            .cambios
                                            .map(
                                              (
                                                cambio,
                                              ) => (

                                                <div
                                                  key={
                                                    cambio.id_cambio
                                                  }
                                                  className="audit-change"
                                                >

                                                  <div
                                                    className="audit-change__field"
                                                  >

                                                    {
                                                      nombreCampo(
                                                        cambio.campo,
                                                      )
                                                    }

                                                  </div>


                                                  <div>

                                                    <span>
                                                      Anterior
                                                    </span>

                                                    <pre>
                                                      {
                                                        valorVisible(
                                                          cambio.valor_anterior,
                                                        )
                                                      }
                                                    </pre>

                                                  </div>


                                                  <ArrowRight
                                                    size={17}
                                                  />


                                                  <div>

                                                    <span>
                                                      Nuevo
                                                    </span>

                                                    <pre>
                                                      {
                                                        valorVisible(
                                                          cambio.valor_nuevo,
                                                        )
                                                      }
                                                    </pre>

                                                  </div>

                                                </div>

                                              ),
                                            )
                                        }

                                      </div>

                                    )
                              }

                            </section>

                          </div>

                        )
                      : null
              }

            </article>

          </div>

        )
      }

    </section>

  );

}