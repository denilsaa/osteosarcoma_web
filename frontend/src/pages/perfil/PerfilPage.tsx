import {
  AlertCircle,
  BadgeCheck,
  BriefcaseMedical,
  CalendarDays,
  CheckCircle2,
  Eye,
  LoaderCircle,
  LockKeyhole,
  Mail,
  Pencil,
  Phone,
  Save,
  ShieldCheck,
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
  actualizarMiPerfil,
  obtenerMensajeErrorPerfil,
  obtenerMiPerfil,
  type MiPerfil,
} from "../../api/perfil.api";

import "./PerfilPage.css";


interface FormularioPerfil {

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string;

  telefono: string;

}


const formularioVacio:
  FormularioPerfil = {

    nombres: "",

    apellido_paterno: "",

    apellido_materno: "",

    telefono: "",

  };


function formatearFecha(
  valor?: string | null,
): string {

  if (!valor) {
    return "Sin registro";
  }


  const fecha =
    new Date(valor);


  if (
    Number.isNaN(
      fecha.getTime(),
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
  ).format(fecha);

}


function nombreRol(
  roles: string[],
): string {

  if (
    roles.includes(
      "JEFE_ONCOLOGIA",
    )
  ) {

    return "Jefe de Oncología";

  }


  if (
    roles.includes(
      "ONCOLOGO",
    )
  ) {

    return "Médico oncólogo";

  }


  return "Personal autorizado";

}


function obtenerIniciales(
  nombre: string,
): string {

  return nombre
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map(
      (parte) =>
        parte.charAt(0),
    )
    .join("")
    .toUpperCase()
    ||
    "US";

}


export function PerfilPage() {

  const [
    perfil,
    setPerfil,
  ] = useState<
    MiPerfil | null
  >(null);


  const [
    cargando,
    setCargando,
  ] = useState(true);


  const [
    editando,
    setEditando,
  ] = useState(false);


  const [
    guardando,
    setGuardando,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  const [
    exito,
    setExito,
  ] = useState("");


  const [
    erroresFormulario,
    setErroresFormulario,
  ] = useState<
    Record<string, string>
  >({});


  const [
    formulario,
    setFormulario,
  ] = useState<
    FormularioPerfil
  >(
    formularioVacio,
  );


  // ========================================================
  // CARGAR PERFIL REAL
  // ========================================================

  useEffect(
    () => {

      const cargarPerfil =
        async () => {

          try {

            setCargando(true);

            setError("");


            const response =
              await obtenerMiPerfil();


            setPerfil(
              response,
            );

          } catch (errorActual) {

            setError(
              obtenerMensajeErrorPerfil(
                errorActual,
              ),
            );

          } finally {

            setCargando(false);

          }

        };


      void cargarPerfil();

    },
    [],
  );


  // ========================================================
  // DATOS DERIVADOS
  // ========================================================

  const rolVisible =
    useMemo(
      () =>
        nombreRol(
          perfil?.roles ?? [],
        ),
      [
        perfil,
      ],
    );


  const iniciales =
    useMemo(
      () =>
        obtenerIniciales(
          perfil?.nombre_completo
          ??
          "Usuario",
        ),
      [
        perfil,
      ],
    );


  // ========================================================
  // ABRIR EDICIÓN
  // ========================================================

  const abrirEdicion =
    () => {

      if (!perfil) {
        return;
      }


      setFormulario({

        nombres:
          perfil.nombres ?? "",

        apellido_paterno:
          perfil.apellido_paterno
          ?? "",

        apellido_materno:
          perfil.apellido_materno
          ?? "",

        telefono:
          perfil.telefono
          ?? "",

      });


      setErroresFormulario({});

      setError("");

      setEditando(true);

    };


  const cerrarEdicion =
    () => {

      if (guardando) {
        return;
      }


      setEditando(false);

      setErroresFormulario({});

      setFormulario(
        formularioVacio,
      );

    };


  // ========================================================
  // ACTUALIZAR INPUT
  // ========================================================

  const actualizarCampo =
    (
      campo:
        keyof FormularioPerfil,

      valor: string,
    ) => {

      setFormulario(
        (actual) => ({

          ...actual,

          [campo]:
            valor,

        }),
      );


      setErroresFormulario(
        (actual) => {

          const nuevos = {
            ...actual,
          };


          delete nuevos[campo];


          return nuevos;

        },
      );

    };


  // ========================================================
  // VALIDACIONES VISIBLES
  // ========================================================

  const validar =
    (): Record<
      string,
      string
    > => {

      const errores:
        Record<
          string,
          string
        > = {};


      if (
        formulario
          .nombres
          .trim()
          .length < 2
      ) {

        errores.nombres =
          "Ingrese sus nombres.";

      }


      if (
        formulario
          .apellido_paterno
          .trim()
          .length < 2
      ) {

        errores.apellido_paterno =
          "Ingrese su apellido paterno.";

      }


      if (
        formulario.telefono.trim()
      ) {

        const telefonoValido =
          /^[0-9+\-\s()]{7,25}$/;


        if (
          !telefonoValido.test(
            formulario.telefono.trim(),
          )
        ) {

          errores.telefono =
            "Ingrese un número de teléfono válido.";

        }

      }


      return errores;

    };


  // ========================================================
  // GUARDAR
  // ========================================================

  const guardar =
    async () => {

      const erroresLocales =
        validar();


      if (
        Object.keys(
          erroresLocales,
        ).length > 0
      ) {

        setErroresFormulario(
          erroresLocales,
        );

        return;

      }


      try {

        setGuardando(true);

        setError("");

        setExito("");

        setErroresFormulario({});


        const response =
          await actualizarMiPerfil(
            {
              nombres:
                formulario
                  .nombres
                  .trim(),

              apellido_paterno:
                formulario
                  .apellido_paterno
                  .trim(),

              apellido_materno:
                formulario
                  .apellido_materno
                  .trim()
                ||
                null,

              telefono:
                formulario
                  .telefono
                  .trim()
                ||
                null,
            },
          );


        setPerfil(
          response.perfil,
        );


        setEditando(
          false,
        );


        setExito(
          response.mensaje,
        );


        window.setTimeout(
          () => {

            setExito("");

          },
          3500,
        );

      } catch (errorActual) {

        setError(
          obtenerMensajeErrorPerfil(
            errorActual,
          ),
        );

      } finally {

        setGuardando(false);

      }

    };


  // ========================================================
  // LOADING
  // ========================================================

  if (cargando) {

    return (

      <div className="profile-page">

        <div className="profile-loading">

          <LoaderCircle
            size={30}
            className="profile-spin"
          />

          <strong>
            Cargando perfil...
          </strong>

          <span>
            Consultando información de su cuenta.
          </span>

        </div>

      </div>

    );

  }


  if (!perfil) {

    return (

      <div className="profile-page">

        <div className="profile-error-state">

          <AlertCircle
            size={30}
          />

          <strong>
            No fue posible cargar el perfil
          </strong>

          <span>
            {error}
          </span>

        </div>

      </div>

    );

  }


  return (

    <div className="profile-page">


      {/* ====================================================
          CABECERA
          ==================================================== */}

      <section className="profile-hero">


        <div>

          <span className="profile-hero__eyebrow">
            Cuenta institucional
          </span>

          <h1>
            Mi perfil
          </h1>

          <p>

            Consulte su información personal
            y actualice únicamente los datos
            autorizados.

          </p>

        </div>


        <button

          type="button"

          className="profile-edit-button"

          onClick={
            abrirEdicion
          }

        >

          <Pencil
            size={17}
          />

          Editar mis datos

        </button>


      </section>


      {/* ====================================================
          MENSAJES
          ==================================================== */}

      {exito && (

        <div className="profile-alert profile-alert--success">

          <CheckCircle2
            size={18}
          />

          {exito}

        </div>

      )}


      {error && (

        <div className="profile-alert profile-alert--error">

          <AlertCircle
            size={18}
          />

          {error}

        </div>

      )}


      {/* ====================================================
          PERFIL
          ==================================================== */}

      <div className="profile-grid">


        <section className="profile-card">


          <div className="profile-card__heading">

            <div className="profile-card__icon">

              <UserRound
                size={20}
              />

            </div>

            <div>

              <h2>
                Información personal
              </h2>

              <p>
                Datos asociados a su cuenta.
              </p>

            </div>

          </div>


          <div className="profile-account">


            <div className="profile-account__avatar">

              {iniciales}

            </div>


            <div>

              <strong>
                {perfil.nombre_completo}
              </strong>

              <span>
                {rolVisible}
              </span>

            </div>


            <span
              className={`
                profile-state
                ${
                  perfil.estado === "ACTIVO"
                    ? "profile-state--active"
                    : "profile-state--inactive"
                }
              `}
            >

              <span />

              {perfil.estado_nombre}

            </span>


          </div>


          <div className="profile-data-grid">


            <div className="profile-data-item">

              <UserRound
                size={17}
              />

              <span>
                Nombres
              </span>

              <strong>
                {perfil.nombres}
              </strong>

            </div>


            <div className="profile-data-item">

              <UserRound
                size={17}
              />

              <span>
                Apellidos
              </span>

              <strong>

                {
                  [
                    perfil.apellido_paterno,
                    perfil.apellido_materno,
                  ]
                    .filter(Boolean)
                    .join(" ")
                }

              </strong>

            </div>


            <div className="profile-data-item">

              <Phone
                size={17}
              />

              <span>
                Teléfono personal
              </span>

              <strong>

                {perfil.telefono
                  ||
                  "Sin registro"}

              </strong>

            </div>


            <div className="profile-data-item">

              <CalendarDays
                size={17}
              />

              <span>
                Registrado
              </span>

              <strong>

                {formatearFecha(
                  perfil.fecha_creacion,
                )}

              </strong>

            </div>


          </div>


        </section>


        {/* ==================================================
            INFORMACIÓN INSTITUCIONAL
            ================================================== */}

        <section className="profile-card">


          <div className="profile-card__heading">

            <div className="profile-card__icon">

              <ShieldCheck
                size={20}
              />

            </div>

            <div>

              <h2>
                Información institucional
              </h2>

              <p>
                Datos administrados por Jefatura.
              </p>

            </div>

          </div>


          <div className="profile-institutional-list">


            <div>

              <Mail
                size={18}
              />

              <span>
                Correo institucional
              </span>

              <strong>
                {perfil.correo}
              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div>

              <UserRound
                size={18}
              />

              <span>
                Nombre de usuario
              </span>

              <strong>
                {perfil.nombre_usuario}
              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div>

              <Stethoscope
                size={18}
              />

              <span>
                Rol
              </span>

              <strong>
                {rolVisible}
              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div>

              <BadgeCheck
                size={18}
              />

              <span>
                Matrícula profesional
              </span>

              <strong>

                {
                  perfil
                    .perfil_profesional
                    .matricula_profesional
                  ||
                  "Sin registro"
                }

              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div>

              <BriefcaseMedical
                size={18}
              />

              <span>
                Especialidad
              </span>

              <strong>

                {
                  perfil
                    .perfil_profesional
                    .especialidad
                  ||
                  "Sin registro"
                }

              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div>

              <Stethoscope
                size={18}
              />

              <span>
                Cargo
              </span>

              <strong>

                {
                  perfil
                    .perfil_profesional
                    .cargo
                  ||
                  rolVisible
                }

              </strong>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


          </div>


          <div className="profile-protected-note">

            <ShieldCheck
              size={19}
            />

            <div>

              <strong>
                Información protegida
              </strong>

              <span>

                Estos datos no pueden
                modificarse desde Mi perfil.

              </span>

            </div>

          </div>


        </section>


      </div>


      {/* ====================================================
          SEGURIDAD
          ==================================================== */}

      <section className="profile-card">


        <div className="profile-card__heading">

          <div className="profile-card__icon">

            <ShieldCheck
              size={20}
            />

          </div>

          <div>

            <h2>
              Seguridad de la cuenta
            </h2>

            <p>
              Estado actual del acceso institucional.
            </p>

          </div>

        </div>


        <div className="profile-security-grid">


          <div className="profile-security-status">

            <div className="profile-security-status__icon">

              <CheckCircle2
                size={23}
              />

            </div>

            <div>

              <strong>
                Sesión activa
              </strong>

              <span>
                Su sesión se encuentra validada.
              </span>

            </div>

          </div>


          <div className="profile-security-info">

            <ShieldCheck
              size={20}
            />

            <div>

              <strong>
                Acceso protegido
              </strong>

              <span>

                La plataforma valida automáticamente
                su sesión y sus permisos.

              </span>

            </div>

          </div>


          <div className="profile-security-info">

            <Eye
              size={20}
            />

            <div>

              <strong>
                Último acceso
              </strong>

              <span>

                {formatearFecha(
                  perfil.ultimo_acceso,
                )}

              </span>

            </div>

          </div>


        </div>


      </section>


      {/* ====================================================
          MODAL EDICIÓN
          ==================================================== */}

      {editando && (

        <div
          className="profile-modal-backdrop"
          onMouseDown={
            cerrarEdicion
          }
        >

          <section

            className="profile-modal"

            onMouseDown={(event) =>
              event.stopPropagation()
            }

          >


            <header className="profile-modal__header">

              <div>

                <span>
                  Mi perfil
                </span>

                <h2>
                  Editar datos personales
                </h2>

              </div>


              <button

                type="button"

                onClick={
                  cerrarEdicion
                }

                disabled={
                  guardando
                }

              >

                <X
                  size={19}
                />

              </button>

            </header>


            <div className="profile-modal__notice">

              <ShieldCheck
                size={19}
              />

              <div>

                <strong>
                  Datos autorizados
                </strong>

                <span>

                  Puede modificar únicamente
                  sus datos personales.

                </span>

              </div>

            </div>


            <div className="profile-edit-grid">


              <label>

                <span>
                  Nombres *
                </span>

                <input

                  value={
                    formulario.nombres
                  }

                  onChange={(event) =>
                    actualizarCampo(
                      "nombres",
                      event.target.value,
                    )
                  }

                />

                {erroresFormulario.nombres && (

                  <small>
                    {erroresFormulario.nombres}
                  </small>

                )}

              </label>


              <label>

                <span>
                  Apellido paterno *
                </span>

                <input

                  value={
                    formulario
                      .apellido_paterno
                  }

                  onChange={(event) =>
                    actualizarCampo(
                      "apellido_paterno",
                      event.target.value,
                    )
                  }

                />

                {erroresFormulario.apellido_paterno && (

                  <small>

                    {
                      erroresFormulario
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
                    formulario
                      .apellido_materno
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
                  Teléfono personal
                </span>

                <input

                  value={
                    formulario.telefono
                  }

                  onChange={(event) =>
                    actualizarCampo(
                      "telefono",
                      event.target.value,
                    )
                  }

                  placeholder="Ej. 71234567"

                />

                {erroresFormulario.telefono && (

                  <small>
                    {erroresFormulario.telefono}
                  </small>

                )}

              </label>


            </div>


            <div className="profile-readonly-preview">

              <LockKeyhole
                size={18}
              />

              <div>

                <strong>
                  Datos institucionales bloqueados
                </strong>

                <span>

                  Correo, usuario, rol, matrícula,
                  especialidad y cargo solo pueden ser
                  administrados por personal autorizado.

                </span>

              </div>

            </div>


            <footer className="profile-modal__footer">


              <button

                type="button"

                className="profile-secondary-button"

                onClick={
                  cerrarEdicion
                }

                disabled={
                  guardando
                }

              >

                Cancelar

              </button>


              <button

                type="button"

                className="profile-primary-button"

                onClick={() =>
                  void guardar()
                }

                disabled={
                  guardando
                }

              >

                {guardando ? (

                  <LoaderCircle
                    size={17}
                    className="profile-spin"
                  />

                ) : (

                  <Save
                    size={17}
                  />

                )}

                {guardando
                  ? "Guardando..."
                  : "Guardar cambios"}

              </button>


            </footer>


          </section>

        </div>

      )}


    </div>

  );

}