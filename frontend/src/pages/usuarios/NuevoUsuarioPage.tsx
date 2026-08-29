import {
  AlertCircle,
  ArrowLeft,
  BadgeCheck,
  Eye,
  EyeOff,
  LoaderCircle,
  Save,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  crearOncologo,
  normalizarErroresApi,
  type CrearOncologoPayload,
  type ErroresFormulario,
} from "../../api/oncologos.api";

import "./UsuariosPage.css";


interface FormularioOncologo
  extends CrearOncologoPayload {

  confirmar_password: string;

}


const formularioInicial:
  FormularioOncologo = {

    nombres: "",

    apellido_paterno: "",

    apellido_materno: "",

    correo: "",

    nombre_usuario: "",

    telefono: "",

    password: "",

    confirmar_password: "",

    matricula_profesional: "",

    especialidad:
      "Oncología",

    subespecialidad: "",

    telefono_institucional: "",

  };


export function NuevoUsuarioPage() {

  const navigate =
    useNavigate();


  const [
    formulario,
    setFormulario,
  ] = useState<
    FormularioOncologo
  >(
    formularioInicial,
  );


  const [
    errores,
    setErrores,
  ] = useState<
    ErroresFormulario
  >({});


  const [
    guardando,
    setGuardando,
  ] = useState(false);


  const [
    mostrarPassword,
    setMostrarPassword,
  ] = useState(false);


  const [
    mensajeExito,
    setMensajeExito,
  ] = useState("");


  const actualizarCampo =
    (
      campo:
        keyof FormularioOncologo,

      valor: string,
    ) => {

      setFormulario(
        (actual) => ({

          ...actual,

          [campo]:
            valor,

        }),
      );


      setErrores(
        (actual) => {

          const nuevo = {
            ...actual,
          };


          delete nuevo[campo];

          delete nuevo.general;


          return nuevo;

        },
      );

    };


  const validarFormulario =
    (): ErroresFormulario => {

      const nuevos:
        ErroresFormulario = {};


      if (
        formulario
          .nombres
          .trim()
          .length < 2
      ) {

        nuevos.nombres =
          "Ingrese los nombres del oncólogo.";

      }


      if (
        formulario
          .apellido_paterno
          .trim()
          .length < 2
      ) {

        nuevos
          .apellido_paterno =
            "Ingrese el apellido paterno.";

      }


      const patronCorreo =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


      if (
        !patronCorreo.test(
          formulario
            .correo
            .trim(),
        )
      ) {

        nuevos.correo =
          "Ingrese un correo electrónico válido.";

      }


      if (
        formulario
          .nombre_usuario
          .trim()
          .length < 3
      ) {

        nuevos.nombre_usuario =
          "El usuario debe tener al menos 3 caracteres.";

      }


      if (
        /\s/.test(
          formulario
            .nombre_usuario,
        )
      ) {

        nuevos.nombre_usuario =
          "El usuario no puede contener espacios.";

      }


      if (
        formulario
          .password
          .length < 8
      ) {

        nuevos.password =
          "La contraseña debe tener al menos 8 caracteres.";

      }


      if (
        formulario.password !==
        formulario
          .confirmar_password
      ) {

        nuevos
          .confirmar_password =
            "Las contraseñas no coinciden.";

      }


      if (
        !formulario
          .matricula_profesional
          ?.trim()
      ) {

        nuevos
          .matricula_profesional =
            "Ingrese la matrícula profesional.";

      }


      const patronTelefono =
        /^[0-9+\-\s()]{7,25}$/;


      if (
        formulario.telefono &&
        !patronTelefono.test(
          formulario.telefono,
        )
      ) {

        nuevos.telefono =
          "Ingrese un teléfono válido.";

      }


      if (
        formulario
          .telefono_institucional &&
        !patronTelefono.test(
          formulario
            .telefono_institucional,
        )
      ) {

        nuevos
          .telefono_institucional =
            "Ingrese un teléfono institucional válido.";

      }


      return nuevos;

    };


  const registrar =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {

      event.preventDefault();


      const erroresLocales =
        validarFormulario();


      if (
        Object.keys(
          erroresLocales,
        ).length > 0
      ) {

        setErrores(
          erroresLocales,
        );

        return;

      }


      try {

        setGuardando(true);

        setErrores({});

        setMensajeExito("");


        const {
          confirmar_password:
            _confirmarPassword,

          ...payload
        } = formulario;


        const response =
          await crearOncologo(
            {

              ...payload,

              nombres:
                payload
                  .nombres
                  .trim(),

              apellido_paterno:
                payload
                  .apellido_paterno
                  .trim(),

              apellido_materno:
                payload
                  .apellido_materno
                  ?.trim()
                || null,

              correo:
                payload
                  .correo
                  .trim()
                  .toLowerCase(),

              nombre_usuario:
                payload
                  .nombre_usuario
                  .trim(),

              telefono:
                payload
                  .telefono
                  ?.trim()
                || null,

              matricula_profesional:
                payload
                  .matricula_profesional
                  ?.trim()
                || null,

              especialidad:
                payload
                  .especialidad
                  ?.trim()
                || null,

              subespecialidad:
                payload
                  .subespecialidad
                  ?.trim()
                || null,

              telefono_institucional:
                payload
                  .telefono_institucional
                  ?.trim()
                || null,

            },
          );


        setMensajeExito(
          response.mensaje,
        );


        window.setTimeout(
          () => {

            navigate(
              "/usuarios",
              {
                replace: true,
              },
            );

          },
          900,
        );

      } catch (error) {

        setErrores(
          normalizarErroresApi(
            error,
          ),
        );

      } finally {

        setGuardando(false);

      }

    };


  return (

    <div className="oncologists-page">


      <button

        type="button"

        className="oncologist-form-back"

        onClick={() =>
          navigate(
            "/usuarios",
          )
        }

      >

        <ArrowLeft
          size={17}
        />

        Volver a oncólogos

      </button>


      <section className="oncologists-header">

        <div>

          <span className="oncologists-header__eyebrow">

            Administración

          </span>

          <h1>
            Registrar oncólogo
          </h1>

          <p>

            Cree una cuenta institucional
            para un nuevo médico oncólogo.

          </p>

        </div>

      </section>


      {mensajeExito && (

        <div className="oncologists-alert oncologists-alert--success">

          <BadgeCheck
            size={18}
          />

          {mensajeExito}

        </div>

      )}


      {errores.general && (

        <div className="oncologists-alert oncologists-alert--error">

          <AlertCircle
            size={18}
          />

          {errores.general}

        </div>

      )}


      <form
        className="oncologist-form-card"
        onSubmit={registrar}
        noValidate
      >


        <div className="oncologist-form-section-title">

          <div>

            <UserRound
              size={19}
            />

          </div>

          <span>

            <strong>
              Datos personales
            </strong>

            <small>

              Información básica de
              identificación.

            </small>

          </span>

        </div>


        <div className="oncologist-form-grid">


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

              placeholder="Ej. Andrea María"

            />

            {errores.nombres && (
              <small>
                {errores.nombres}
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

              placeholder="Ej. López"

            />

            {
              errores
                .apellido_paterno &&
              (
                <small>
                  {
                    errores
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
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "apellido_materno",
                  event.target.value,
                )
              }

              placeholder="Ej. Vargas"

            />

          </label>


          <label>

            <span>
              Teléfono personal
            </span>

            <input

              value={
                formulario.telefono
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "telefono",
                  event.target.value,
                )
              }

              placeholder="Ej. 71234567"

            />

            {errores.telefono && (
              <small>
                {errores.telefono}
              </small>
            )}

          </label>


        </div>


        <div className="oncologist-form-divider" />


        <div className="oncologist-form-section-title">

          <div>

            <Stethoscope
              size={19}
            />

          </div>

          <span>

            <strong>
              Información profesional
            </strong>

            <small>

              Datos institucionales
              del especialista.

            </small>

          </span>

        </div>


        <div className="oncologist-form-grid">


          <label>

            <span>
              Matrícula profesional *
            </span>

            <input

              value={
                formulario
                  .matricula_profesional
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "matricula_profesional",
                  event.target.value,
                )
              }

              placeholder="Ej. MED-5487"

            />

            {
              errores
                .matricula_profesional &&
              (
                <small>
                  {
                    errores
                      .matricula_profesional
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Especialidad
            </span>

            <input

              value={
                formulario
                  .especialidad
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "especialidad",
                  event.target.value,
                )
              }

              placeholder="Oncología"

            />

          </label>


          <label>

            <span>
              Subespecialidad
            </span>

            <input

              value={
                formulario
                  .subespecialidad
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "subespecialidad",
                  event.target.value,
                )
              }

              placeholder="Opcional"

            />

          </label>


          <label>

            <span>
              Teléfono institucional
            </span>

            <input

              value={
                formulario
                  .telefono_institucional
                ?? ""
              }

              onChange={(event) =>
                actualizarCampo(
                  "telefono_institucional",
                  event.target.value,
                )
              }

              placeholder="Ej. 22123456"

            />

            {
              errores
                .telefono_institucional &&
              (
                <small>
                  {
                    errores
                      .telefono_institucional
                  }
                </small>
              )
            }

          </label>


        </div>


        <div className="oncologist-form-divider" />


        <div className="oncologist-form-section-title">

          <div>

            <ShieldCheck
              size={19}
            />

          </div>

          <span>

            <strong>
              Acceso al sistema
            </strong>

            <small>

              Credenciales institucionales
              del nuevo oncólogo.

            </small>

          </span>

        </div>


        <div className="oncologist-form-grid">


          <label>

            <span>
              Correo institucional *
            </span>

            <input

              type="email"

              value={
                formulario.correo
              }

              onChange={(event) =>
                actualizarCampo(
                  "correo",
                  event.target.value,
                )
              }

              placeholder="oncologo@hospital.com"

            />

            {errores.correo && (
              <small>
                {errores.correo}
              </small>
            )}

          </label>


          <label>

            <span>
              Nombre de usuario *
            </span>

            <input

              value={
                formulario
                  .nombre_usuario
              }

              onChange={(event) =>
                actualizarCampo(
                  "nombre_usuario",
                  event.target.value,
                )
              }

              placeholder="Ej. alopez"

            />

            {
              errores
                .nombre_usuario &&
              (
                <small>
                  {
                    errores
                      .nombre_usuario
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Contraseña temporal *
            </span>

            <div className="oncologist-password">

              <input

                type={
                  mostrarPassword
                    ? "text"
                    : "password"
                }

                value={
                  formulario.password
                }

                onChange={(event) =>
                  actualizarCampo(
                    "password",
                    event.target.value,
                  )
                }

                placeholder="Mínimo 8 caracteres"

              />

              <button

                type="button"

                onClick={() =>
                  setMostrarPassword(
                    (actual) =>
                      !actual,
                  )
                }

                aria-label={
                  mostrarPassword
                    ? "Ocultar contraseña"
                    : "Mostrar contraseña"
                }

              >

                {
                  mostrarPassword
                    ? (
                      <EyeOff
                        size={17}
                      />
                    )
                    : (
                      <Eye
                        size={17}
                      />
                    )
                }

              </button>

            </div>

            {errores.password && (
              <small>
                {errores.password}
              </small>
            )}

          </label>


          <label>

            <span>
              Confirmar contraseña *
            </span>

            <input

              type={
                mostrarPassword
                  ? "text"
                  : "password"
              }

              value={
                formulario
                  .confirmar_password
              }

              onChange={(event) =>
                actualizarCampo(
                  "confirmar_password",
                  event.target.value,
                )
              }

              placeholder="Repita la contraseña"

            />

            {
              errores
                .confirmar_password &&
              (
                <small>
                  {
                    errores
                      .confirmar_password
                  }
                </small>
              )
            }

          </label>


        </div>


        <div className="oncologist-form-note">

          <ShieldCheck
            size={18}
          />

          <div>

            <strong>
              Contraseña temporal
            </strong>

            <span>

              La cuenta se registrará como
              oncólogo activo y quedará
              identificada para cambio posterior
              de contraseña.

            </span>

          </div>

        </div>


        <footer className="oncologist-form-footer">


          <button

            type="button"

            className="oncologists-secondary-button"

            onClick={() =>
              navigate(
                "/usuarios",
              )
            }

            disabled={
              guardando
            }

          >

            Cancelar

          </button>


          <button

            type="submit"

            className="oncologists-primary-button"

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
                ? "Registrando..."
                : "Registrar oncólogo"
            }

          </button>


        </footer>


      </form>


    </div>

  );

}