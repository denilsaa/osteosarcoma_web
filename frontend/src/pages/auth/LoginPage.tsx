import {
  AlertCircle,
  ArrowRight,
  Eye,
  EyeOff,
  HeartPulse,
  LoaderCircle,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Stethoscope,
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


  if (
    autenticado
  ) {

    return (

      <Navigate
        to="/dashboard"
        replace
      />

    );
  }


  const iniciarSesion =
    async (
      event:
        React.FormEvent<
          HTMLFormElement
        >,
    ) => {

      event.preventDefault();

      setError("");


      if (
        !correo.trim()
      ) {

        setError(
          "Ingrese su correo institucional.",
        );

        return;
      }


      if (
        !password
      ) {

        setError(
          "Ingrese su contraseña.",
        );

        return;
      }


      try {

        setCargando(
          true,
        );


        await login(
          correo
            .trim()
            .toLowerCase(),

          password,
        );


        const state =
          location.state as
            | LocationState
            | null;


        navigate(
          state?.from
          ||
          "/dashboard",
          {
            replace: true,
          },
        );

      } catch (errorActual) {

        console.error(
          errorActual,
        );

        setError(
          "Correo o contraseña incorrectos. "
          +
          "Verifique sus datos e inténtelo nuevamente.",
        );

      } finally {

        setCargando(
          false,
        );
      }
    };


  return (

    <div className="login-page">


      <section className="login-visual">

        <div className="login-visual__overlay" />

        <div className="login-visual__content">


          <div className="login-visual__brand">

            <div className="login-visual__brand-icon">

              <HeartPulse
                size={28}
              />

            </div>


            <div>

              <strong>
                OSTEOSARCOMA
              </strong>

              <span>
                SAN JUAN DE DIOS
              </span>

            </div>

          </div>


          <div className="login-visual__message">

            <div className="login-visual__medical-icon">

              <Stethoscope
                size={34}
              />

            </div>


            <span>
              Plataforma clínica
            </span>


            <h1>

              Apoyo inteligente para
              la atención oncológica.

            </h1>


            <p>

              Gestión clínica segura y
              herramientas de apoyo para
              el personal médico de la
              Clínica San Juan de Dios.

            </p>

          </div>


          <div className="login-visual__security">

            <ShieldCheck
              size={18}
            />

            <span>

              Acceso restringido al
              personal autorizado.

            </span>

          </div>


        </div>

      </section>


      <section className="login-panel">


        <div className="login-card">


          <div className="login-card__mobile-brand">

            <div>

              <HeartPulse
                size={23}
              />

            </div>


            <span>

              <strong>
                OSTEOSARCOMA
              </strong>

              <small>
                SAN JUAN DE DIOS
              </small>

            </span>

          </div>


          <div className="login-card__heading">

            <span>
              ACCESO INSTITUCIONAL
            </span>

            <h2>
              Iniciar sesión
            </h2>

            <p>

              Ingrese sus credenciales
              institucionales para acceder
              al sistema.

            </p>

          </div>


          {error && (

            <div
              className="login-error"
              role="alert"
            >

              <AlertCircle
                size={18}
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


            <label className="login-field">

              <span>
                Correo institucional
              </span>

              <div className="login-field__control">

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
                />

              </div>

            </label>


            <label className="login-field">

              <span>
                Contraseña
              </span>

              <div className="login-field__control">

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
                />


                <button
                  type="button"
                  className="login-password-toggle"
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


            <div className="login-recovery-link">

              <Link
                to="/recuperar-contrasena"
              >

                ¿Olvidó su contraseña?

              </Link>

            </div>


            <button
              type="submit"
              className="login-submit"
              disabled={
                cargando
              }
            >

              {cargando
                ? (
                  <LoaderCircle
                    size={19}
                    className="login-spinner"
                  />
                )
                : (
                  <ArrowRight
                    size={19}
                  />
                )}


              <span>

                {cargando
                  ? "Verificando..."
                  : "Ingresar"}

              </span>

            </button>


          </form>


          <div className="login-card__footer">

            <ShieldCheck
              size={15}
            />

            <span>

              Sus credenciales se procesan
              mediante una conexión segura.

            </span>

          </div>


        </div>

      </section>


    </div>

  );
}