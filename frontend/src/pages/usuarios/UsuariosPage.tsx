import {
  AlertCircle,
  BadgeCheck,
  BriefcaseMedical,
  CalendarDays,
  CheckCircle2,
  Eye,
  IdCard,
  LoaderCircle,
  Mail,
  MapPin,
  Pencil,
  Phone,
  Power,
  PowerOff,
  RefreshCw,
  Save,
  Search,
  ShieldCheck,
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
  type ExpedicionBolivia,
  type OncologoDetalle,
  type OncologoResumen,
  type RolOncologia,
} from "../../api/oncologos.api";

import "./UsuariosPage.css";


/* =========================================================
   TIPOS
   ========================================================= */

type EstadoFiltro =
  | ""
  | "ACTIVO"
  | "INACTIVO";


type RolFiltro =
  | ""
  | RolOncologia;


/* =========================================================
   CATÁLOGOS
   ========================================================= */

const DEPARTAMENTOS: Array<{
  codigo: ExpedicionBolivia;
  nombre: string;
}> = [
  {
    codigo: "LP",
    nombre: "La Paz",
  },
  {
    codigo: "CB",
    nombre: "Cochabamba",
  },
  {
    codigo: "SC",
    nombre: "Santa Cruz",
  },
  {
    codigo: "OR",
    nombre: "Oruro",
  },
  {
    codigo: "PT",
    nombre: "Potosí",
  },
  {
    codigo: "CH",
    nombre: "Chuquisaca",
  },
  {
    codigo: "TJ",
    nombre: "Tarija",
  },
  {
    codigo: "BE",
    nombre: "Beni",
  },
  {
    codigo: "PD",
    nombre: "Pando",
  },
];


const SUBESPECIALIDADES = [
  "Oncología médica",
  "Oncología pediátrica",
  "Oncología quirúrgica",
  "Oncología radioterápica",
  "Oncología ortopédica",
  "Otra",
];


/* =========================================================
   UTILIDADES
   ========================================================= */

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
      valor.getTime()
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
        parte.charAt(0)
    )
    .join("")
    .toUpperCase();
}


function nombreRol(
  codigo?: string | null,
): string {

  if (
    codigo ===
    "JEFE_ONCOLOGIA"
  ) {
    return "Jefe de Oncología";
  }

  if (
    codigo ===
    "ONCOLOGO"
  ) {
    return "Oncólogo";
  }

  return "Personal oncológico";
}


function nombreDepartamento(
  codigo?: string | null,
): string {

  const encontrado =
    DEPARTAMENTOS.find(
      (departamento) =>
        departamento.codigo === codigo
    );

  return (
    encontrado?.nombre
    ??
    codigo
    ??
    "Sin registro"
  );
}


function construirCi(
  numero?: string | null,
  complemento?: string | null,
  expedido?: string | null,
): string {

  if (!numero) {
    return "Sin registro";
  }

  let valor =
    numero;

  if (complemento) {
    valor += `-${complemento}`;
  }

  if (expedido) {
    valor += ` ${expedido}`;
  }

  return valor;
}


/* =========================================================
   COMPONENTE
   ========================================================= */

