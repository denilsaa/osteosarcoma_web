import {
  Activity,
  AlertCircle,
  ArrowRight,
  Ban,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
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
    valor.includes("T")
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

  if (
    !valor
  ) {
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
      dateStyle:
        "medium",

      timeStyle:
        "short",
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
    typeof nombre ===
      "string" &&
    nombre.trim()
  ) {

    return nombre.trim();
  }


  if (
    evento.actor_usuario_uuid
  ) {

    return (
      "Usuario " +
      evento.actor_usuario_uuid
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
    typeof rol ===
      "string" &&
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
    typeof descripcion ===
      "string" &&
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
    typeof motivo ===
      "string" &&
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
    valor === null ||
    valor === undefined ||
    valor === ""
  ) {

    return "—";
  }


  if (
    typeof valor ===
    "boolean"
  ) {

    return valor
      ? "Sí"
      : "No";
  }


  if (
    Array.isArray(
      valor,
    )
  ) {

    return (
      valor.length
        ? valor
            .map(
              (
                item,
              ) =>
                String(
                  item,
                ),
            )
            .join(", ")
        : "Ninguno"
    );
  }


  if (
    typeof valor ===
    "object"
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
      return "audit-result audit-result--success";

    case "DENEGADO":
      return "audit-result audit-result--denied";

    case "FALLIDO":
      return "audit-result audit-result--failed";

    default:
      return "audit-result";
  }
}


function textoResultado(
  evento: EventoAuditoria,
): string {

  return (
    evento.resultado_nombre ||
    evento.resultado
  );
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function AuditoriaPage() {

  const {
    tieneRol,
  } =
    useAuth();


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
    useState<CatalogosAuditoria>({
      servicios: [],
      modulos: [],
      acciones: [],
      resultados: [],
    });


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


  // ========================================================
  // PAGINACIÓN
  // ========================================================

  const [
    pagina,
    setPagina,
  ] =
    useState(1);


  // ========================================================
  // EVENTOS
  // ========================================================

  const [
    respuesta,
    setRespuesta,
  ] =
    useState<
      RespuestaPaginadaAuditoria | null
    >(null);


  const [
    cargando,
    setCargando,
  ] =
    useState(false);


  const [
    error,
    setError,
  ] =
    useState("");


  const [
    recarga,
    setRecarga,
  ] =
    useState(0);


  // ========================================================
  // DETALLE
  // ========================================================

  const [
    detalle,
    setDetalle,
  ] =
    useState<
      DetalleEventoAuditoria | null
    >(null);


  const [
    detalleVisible,
    setDetalleVisible,
  ] =
    useState(false);


  const [
    cargandoDetalle,
    setCargandoDetalle,
  ] =
    useState(false);


  const [
    errorDetalle,
    setErrorDetalle,
  ] =
    useState("");


  // ========================================================
  // CATÁLOGOS
  // ========================================================

  useEffect(
    () => {

      if (
        !esJefe
      ) {
        return;
      }


      const controller =
        new AbortController();


      const cargar =
        async () => {

          try {

            const data =
              await obtenerCatalogosAuditoria(
                controller.signal,
              );

            setCatalogos(
              data,
            );

          } catch (
            err
          ) {

            const mensaje =
              mensajeErrorAuditoria(
                err,
              );

            if (
              mensaje
            ) {

              setError(
                mensaje,
              );
            }
          }
        };


      void cargar();


      return () =>
        controller.abort();

    },
    [
      esJefe,
    ],
  );


  // ========================================================
  // EVENTOS
  // ========================================================

  useEffect(
    () => {

      if (
        !esJefe
      ) {
        return;
      }


      const controller =
        new AbortController();


      const cargar =
        async () => {

          try {

            setCargando(
              true,
            );

            setError("");


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
            err
          ) {

            const mensaje =
              mensajeErrorAuditoria(
                err,
              );


            if (
              mensaje
            ) {

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
        };


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
  // ESCAPE MODAL
  // ========================================================

  useEffect(
    () => {

      if (
        !detalleVisible
      ) {
        return;
      }


      const cerrarConEscape =
        (
          event: KeyboardEvent,
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
        cerrarConEscape,
      );


      return () =>
        window.removeEventListener(
          "keydown",
          cerrarConEscape,
        );

    },
    [
      detalleVisible,
    ],
  );


  // ========================================================
  // MÓDULOS SEGÚN SERVICIO
  // ========================================================

  const modulosDisponibles =
    useMemo(
      () => {

        if (
          !filtrosFormulario
            .servicio
        ) {

          return (
            catalogos.modulos
          );
        }


        return (
          catalogos.modulos
          .filter(
            (
              modulo,
            ) =>
              modulo.servicio ===
              filtrosFormulario
                .servicio,
          )
        );
      },
      [
        catalogos.modulos,
        filtrosFormulario
          .servicio,
      ],
    );


  // ========================================================
  // EVENTOS ACTUALES
  // ========================================================

  const eventos =
    respuesta?.data ||
    [];


  const exitososPagina =
    eventos.filter(
      (
        evento,
      ) =>
        evento.resultado ===
        "EXITOSO",
    ).length;


  const denegadosPagina =
    eventos.filter(
      (
        evento,
      ) =>
        evento.resultado ===
        "DENEGADO",
    ).length;


  const conCambiosPagina =
    eventos.filter(
      (
        evento,
      ) =>
        evento
          .cantidad_cambios >
        0,
    ).length;


  // ========================================================
  // APLICAR FILTROS
  // ========================================================

  const aplicarFiltros =
    (
      event:
        FormEvent<HTMLFormElement>,
    ) => {

      event.preventDefault();


      setPagina(
        1,
      );


      setFiltrosAplicados({
        ...filtrosFormulario,

        entidad:
          filtrosFormulario
            .entidad
            .trim(),
      });
    };


  // ========================================================
  // LIMPIAR
  // ========================================================

  const limpiarFiltros =
    () => {

      setFiltrosFormulario(
        FILTROS_INICIALES,
      );

      setFiltrosAplicados(
        FILTROS_INICIALES,
      );

      setPagina(
        1,
      );
    };


  // ========================================================
  // ABRIR DETALLE
  // ========================================================

  const abrirDetalle =
    async (
      idEvento: string,
    ) => {

      setDetalleVisible(
        true,
      );

      setDetalle(
        null,
      );

      setErrorDetalle("");

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
        err
      ) {

        setErrorDetalle(
          mensajeErrorAuditoria(
            err,
          ),
        );

      } finally {

        setCargandoDetalle(
          false,
        );
      }
    };


  // ========================================================
  // ACCESO
  // ========================================================

  if (
    !esJefe
  ) {

    return (

      <section className="audit-access-denied">

        <div className="audit-access-denied__icon">

          <ShieldX
            size={31}
          />

        </div>

        <h1>
          Acceso restringido
        </h1>

        <p>
          El historial de auditoría
          está disponible únicamente
          para Jefatura de Oncología.
        </p>

      </section>
    );
  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section className="audit-page">


      {/* ==================================================
          CABECERA
          ================================================== */}

      <header className="audit-page__heading">


        <div>

          <div className="audit-page__eyebrow">

            <ShieldCheck
              size={16}
            />

            CONTROL Y TRAZABILIDAD

          </div>


          <h1>
            Historial de auditoría
          </h1>


          <p>
            Consulte quién realizó
            una acción, cuándo ocurrió,
            qué información cambió y
            si la operación fue exitosa,
            fallida o denegada.
          </p>

        </div>


        <div className="audit-page__readonly">

          <LockKeyhole
            size={17}
          />

          <div>

            <strong>
              Historial inmutable
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

      <div className="audit-summary">


        <article>

          <div className="audit-summary__icon">

            <Database
              size={20}
            />

          </div>

          <div>

            <span>
              Eventos registrados
            </span>

            <strong>
              {
                respuesta
                  ?.total ??
                0
              }
            </strong>

          </div>

        </article>


        <article>

          <div className="audit-summary__icon audit-summary__icon--success">

            <CheckCircle2
              size={20}
            />

          </div>

          <div>

            <span>
              Exitosos en página
            </span>

            <strong>
              {exitososPagina}
            </strong>

          </div>

        </article>


        <article>

          <div className="audit-summary__icon audit-summary__icon--danger">

            <Ban
              size={20}
            />

          </div>

          <div>

            <span>
              Denegados en página
            </span>

            <strong>
              {denegadosPagina}
            </strong>

          </div>

        </article>


        <article>

          <div className="audit-summary__icon audit-summary__icon--changes">

            <FileClock
              size={20}
            />

          </div>

          <div>

            <span>
              Con cambios
            </span>

            <strong>
              {conCambiosPagina}
            </strong>

          </div>

        </article>


      </div>


      {/* ==================================================
          FILTROS
          ================================================== */}

      <form

        className="audit-filters"

        onSubmit={
          aplicarFiltros
        }

      >


        <div className="audit-filters__heading">

          <div>

            <Filter
              size={17}
            />

            <div>

              <strong>
                Filtros de consulta
              </strong>

              <span>
                Combine criterios para localizar eventos.
              </span>

            </div>

          </div>


          <button

            type="button"

            className="audit-button audit-button--ghost"

            onClick={
              () => {

                setRecarga(
                  (
                    valor,
                  ) =>
                    valor + 1,
                );
              }
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

        </div>


        <div className="audit-filters__grid">


          {/* SERVICIO */}

          <label>

            <span>
              Servicio
            </span>

            <select

              value={
                filtrosFormulario
                  .servicio
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
                      actual,
                    ) => ({
                      ...actual,

                      servicio,

                      modulo: "",
                    }),
                  );
                }
              }

            >

              <option value="">
                Todos
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
                        {servicio.nombre}
                      </option>
                    ),
                  )
              }

            </select>

          </label>


          {/* MÓDULO */}

          <label>

            <span>
              Módulo
            </span>

            <select

              value={
                filtrosFormulario
                  .modulo
              }

              onChange={
                (
                  event,
                ) =>

                  setFiltrosFormulario(
                    (
                      actual,
                    ) => ({
                      ...actual,

                      modulo:
                        event
                          .target
                          .value,
                    }),
                  )
              }

            >

              <option value="">
                Todos
              </option>

              {
                modulosDisponibles
                  .map(
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
                        {modulo.nombre}
                      </option>
                    ),
                  )
              }

            </select>

          </label>


          {/* ACCIÓN */}

          <label>

            <span>
              Acción
            </span>

            <select

              value={
                filtrosFormulario
                  .accion
              }

              onChange={
                (
                  event,
                ) =>

                  setFiltrosFormulario(
                    (
                      actual,
                    ) => ({
                      ...actual,

                      accion:
                        event
                          .target
                          .value,
                    }),
                  )
              }

            >

              <option value="">
                Todas
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
                        {accion.nombre}
                      </option>
                    ),
                  )
              }

            </select>

          </label>


          {/* RESULTADO */}

          <label>

            <span>
              Resultado
            </span>

            <select

              value={
                filtrosFormulario
                  .resultado
              }

              onChange={
                (
                  event,
                ) =>

                  setFiltrosFormulario(
                    (
                      actual,
                    ) => ({
                      ...actual,

                      resultado:
                        event
                          .target
                          .value,
                    }),
                  )
              }

            >

              <option value="">
                Todos
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
                        {resultado.nombre}
                      </option>
                    ),
                  )
              }

            </select>

          </label>


          {/* ENTIDAD */}

          <label className="audit-filters__entity">

            <span>
              Entidad o identificador
            </span>

            <div className="audit-filters__search">

              <Search
                size={16}
              />

              <input

                type="search"

                value={
                  filtrosFormulario
                    .entidad
                }

                onChange={
                  (
                    event,
                  ) =>

                    setFiltrosFormulario(
                      (
                        actual,
                      ) => ({
                        ...actual,

                        entidad:
                          event
                            .target
                            .value,
                      }),
                    )
                }

                placeholder="UUID, usuario, paciente, sesión..."

              />

            </div>

          </label>


        </div>


        <div className="audit-filters__actions">

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

            disabled={
              cargando
            }

          >

            <Filter
              size={16}
            />

            Aplicar filtros

          </button>

        </div>


      </form>


      {/* ==================================================
          ERROR
          ================================================== */}

      {
        error && (

          <div className="audit-alert">

            <AlertCircle
              size={18}
            />

            <div>

              <strong>
                No se pudo cargar Auditoría
              </strong>

              <span>
                {error}
              </span>

            </div>

          </div>
        )
      }


      {/* ==================================================
          TABLA
          ================================================== */}

      <section className="audit-table-card">


        <div className="audit-table-card__header">

          <div>

            <Activity
              size={18}
            />

            <div>

              <h2>
                Eventos registrados
              </h2>

              <p>
                Historial ordenado desde
                la acción más reciente.
              </p>

            </div>

          </div>


          <span>

            {
              respuesta
                ? (
                    `${respuesta.from ?? 0}–${respuesta.to ?? 0} de ${respuesta.total}`
                  )
                : (
                    "0 eventos"
                  )
            }

          </span>

        </div>


        {
          cargando
            ? (

                <div className="audit-loading">

                  <LoaderCircle
                    size={27}
                    className="audit-spin"
                  />

                  <strong>
                    Consultando historial...
                  </strong>

                  <span>
                    Espere un momento.
                  </span>

                </div>

              )
            : eventos.length ===
                0
              ? (

                  <div className="audit-empty">

                    <Search
                      size={29}
                    />

                    <strong>
                      No se encontraron eventos
                    </strong>

                    <span>
                      Cambie los filtros e intente nuevamente.
                    </span>

                  </div>

                )
              : (

                  <div className="audit-table-wrap">

                    <table className="audit-table">

                      <thead>

                        <tr>

                          <th>
                            Fecha y hora
                          </th>

                          <th>
                            Actor
                          </th>

                          <th>
                            Acción
                          </th>

                          <th>
                            Módulo
                          </th>

                          <th>
                            Entidad
                          </th>

                          <th>
                            Resultado
                          </th>

                          <th>
                            Cambios
                          </th>

                          <th aria-label="Detalle" />

                        </tr>

                      </thead>


                      <tbody>

                        {
                          eventos.map(
                            (
                              evento,
                            ) => (

                              <tr
                                key={
                                  evento.id_evento
                                }
                              >


                                <td>

                                  <div className="audit-date">

                                    <Clock3
                                      size={15}
                                    />

                                    <span>
                                      {
                                        formatearFecha(
                                          evento.fecha_evento,
                                        )
                                      }
                                    </span>

                                  </div>

                                </td>


                                <td>

                                  <div className="audit-actor">

                                    <div className="audit-actor__icon">

                                      <UserRound
                                        size={15}
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

                                </td>


                                <td>

                                  <div className="audit-action">

                                    <strong>
                                      {
                                        evento
                                          .accion_nombre ||
                                        evento.accion
                                      }
                                    </strong>

                                    <span>
                                      {evento.accion}
                                    </span>

                                  </div>

                                </td>


                                <td>

                                  <div className="audit-module">

                                    <Layers3
                                      size={15}
                                    />

                                    <div>

                                      <strong>
                                        {
                                          evento
                                            .modulo_nombre ||
                                          evento.modulo
                                        }
                                      </strong>

                                      <span>
                                        {
                                          evento
                                            .servicio_nombre ||
                                          evento.servicio
                                        }
                                      </span>

                                    </div>

                                  </div>

                                </td>


                                <td>

                                  <div className="audit-entity">

                                    <strong>
                                      {
                                        evento.entidad_tipo ||
                                        "—"
                                      }
                                    </strong>

                                    <span
                                      title={
                                        evento.entidad_id ||
                                        ""
                                      }
                                    >
                                      {
                                        evento.entidad_id ||
                                        "Sin identificador"
                                      }
                                    </span>

                                  </div>

                                </td>


                                <td>

                                  <span
                                    className={
                                      claseResultado(
                                        evento.resultado,
                                      )
                                    }
                                  >

                                    {
                                      evento.resultado ===
                                        "EXITOSO"
                                        ? (
                                            <CheckCircle2
                                              size={14}
                                            />
                                          )
                                        : evento.resultado ===
                                            "DENEGADO"
                                          ? (
                                              <Ban
                                                size={14}
                                              />
                                            )
                                          : (
                                              <AlertCircle
                                                size={14}
                                              />
                                            )
                                    }

                                    {
                                      textoResultado(
                                        evento,
                                      )
                                    }

                                  </span>

                                </td>


                                <td>

                                  <span
                                    className={
                                      evento
                                        .cantidad_cambios >
                                      0
                                        ? "audit-changes audit-changes--active"
                                        : "audit-changes"
                                    }
                                  >

                                    {
                                      evento
                                        .cantidad_cambios
                                    }

                                  </span>

                                </td>


                                <td>

                                  <button

                                    type="button"

                                    className="audit-detail-button"

                                    onClick={
                                      () =>
                                        void abrirDetalle(
                                          evento.id_evento,
                                        )
                                    }

                                    title="Ver detalle"

                                  >

                                    <Eye
                                      size={17}
                                    />

                                  </button>

                                </td>


                              </tr>
                            ),
                          )
                        }

                      </tbody>

                    </table>

                  </div>
                )
        }


        {/* ================================================
            PAGINACIÓN
            ================================================ */}

        {
          respuesta &&
          respuesta.total >
            0 && (

            <footer className="audit-pagination">


              <div>

                Página{" "}

                <strong>
                  {
                    respuesta.current_page
                  }
                </strong>

                {" "}de{" "}

                <strong>
                  {
                    respuesta.last_page
                  }
                </strong>

              </div>


              <div className="audit-pagination__buttons">


                <button

                  type="button"

                  onClick={
                    () =>
                      setPagina(
                        (
                          actual,
                        ) =>
                          Math.max(
                            1,
                            actual - 1,
                          ),
                      )
                  }

                  disabled={
                    cargando ||
                    respuesta.current_page <=
                      1
                  }

                >

                  <ChevronLeft
                    size={17}
                  />

                  Anterior

                </button>


                <button

                  type="button"

                  onClick={
                    () =>
                      setPagina(
                        (
                          actual,
                        ) =>
                          Math.min(
                            respuesta.last_page,
                            actual + 1,
                          ),
                      )
                  }

                  disabled={
                    cargando ||
                    respuesta.current_page >=
                      respuesta.last_page
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


      </section>


      {/* ==================================================
          MODAL DETALLE
          ================================================== */}

      {
        detalleVisible && (

          <div

            className="audit-modal__overlay"

            role="presentation"

            onMouseDown={
              (
                event,
              ) => {

                if (
                  event.target ===
                  event.currentTarget
                ) {

                  setDetalleVisible(
                    false,
                  );
                }
              }
            }

          >

            <section

              className="audit-modal"

              role="dialog"

              aria-modal="true"

              aria-labelledby="audit-detail-title"

            >


              <header className="audit-modal__header">

                <div>

                  <div className="audit-modal__icon">

                    <FileClock
                      size={21}
                    />

                  </div>

                  <div>

                    <span>
                      EVENTO DE AUDITORÍA
                    </span>

                    <h2
                      id="audit-detail-title"
                    >
                      Detalle del evento
                    </h2>

                  </div>

                </div>


                <button

                  type="button"

                  onClick={
                    () =>
                      setDetalleVisible(
                        false,
                      )
                  }

                  aria-label="Cerrar"

                >

                  <X
                    size={19}
                  />

                </button>

              </header>


              {
                cargandoDetalle
                  ? (

                      <div className="audit-modal__loading">

                        <LoaderCircle
                          size={27}
                          className="audit-spin"
                        />

                        Consultando evento...

                      </div>

                    )
                  : errorDetalle
                    ? (

                        <div className="audit-modal__error">

                          <AlertCircle
                            size={19}
                          />

                          {errorDetalle}

                        </div>

                      )
                    : detalle
                      ? (

                          <>


                            {/* ACTOR */}

                            <div className="audit-modal__actor">

                              <div className="audit-modal__actor-icon">

                                <UserRound
                                  size={21}
                                />

                              </div>

                              <div>

                                <span>
                                  Acción realizada por
                                </span>

                                <strong>
                                  {
                                    nombreActor(
                                      detalle.evento,
                                    )
                                  }
                                </strong>

                                <small>
                                  {
                                    rolActor(
                                      detalle.evento,
                                    )
                                  }
                                </small>

                              </div>


                              <span
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

                              </span>

                            </div>


                            {/* INFORMACIÓN GENERAL */}

                            <div className="audit-modal__grid">


                              <div>

                                <span>
                                  Fecha y hora
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


                              <div>

                                <span>
                                  Acción
                                </span>

                                <strong>
                                  {
                                    detalle
                                      .evento
                                      .accion_nombre ||
                                    detalle
                                      .evento
                                      .accion
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
                                      .servicio_nombre ||
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
                                      .modulo_nombre ||
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
                                      .entidad_tipo ||
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
                                      .direccion_ip ||
                                    "—"
                                  }
                                </strong>

                              </div>


                            </div>


                            {/* ID */}

                            <div className="audit-modal__identifier">

                              <span>
                                Identificador del evento
                              </span>

                              <code>
                                {
                                  detalle
                                    .evento
                                    .id_evento
                                }
                              </code>

                            </div>


                            {
                              detalle
                                .evento
                                .entidad_id && (

                                <div className="audit-modal__identifier">

                                  <span>
                                    Identificador de entidad
                                  </span>

                                  <code>
                                    {
                                      detalle
                                        .evento
                                        .entidad_id
                                    }
                                  </code>

                                </div>
                              )
                            }


                            {/* DESCRIPCIÓN */}

                            <div className="audit-modal__description">

                              <span>
                                Descripción
                              </span>

                              <p>
                                {
                                  descripcionEvento(
                                    detalle.evento,
                                  )
                                }
                              </p>

                            </div>


                            {
                              motivoEvento(
                                detalle.evento,
                              ) && (

                                <div className="audit-modal__reason">

                                  <AlertCircle
                                    size={17}
                                  />

                                  <div>

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

                                </div>
                              )
                            }


                            {/* CAMBIOS */}

                            <section className="audit-modal__changes">


                              <div className="audit-modal__section-heading">

                                <div>

                                  <ArrowRight
                                    size={17}
                                  />

                                  <h3>
                                    Cambios registrados
                                  </h3>

                                </div>

                                <span>
                                  {
                                    detalle
                                      .cambios
                                      .length
                                  }
                                </span>

                              </div>


                              {
                                detalle
                                  .cambios
                                  .length ===
                                0
                                  ? (

                                      <div className="audit-modal__no-changes">

                                        Este evento no modificó información.

                                      </div>

                                    )
                                  : (

                                      <div className="audit-change-list">

                                        {
                                          detalle
                                            .cambios
                                            .map(
                                              (
                                                cambio,
                                              ) => (

                                                <article

                                                  key={
                                                    cambio.id_cambio
                                                  }

                                                  className="audit-change"

                                                >


                                                  <strong className="audit-change__field">

                                                    {
                                                      nombreCampo(
                                                        cambio.campo,
                                                      )
                                                    }

                                                  </strong>


                                                  <div className="audit-change__values">


                                                    <div>

                                                      <span>
                                                        Valor anterior
                                                      </span>

                                                      <strong>
                                                        {
                                                          cambio
                                                            .valor_anterior ??
                                                          "—"
                                                        }
                                                      </strong>

                                                    </div>


                                                    <ArrowRight
                                                      size={18}
                                                    />


                                                    <div>

                                                      <span>
                                                        Valor nuevo
                                                      </span>

                                                      <strong>
                                                        {
                                                          cambio
                                                            .valor_nuevo ??
                                                          "—"
                                                        }
                                                      </strong>

                                                    </div>


                                                  </div>

                                                </article>
                                              ),
                                            )
                                        }

                                      </div>
                                    )
                              }


                            </section>


                            {/* INFORMACIÓN ADICIONAL */}

                            {
                              detalle
                                .evento
                                .detalle_json && (

                                <section className="audit-modal__metadata">


                                  <div className="audit-modal__section-heading">

                                    <div>

                                      <Layers3
                                        size={17}
                                      />

                                      <h3>
                                        Información adicional
                                      </h3>

                                    </div>

                                  </div>


                                  <div className="audit-metadata-list">

                                    {
                                      Object
                                        .entries(
                                          detalle
                                            .evento
                                            .detalle_json,
                                        )
                                        .filter(
                                          (
                                            [
                                              clave,
                                            ],
                                          ) =>
                                            ![
                                              "actor_nombre",
                                              "actor_rol",
                                              "descripcion",
                                            ].includes(
                                              clave,
                                            ),
                                        )
                                        .map(
                                          (
                                            [
                                              clave,
                                              valor,
                                            ],
                                          ) => (

                                            <div
                                              key={
                                                clave
                                              }
                                            >

                                              <span>
                                                {
                                                  nombreCampo(
                                                    clave,
                                                  )
                                                }
                                              </span>

                                              <strong>
                                                {
                                                  valorVisible(
                                                    valor,
                                                  )
                                                }
                                              </strong>

                                            </div>
                                          ),
                                        )
                                    }

                                  </div>


                                </section>
                              )
                            }


                          </>

                        )
                      : null
              }


            </section>

          </div>
        )
      }


    </section>
  );
}