import {
  AlertCircle,
  BadgeCheck,
  CalendarDays,
  CheckCircle2,
  Eye,
  LoaderCircle,
  Mail,
  Pencil,
  Phone,
  Power,
  PowerOff,
  RefreshCw,
  Save,
  Search,
  Stethoscope,
  UserPlus,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  cambiarEstadoOncologo,
  editarOncologo,
  listarOncologos,
  normalizarErroresApi,
  obtenerOncologo,
  obtenerStatusError,
  type EditarOncologoPayload,
  type ErroresFormulario,
  type OncologoDetalle,
  type OncologoResumen,
} from "../../api/oncologos.api";

import "./UsuariosPage.css";


type EstadoFiltro =
  | ""
  | "ACTIVO"
  | "INACTIVO";


function formatearFecha(
  fecha?: string | null,
): string {

  if (!fecha) {
    return "Sin registro";
  }

  const valor =
    new Date(fecha);

  if (
    Number.isNaN(
      valor.getTime(),
    )
  ) {
    return "Sin registro";
  }

  return new Intl.DateTimeFormat(
    "es-BO",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(valor);
}


function obtenerIniciales(
  nombre?: string | null,
): string {

  if (!nombre) {
    return "ON";
  }

  return nombre
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (parte) =>
        parte.charAt(0),
    )
    .join("")
    .toUpperCase();
}


function construirNombreCompleto(
  nombres?: string | null,
  apellidoPaterno?: string | null,
  apellidoMaterno?: string | null,
): string {

  return [
    nombres,
    apellidoPaterno,
    apellidoMaterno,
  ]
    .filter(Boolean)
    .join(" ")
    .trim();
}


