import {
  AlertCircle,
  ArrowLeft,
  CheckCircle2,
  Eye,
  EyeOff,
  KeyRound,
  LoaderCircle,
  ShieldCheck,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import {
  cambiarPasswordRecuperacion,
  consultarEstadoRecuperacion,
  mensajeErrorRecuperacion,
} from "../../api/recuperaciones.api";

import "./RecuperacionPage.css";


type EstadoPantalla =
  | "VALIDANDO"
  | "LISTA"
  | "ERROR"
  | "FINALIZADA";


export function CambiarPasswordRecuperacionPage() {
  const navigate =
    useNavigate();

  const [searchParams] =
    useSearchParams();

  const token =
    searchParams.get("token")?.trim() ?? "";

  const [
    estadoPantalla,
    setEstadoPantalla,
  ] = useState<EstadoPantalla>(
    "VALIDANDO",
  );

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
    mostrarConfirmacion,
    setMostrarConfirmacion,
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
    mensajeFinal,
    setMensajeFinal,
  ] = useState("");


  const reglas =
    useMemo(
      () => ({
        longitud:
          nuevaPassword.length >= 8 &&
          nuevaPassword.length <= 64,

        mayuscula:
          /[A-Z]/.test(
            nuevaPassword,
          ),

        minuscula:
          /[a-z]/.test(
            nuevaPassword,
          ),

        numero:
          /[0-9]/.test(
            nuevaPassword,
          ),

        especial:
          /[^A-Za-z0-9]/.test(
            nuevaPassword,
          ),

        sinEspacios:
          !/\s/.test(
            nuevaPassword,
          ),
      }),
      [nuevaPassword],
    );


  const passwordValida =
    Object.values(
      reglas,
    ).every(Boolean);


  useEffect(
    () => {
      let activo = true;

      const validar =
        async () => {
          if (!token) {
            if (activo) {
              setError(
                "El enlace de recuperación está incompleto.",
              );

              setEstadoPantalla(
                "ERROR",
              );
            }

            return;
          }

          try {
            const response =
              await consultarEstadoRecuperacion(
                token,
              );

            if (!activo) {
              return;
            }

            if (
              response.estado === "APROBADA" &&
              response.puede_cambiar_password
            ) {
              setEstadoPantalla(
                "LISTA",
              );

              return;
            }

            setError(
              response.mensaje,
            );

            setEstadoPantalla(
              "ERROR",
            );
          } catch (errorActual) {
            if (!activo) {
              return;
            }

            setError(
              mensajeErrorRecuperacion(
                errorActual,
              ),
            );

            setEstadoPantalla(
              "ERROR",
            );
          }
        };

      void validar();

      return () => {
        activo = false;
      };
    },
    [token],
  );


  const cambiarPassword =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {
      event.preventDefault();

      setError("");

      if (!passwordValida) {
        setError(
          "La nueva contraseña todavía no cumple todos los requisitos de seguridad.",
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

        setMensajeFinal(
          response.mensaje,
        );

        setEstadoPantalla(
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
              Nueva contraseña
            </strong>

            <span>
              Clínica San Juan de Dios
            </span>
          </div>
        </header>

        {estadoPantalla ===
          "VALIDANDO" && (
          <div className="recovery-content">
            <section className="recovery-status recovery-status--pending">
              <div className="recovery-status__icon">
                <LoaderCircle
                  size={29}
                  className="recovery-spin"
                />
              </div>

              <h1>
                Validando enlace
              </h1>

              <p>
                Estamos comprobando que el enlace sea válido,
                esté aprobado y no haya expirado.
              </p>
            </section>
          </div>
        )}

        {estadoPantalla ===
          "ERROR" && (
          <div className="recovery-content">
            <section className="recovery-status recovery-status--expired">
              <div className="recovery-status__icon">
                <AlertCircle
                  size={29}
                />
              </div>

              <h1>
                Enlace no disponible
              </h1>

              <p>
                {error}
              </p>
            </section>

            <button
              type="button"
              className="recovery-primary-button"
              onClick={() =>
                navigate(
                  "/recuperar-contrasena",
                )
              }
            >
              Solicitar una nueva recuperación
            </button>
          </div>
        )}

        {estadoPantalla ===
          "LISTA" && (
          <form
            className="recovery-content"
            onSubmit={
              cambiarPassword
            }
          >
            <div className="recovery-approved-heading">
              <div>
                <CheckCircle2
                  size={29}
                />
              </div>

              <h1>
                Recuperación autorizada
              </h1>

              <p>
                El enlace fue validado correctamente.
                Establezca una contraseña nueva y segura.
              </p>
            </div>

            <label className="recovery-field">
              Nueva contraseña

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
                  value={nuevaPassword}
                  onChange={(event) =>
                    setNuevaPassword(
                      event.target.value,
                    )
                  }
                  autoComplete="new-password"
                  maxLength={64}
                  required
                />

                <button
                  type="button"
                  className="recovery-password-toggle"
                  onClick={() =>
                    setMostrarPassword(
                      (valor) =>
                        !valor,
                    )
                  }
                  aria-label="Mostrar u ocultar contraseña"
                >
                  {mostrarPassword ? (
                    <EyeOff
                      size={17}
                    />
                  ) : (
                    <Eye
                      size={17}
                    />
                  )}
                </button>
              </div>
            </label>

            <div className="recovery-password-rules">
              <ShieldCheck
                size={17}
              />

              <span>
                8–64 caracteres · mayúscula · minúscula · número ·
                carácter especial · sin espacios
              </span>
            </div>

            <label className="recovery-field">
              Confirmar contraseña

              <div>
                <KeyRound
                  size={18}
                />

                <input
                  type={
                    mostrarConfirmacion
                      ? "text"
                      : "password"
                  }
                  value={confirmarPassword}
                  onChange={(event) =>
                    setConfirmarPassword(
                      event.target.value,
                    )
                  }
                  autoComplete="new-password"
                  maxLength={64}
                  required
                />

                <button
                  type="button"
                  className="recovery-password-toggle"
                  onClick={() =>
                    setMostrarConfirmacion(
                      (valor) =>
                        !valor,
                    )
                  }
                  aria-label="Mostrar u ocultar confirmación"
                >
                  {mostrarConfirmacion ? (
                    <EyeOff
                      size={17}
                    />
                  ) : (
                    <Eye
                      size={17}
                    />
                  )}
                </button>
              </div>
            </label>

            {error && (
              <div className="recovery-alert recovery-alert--error">
                <AlertCircle
                  size={17}
                />

                {error}
              </div>
            )}

            <button
              type="submit"
              className="recovery-primary-button"
              disabled={
                cargando ||
                !passwordValida ||
                nuevaPassword !==
                  confirmarPassword
              }
            >
              {cargando ? (
                <LoaderCircle
                  size={18}
                  className="recovery-spin"
                />
              ) : (
                <ShieldCheck
                  size={18}
                />
              )}

              {cargando
                ? "Actualizando contraseña..."
                : "Guardar nueva contraseña"}
            </button>
          </form>
        )}

        {estadoPantalla ===
          "FINALIZADA" && (
          <div className="recovery-content">
            <section className="recovery-finished">
              <div>
                <CheckCircle2
                  size={30}
                />
              </div>

              <h1>
                Contraseña actualizada
              </h1>

              <p>
                {mensajeFinal}
              </p>
            </section>

            <button
              type="button"
              className="recovery-primary-button"
              onClick={() =>
                navigate(
                  "/login",
                )
              }
            >
              Ir al inicio de sesión
            </button>
          </div>
        )}
      </section>
    </main>
  );
}
