import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  HeartPulse,
  LoaderCircle,
  LockKeyhole,
  Mail,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./Auth.css";


interface LocationState {
  from?: string;
}


export function LoginPage() {
  const navigate =
    useNavigate();

  const location =
    useLocation();

  const {
    login,
    autenticado,
  } = useAuth();

  const [
    correo,
    setCorreo,
  ] = useState("");

  const [
    password,
    setPassword,
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


  if (autenticado) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }


  const iniciarSesion =
    async (
      event: React.FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault();

      setError("");

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

      const formatoCorreo =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

      if (
        !formatoCorreo.test(
          correoNormalizado,
        )
      ) {
        setError(
          "Ingrese un correo institucional válido.",
        );

        return;
      }

      if (!password) {
        setError(
          "Ingrese su contraseña.",
        );

        return;
      }

      try {
        setCargando(true);

        await login(
          correoNormalizado,
          password,
        );

        const state =
          location.state as
            | LocationState
            | null;

        navigate(
          state?.from
          || "/dashboard",
          {
            replace: true,
          },
        );
      } catch (errorActual) {
        console.error(
          errorActual,
        );

        setError(
          "Correo o contraseña incorrectos. Verifique sus datos e inténtelo nuevamente.",
        );
      } finally {
        setCargando(false);
      }
    };


  return (
    <main className="login-page">
      {/* =====================================================
          PANEL VISUAL - DISEÑO DEL LOGIN ANTERIOR
          ===================================================== */}
      <section className="login-visual">
        <div className="login-visual__background">
          <img
            src="/branding/radiografia-login.png"
            alt=""
            aria-hidden="true"
          />
        </div>

        <div className="login-visual__overlay" />
        <div className="login-visual__grid" />

        <div className="login-visual__glow login-visual__glow--one" />
        <div className="login-visual__glow login-visual__glow--two" />

        <div className="login-visual__content">
          <div className="login-visual__copy">
            <h1>
              Tecnología al
              <br />
              servicio del
              <span>
                cuidado
                <br />
                oncológico.
              </span>
            </h1>

            <p>
              Gestión clínica, radiografías y herramientas de apoyo
              mediante inteligencia artificial en un solo entorno
              diseñado para el especialista.
            </p>
          </div>
        </div>
      </section>

      {/* =====================================================
          PANEL DE ACCESO - FUNCIONALIDAD ACTUAL
          ===================================================== */}
      <section className="login-access">
        <div className="login-access__glow login-access__glow--top" />
        <div className="login-access__glow login-access__glow--bottom" />

        <div className="login-card">
          <div className="login-card__logo">
            <img
              src="/branding/logo-san-juan.png"
              alt="Clínica San Juan de Dios"
            />
          </div>

          <div className="login-card__heading">
            <div className="login-card__tag">
              <HeartPulse
                size={14}
              />

              <span>
                Portal clínico
              </span>
            </div>

            <h2>
              Bienvenido
            </h2>

            <p>
              Ingrese sus credenciales institucionales para acceder al sistema.
            </p>
          </div>

          {error && (
            <div
              className="login-form__error"
              role="alert"
            >
              <AlertCircle
                size={17}
              />

              <span>
                {error}
              </span>
            </div>
          )}

          <form
            className="login-form"
            onSubmit={
              iniciarSesion
            }
            noValidate
          >
            <label className="login-form__field">
              <span className="login-form__label">
                Correo institucional
              </span>

              <div className="login-form__control">
                <Mail
                  size={18}
                />

                <input
                  type="email"
                  value={correo}
                  onChange={(event) => {
                    setCorreo(
                      event.target.value,
                    );

                    setError("");
                  }}
                  placeholder="nombre@hospital.com"
                  autoComplete="email"
                  autoFocus
                  disabled={cargando}
                />
              </div>
            </label>

            <label className="login-form__field">
              <span className="login-form__label">
                Contraseña
              </span>

              <div className="login-form__control">
                <LockKeyhole
                  size={18}
                />

                <input
                  type={
                    mostrarPassword
                      ? "text"
                      : "password"
                  }
                  value={password}
                  onChange={(event) => {
                    setPassword(
                      event.target.value,
                    );

                    setError("");
                  }}
                  placeholder="Ingrese su contraseña"
                  autoComplete="current-password"
                  disabled={cargando}
                />

                <button
                  type="button"
                  className="login-form__password-toggle"
                  onClick={() =>
                    setMostrarPassword(
                      (valor) => !valor,
                    )
                  }
                  aria-label={
                    mostrarPassword
                      ? "Ocultar contraseña"
                      : "Mostrar contraseña"
                  }
                  disabled={cargando}
                >
                  {mostrarPassword
                    ? (
                      <EyeOff
                        size={18}
                      />
                    )
                    : (
                      <Eye
                        size={18}
                      />
                    )}
                </button>
              </div>
            </label>

            <div className="login-form__options login-form__options--end">
              <Link to="/recuperar-contrasena">
                ¿Olvidó su contraseña?
              </Link>
            </div>

            <button
              type="submit"
              className="login-form__submit"
              disabled={cargando}
            >
              <span
                className="login-form__submit-icon"
                aria-hidden="true"
              >
                {cargando
                  ? (
                    <LoaderCircle
                      size={18}
                      className="login-form__spinner"
                    />
                  )
                  : (
                    <ArrowRight
                      size={18}
                    />
                  )}
              </span>

              <span>
                {cargando
                  ? "Verificando..."
                  : "Ingresar al sistema"}
              </span>
            </button>
          </form>

          <div className="login-card__security">
            <div className="login-card__security-icon">
              <CheckCircle2
                size={15}
              />
            </div>

            <div>
              <strong>
                Acceso protegido
              </strong>

              <span>
                Exclusivo para personal autorizado de la clínica.
              </span>
            </div>
          </div>
        </div>

        <footer className="login-access__footer">
          <span>
            Clínica San Juan de Dios
          </span>

          <span className="login-access__footer-dot" />

          <span>
            Sistema de apoyo clínico
          </span>
        </footer>
      </section>
    </main>
  );
}