export function UsuariosPage() {

  const navigate =
    useNavigate();


  // ========================================================
  // LISTADO
  // ========================================================

  const [
    oncologos,
    setOncologos,
  ] = useState<
    OncologoResumen[]
  >([]);


  const [
    buscar,
    setBuscar,
  ] = useState("");


  const [
    estado,
    setEstado,
  ] = useState<
    EstadoFiltro
  >("");


  const [
    cargando,
    setCargando,
  ] = useState(true);


  const [
    accesoDenegado,
    setAccesoDenegado,
  ] = useState(false);


  const [
    errorGeneral,
    setErrorGeneral,
  ] = useState("");


  const [
    mensajeExito,
    setMensajeExito,
  ] = useState("");


  // ========================================================
  // DETALLE / EDICIÓN
  // ========================================================

  const [
    detalle,
    setDetalle,
  ] = useState<
    OncologoDetalle | null
  >(null);


  const [
    cargandoDetalle,
    setCargandoDetalle,
  ] = useState(false);


  const [
    modoEdicion,
    setModoEdicion,
  ] = useState(false);


  const [
    guardando,
    setGuardando,
  ] = useState(false);


  const [
    erroresEdicion,
    setErroresEdicion,
  ] = useState<
    ErroresFormulario
  >({});


  const [
    formEdicion,
    setFormEdicion,
  ] = useState<
    EditarOncologoPayload
  >({});


  // ========================================================
  // MODAL ACTIVAR / DESACTIVAR
  // ========================================================

  const [
    oncologoEstado,
    setOncologoEstado,
  ] = useState<
    OncologoResumen | null
  >(null);


  const [
    procesandoEstado,
    setProcesandoEstado,
  ] = useState(false);


  // ========================================================
  // MENSAJES TEMPORALES
  // ========================================================

  const mostrarExito =
    (
      mensaje: string,
    ) => {

      setMensajeExito(
        mensaje,
      );

      window.setTimeout(
        () => {

          setMensajeExito("");

        },
        3500,
      );
    };


  // ========================================================
  // LISTAR
  // ========================================================

  useEffect(
    () => {

      const temporizador =
        window.setTimeout(
          async () => {

            try {

              setCargando(true);

              setErrorGeneral("");

              setAccesoDenegado(
                false,
              );


              const response =
                await listarOncologos(
                  buscar,
                  estado,
                );


              setOncologos(
                Array.isArray(
                  response.resultados,
                )
                  ? response.resultados
                  : [],
              );

            } catch (error) {

              const status =
                obtenerStatusError(
                  error,
                );


              if (
                status === 403
              ) {

                setAccesoDenegado(
                  true,
                );

                setOncologos([]);

                return;
              }


              const errores =
                normalizarErroresApi(
                  error,
                );


              setErrorGeneral(
                errores.general ??
                "No fue posible cargar los oncólogos.",
              );

            } finally {

              setCargando(false);
            }

          },
          300,
        );


      return () => {

        window.clearTimeout(
          temporizador,
        );

      };

    },
    [
      buscar,
      estado,
    ],
  );


  // ========================================================
  // RECARGAR
  // ========================================================

  const recargar =
    async () => {

      try {

        setCargando(true);

        setErrorGeneral("");


        const response =
          await listarOncologos(
            buscar,
            estado,
          );


        setOncologos(
          Array.isArray(
            response.resultados,
          )
            ? response.resultados
            : [],
        );

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error,
          );


        setErrorGeneral(
          errores.general ??
          "No fue posible actualizar la lista.",
        );

      } finally {

        setCargando(false);
      }

    };


  // ========================================================
  // CONSULTAR
  // ========================================================

  const abrirDetalle =
    async (
      idUsuario: string,
    ) => {

      try {

        setCargandoDetalle(
          true,
        );

        setErrorGeneral("");

        setErroresEdicion({});

        setModoEdicion(false);

        setDetalle(null);


        const response =
          await obtenerOncologo(
            idUsuario,
          );


        setDetalle(
          response,
        );


        setFormEdicion({

          nombres:
            response.nombres ?? "",

          apellido_paterno:
            response.apellido_paterno ?? "",

          apellido_materno:
            response.apellido_materno ?? "",

          correo:
            response.correo ?? "",

          nombre_usuario:
            response.nombre_usuario ?? "",

          telefono:
            response.telefono ?? "",

          matricula_profesional:
            response.perfil
              ?.matricula_profesional
            ?? "",

          especialidad:
            response.perfil
              ?.especialidad
            ?? "",

          subespecialidad:
            response.perfil
              ?.subespecialidad
            ?? "",

          telefono_institucional:
            response.perfil
              ?.telefono_institucional
            ?? "",

        });

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error,
          );


        setErrorGeneral(
          errores.general ??
          "No fue posible consultar al oncólogo.",
        );

      } finally {

        setCargandoDetalle(
          false,
        );
      }

    };


  const cerrarDetalle =
    () => {

      if (guardando) {
        return;
      }

      setDetalle(null);

      setModoEdicion(false);

      setErroresEdicion({});

      setFormEdicion({});
    };


  // ========================================================
  // CAMPOS EDICIÓN
  // ========================================================

  const actualizarCampo =
    (
      campo:
        keyof EditarOncologoPayload,

      valor: string,
    ) => {

      setFormEdicion(
        (actual) => ({

          ...actual,

          [campo]:
            valor,

        }),
      );


      setErroresEdicion(
        (actual) => {

          const nuevos = {
            ...actual,
          };

          delete nuevos[campo];

          delete nuevos.general;

          return nuevos;
        },
      );
    };


  // ========================================================
  // GUARDAR EDICIÓN
  // ========================================================

  const guardarEdicion =
    async () => {

      if (!detalle) {
        return;
      }


      const erroresLocales:
        ErroresFormulario = {};


      if (
        !formEdicion
          .nombres
          ?.trim()
      ) {

        erroresLocales.nombres =
          "Los nombres son obligatorios.";
      }


      if (
        !formEdicion
          .apellido_paterno
          ?.trim()
      ) {

        erroresLocales
          .apellido_paterno =
            "El apellido paterno es obligatorio.";
      }


      if (
        !formEdicion
          .correo
          ?.trim()
      ) {

        erroresLocales.correo =
          "El correo es obligatorio.";
      }


      if (
        !formEdicion
          .nombre_usuario
          ?.trim()
      ) {

        erroresLocales
          .nombre_usuario =
            "El usuario es obligatorio.";
      }


      if (
        Object.keys(
          erroresLocales,
        ).length > 0
      ) {

        setErroresEdicion(
          erroresLocales,
        );

        return;
      }


      try {

        setGuardando(true);

        setErroresEdicion({});

        setErrorGeneral("");


        const idUsuario =
          detalle.id_usuario;


        const response =
          await editarOncologo(
            idUsuario,
            formEdicion,
          );


        // ==================================================
        // ACTUALIZAR FILA LOCALMENTE
        // No hacemos otra petición inmediatamente.
        // Esto evita el render que te dejaba la pantalla blanca.
        // ==================================================

        const nuevoNombre =
          construirNombreCompleto(

            formEdicion.nombres,

            formEdicion
              .apellido_paterno,

            formEdicion
              .apellido_materno,

          );


        setOncologos(
          (actuales) =>
            actuales.map(
              (oncologo) => {

                if (
                  oncologo.id_usuario !==
                  idUsuario
                ) {

                  return oncologo;
                }


                return {

                  ...oncologo,

                  nombres:
                    formEdicion
                      .nombres
                    ??
                    oncologo.nombres,

                  apellido_paterno:
                    formEdicion
                      .apellido_paterno
                    ??
                    oncologo
                      .apellido_paterno,

                  apellido_materno:
                    formEdicion
                      .apellido_materno
                    ??
                    null,

                  nombre_completo:
                    nuevoNombre ||
                    oncologo
                      .nombre_completo,

                  correo:
                    formEdicion
                      .correo
                    ??
                    oncologo.correo,

                  nombre_usuario:
                    formEdicion
                      .nombre_usuario
                    ??
                    oncologo
                      .nombre_usuario,

                  telefono:
                    formEdicion
                      .telefono
                    ??
                    null,

                  matricula_profesional:
                    formEdicion
                      .matricula_profesional
                    ??
                    null,

                  especialidad:
                    formEdicion
                      .especialidad
                    ??
                    null,

                  subespecialidad:
                    formEdicion
                      .subespecialidad
                    ??
                    null,

                  telefono_institucional:
                    formEdicion
                      .telefono_institucional
                    ??
                    null,

                };

              },
            ),
        );


        // Cerramos el modal
        // después de actualizar el estado.
        setDetalle(null);

        setModoEdicion(false);

        setFormEdicion({});


        mostrarExito(
          response.mensaje,
        );

      } catch (error) {

        setErroresEdicion(
          normalizarErroresApi(
            error,
          ),
        );

      } finally {

        setGuardando(false);
      }

    };


  // ========================================================
  // ABRIR CONFIRMACIÓN DE ESTADO
  // ========================================================

  const abrirCambioEstado =
    (
      oncologo:
        OncologoResumen,
    ) => {

      setErrorGeneral("");

      setOncologoEstado(
        oncologo,
      );
    };


  const cerrarCambioEstado =
    () => {

      if (
        procesandoEstado
      ) {
        return;
      }

      setOncologoEstado(
        null,
      );
    };


  // ========================================================
  // CONFIRMAR ACTIVAR / DESACTIVAR
  // ========================================================

  const confirmarCambioEstado =
    async () => {

      if (
        !oncologoEstado
      ) {
        return;
      }


      const nuevoEstado:
        "ACTIVO" | "INACTIVO" =

        oncologoEstado.estado ===
        "ACTIVO"

          ? "INACTIVO"

          : "ACTIVO";


      try {

        setProcesandoEstado(
          true,
        );

        setErrorGeneral("");


        const response =
          await cambiarEstadoOncologo(

            oncologoEstado.id_usuario,

            nuevoEstado,

          );


        setOncologos(
          (actuales) =>
            actuales.map(
              (oncologo) => {

                if (
                  oncologo.id_usuario !==
                  oncologoEstado.id_usuario
                ) {

                  return oncologo;
                }


                return {

                  ...oncologo,

                  estado:
                    response.estado,

                  estado_nombre:
                    response.estado_nombre,

                };

              },
            ),
        );


        setOncologoEstado(
          null,
        );


        mostrarExito(
          response.mensaje,
        );

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error,
          );


        setOncologoEstado(
          null,
        );


        setErrorGeneral(
          errores.general ??
          "No fue posible cambiar el estado de la cuenta.",
        );

      } finally {

        setProcesandoEstado(
          false,
        );
      }

    };


  // ========================================================
  // ACCESO DENEGADO
  // ========================================================

  if (
    accesoDenegado
  ) {

    return (

      <div className="oncologists-page">

        <section className="oncologists-access-denied">

          <div className="oncologists-access-denied__icon">

            <AlertCircle
              size={28}
            />

          </div>

          <h1>
            Acceso restringido
          </h1>

          <p>

            La gestión de cuentas de oncólogos
            está disponible únicamente para
            personal autorizado de Jefatura de
            Oncología.

          </p>

          <button

            type="button"

            onClick={() =>
              navigate(
                "/dashboard",
              )
            }

          >

            Volver al inicio

          </button>

        </section>

      </div>

    );
  }


  // ========================================================
  // PÁGINA
  // ========================================================

  return (

    <div className="oncologists-page">


      {/* CABECERA */}

      <section className="oncologists-header">

        <div>

          <span className="oncologists-header__eyebrow">
            Administración
          </span>

          <h1>
            Gestión de oncólogos
          </h1>

          <p>

            Registre, busque, consulte y
            actualice las cuentas del personal
            médico oncológico.

          </p>

        </div>


        <button

          type="button"

          className="oncologists-primary-button"

          onClick={() =>
            navigate(
              "/usuarios/nuevo",
            )
          }

        >

          <UserPlus
            size={18}
          />

          Nuevo oncólogo

        </button>

      </section>


      {/* MENSAJE ÉXITO */}

      {mensajeExito && (

        <div className="oncologists-alert oncologists-alert--success">

          <CheckCircle2
            size={18}
          />

          {mensajeExito}

        </div>

      )}


      {/* ERROR */}

      {errorGeneral && (

        <div className="oncologists-alert oncologists-alert--error">

          <AlertCircle
            size={18}
          />

          {errorGeneral}

        </div>

      )}


      {/* TABLA */}

      <section className="oncologists-card">


        <div className="oncologists-toolbar">


          <div className="oncologists-search">

            <Search
              size={18}
            />

            <input

              type="search"

              value={buscar}

              onChange={(event) =>
                setBuscar(
                  event.target.value,
                )
              }

              placeholder="Buscar por nombre, correo, usuario o matrícula..."

            />

          </div>


          <select

            value={estado}

            onChange={(event) =>
              setEstado(
                event.target
                  .value as EstadoFiltro,
              )
            }

            className="oncologists-filter"

          >

            <option value="">
              Todos los estados
            </option>

            <option value="ACTIVO">
              Activos
            </option>

            <option value="INACTIVO">
              Inactivos
            </option>

          </select>


          <button

            type="button"

            className="oncologists-refresh-button"

            onClick={() =>
              void recargar()
            }

            aria-label="Actualizar"

          >

            <RefreshCw
              size={18}
            />

          </button>


        </div>


        <div className="oncologists-summary">

          <div>

            <strong>
              {oncologos.length}
            </strong>

            <span>
              oncólogos encontrados
            </span>

          </div>

        </div>


        {cargando ? (

          <div className="oncologists-loading">

            <LoaderCircle
              size={26}
              className="oncologists-spin"
            />

            <span>
              Cargando oncólogos...
            </span>

          </div>

        ) : oncologos.length === 0 ? (

          <div className="oncologists-empty">

            <UserRound
              size={30}
            />

            <strong>
              No se encontraron oncólogos
            </strong>

            <span>

              Pruebe con otro criterio
              de búsqueda.

            </span>

          </div>

        ) : (

          <div className="oncologists-table-wrapper">

            <table className="oncologists-table">

              <thead>

                <tr>

                  <th>
                    Oncólogo
                  </th>

                  <th>
                    Matrícula
                  </th>

                  <th>
                    Especialidad
                  </th>

                  <th>
                    Estado
                  </th>

                  <th>
                    Acciones
                  </th>

                </tr>

              </thead>


              <tbody>

                {oncologos.map(
                  (oncologo) => (

                    <tr
                      key={
                        oncologo.id_usuario
                      }
                    >

                      <td>

                        <div className="oncologists-person">

                          <div className="oncologists-avatar">

                            {obtenerIniciales(
                              oncologo
                                .nombre_completo,
                            )}

                          </div>

                          <div>

                            <strong>

                              {
                                oncologo
                                  .nombre_completo
                              }

                            </strong>

                            <span>

                              {
                                oncologo
                                  .correo
                              }

                            </span>

                          </div>

                        </div>

                      </td>


                      <td>

                        {
                          oncologo
                            .matricula_profesional
                          ??
                          "Sin registro"
                        }

                      </td>


                      <td>

                        {
                          oncologo
                            .especialidad
                          ??
                          "Oncología"
                        }

                      </td>


                      <td>

                        <span
                          className={`
                            oncologists-status
                            ${
                              oncologo.estado ===
                              "ACTIVO"

                                ? "oncologists-status--active"

                                : "oncologists-status--inactive"
                            }
                          `}
                        >

                          <span />

                          {
                            oncologo
                              .estado_nombre
                          }

                        </span>

                      </td>


                      <td>

                        <div className="oncologists-actions">


                          <button

                            type="button"

                            onClick={() =>
                              void abrirDetalle(
                                oncologo
                                  .id_usuario,
                              )
                            }

                          >

                            <Eye
                              size={16}
                            />

                            Consultar

                          </button>


                          <button

                            type="button"

                            className={
                              oncologo.estado ===
                              "ACTIVO"

                                ? "oncologists-action-state oncologists-action-state--disable"

                                : "oncologists-action-state oncologists-action-state--enable"
                            }

                            onClick={() =>
                              abrirCambioEstado(
                                oncologo,
                              )
                            }

                          >

                            {
                              oncologo.estado ===
                              "ACTIVO"

                                ? (
                                  <PowerOff
                                    size={15}
                                  />
                                )

                                : (
                                  <Power
                                    size={15}
                                  />
                                )
                            }

                            {
                              oncologo.estado ===
                              "ACTIVO"

                                ? "Desactivar"

                                : "Activar"
                            }

                          </button>


                        </div>

                      </td>

                    </tr>

                  ),
                )}

              </tbody>

            </table>

          </div>

        )}


      </section>


      {/* CARGANDO DETALLE */}

      {cargandoDetalle && (

        <div className="oncologists-modal-backdrop">

          <div className="oncologists-modal oncologists-modal--loading">

            <LoaderCircle
              size={28}
              className="oncologists-spin"
            />

            Consultando oncólogo...

          </div>

        </div>

      )}


      {/* DETALLE / EDICIÓN */}

      {detalle && (

        <div
          className="oncologists-modal-backdrop"
          onMouseDown={
            cerrarDetalle
          }
        >

          <section

            className="oncologists-modal"

            onMouseDown={(
              event,
            ) =>
              event.stopPropagation()
            }

          >


            <header className="oncologists-modal__header">

              <div>

                <span>
                  Cuenta médica
                </span>

                <h2>

                  {
                    detalle
                      .nombre_completo
                  }

                </h2>

              </div>


              <button

                type="button"

                onClick={
                  cerrarDetalle
                }

                className="oncologists-modal__close"

              >

                <X
                  size={20}
                />

              </button>

            </header>


            {erroresEdicion.general && (

              <div className="oncologists-alert oncologists-alert--error">

                <AlertCircle
                  size={18}
                />

                {
                  erroresEdicion.general
                }

              </div>

            )}


            {!modoEdicion ? (

              <>

                <div className="oncologists-detail-profile">

                  <div className="oncologists-detail-profile__avatar">

                    {obtenerIniciales(
                      detalle
                        .nombre_completo,
                    )}

                  </div>

                  <div>

                    <strong>

                      {
                        detalle
                          .nombre_completo
                      }

                    </strong>

                    <span>

                      {
                        detalle
                          .perfil
                          ?.cargo
                        ??
                        "Médico oncólogo"
                      }

                    </span>

                  </div>


                  <span
                    className={`
                      oncologists-status
                      ${
                        detalle.estado ===
                        "ACTIVO"

                          ? "oncologists-status--active"

                          : "oncologists-status--inactive"
                      }
                    `}
                  >

                    <span />

                    {
                      detalle
                        .estado_nombre
                    }

                  </span>

                </div>


                <div className="oncologists-detail-grid">

                  <div>

                    <Mail
                      size={17}
                    />

                    <span>
                      Correo institucional
                    </span>

                    <strong>
                      {detalle.correo}
                    </strong>

                  </div>


                  <div>

                    <UserRound
                      size={17}
                    />

                    <span>
                      Usuario
                    </span>

                    <strong>

                      {
                        detalle
                          .nombre_usuario
                      }

                    </strong>

                  </div>


                  <div>

                    <Stethoscope
                      size={17}
                    />

                    <span>
                      Especialidad
                    </span>

                    <strong>

                      {
                        detalle
                          .perfil
                          ?.especialidad
                        ??
                        "Sin registro"
                      }

                    </strong>

                  </div>


                  <div>

                    <BadgeCheck
                      size={17}
                    />

                    <span>
                      Matrícula profesional
                    </span>

                    <strong>

                      {
                        detalle
                          .perfil
                          ?.matricula_profesional
                        ??
                        "Sin registro"
                      }

                    </strong>

                  </div>


                  <div>

                    <Phone
                      size={17}
                    />

                    <span>
                      Teléfono personal
                    </span>

                    <strong>

                      {
                        detalle
                          .telefono
                        ??
                        "Sin registro"
                      }

                    </strong>

                  </div>


                  <div>

                    <CalendarDays
                      size={17}
                    />

                    <span>
                      Registrado
                    </span>

                    <strong>

                      {formatearFecha(
                        detalle
                          .fecha_creacion,
                      )}

                    </strong>

                  </div>

                </div>


                <footer className="oncologists-modal__footer">

                  <button

                    type="button"

                    className="oncologists-secondary-button"

                    onClick={
                      cerrarDetalle
                    }

                  >

                    Cerrar

                  </button>


                  <button

                    type="button"

                    className="oncologists-primary-button"

                    onClick={() =>
                      setModoEdicion(
                        true,
                      )
                    }

                  >

                    <Pencil
                      size={17}
                    />

                    Editar oncólogo

                  </button>

                </footer>

              </>

            ) : (

              <>

                <div className="oncologists-edit-grid">


                  <label>

                    <span>
                      Nombres *
                    </span>

                    <input

                      value={
                        formEdicion
                          .nombres
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "nombres",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.nombres && (

                      <small>
                        {erroresEdicion.nombres}
                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Apellido paterno *
                    </span>

                    <input

                      value={
                        formEdicion
                          .apellido_paterno
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "apellido_paterno",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.apellido_paterno && (

                      <small>

                        {
                          erroresEdicion
                            .apellido_paterno
                        }

                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Apellido materno
                    </span>

                    <input

                      value={
                        formEdicion
                          .apellido_materno
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "apellido_materno",
                          event.target.value,
                        )
                      }

                    />

                  </label>


                  <label>

                    <span>
                      Correo institucional *
                    </span>

                    <input

                      type="email"

                      value={
                        formEdicion
                          .correo
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "correo",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.correo && (

                      <small>
                        {erroresEdicion.correo}
                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Nombre de usuario *
                    </span>

                    <input

                      value={
                        formEdicion
                          .nombre_usuario
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "nombre_usuario",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.nombre_usuario && (

                      <small>

                        {
                          erroresEdicion
                            .nombre_usuario
                        }

                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Teléfono personal
                    </span>

                    <input

                      value={
                        formEdicion
                          .telefono
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "telefono",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.telefono && (

                      <small>
                        {erroresEdicion.telefono}
                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Matrícula profesional
                    </span>

                    <input

                      value={
                        formEdicion
                          .matricula_profesional
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "matricula_profesional",
                          event.target.value,
                        )
                      }

                    />

                    {erroresEdicion.matricula_profesional && (

                      <small>

                        {
                          erroresEdicion
                            .matricula_profesional
                        }

                      </small>

                    )}

                  </label>


                  <label>

                    <span>
                      Especialidad
                    </span>

                    <input

                      value={
                        formEdicion
                          .especialidad
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "especialidad",
                          event.target.value,
                        )
                      }

                    />

                  </label>


                  <label>

                    <span>
                      Subespecialidad
                    </span>

                    <input

                      value={
                        formEdicion
                          .subespecialidad
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "subespecialidad",
                          event.target.value,
                        )
                      }

                    />

                  </label>


                  <label>

                    <span>
                      Teléfono institucional
                    </span>

                    <input

                      value={
                        formEdicion
                          .telefono_institucional
                        ?? ""
                      }

                      onChange={(event) =>
                        actualizarCampo(
                          "telefono_institucional",
                          event.target.value,
                        )
                      }

                    />

                  </label>

                </div>


                <footer className="oncologists-modal__footer">

                  <button

                    type="button"

                    className="oncologists-secondary-button"

                    onClick={() => {

                      setModoEdicion(
                        false,
                      );

                      setErroresEdicion(
                        {},
                      );

                    }}

                    disabled={
                      guardando
                    }

                  >

                    Cancelar

                  </button>


                  <button

                    type="button"

                    className="oncologists-primary-button"

                    onClick={() =>
                      void guardarEdicion()
                    }

                    disabled={
                      guardando
                    }

                  >

                    {guardando ? (

                      <LoaderCircle
                        size={17}
                        className="oncologists-spin"
                      />

                    ) : (

                      <Save
                        size={17}
                      />

                    )}

                    {
                      guardando
                        ? "Guardando..."
                        : "Guardar cambios"
                    }

                  </button>

                </footer>

              </>

            )}

          </section>

        </div>

      )}


      {/* ====================================================
          MODAL ACTIVAR / DESACTIVAR
          ==================================================== */}

      {oncologoEstado && (

        <div
          className="oncologists-modal-backdrop"
          onMouseDown={
            cerrarCambioEstado
          }
        >

          <section

            className="oncologists-confirm-modal"

            onMouseDown={(
              event,
            ) =>
              event.stopPropagation()
            }

          >


            <button

              type="button"

              className="oncologists-confirm-modal__close"

              onClick={
                cerrarCambioEstado
              }

              disabled={
                procesandoEstado
              }

            >

              <X
                size={19}
              />

            </button>


            <div
              className={`
                oncologists-confirm-modal__icon
                ${
                  oncologoEstado.estado ===
                  "ACTIVO"

                    ? "oncologists-confirm-modal__icon--danger"

                    : "oncologists-confirm-modal__icon--success"
                }
              `}
            >

              {
                oncologoEstado.estado ===
                "ACTIVO"

                  ? (
                    <PowerOff
                      size={27}
                    />
                  )

                  : (
                    <Power
                      size={27}
                    />
                  )
              }

            </div>


            <h2>

              {
                oncologoEstado.estado ===
                "ACTIVO"

                  ? "Desactivar cuenta"

                  : "Activar cuenta"
              }

            </h2>


            <p>

              {
                oncologoEstado.estado ===
                "ACTIVO"

                  ? (
                    <>
                      ¿Desea desactivar la cuenta de{" "}
                      <strong>
                        {
                          oncologoEstado
                            .nombre_completo
                        }
                      </strong>
                      ?
                    </>
                  )

                  : (
                    <>
                      ¿Desea activar nuevamente la cuenta de{" "}
                      <strong>
                        {
                          oncologoEstado
                            .nombre_completo
                        }
                      </strong>
                      ?
                    </>
                  )
              }

            </p>


            {oncologoEstado.estado ===
            "ACTIVO" && (

              <div className="oncologists-confirm-modal__notice">

                <AlertCircle
                  size={18}
                />

                <span>

                  La cuenta será deshabilitada,
                  pero <strong>no será eliminada</strong>.
                  Su información e historial se
                  conservarán.

                </span>

              </div>

            )}


            <div className="oncologists-confirm-modal__actions">


              <button

                type="button"

                className="oncologists-secondary-button"

                onClick={
                  cerrarCambioEstado
                }

                disabled={
                  procesandoEstado
                }

              >

                Cancelar

              </button>


              <button

                type="button"

                className={
                  oncologoEstado.estado ===
                  "ACTIVO"

                    ? "oncologists-confirm-button oncologists-confirm-button--danger"

                    : "oncologists-confirm-button oncologists-confirm-button--success"
                }

                onClick={() =>
                  void confirmarCambioEstado()
                }

                disabled={
                  procesandoEstado
                }

              >

                {procesandoEstado ? (

                  <LoaderCircle
                    size={17}
                    className="oncologists-spin"
                  />

                ) : oncologoEstado.estado ===
                  "ACTIVO" ? (

                  <PowerOff
                    size={17}
                  />

                ) : (

                  <Power
                    size={17}
                  />

                )}


                {
                  procesandoEstado

                    ? "Procesando..."

                    : oncologoEstado.estado ===
                      "ACTIVO"

                      ? "Sí, desactivar"

                      : "Sí, activar"
                }

              </button>


            </div>

          </section>

        </div>

      )}


    </div>

  );
}