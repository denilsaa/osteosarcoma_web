import {
  AlertCircle,
  ArrowLeft,
  BadgeCheck,
  CheckCircle2,
  Clock3,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  Mail,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  cambiarPasswordRecuperacion,
  consultarEstadoRecuperacion,
  mensajeErrorRecuperacion,
  solicitarRecuperacion,
  type EstadoRecuperacionResponse,
} from "../../api/recuperaciones.api";

import "./RecuperacionPage.css";


const TOKEN_KEY =
  "recovery_demo_token";


type PasoRecuperacion =
  | "SOLICITUD"
  | "ESTADO"
  | "PASSWORD"
  | "FINALIZADA";


export function RecuperacionPage() {

  const navigate =
    useNavigate();


  const [
    paso,
    setPaso,
  ] = useState<
    PasoRecuperacion
  >(
    () =>
      sessionStorage.getItem(
        TOKEN_KEY,
      )
        ? "ESTADO"
        : "SOLICITUD",
  );


  const [
    correo,
    setCorreo,
  ] = useState("");


  const [
    estado,
    setEstado,
  ] = useState<
    EstadoRecuperacionResponse | null
  >(null);


  const [
    nuevaPassword,
    setNuevaPassword,
  ] = useState("");


  const [
    confirmarPassword,
    setConfirmarPassword,
  ] = useState("");


  const [
    mostrarPassword,
    setMostrarPassword,
  ] = useState(false);


  const [
    cargando,
    setCargando,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState("");


  const [
    mensaje,
    setMensaje,
  ] = useState("");


  // ========================================================
  // TOKEN INTERNO DE DEMOSTRACIÓN
  // ========================================================

  const obtenerToken =
    () =>
      sessionStorage.getItem(
        TOKEN_KEY,
      );


  // ========================================================
  // CONSULTAR ESTADO
  // ========================================================

  const consultar =
    async () => {

      const token =
        obtenerToken();


      if (!token) {

        setPaso(
          "SOLICITUD",
        );

        return;
      }


      try {

        setCargando(true);

        setError("");


        const response =
          await consultarEstadoRecuperacion(
            token,
          );


        setEstado(
          response,
        );


        if (
          response.estado ===
          "APROBADA"
          &&
          response
            .puede_cambiar_password
        ) {

          setPaso(
            "PASSWORD",
          );

        } else {

          setPaso(
            "ESTADO",
          );

        }

      } catch (errorActual) {

        setError(
          mensajeErrorRecuperacion(
            errorActual,
          ),
        );

      } finally {

        setCargando(false);
      }

    };


  useEffect(
    () => {

      if (
        paso === "ESTADO"
      ) {

        void consultar();

      }

    // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    [],
  );


  // ========================================================
  // SOLICITAR
  // ========================================================

  const enviarSolicitud =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {

      event.preventDefault();


      if (
        !correo.trim()
      ) {

        setError(
          "Ingrese su correo institucional.",
        );

        return;
      }


      try {

        setCargando(true);

        setError("");

        setMensaje("");


        const response =
          await solicitarRecuperacion(
            correo
              .trim()
              .toLowerCase(),
          );


        setMensaje(
          response.mensaje,
        );


        if (
          response
            .token_recuperacion
        ) {

          sessionStorage.setItem(

            TOKEN_KEY,

            response
              .token_recuperacion,

          );


          setEstado({
            id_solicitud:
              response.id_solicitud ?? "",

            estado:
              "PENDIENTE",

            puede_cambiar_password:
              false,

            mensaje:
              response.mensaje,

            fecha_expiracion:
              response.fecha_expiracion,
          });


          setPaso(
            "ESTADO",
          );

        }

      } catch (errorActual) {

        setError(
          mensajeErrorRecuperacion(
            errorActual,
          ),
        );

      } finally {

        setCargando(false);
      }

    };


  // ========================================================
  // CAMBIAR PASSWORD
  // ========================================================

  const cambiarPassword =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {

      event.preventDefault();


      setError("");


      if (
        nuevaPassword.length < 8
      ) {

        setError(
          "La contraseña debe tener al menos 8 caracteres.",
        );

        return;
      }


      if (
        !/[A-Za-z]/.test(
          nuevaPassword,
        )
      ) {

        setError(
          "La contraseña debe contener al menos una letra.",
        );

        return;
      }


      if (
        !/[0-9]/.test(
          nuevaPassword,
        )
      ) {

        setError(
          "La contraseña debe contener al menos un número.",
        );

        return;
      }


      if (
        nuevaPassword !==
        confirmarPassword
      ) {

        setError(
          "Las contraseñas no coinciden.",
        );

        return;
      }


      const token =
        obtenerToken();


      if (!token) {

        setError(
          "La solicitud de recuperación ya no está disponible.",
        );

        return;
      }


      try {

        setCargando(true);


        const response =
          await cambiarPasswordRecuperacion(
            {
              token,

              nueva_password:
                nuevaPassword,

              confirmar_password:
                confirmarPassword,
            },
          );


        sessionStorage.removeItem(
          TOKEN_KEY,
        );


        setMensaje(
          response.mensaje,
        );


        setPaso(
          "FINALIZADA",
        );

      } catch (errorActual) {

        setError(
          mensajeErrorRecuperacion(
            errorActual,
          ),
        );

      } finally {

        setCargando(false);
      }

    };


  // ========================================================
  // CANCELAR SOLICITUD LOCAL
  // ========================================================

  const comenzarOtra =
    () => {

      sessionStorage.removeItem(
        TOKEN_KEY,
      );

      setCorreo("");

      setEstado(null);

      setNuevaPassword("");

      setConfirmarPassword("");

      setError("");

      setMensaje("");

      setPaso(
        "SOLICITUD",
      );

    };


  // ========================================================
  // ICONO SEGÚN ESTADO
  // ========================================================

  const estadoVisual =
    estado?.estado === "APROBADA"
      ? {
          clase: "approved",
          icono:
            <CheckCircle2
              size={28}
            />,
          titulo:
            "Solicitud aprobada",
        }
      : estado?.estado ===
        "RECHAZADA"
        ? {
            clase: "rejected",
            icono:
              <AlertCircle
                size={28}
              />,
            titulo:
              "Solicitud rechazada",
          }
        : estado?.estado ===
          "EXPIRADA"
          ? {
              clase: "expired",
              icono:
                <AlertCircle
                  size={28}
                />,
              titulo:
                "Solicitud expirada",
            }
          : {
              clase: "pending",
              icono:
                <Clock3
                  size={28}
                />,
              titulo:
                "Pendiente de aprobación",
            };


  return (

    <div className="recovery-page">


      <div className="recovery-background recovery-background--one" />

      <div className="recovery-background recovery-background--two" />


      <section className="recovery-card">


        <button

          type="button"

          className="recovery-back"

          onClick={() =>
            navigate(
              "/login",
            )
          }

        >

          <ArrowLeft
            size={17}
          />

          Volver al inicio de sesión

        </button>


        <div className="recovery-brand">

          <div className="recovery-brand__icon">

            <ShieldCheck
              size={28}
            />

          </div>

          <div>

            <strong>
              Recuperación de acceso
            </strong>

            <span>
              Clínica San Juan de Dios
            </span>

          </div>

        </div>


        {/* ==================================================
            PASO 1
            ================================================== */}

        {paso === "SOLICITUD" && (

          <form
            onSubmit={
              enviarSolicitud
            }
            className="recovery-content"
            noValidate
          >

            <div className="recovery-heading">

              <h1>
                ¿Olvidó su contraseña?
              </h1>

              <p>

                Ingrese su correo institucional.
                La solicitud deberá ser revisada
                por Jefatura de Oncología antes
                de permitir un cambio de contraseña.

              </p>

            </div>


            {error && (

              <div className="recovery-alert recovery-alert--error">

                <AlertCircle
                  size={18}
                />

                {error}

              </div>

            )}


            {mensaje && (

              <div className="recovery-alert recovery-alert--info">

                <BadgeCheck
                  size={18}
                />

                {mensaje}

              </div>

            )}


            <label className="recovery-field">

              <span>
                Correo institucional
              </span>

              <div>

                <Mail
                  size={18}
                />

                <input

                  type="email"

                  value={correo}

                  onChange={(event) =>
                    setCorreo(
                      event.target.value,
                    )
                  }

                  placeholder="nombre@hospital.com"

                  autoFocus

                />

              </div>

            </label>


            <button

              type="submit"

              className="recovery-primary-button"

              disabled={
                cargando
              }

            >

              {cargando ? (

                <LoaderCircle
                  size={18}
                  className="recovery-spin"
                />

              ) : (

                <KeyRound
                  size={18}
                />

              )}

              {cargando
                ? "Enviando solicitud..."
                : "Solicitar recuperación"}

            </button>

          </form>

        )}


        {/* ==================================================
            ESTADO
            ================================================== */}

        {paso === "ESTADO" && (

          <div className="recovery-content">


            <div
              className={`
                recovery-status
                recovery-status--${estadoVisual.clase}
              `}
            >

              <div className="recovery-status__icon">

                {estadoVisual.icono}

              </div>


              <h1>
                {estadoVisual.titulo}
              </h1>


              <p>

                {estado?.mensaje ??
                  "Consultando estado de recuperación..."}

              </p>

            </div>


            {error && (

              <div className="recovery-alert recovery-alert--error">

                <AlertCircle
                  size={18}
                />

                {error}

              </div>

            )}


            <div className="recovery-process">

              <div className="recovery-process__step recovery-process__step--done">

                <span>
                  1
                </span>

                <div>

                  <strong>
                    Solicitud registrada
                  </strong>

                  <small>
                    La petición fue recibida.
                  </small>

                </div>

              </div>


              <div
                className={`
                  recovery-process__step
                  ${
                    estado?.estado ===
                    "PENDIENTE"

                      ? "recovery-process__step--current"

                      : estado?.estado ===
                        "APROBADA"

                        ? "recovery-process__step--done"

                        : ""
                  }
                `}
              >

                <span>
                  2
                </span>

                <div>

                  <strong>
                    Revisión de Jefatura
                  </strong>

                  <small>

                    El Jefe de Oncología
                    aprueba o rechaza.

                  </small>

                </div>

              </div>


              <div
                className={`
                  recovery-process__step
                  ${
                    estado?.estado ===
                    "APROBADA"

                      ? "recovery-process__step--current"

                      : ""
                  }
                `}
              >

                <span>
                  3
                </span>

                <div>

                  <strong>
                    Nueva contraseña
                  </strong>

                  <small>
                    Disponible solo después de aprobarse.
                  </small>

                </div>

              </div>

            </div>


            <button

              type="button"

              className="recovery-primary-button"

              onClick={() =>
                void consultar()
              }

              disabled={
                cargando
              }

            >

              {cargando ? (

                <LoaderCircle
                  size={18}
                  className="recovery-spin"
                />

              ) : (

                <RefreshCw
                  size={18}
                />

              )}

              Consultar estado

            </button>


            {(
              estado?.estado ===
                "RECHAZADA"
              ||
              estado?.estado ===
                "EXPIRADA"
            ) && (

              <button

                type="button"

                className="recovery-secondary-button"

                onClick={
                  comenzarOtra
                }

              >

                Crear nueva solicitud

              </button>

            )}

          </div>

        )}


        {/* ==================================================
            NUEVA CONTRASEÑA
            ================================================== */}

        {paso === "PASSWORD" && (

          <form
            onSubmit={
              cambiarPassword
            }
            className="recovery-content"
            noValidate
          >

            <div className="recovery-approved-heading">

              <div>

                <CheckCircle2
                  size={30}
                />

              </div>

              <h1>
                Solicitud aprobada
              </h1>

              <p>

                Jefatura autorizó la recuperación.
                Ahora puede establecer su nueva
                contraseña.

              </p>

            </div>


            {error && (

              <div className="recovery-alert recovery-alert--error">

                <AlertCircle
                  size={18}
                />

                {error}

              </div>

            )}


            <label className="recovery-field">

              <span>
                Nueva contraseña
              </span>

              <div>

                <KeyRound
                  size={18}
                />

                <input

                  type={
                    mostrarPassword
                      ? "text"
                      : "password"
                  }

                  value={
                    nuevaPassword
                  }

                  onChange={(event) =>
                    setNuevaPassword(
                      event.target.value,
                    )
                  }

                  placeholder="Mínimo 8 caracteres"

                />

                <button

                  type="button"

                  className="recovery-password-toggle"

                  onClick={() =>
                    setMostrarPassword(
                      (actual) =>
                        !actual,
                    )
                  }

                >

                  {mostrarPassword
                    ? <EyeOff size={17} />
                    : <Eye size={17} />}

                </button>

              </div>

            </label>


            <label className="recovery-field">

              <span>
                Confirmar contraseña
              </span>

              <div>

                <KeyRound
                  size={18}
                />

                <input

                  type={
                    mostrarPassword
                      ? "text"
                      : "password"
                  }

                  value={
                    confirmarPassword
                  }

                  onChange={(event) =>
                    setConfirmarPassword(
                      event.target.value,
                    )
                  }

                  placeholder="Repita la contraseña"

                />

              </div>

            </label>


            <div className="recovery-password-rules">

              <ShieldCheck
                size={18}
              />

              <span>

                Use al menos 8 caracteres,
                una letra y un número.

              </span>

            </div>


            <button

              type="submit"

              className="recovery-primary-button"

              disabled={
                cargando
              }

            >

              {cargando
                ? (
                  <LoaderCircle
                    size={18}
                    className="recovery-spin"
                  />
                )
                : (
                  <KeyRound
                    size={18}
                  />
                )}

              {cargando
                ? "Actualizando..."
                : "Cambiar contraseña"}

            </button>

          </form>

        )}


        {/* ==================================================
            FINALIZADA
            ================================================== */}

        {paso === "FINALIZADA" && (

          <div className="recovery-content">

            <div className="recovery-finished">

              <div>

                <CheckCircle2
                  size={34}
                />

              </div>

              <h1>
                Contraseña actualizada
              </h1>

              <p>

                {mensaje ||
                  "La contraseña fue actualizada correctamente."}

              </p>

            </div>


            <button

              type="button"

              className="recovery-primary-button"

              onClick={() =>
                navigate(
                  "/login",
                  {
                    replace: true,
                  },
                )
              }

            >

              Ir al inicio de sesión

            </button>

          </div>

        )}


      </section>

    </div>

  );
}