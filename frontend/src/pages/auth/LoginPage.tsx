import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  HeartPulse,
  LockKeyhole,
  Mail,
} from "lucide-react";

import {
  useState,
  type FormEvent,
} from "react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./Auth.css";


export function LoginPage() {

  const navigate = useNavigate();

  const {
    login,
  } = useAuth();


  // ==========================================================
  // ESTADOS
  // ==========================================================

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
    recordarSesion,
    setRecordarSesion,
  ] = useState(false);

  const [
    cargando,
    setCargando,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");


  // ==========================================================
  // LOGIN
  // ==========================================================

  const iniciarSesion = async (
    event: FormEvent<HTMLFormElement>,
  ) => {

    event.preventDefault();

    setError("");


    // --------------------------------------------------------
    // VALIDACIÓN CORREO
    // --------------------------------------------------------

    if (!correo.trim()) {

      setError(
        "Ingrese su correo electrónico.",
      );

      return;
    }


    // --------------------------------------------------------
    // VALIDACIÓN PASSWORD
    // --------------------------------------------------------

    if (!password) {

      setError(
        "Ingrese su contraseña.",
      );

      return;
    }


    try {

      setCargando(true);


      // ------------------------------------------------------
      // LLAMADA REAL AL BACKEND
      // ------------------------------------------------------

      await login(
        correo.trim(),
        password,
      );


      // ------------------------------------------------------
      // LOGIN CORRECTO
      // ------------------------------------------------------

      navigate(
        "/dashboard",
        {
          replace: true,
        },
      );


    } catch (error: any) {

      console.error(
        "Error al iniciar sesión:",
        error,
      );


      // ------------------------------------------------------
      // MENSAJE DEL BACKEND
      // ------------------------------------------------------

      const mensaje =
        error?.response?.data?.error ||
        error?.response?.data?.detail ||
        "Correo o contraseña incorrectos.";


      setError(
        mensaje,
      );


    } finally {

      setCargando(false);

    }
  };


  // ==========================================================
  // INTERFAZ
  // ==========================================================

  return (

    <main className="login-page">


      {/* =====================================================
          PANEL VISUAL
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


        <div
          className="
            login-visual__glow
            login-visual__glow--one
          "
        />


        <div
          className="
            login-visual__glow
            login-visual__glow--two
          "
        />


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

              Gestión clínica, radiografías y herramientas
              de apoyo mediante inteligencia artificial en un
              solo entorno diseñado para el especialista.

            </p>

          </div>

        </div>

      </section>



      {/* =====================================================
          PANEL DE ACCESO
          ===================================================== */}

      <section className="login-access">


        <div
          className="
            login-access__glow
            login-access__glow--top
          "
        />


        <div
          className="
            login-access__glow
            login-access__glow--bottom
          "
        />


        <div className="login-card">


          {/* =================================================
              LOGO
              ================================================= */}

          <div className="login-card__logo">

            <img
              src="/branding/logo-san-juan.png"
              alt="Clínica San Juan de Dios"
            />

          </div>



          {/* =================================================
              ENCABEZADO
              ================================================= */}

          <div className="login-card__heading">


            <div className="login-card__tag">

              <HeartPulse size={14} />

              <span>
                Portal clínico
              </span>

            </div>


            <h2>
              Bienvenido
            </h2>


            <p>

              Ingrese sus credenciales institucionales
              para acceder al sistema.

            </p>

          </div>



          {/* =================================================
              FORMULARIO
              ================================================= */}

          <form
            className="login-form"
            onSubmit={iniciarSesion}
          >


            {/* =================================================
                CORREO
                ================================================= */}

            <label className="login-form__field">

              <span className="login-form__label">

                Correo o usuario

              </span>


              <div className="login-form__control">

                <Mail size={18} />


                <input
                  type="text"
                  placeholder="usuario@clinica.com"
                  autoComplete="username"

                  value={correo}

                  onChange={(event) => {

                    setCorreo(
                      event.target.value,
                    );

                    if (error) {
                      setError("");
                    }

                  }}

                  disabled={cargando}
                />

              </div>

            </label>



            {/* =================================================
                CONTRASEÑA
                ================================================= */}

            <label className="login-form__field">

              <span className="login-form__label">

                Contraseña

              </span>


              <div className="login-form__control">

                <LockKeyhole size={18} />


                <input

                  type={
                    mostrarPassword
                      ? "text"
                      : "password"
                  }

                  placeholder="Ingrese su contraseña"

                  autoComplete="current-password"

                  value={password}

                  onChange={(event) => {

                    setPassword(
                      event.target.value,
                    );

                    if (error) {
                      setError("");
                    }

                  }}

                  disabled={cargando}

                />


                <button

                  type="button"

                  className="
                    login-form__password-toggle
                  "

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

                  {mostrarPassword ? (

                    <EyeOff size={18} />

                  ) : (

                    <Eye size={18} />

                  )}

                </button>

              </div>

            </label>



            {/* =================================================
                ERROR
                ================================================= */}

            {error && (

              <div
                role="alert"
                style={{
                  marginTop: "10px",
                  padding: "12px 14px",
                  borderRadius: "10px",
                  background:
                    "rgba(220, 38, 38, 0.10)",
                  border:
                    "1px solid rgba(220, 38, 38, 0.25)",
                  color: "#b91c1c",
                  fontSize: "14px",
                  lineHeight: 1.4,
                }}
              >

                {error}

              </div>

            )}



            {/* =================================================
                OPCIONES
                ================================================= */}

            <div className="login-form__options">


              <label className="login-form__remember">

                <input
                  type="checkbox"

                  checked={
                    recordarSesion
                  }

                  onChange={(event) =>
                    setRecordarSesion(
                      event.target.checked,
                    )
                  }

                  disabled={cargando}
                />


                <span>

                  Recordar sesión

                </span>

              </label>



              <Link
                to="/recuperar-contrasena"
              >

                ¿Olvidó su contraseña?

              </Link>


            </div>



            {/* =================================================
                BOTÓN
                ================================================= */}

            <button

              type="submit"

              className="
                login-form__submit
              "

              disabled={cargando}

            >

              <span>

                {cargando
                  ? "Verificando..."
                  : "Ingresar al sistema"}

              </span>


              <ArrowRight size={18} />

            </button>


          </form>



          {/* =================================================
              SEGURIDAD
              ================================================= */}

          <div className="login-card__security">


            <div className="login-card__security-icon">

              <CheckCircle2 size={15} />

            </div>


            <div>

              <strong>
                Acceso protegido
              </strong>


              <span>

                Exclusivo para personal autorizado
                de la clínica.

              </span>

            </div>


          </div>


        </div>



        {/* ===================================================
            FOOTER
            =================================================== */}

        <footer className="login-access__footer">

          <span>
            Clínica San Juan de Dios
          </span>


          <span
            className="
              login-access__footer-dot
            "
          />


          <span>
            Sistema de apoyo clínico
          </span>

        </footer>


      </section>


    </main>

  );
}