export function UsuariosPage() {

  const navigate =
    useNavigate();


  /* =======================================================
     LISTADO
     ======================================================= */

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
  ] = useState<EstadoFiltro>("");


  const [
    rol,
    setRol,
  ] = useState<RolFiltro>("");


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


  /* =======================================================
     DETALLE
     ======================================================= */

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
  ] = useState<ErroresFormulario>({});


  const [
    formEdicion,
    setFormEdicion,
  ] = useState<EditarOncologoPayload>({});


  /* =======================================================
     ESTADO
     ======================================================= */

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


  /* =======================================================
     MENSAJE TEMPORAL
     ======================================================= */

  const mostrarExito = (
    mensaje: string,
  ) => {

    setMensajeExito(
      mensaje
    );

    window.setTimeout(
      () => {
        setMensajeExito("");
      },
      3500,
    );
  };


  /* =======================================================
     CARGAR LISTADO
     ======================================================= */

  useEffect(
    () => {

      const temporizador =
        window.setTimeout(
          async () => {

            try {

              setCargando(true);

              setErrorGeneral("");

              setAccesoDenegado(false);


              const response =
                await listarOncologos(
                  buscar,
                  estado,
                  rol,
                );


              setOncologos(
                Array.isArray(
                  response.resultados
                )
                  ? response.resultados
                  : []
              );

            } catch (error) {

              const status =
                obtenerStatusError(
                  error
                );


              if (
                status === 403
              ) {

                setAccesoDenegado(
                  true
                );

                setOncologos([]);

                return;
              }


              const errores =
                normalizarErroresApi(
                  error
                );


              setErrorGeneral(
                errores.general
                ??
                "No fue posible cargar el personal de Oncología."
              );

            } finally {

              setCargando(false);

            }

          },
          300,
        );


      return () => {
        window.clearTimeout(
          temporizador
        );
      };

    },
    [
      buscar,
      estado,
      rol,
    ],
  );


  /* =======================================================
     RECARGAR
     ======================================================= */

  const recargar =
    async () => {

      try {

        setCargando(true);

        setErrorGeneral("");


        const response =
          await listarOncologos(
            buscar,
            estado,
            rol,
          );


        setOncologos(
          response.resultados ?? []
        );

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error
          );


        setErrorGeneral(
          errores.general
          ??
          "No fue posible actualizar el listado."
        );

      } finally {

        setCargando(false);

      }

    };


  /* =======================================================
     DETALLE
     ======================================================= */

  const abrirDetalle =
    async (
      idUsuario: string,
    ) => {

      try {

        setCargandoDetalle(true);

        setErrorGeneral("");

        setErroresEdicion({});

        setModoEdicion(false);

        setDetalle(null);


        const response =
          await obtenerOncologo(
            idUsuario
          );


        setDetalle(
          response
        );


        setFormEdicion({
          nombres:
            response.nombres ?? "",

          apellido_paterno:
            response.apellido_paterno ?? "",

          apellido_materno:
            response.apellido_materno ?? "",

          telefono:
            response.telefono ?? "",

          correo:
            response.correo ?? "",

          ci_numero:
            response.ci_numero ?? "",

          ci_complemento:
            response.ci_complemento ?? "",

          ci_expedido:
            response.ci_expedido ?? "LP",

          matricula_profesional:
            response.perfil
              ?.matricula_profesional
            ?? "",

          subespecialidad:
            response.perfil
              ?.subespecialidad
            ?? "Oncología médica",

          telefono_institucional:
            response.perfil
              ?.telefono_institucional
            ?? "",

          rol_codigo:
            response.rol_codigo
            ??
            "ONCOLOGO",
        });

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error
          );


        setErrorGeneral(
          errores.general
          ??
          "No fue posible consultar al profesional."
        );

      } finally {

        setCargandoDetalle(
          false
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


  /* =======================================================
     ACTUALIZAR FORM EDICIÓN
     ======================================================= */

  const actualizarCampo = (
    campo:
      keyof EditarOncologoPayload,

    valorOriginal:
      string,
  ) => {

    let valor =
      valorOriginal;


    if (
      campo === "telefono"
      ||
      campo === "telefono_institucional"
    ) {

      valor =
        valorOriginal
          .replace(
            /\D/g,
            ""
          )
          .slice(
            0,
            8
          );
    }


    if (
      campo === "ci_numero"
    ) {

      valor =
        valorOriginal
          .replace(
            /\D/g,
            ""
          )
          .slice(
            0,
            20
          );
    }


    if (
      campo === "ci_complemento"
    ) {

      valor =
        valorOriginal
          .toUpperCase()
          .replace(
            /[^A-Z0-9]/g,
            ""
          )
          .slice(
            0,
            10
          );
    }


    if (
      campo === "matricula_profesional"
    ) {

      valor =
        valorOriginal
          .toUpperCase()
          .replace(
            /\s+/g,
            ""
          )
          .replace(
            /[^A-Z0-9./-]/g,
            ""
          )
          .slice(
            0,
            30
          );
    }


    if (
      campo === "correo"
    ) {

      valor =
        valorOriginal
          .toLowerCase();
    }


    setFormEdicion(
      (actual) => ({
        ...actual,
        [campo]:
          valor,
      })
    );


    setErroresEdicion(
      (actual) => {

        const nuevos = {
          ...actual,
        };

        delete nuevos[
          campo
        ];

        delete nuevos.general;

        return nuevos;
      }
    );
  };


  /* =======================================================
     VALIDAR EDICIÓN
     ======================================================= */

  const validarEdicion =
    (): ErroresFormulario => {

      const errores:
        ErroresFormulario = {};


      if (
        !formEdicion
          .nombres
          ?.trim()
      ) {

        errores.nombres =
          "Los nombres son obligatorios.";
      }


      if (
        !formEdicion
          .apellido_paterno
          ?.trim()
      ) {

        errores.apellido_paterno =
          "El apellido paterno es obligatorio.";
      }


      if (
        !formEdicion
          .correo
          ?.trim()
      ) {

        errores.correo =
          "El correo es obligatorio.";
      }


      if (
        !formEdicion
          .ci_numero
          ?.trim()
      ) {

        errores.ci_numero =
          "La cédula de identidad es obligatoria.";
      }


      if (
        !formEdicion
          .matricula_profesional
          ?.trim()
      ) {

        errores.matricula_profesional =
          "La matrícula profesional es obligatoria.";
      }


      if (
        formEdicion.telefono
        &&
        !/^[67]\d{7}$/.test(
          String(
            formEdicion.telefono
          )
        )
      ) {

        errores.telefono =
          "Debe tener 8 dígitos y comenzar con 6 o 7.";
      }


      if (
        formEdicion
          .telefono_institucional
        &&
        !/^\d{8}$/.test(
          String(
            formEdicion
              .telefono_institucional
          )
        )
      ) {

        errores.telefono_institucional =
          "Debe tener exactamente 8 dígitos.";
      }


      return errores;
    };


  /* =======================================================
     GUARDAR EDICIÓN
     ======================================================= */

  const guardarEdicion =
    async () => {

      if (!detalle) {
        return;
      }


      const erroresLocales =
        validarEdicion();


      if (
        Object.keys(
          erroresLocales
        ).length > 0
      ) {

        setErroresEdicion(
          erroresLocales
        );

        return;
      }


      try {

        setGuardando(true);

        setErroresEdicion({});

        setErrorGeneral("");


        const payload:
          EditarOncologoPayload = {

          nombres:
            formEdicion
              .nombres
              ?.trim(),

          apellido_paterno:
            formEdicion
              .apellido_paterno
              ?.trim(),

          apellido_materno:
            formEdicion
              .apellido_materno
              ?.trim()
            ||
            null,

          telefono:
            formEdicion
              .telefono
              ?.trim()
            ||
            null,

          correo:
            formEdicion
              .correo
              ?.trim()
              .toLowerCase(),

          ci_numero:
            formEdicion
              .ci_numero
              ?.trim(),

          ci_complemento:
            formEdicion
              .ci_complemento
              ?.trim()
            ||
            null,

          ci_expedido:
            formEdicion
              .ci_expedido,

          matricula_profesional:
            formEdicion
              .matricula_profesional
              ?.trim()
              .toUpperCase(),

          subespecialidad:
            formEdicion
              .subespecialidad,

          telefono_institucional:
            formEdicion
              .telefono_institucional
              ?.trim()
            ||
            null,

          rol_codigo:
            formEdicion
              .rol_codigo,
        };


        const response =
          await editarOncologo(
            detalle.id_usuario,
            payload,
          );


        setDetalle(null);

        setModoEdicion(false);

        setFormEdicion({});


        mostrarExito(
          response.mensaje
        );


        await recargar();

      } catch (error) {

        setErroresEdicion(
          normalizarErroresApi(
            error
          )
        );

      } finally {

        setGuardando(false);

      }

    };


  /* =======================================================
     CAMBIO DE ESTADO
     ======================================================= */

  const abrirCambioEstado = (
    oncologo:
      OncologoResumen,
  ) => {

    setErrorGeneral("");

    setOncologoEstado(
      oncologo
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
        null
      );
    };


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
          true
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
              (oncologo) =>
                oncologo.id_usuario ===
                oncologoEstado.id_usuario
                  ? {
                      ...oncologo,
                      estado:
                        response.estado,
                      estado_nombre:
                        response.estado_nombre,
                    }
                  : oncologo
            )
        );


        setOncologoEstado(null);

        mostrarExito(
          response.mensaje
        );

      } catch (error) {

        const errores =
          normalizarErroresApi(
            error
          );


        setOncologoEstado(null);


        setErrorGeneral(
          errores.general
          ??
          "No fue posible cambiar el estado de la cuenta."
        );

      } finally {

        setProcesandoEstado(false);

      }

    };


  /* =======================================================
     ACCESO DENEGADO
     ======================================================= */

  if (
    accesoDenegado
  ) {

    return (

      <div
        className="oncologists-page"
      >

        <section
          className="oncologists-access-denied"
        >

          <div
            className="oncologists-access-denied__icon"
          >

            <AlertCircle
              size={28}
            />

          </div>

          <h1>
            Acceso restringido
          </h1>

          <p>
            La administración del personal
            oncológico está disponible únicamente
            para Jefatura de Oncología.
          </p>

          <button
            type="button"
            onClick={
              () =>
                navigate(
                  "/dashboard"
                )
            }
          >
            Volver al inicio
          </button>

        </section>

      </div>

    );
  }


  /* =======================================================
     RENDER
     ======================================================= */

  return (

    <div
      className="oncologists-page"
    >

      {/* =================================================
          CABECERA
          ================================================= */}

      <section
        className="oncologists-header"
      >

        <div>

          <span
            className="oncologists-header__eyebrow"
          >
            Administración
          </span>

          <h1>
            Personal de Oncología
          </h1>

          <p>
            Registre, consulte y administre las
            cuentas de oncólogos y Jefatura de Oncología.
          </p>

        </div>


        <button
          type="button"
          className="oncologists-primary-button"
          onClick={
            () =>
              navigate(
                "/usuarios/nuevo"
              )
          }
        >

          <UserPlus
            size={18}
          />

          Registrar profesional

        </button>

      </section>


      {/* =================================================
          MENSAJES
          ================================================= */}

      {
        mensajeExito
        &&
        (
          <div
            className="oncologists-alert oncologists-alert--success"
          >

            <CheckCircle2
              size={18}
            />

            {mensajeExito}

          </div>
        )
      }


      {
        errorGeneral
        &&
        (
          <div
            className="oncologists-alert oncologists-alert--error"
          >

            <AlertCircle
              size={18}
            />

            {errorGeneral}

          </div>
        )
      }


      {/* =================================================
          LISTADO
          ================================================= */}

      <section
        className="oncologists-card"
      >

        <div
          className="oncologists-toolbar oncologists-toolbar--extended"
        >

          <div
            className="oncologists-search"
          >

            <Search
              size={18}
            />

            <input
              type="search"
              value={buscar}
              onChange={
                (event) =>
                  setBuscar(
                    event.target.value
                  )
              }
              placeholder="Buscar por nombre, CI, correo, usuario o matrícula..."
            />

          </div>


          <select
            value={rol}
            onChange={(event) => {
              const nuevoRol = event.target.value as RolFiltro;

              setRol(nuevoRol);
            }}
            className="oncologists-filter"
          >
            <option value="">
              Todos los roles
            </option>

            <option value="JEFE_ONCOLOGIA">
              Jefes de Oncología
            </option>

            <option value="ONCOLOGO">
              Oncólogos
            </option>
          </select>


          <select
            value={estado}
            onChange={(event) => {
              const nuevoEstado = event.target.value as EstadoFiltro;

              setEstado(nuevoEstado);
            }}
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
            onClick={
              () =>
                void recargar()
            }
            aria-label="Actualizar"
          >

            <RefreshCw
              size={18}
            />

          </button>

        </div>


        <div
          className="oncologists-summary"
        >

          <div>

            <strong>
              {oncologos.length}
            </strong>

            <span>
              profesionales encontrados
            </span>

          </div>

        </div>


        {
          cargando
            ? (
                <div
                  className="oncologists-loading"
                >

                  <LoaderCircle
                    size={26}
                    className="oncologists-spin"
                  />

                  <span>
                    Cargando personal...
                  </span>

                </div>
              )
            : oncologos.length === 0
              ? (
                  <div
                    className="oncologists-empty"
                  >

                    <UserRound
                      size={30}
                    />

                    <strong>
                      No se encontraron profesionales
                    </strong>

                    <span>
                      Pruebe con otros criterios de búsqueda.
                    </span>

                  </div>
                )
              : (
                  <div
                    className="oncologists-table-wrapper"
                  >

                    <table
                      className="oncologists-table"
                    >

                      <thead>

                        <tr>

                          <th>
                            Profesional
                          </th>

                          <th>
                            CI
                          </th>

                          <th>
                            Matrícula
                          </th>

                          <th>
                            Rol
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

                        {
                          oncologos.map(
                            (oncologo) => (

                              <tr
                                key={
                                  oncologo.id_usuario
                                }
                              >

                                <td>

                                  <div
                                    className="oncologists-person"
                                  >

                                    <div
                                      className="oncologists-avatar"
                                    >
                                      {
                                        obtenerIniciales(
                                          oncologo.nombre_completo
                                        )
                                      }
                                    </div>


                                    <div>

                                      <strong>
                                        {
                                          oncologo.nombre_completo
                                        }
                                      </strong>

                                      <span>
                                        {oncologo.correo}
                                      </span>

                                    </div>

                                  </div>

                                </td>


                                <td>

                                  <span
                                    className="oncologists-document"
                                  >
                                    {
                                      oncologo.ci_completo
                                      ??
                                      construirCi(
                                        oncologo.ci_numero,
                                        oncologo.ci_complemento,
                                        oncologo.ci_expedido,
                                      )
                                    }
                                  </span>

                                </td>


                                <td>
                                  {
                                    oncologo.matricula_profesional
                                    ??
                                    "Sin registro"
                                  }
                                </td>


                                <td>

                                  <span
                                    className={`
                                      oncologists-role
                                      ${
                                        oncologo.rol_codigo ===
                                        "JEFE_ONCOLOGIA"
                                          ? "oncologists-role--chief"
                                          : "oncologists-role--oncologist"
                                      }
                                    `}
                                  >

                                    {
                                      oncologo.rol_codigo ===
                                      "JEFE_ONCOLOGIA"
                                        ? (
                                            <ShieldCheck
                                              size={13}
                                            />
                                          )
                                        : (
                                            <Stethoscope
                                              size={13}
                                            />
                                          )
                                    }

                                    {
                                      nombreRol(
                                        oncologo.rol_codigo
                                      )
                                    }

                                  </span>

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
                                      oncologo.estado_nombre
                                    }

                                  </span>

                                </td>


                                <td>

                                  <div
                                    className="oncologists-actions"
                                  >

                                    <button
                                      type="button"
                                      onClick={
                                        () =>
                                          void abrirDetalle(
                                            oncologo.id_usuario
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
                                      onClick={
                                        () =>
                                          abrirCambioEstado(
                                            oncologo
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

                            )
                          )
                        }

                      </tbody>

                    </table>

                  </div>
                )
        }

      </section>


      {/* =================================================
          CARGANDO DETALLE
          ================================================= */}

      {
        cargandoDetalle
        &&
        (
          <div
            className="oncologists-modal-backdrop"
          >

            <div
              className="oncologists-modal oncologists-modal--loading"
            >

              <LoaderCircle
                size={28}
                className="oncologists-spin"
              />

              Consultando profesional...

            </div>

          </div>
        )
      }


      {/* =================================================
          DETALLE
          ================================================= */}

      {
        detalle
        &&
        (
          <div
            className="oncologists-modal-backdrop"
            onMouseDown={
              cerrarDetalle
            }
          >

            <section
              className="oncologists-modal"
              onMouseDown={
                (event) =>
                  event.stopPropagation()
              }
            >

              <header
                className="oncologists-modal__header"
              >

                <div>

                  <span>
                    Personal de Oncología
                  </span>

                  <h2>
                    {detalle.nombre_completo}
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


              {
                erroresEdicion.general
                &&
                (
                  <div
                    className="oncologists-alert oncologists-alert--error"
                  >

                    <AlertCircle
                      size={18}
                    />

                    {
                      erroresEdicion.general
                    }

                  </div>
                )
              }


              {
                !modoEdicion
                  ? (
                      <>

                        <div
                          className="oncologists-detail-profile"
                        >

                          <div
                            className="oncologists-detail-profile__avatar"
                          >
                            {
                              obtenerIniciales(
                                detalle.nombre_completo
                              )
                            }
                          </div>


                          <div>

                            <strong>
                              {
                                detalle.nombre_completo
                              }
                            </strong>

                            <span>
                              {
                                nombreRol(
                                  detalle.rol_codigo
                                )
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
                              detalle.estado_nombre
                            }

                          </span>

                        </div>


                        <div
                          className="oncologists-detail-section-title"
                        >
                          Datos personales
                        </div>


                        <div
                          className="oncologists-detail-grid"
                        >

                          <div>

                            <IdCard
                              size={17}
                            />

                            <span>
                              Cédula de identidad
                            </span>

                            <strong>
                              {
                                detalle.ci_completo
                                ??
                                construirCi(
                                  detalle.ci_numero,
                                  detalle.ci_complemento,
                                  detalle.ci_expedido,
                                )
                              }
                            </strong>

                          </div>


                          <div>

                            <MapPin
                              size={17}
                            />

                            <span>
                              Expedido en
                            </span>

                            <strong>
                              {
                                nombreDepartamento(
                                  detalle.ci_expedido
                                )
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
                                detalle.telefono
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
                              {
                                formatearFecha(
                                  detalle.fecha_creacion
                                )
                              }
                            </strong>

                          </div>

                        </div>


                        <div
                          className="oncologists-detail-section-title"
                        >
                          Información profesional
                        </div>


                        <div
                          className="oncologists-detail-grid"
                        >

                          <div>

                            <BadgeCheck
                              size={17}
                            />

                            <span>
                              Matrícula profesional
                            </span>

                            <strong>
                              {
                                detalle.perfil
                                  ?.matricula_profesional
                                ??
                                "Sin registro"
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
                                detalle.perfil
                                  ?.especialidad
                                ??
                                "Oncología"
                              }
                            </strong>

                          </div>


                          <div>

                            <BriefcaseMedical
                              size={17}
                            />

                            <span>
                              Subespecialidad
                            </span>

                            <strong>
                              {
                                detalle.perfil
                                  ?.subespecialidad
                                ??
                                "Sin registro"
                              }
                            </strong>

                          </div>


                          <div
                            className="oncologists-detail-highlight"
                          >

                            <BadgeCheck
                              size={17}
                            />

                            <span>
                              Área clínica
                            </span>

                            <strong>
                              {
                                detalle.perfil
                                  ?.area_clinica
                                ??
                                "Tumores óseos / Osteosarcoma"
                              }
                            </strong>

                          </div>


                          <div>

                            <Phone
                              size={17}
                            />

                            <span>
                              Teléfono institucional
                            </span>

                            <strong>
                              {
                                detalle.perfil
                                  ?.telefono_institucional
                                ??
                                "Sin registro"
                              }
                            </strong>

                          </div>


                          <div>

                            <ShieldCheck
                              size={17}
                            />

                            <span>
                              Cargo
                            </span>

                            <strong>
                              {
                                detalle.perfil
                                  ?.cargo
                                ??
                                nombreRol(
                                  detalle.rol_codigo
                                )
                              }
                            </strong>

                          </div>

                        </div>


                        <div
                          className="oncologists-detail-section-title"
                        >
                          Cuenta institucional
                        </div>


                        <div
                          className="oncologists-detail-grid"
                        >

                          <div>

                            <Mail
                              size={17}
                            />

                            <span>
                              Correo
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
                              Nombre de usuario
                            </span>

                            <strong>
                              @{detalle.nombre_usuario}
                            </strong>

                          </div>


                          <div>

                            <ShieldCheck
                              size={17}
                            />

                            <span>
                              Rol
                            </span>

                            <strong>
                              {
                                nombreRol(
                                  detalle.rol_codigo
                                )
                              }
                            </strong>

                          </div>

                        </div>


                        <footer
                          className="oncologists-modal__footer"
                        >

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
                            onClick={
                              () =>
                                setModoEdicion(
                                  true
                                )
                            }
                          >

                            <Pencil
                              size={17}
                            />

                            Editar profesional

                          </button>

                        </footer>

                      </>
                    )
                  : (
                      <>

                        <div
                          className="oncologists-edit-note"
                        >

                          <ShieldCheck
                            size={18}
                          />

                          <div>

                            <strong>
                              Campos controlados
                            </strong>

                            <span>
                              El nombre de usuario, especialidad y área clínica
                              son administrados automáticamente por el sistema.
                            </span>

                          </div>

                        </div>


                        <div
                          className="oncologists-edit-grid"
                        >

                          <label>

                            <span>
                              Nombres *
                            </span>

                            <input
                              value={
                                formEdicion.nombres
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "nombres",
                                    event.target.value
                                  )
                              }
                            />

                            {
                              erroresEdicion.nombres
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.nombres
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Apellido paterno *
                            </span>

                            <input
                              value={
                                formEdicion.apellido_paterno
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "apellido_paterno",
                                    event.target.value
                                  )
                              }
                            />

                            {
                              erroresEdicion.apellido_paterno
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.apellido_paterno
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Apellido materno
                            </span>

                            <input
                              value={
                                formEdicion.apellido_materno
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "apellido_materno",
                                    event.target.value
                                  )
                              }
                            />

                          </label>


                          <label>

                            <span>
                              Teléfono personal
                            </span>

                            <input
                              value={
                                formEdicion.telefono
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "telefono",
                                    event.target.value
                                  )
                              }
                              inputMode="numeric"
                              maxLength={8}
                            />

                            {
                              erroresEdicion.telefono
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.telefono
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              CI *
                            </span>

                            <input
                              value={
                                formEdicion.ci_numero
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "ci_numero",
                                    event.target.value
                                  )
                              }
                              inputMode="numeric"
                              maxLength={20}
                            />

                            {
                              erroresEdicion.ci_numero
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.ci_numero
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Complemento
                            </span>

                            <input
                              value={
                                formEdicion.ci_complemento
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "ci_complemento",
                                    event.target.value
                                  )
                              }
                              maxLength={10}
                            />

                          </label>


                          <label>

                            <span>
                              Expedido *
                            </span>

                            <select
                              value={
                                formEdicion.ci_expedido
                                ??
                                "LP"
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "ci_expedido",
                                    event.target.value
                                  )
                              }
                            >

                              {
                                DEPARTAMENTOS.map(
                                  (departamento) => (

                                    <option
                                      key={
                                        departamento.codigo
                                      }
                                      value={
                                        departamento.codigo
                                      }
                                    >
                                      {
                                        departamento.nombre
                                      }
                                    </option>

                                  )
                                )
                              }

                            </select>

                          </label>


                          <label>

                            <span>
                              Correo institucional *
                            </span>

                            <input
                              type="email"
                              value={
                                formEdicion.correo
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "correo",
                                    event.target.value
                                  )
                              }
                            />

                            {
                              erroresEdicion.correo
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.correo
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Matrícula profesional *
                            </span>

                            <input
                              value={
                                formEdicion.matricula_profesional
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "matricula_profesional",
                                    event.target.value
                                  )
                              }
                              maxLength={30}
                            />

                            {
                              erroresEdicion.matricula_profesional
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.matricula_profesional
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Subespecialidad *
                            </span>

                            <select
                              value={
                                formEdicion.subespecialidad
                                ??
                                "Oncología médica"
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "subespecialidad",
                                    event.target.value
                                  )
                              }
                            >

                              {
                                SUBESPECIALIDADES.map(
                                  (opcion) => (

                                    <option
                                      key={opcion}
                                      value={opcion}
                                    >
                                      {opcion}
                                    </option>

                                  )
                                )
                              }

                            </select>

                          </label>


                          <label>

                            <span>
                              Teléfono institucional
                            </span>

                            <input
                              value={
                                formEdicion.telefono_institucional
                                ??
                                ""
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "telefono_institucional",
                                    event.target.value
                                  )
                              }
                              inputMode="numeric"
                              maxLength={8}
                            />

                            {
                              erroresEdicion.telefono_institucional
                              &&
                              (
                                <small>
                                  {
                                    erroresEdicion.telefono_institucional
                                  }
                                </small>
                              )
                            }

                          </label>


                          <label>

                            <span>
                              Rol *
                            </span>

                            <select
                              value={
                                formEdicion.rol_codigo
                                ??
                                "ONCOLOGO"
                              }
                              onChange={
                                (event) =>
                                  actualizarCampo(
                                    "rol_codigo",
                                    event.target.value
                                  )
                              }
                            >

                              <option value="ONCOLOGO">
                                Oncólogo
                              </option>

                              <option value="JEFE_ONCOLOGIA">
                                Jefe de Oncología
                              </option>

                            </select>

                          </label>


                          <label>

                            <span>
                              Especialidad
                            </span>

                            <div
                              className="oncologist-readonly-field"
                            >
                              <Stethoscope
                                size={16}
                              />

                              Oncología

                              <BadgeCheck
                                size={15}
                              />
                            </div>

                          </label>


                          <label>

                            <span>
                              Área clínica
                            </span>

                            <div
                              className="oncologist-readonly-field oncologist-readonly-field--accent"
                            >
                              <BadgeCheck
                                size={16}
                              />

                              Tumores óseos / Osteosarcoma
                            </div>

                          </label>

                        </div>


                        <footer
                          className="oncologists-modal__footer"
                        >

                          <button
                            type="button"
                            className="oncologists-secondary-button"
                            onClick={
                              () => {
                                setModoEdicion(false);
                                setErroresEdicion({});
                              }
                            }
                            disabled={
                              guardando
                            }
                          >
                            Cancelar
                          </button>


                          <button
                            type="button"
                            className="oncologists-primary-button"
                            onClick={
                              () =>
                                void guardarEdicion()
                            }
                            disabled={
                              guardando
                            }
                          >

                            {
                              guardando
                                ? (
                                    <LoaderCircle
                                      size={17}
                                      className="oncologists-spin"
                                    />
                                  )
                                : (
                                    <Save
                                      size={17}
                                    />
                                  )
                            }

                            {
                              guardando
                                ? "Guardando..."
                                : "Guardar cambios"
                            }

                          </button>

                        </footer>

                      </>
                    )
              }

            </section>

          </div>
        )
      }


      {/* =================================================
          CAMBIAR ESTADO
          ================================================= */}

      {
        oncologoEstado
        &&
        (
          <div
            className="oncologists-modal-backdrop"
            onMouseDown={
              cerrarCambioEstado
            }
          >

            <section
              className="oncologists-confirm-modal"
              onMouseDown={
                (event) =>
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
                              oncologoEstado.nombre_completo
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
                              oncologoEstado.nombre_completo
                            }
                          </strong>
                          ?
                        </>
                      )
                }
              </p>


              {
                oncologoEstado.estado ===
                "ACTIVO"
                &&
                (
                  <div
                    className="oncologists-confirm-modal__notice"
                  >

                    <AlertCircle
                      size={18}
                    />

                    <span>
                      La cuenta será deshabilitada,
                      pero <strong>no será eliminada</strong>.
                      Su información e historial serán conservados.
                    </span>

                  </div>
                )
              }


              <div
                className="oncologists-confirm-modal__actions"
              >

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
                  onClick={
                    () =>
                      void confirmarCambioEstado()
                  }
                  disabled={
                    procesandoEstado
                  }
                >

                  {
                    procesandoEstado
                      ? (
                          <LoaderCircle
                            size={17}
                            className="oncologists-spin"
                          />
                        )
                      : oncologoEstado.estado ===
                        "ACTIVO"
                        ? (
                            <PowerOff
                              size={17}
                            />
                          )
                        : (
                            <Power
                              size={17}
                            />
                          )
                  }

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
        )
      }

    </div>

  );
}