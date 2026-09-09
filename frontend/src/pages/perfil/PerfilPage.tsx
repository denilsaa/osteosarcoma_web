import {
  AlertCircle,
  BadgeCheck,
  BriefcaseMedical,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Fingerprint,
  IdCard,
  LoaderCircle,
  LockKeyhole,
  Mail,
  MapPin,
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


/* =========================================================
   FORMULARIO
   ========================================================= */

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


/* =========================================================
   DEPARTAMENTOS
   ========================================================= */

const DEPARTAMENTOS:
  Record<string, string> = {

  LP: "La Paz",

  CB: "Cochabamba",

  SC: "Santa Cruz",

  OR: "Oruro",

  PT: "Potosí",

  CH: "Chuquisaca",

  TJ: "Tarija",

  BE: "Beni",

  PD: "Pando",

};


/* =========================================================
   UTILIDADES
   ========================================================= */

function formatearFecha(
  valor?: string | null,
): string {

  if (
    !valor
  ) {

    return "Sin registro";

  }


  const fecha =
    new Date(
      valor
    );


  if (
    Number.isNaN(
      fecha.getTime()
    )
  ) {

    return "Sin registro";

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
    fecha
  );

}


function obtenerIniciales(
  nombre: string,
): string {

  return (
    nombre
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map(
        (
          parte
        ) =>
          parte.charAt(0)
      )
      .join("")
      .toUpperCase()
    ||
    "US"
  );

}


function nombreDepartamento(
  codigo?: string | null,
): string {

  if (
    !codigo
  ) {

    return "Sin registro";

  }


  return (
    DEPARTAMENTOS[
      codigo
    ]
    ||
    codigo
  );

}


/* =========================================================
   COMPONENTE
   ========================================================= */

export function PerfilPage() {

  const [
    perfil,
    setPerfil,
  ] = useState<
    MiPerfil | null
  >(
    null
  );


  const [
    cargando,
    setCargando,
  ] = useState(
    true
  );


  const [
    editando,
    setEditando,
  ] = useState(
    false
  );


  const [
    guardando,
    setGuardando,
  ] = useState(
    false
  );


  const [
    error,
    setError,
  ] = useState(
    ""
  );


  const [
    exito,
    setExito,
  ] = useState(
    ""
  );


  const [
    erroresFormulario,
    setErroresFormulario,
  ] = useState<
    Record<
      string,
      string
    >
  >(
    {}
  );


  const [
    formulario,
    setFormulario,
  ] = useState<
    FormularioPerfil
  >(
    formularioVacio
  );


  /* =======================================================
     CARGAR PERFIL
     ======================================================= */

  useEffect(
    () => {

      const cargarPerfil =
        async () => {

          try {

            setCargando(
              true
            );

            setError(
              ""
            );


            const response =
              await obtenerMiPerfil();


            setPerfil(
              response
            );

          } catch (
            errorActual
          ) {

            setError(
              obtenerMensajeErrorPerfil(
                errorActual
              )
            );

          } finally {

            setCargando(
              false
            );

          }

        };


      void cargarPerfil();

    },
    [],
  );


  /* =======================================================
     DATOS DERIVADOS
     ======================================================= */

  const rolVisible =
    useMemo(
      () => {

        if (
          perfil?.rol_nombre
        ) {

          return (
            perfil.rol_nombre
          );

        }


        if (
          perfil?.roles.includes(
            "JEFE_ONCOLOGIA"
          )
        ) {

          return (
            "Jefe de Oncología"
          );

        }


        if (
          perfil?.roles.includes(
            "ONCOLOGO"
          )
        ) {

          return (
            "Oncólogo"
          );

        }


        return (
          "Personal autorizado"
        );

      },
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
          "Usuario"
        ),
      [
        perfil,
      ],
    );


  /* =======================================================
     ABRIR EDICIÓN
     ======================================================= */

  const abrirEdicion =
    () => {

      if (
        !perfil
      ) {

        return;

      }


      setFormulario(
        {

          nombres:
            perfil.nombres
            ??
            "",

          apellido_paterno:
            perfil.apellido_paterno
            ??
            "",

          apellido_materno:
            perfil.apellido_materno
            ??
            "",

          telefono:
            perfil.telefono
            ??
            "",

        }
      );


      setErroresFormulario(
        {}
      );


      setError(
        ""
      );


      setEditando(
        true
      );

    };


  /* =======================================================
     CERRAR EDICIÓN
     ======================================================= */

  const cerrarEdicion =
    () => {

      if (
        guardando
      ) {

        return;

      }


      setEditando(
        false
      );


      setErroresFormulario(
        {}
      );


      setFormulario(
        formularioVacio
      );

    };


  /* =======================================================
     ACTUALIZAR CAMPO
     ======================================================= */

  const actualizarCampo = (
    campo:
      keyof FormularioPerfil,

    valorOriginal:
      string,
  ) => {

    let valor =
      valorOriginal;


    if (
      campo ===
      "telefono"
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


    setFormulario(
      (
        actual
      ) => ({
        ...actual,
        [campo]:
          valor,
      })
    );


    setErroresFormulario(
      (
        actual
      ) => {

        const nuevos = {
          ...actual,
        };


        delete nuevos[
          campo
        ];


        return nuevos;

      }
    );

  };


  /* =======================================================
     VALIDAR
     ======================================================= */

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
        formulario
          .telefono
          .trim()
      ) {

        if (
          !/^[67]\d{7}$/.test(
            formulario
              .telefono
              .trim()
          )
        ) {

          errores.telefono =
            (
              "El teléfono debe tener 8 dígitos " +
              "y comenzar con 6 o 7."
            );

        }

      }


      return errores;

    };


  /* =======================================================
     GUARDAR
     ======================================================= */

  const guardar =
    async () => {

      const erroresLocales =
        validar();


      if (
        Object.keys(
          erroresLocales
        ).length > 0
      ) {

        setErroresFormulario(
          erroresLocales
        );

        return;

      }


      try {

        setGuardando(
          true
        );


        setError(
          ""
        );


        setExito(
          ""
        );


        setErroresFormulario(
          {}
        );


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

            }
          );


        setPerfil(
          response.perfil
        );


        setEditando(
          false
        );


        setExito(
          response.mensaje
        );


        window.setTimeout(
          () => {

            setExito(
              ""
            );

          },
          3500
        );

      } catch (
        errorActual
      ) {

        setError(
          obtenerMensajeErrorPerfil(
            errorActual
          )
        );

      } finally {

        setGuardando(
          false
        );

      }

    };


  /* =======================================================
     CARGANDO
     ======================================================= */

  if (
    cargando
  ) {

    return (

      <div
        className="profile-page"
      >

        <div
          className="profile-loading"
        >

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


  /* =======================================================
     ERROR
     ======================================================= */

  if (
    !perfil
  ) {

    return (

      <div
        className="profile-page"
      >

        <div
          className="profile-error-state"
        >

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


  /* =======================================================
     RENDER
     ======================================================= */

  return (

    <div
      className="profile-page"
    >

      {/* =================================================
          HERO
          ================================================= */}

      <section
        className="profile-hero"
      >

        <div>

          <span
            className="profile-hero__eyebrow"
          >
            Cuenta institucional
          </span>

          <h1>
            Mi perfil
          </h1>

          <p>
            Consulte su información personal, profesional
            y los datos institucionales asociados a su cuenta.
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


      {/* =================================================
          MENSAJES
          ================================================= */}

      {
        exito
        &&
        (
          <div
            className="profile-alert profile-alert--success"
          >

            <CheckCircle2
              size={18}
            />

            {exito}

          </div>
        )
      }


      {
        error
        &&
        (
          <div
            className="profile-alert profile-alert--error"
          >

            <AlertCircle
              size={18}
            />

            {error}

          </div>
        )
      }


      {/* =================================================
          RESUMEN CUENTA
          ================================================= */}

      <section
        className="profile-summary-card"
      >

        <div
          className="profile-summary-card__avatar"
        >
          {iniciales}
        </div>


        <div
          className="profile-summary-card__identity"
        >

          <span>
            Perfil profesional
          </span>

          <h2>
            {perfil.nombre_completo}
          </h2>

          <div>

            <span
              className="profile-role-badge"
            >
              <Stethoscope
                size={13}
              />

              {rolVisible}
            </span>


            <span
              className={`
                profile-state
                ${
                  perfil.estado ===
                  "ACTIVO"
                    ? "profile-state--active"
                    : "profile-state--inactive"
                }
              `}
            >

              <span />

              {perfil.estado_nombre}

            </span>

          </div>

        </div>


        <div
          className="profile-summary-card__meta"
        >

          <span>
            <Mail
              size={14}
            />

            {perfil.correo}
          </span>

          <span>
            <Fingerprint
              size={14}
            />

            @{perfil.nombre_usuario}
          </span>

        </div>

      </section>


      {/* =================================================
          BLOQUES PRINCIPALES
          ================================================= */}

      <div
        className="profile-grid"
      >

        {/* ===============================================
            INFORMACIÓN PERSONAL
            =============================================== */}

        <section
          className="profile-card"
        >

          <div
            className="profile-card__heading"
          >

            <div
              className="profile-card__icon"
            >

              <UserRound
                size={20}
              />

            </div>


            <div>

              <h2>
                Información personal
              </h2>

              <p>
                Datos personales e identificación.
              </p>

            </div>

          </div>


          <div
            className="profile-data-grid"
          >

            <div
              className="profile-data-item"
            >

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


            <div
              className="profile-data-item"
            >

              <UserRound
                size={17}
              />

              <span>
                Apellidos
              </span>

              <strong>

                {
                  [
                    perfil
                      .apellido_paterno,

                    perfil
                      .apellido_materno,
                  ]
                    .filter(Boolean)
                    .join(" ")
                }

              </strong>

            </div>


            <div
              className="profile-data-item"
            >

              <IdCard
                size={17}
              />

              <span>
                Cédula de identidad
              </span>

              <strong>
                {
                  perfil.ci_completo
                  ||
                  "Sin registro"
                }
              </strong>

            </div>


            <div
              className="profile-data-item"
            >

              <MapPin
                size={17}
              />

              <span>
                Expedido en
              </span>

              <strong>
                {
                  nombreDepartamento(
                    perfil.ci_expedido
                  )
                }
              </strong>

            </div>


            <div
              className="profile-data-item"
            >

              <Phone
                size={17}
              />

              <span>
                Teléfono personal
              </span>

              <strong>
                {
                  perfil.telefono
                  ||
                  "Sin registro"
                }
              </strong>

            </div>


            <div
              className="profile-data-item"
            >

              <CalendarDays
                size={17}
              />

              <span>
                Cuenta registrada
              </span>

              <strong>
                {
                  formatearFecha(
                    perfil.fecha_creacion
                  )
                }
              </strong>

            </div>

          </div>


          <div
            className="profile-protected-note"
          >

            <LockKeyhole
              size={18}
            />

            <div>

              <strong>
                Documento protegido
              </strong>

              <span>
                La cédula de identidad no puede modificarse
                desde Mi perfil.
              </span>

            </div>

          </div>

        </section>


        {/* ===============================================
            INFORMACIÓN PROFESIONAL
            =============================================== */}

        <section
          className="profile-card"
        >

          <div
            className="profile-card__heading"
          >

            <div
              className="profile-card__icon"
            >

              <BriefcaseMedical
                size={20}
              />

            </div>


            <div>

              <h2>
                Información profesional
              </h2>

              <p>
                Información médica registrada por Jefatura.
              </p>

            </div>

          </div>


          <div
            className="profile-professional-grid"
          >

            <div
              className="profile-professional-item"
            >

              <BadgeCheck
                size={18}
              />

              <div>

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

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div
              className="profile-professional-item"
            >

              <Stethoscope
                size={18}
              />

              <div>

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

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div
              className="profile-professional-item"
            >

              <BriefcaseMedical
                size={18}
              />

              <div>

                <span>
                  Subespecialidad
                </span>

                <strong>
                  {
                    perfil
                      .perfil_profesional
                      .subespecialidad
                    ||
                    "Sin registro"
                  }
                </strong>

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div
              className="profile-professional-item profile-professional-item--highlight"
            >

              <BadgeCheck
                size={18}
              />

              <div>

                <span>
                  Área clínica
                </span>

                <strong>
                  {
                    perfil
                      .perfil_profesional
                      .area_clinica
                    ||
                    "Sin registro"
                  }
                </strong>

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div
              className="profile-professional-item"
            >

              <ShieldCheck
                size={18}
              />

              <div>

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

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>


            <div
              className="profile-professional-item"
            >

              <Phone
                size={18}
              />

              <div>

                <span>
                  Teléfono institucional
                </span>

                <strong>
                  {
                    perfil
                      .perfil_profesional
                      .telefono_institucional
                    ||
                    "Sin registro"
                  }
                </strong>

              </div>

              <LockKeyhole
                size={14}
                className="profile-lock"
              />

            </div>

          </div>


          <div
            className="profile-protected-note"
          >

            <ShieldCheck
              size={19}
            />

            <div>

              <strong>
                Información profesional protegida
              </strong>

              <span>
                Matrícula, especialidad, subespecialidad,
                área clínica y cargo son administrados
                por personal autorizado.
              </span>

            </div>

          </div>

        </section>

      </div>


      {/* =================================================
          CUENTA INSTITUCIONAL
          ================================================= */}

      <section
        className="profile-card"
      >

        <div
          className="profile-card__heading"
        >

          <div
            className="profile-card__icon"
          >

            <ShieldCheck
              size={20}
            />

          </div>


          <div>

            <h2>
              Cuenta institucional
            </h2>

            <p>
              Credenciales e información de acceso.
            </p>

          </div>

        </div>


        <div
          className="profile-institutional-grid"
        >

          <div
            className="profile-institutional-item"
          >

            <Mail
              size={18}
            />

            <div>

              <span>
                Correo institucional
              </span>

              <strong>
                {perfil.correo}
              </strong>

            </div>

            <LockKeyhole
              size={14}
              className="profile-lock"
            />

          </div>


          <div
            className="profile-institutional-item"
          >

            <Fingerprint
              size={18}
            />

            <div>

              <span>
                Nombre de usuario
              </span>

              <strong>
                @{perfil.nombre_usuario}
              </strong>

            </div>

            <LockKeyhole
              size={14}
              className="profile-lock"
            />

          </div>


          <div
            className="profile-institutional-item"
          >

            <Stethoscope
              size={18}
            />

            <div>

              <span>
                Rol principal
              </span>

              <strong>
                {rolVisible}
              </strong>

            </div>

            <LockKeyhole
              size={14}
              className="profile-lock"
            />

          </div>


          <div
            className="profile-institutional-item"
          >

            <CheckCircle2
              size={18}
            />

            <div>

              <span>
                Estado de cuenta
              </span>

              <strong>
                {perfil.estado_nombre}
              </strong>

            </div>

            <LockKeyhole
              size={14}
              className="profile-lock"
            />

          </div>

        </div>

      </section>


      {/* =================================================
          SEGURIDAD
          ================================================= */}

      <section
        className="profile-card"
      >

        <div
          className="profile-card__heading"
        >

          <div
            className="profile-card__icon"
          >

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


        <div
          className="profile-security-grid"
        >

          <div
            className="profile-security-status"
          >

            <div
              className="profile-security-status__icon"
            >

              <CheckCircle2
                size={23}
              />

            </div>


            <div>

              <strong>
                Sesión autenticada
              </strong>

              <span>
                Su sesión actual se encuentra validada.
              </span>

            </div>

          </div>


          <div
            className="profile-security-info"
          >

            <Clock3
              size={20}
            />

            <div>

              <strong>
                Último acceso
              </strong>

              <span>
                {
                  formatearFecha(
                    perfil.ultimo_acceso
                  )
                }
              </span>

            </div>

          </div>


          <div
            className="profile-security-info"
          >

            <CalendarDays
              size={20}
            />

            <div>

              <strong>
                Última actualización
              </strong>

              <span>
                {
                  formatearFecha(
                    perfil.fecha_actualizacion
                  )
                }
              </span>

            </div>

          </div>

        </div>

      </section>


      {/* =================================================
          MODAL EDICIÓN
          ================================================= */}

      {
        editando
        &&
        (
          <div
            className="profile-modal-backdrop"
            onMouseDown={
              cerrarEdicion
            }
          >

            <section
              className="profile-modal"
              onMouseDown={
                (
                  event
                ) =>
                  event.stopPropagation()
              }
            >

              <header
                className="profile-modal__header"
              >

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
                  aria-label="Cerrar"
                >

                  <X
                    size={19}
                  />

                </button>

              </header>


              <div
                className="profile-modal__notice"
              >

                <ShieldCheck
                  size={19}
                />

                <div>

                  <strong>
                    Datos autorizados
                  </strong>

                  <span>
                    Puede modificar únicamente sus nombres,
                    apellidos y teléfono personal.
                  </span>

                </div>

              </div>


              <div
                className="profile-edit-grid"
              >

                <label>

                  <span>
                    Nombres *
                  </span>

                  <input
                    value={
                      formulario.nombres
                    }
                    onChange={
                      (
                        event
                      ) =>
                        actualizarCampo(
                          "nombres",
                          event.target.value
                        )
                    }
                    maxLength={100}
                    aria-invalid={
                      Boolean(
                        erroresFormulario.nombres
                      )
                    }
                  />

                  {
                    erroresFormulario.nombres
                    &&
                    (
                      <small>
                        {
                          erroresFormulario
                            .nombres
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
                      formulario
                        .apellido_paterno
                    }
                    onChange={
                      (
                        event
                      ) =>
                        actualizarCampo(
                          "apellido_paterno",
                          event.target.value
                        )
                    }
                    maxLength={80}
                    aria-invalid={
                      Boolean(
                        erroresFormulario
                          .apellido_paterno
                      )
                    }
                  />

                  {
                    erroresFormulario
                      .apellido_paterno
                    &&
                    (
                      <small>
                        {
                          erroresFormulario
                            .apellido_paterno
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
                      formulario
                        .apellido_materno
                    }
                    onChange={
                      (
                        event
                      ) =>
                        actualizarCampo(
                          "apellido_materno",
                          event.target.value
                        )
                    }
                    maxLength={80}
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
                    onChange={
                      (
                        event
                      ) =>
                        actualizarCampo(
                          "telefono",
                          event.target.value
                        )
                    }
                    placeholder="Ej. 71234567"
                    inputMode="numeric"
                    maxLength={8}
                    aria-invalid={
                      Boolean(
                        erroresFormulario.telefono
                      )
                    }
                  />

                  {
                    erroresFormulario.telefono
                    &&
                    (
                      <small>
                        {
                          erroresFormulario
                            .telefono
                        }
                      </small>
                    )
                  }

                </label>

              </div>


              <div
                className="profile-readonly-preview"
              >

                <LockKeyhole
                  size={18}
                />

                <div>

                  <strong>
                    Datos protegidos
                  </strong>

                  <span>
                    CI, correo, usuario, rol, matrícula,
                    especialidad, subespecialidad, área clínica
                    y cargo no pueden modificarse desde esta sección.
                  </span>

                </div>

              </div>


              <footer
                className="profile-modal__footer"
              >

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
                  onClick={
                    () =>
                      void guardar()
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
                            className="profile-spin"
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

            </section>

          </div>
        )
      }

    </div>

  );

}