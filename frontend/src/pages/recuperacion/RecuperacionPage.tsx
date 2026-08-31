import {
  ArrowLeft,
  CheckCircle2,
  LoaderCircle,
  Mail,
  ShieldCheck,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  mensajeErrorRecuperacion,
  solicitarRecuperacion,
} from "../../api/recuperaciones.api";

import "./RecuperacionPage.css";


function enmascararCorreo(
  correo: string,
): string {
  const [local, dominio] =
    correo.split("@");

  if (
    !local ||
    !dominio
  ) {
    return correo;
  }

  const visible =
    local.slice(0, 1);

  const ocultos =
    "•".repeat(
      Math.max(
        4,
        local.length - 1,
      ),
    );

  return `${visible}${ocultos}@${dominio}`;
}


export function RecuperacionPage() {
  const navigate =
    useNavigate();

  const [
    correo,
    setCorreo,
  ] = useState("");

  const [
    correoSolicitado,
    setCorreoSolicitado,
  ] = useState("");

  const [
    enviada,
    setEnviada,
  ] = useState(false);

  const [
    cargando,
    setCargando,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");


  const enviarSolicitud =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {
      event.preventDefault();

      const correoNormalizado =
        correo
          .trim()
          .toLowerCase();

      if (!correoNormalizado) {
        setError(
          "Ingrese su correo institucional.",
        );

        return;
      }

      try {
        setCargando(true);
        setError("");

        await solicitarRecuperacion(
          correoNormalizado,
        );

        setCorreoSolicitado(
          correoNormalizado,
        );

        setEnviada(true);
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


  return (
    <main className="recovery-page">
      <div
        className="recovery-background recovery-background--one"
        aria-hidden="true"
      />

      <div
        className="recovery-background recovery-background--two"
        aria-hidden="true"
      />

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

        <header className="recovery-brand">
          <div className="recovery-brand__icon">
            <ShieldCheck
              size={25}
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
        </header>

        {!enviada ? (
          <form
            className="recovery-content"
            onSubmit={
              enviarSolicitud
            }
          >
            <div className="recovery-heading">
              <h1>
                ¿Olvidó su contraseña?
              </h1>

              <p>
                Ingrese el correo institucional asociado a su cuenta.
                Jefatura de Oncología revisará la solicitud y, si es
                aprobada, recibirá un enlace seguro para establecer
                una nueva contraseña.
              </p>
            </div>

            <label className="recovery-field">
              Correo institucional

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
                  placeholder="medico@hospital.com"
                  autoComplete="email"
                  maxLength={150}
                  required
                />
              </div>
            </label>

            {error && (
              <div className="recovery-alert recovery-alert--error">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="recovery-primary-button"
              disabled={cargando}
            >
              {cargando ? (
                <LoaderCircle
                  size={18}
                  className="recovery-spin"
                />
              ) : (
                <Mail
                  size={18}
                />
              )}

              {cargando
                ? "Enviando solicitud..."
                : "Solicitar recuperación"}
            </button>
          </form>
        ) : (
          <div className="recovery-content">
            <section className="recovery-status recovery-status--approved">
              <div className="recovery-status__icon">
                <CheckCircle2
                  size={29}
                />
              </div>

              <h1>
                Solicitud recibida
              </h1>

              <p>
                La solicitud fue enviada a Jefatura de Oncología.
                Puede cerrar esta página; no necesita permanecer aquí
                esperando la aprobación.
              </p>
            </section>

            <div className="recovery-process">
              <div className="recovery-process__step recovery-process__step--done">
                <span>1</span>

                <div>
                  <strong>
                    Solicitud registrada
                  </strong>

                  <small>
                    La petición fue recibida por el sistema.
                  </small>
                </div>
              </div>

              <div className="recovery-process__step recovery-process__step--current">
                <span>2</span>

                <div>
                  <strong>
                    Revisión de Jefatura
                  </strong>

                  <small>
                    El Jefe de Oncología aprobará o rechazará la solicitud.
                  </small>
                </div>
              </div>

              <div className="recovery-process__step">
                <span>3</span>

                <div>
                  <strong>
                    Enlace seguro por correo
                  </strong>

                  <small>
                    Si se aprueba, llegará un enlace temporal al correo registrado.
                  </small>
                </div>
              </div>
            </div>

            <div className="recovery-alert recovery-alert--info">
              <Mail
                size={17}
              />

              <span>
                Por seguridad, el sistema no confirma públicamente la
                existencia de una cuenta. Si corresponde a una cuenta activa,
                el enlace llegará a:
                {" "}
                <strong>
                  {enmascararCorreo(
                    correoSolicitado,
                  )}
                </strong>
              </span>
            </div>

            <button
              type="button"
              className="recovery-primary-button"
              onClick={() =>
                navigate(
                  "/login",
                )
              }
            >
              Volver al inicio de sesión
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
