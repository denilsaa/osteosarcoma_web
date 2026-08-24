import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  HeartPulse,
  LockKeyhole,
  Mail,
} from "lucide-react";

import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import "./Auth.css";

export function LoginPage() {
  const navigate = useNavigate();

  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [recordarSesion, setRecordarSesion] = useState(false);

  const iniciarSesion = () => {
    navigate("/dashboard");
  };

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
          PANEL DE ACCESO
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
              <HeartPulse size={14} />
              <span>Portal clínico</span>
            </div>

            <h2>Bienvenido</h2>

            <p>
              Ingrese sus credenciales institucionales para acceder al
              sistema.
            </p>
          </div>

          <form
            className="login-form"
            onSubmit={(event) => {
              event.preventDefault();
              iniciarSesion();
            }}
          >
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
                />
              </div>
            </label>

            <label className="login-form__field">
              <span className="login-form__label">
                Contraseña
              </span>

              <div className="login-form__control">
                <LockKeyhole size={18} />

                <input
                  type={mostrarPassword ? "text" : "password"}
                  placeholder="Ingrese su contraseña"
                  autoComplete="current-password"
                />

                <button
                  type="button"
                  className="login-form__password-toggle"
                  onClick={() =>
                    setMostrarPassword((valor) => !valor)
                  }
                  aria-label={
                    mostrarPassword
                      ? "Ocultar contraseña"
                      : "Mostrar contraseña"
                  }
                >
                  {mostrarPassword ? (
                    <EyeOff size={18} />
                  ) : (
                    <Eye size={18} />
                  )}
                </button>
              </div>
            </label>

            <div className="login-form__options">
              <label className="login-form__remember">
                <input
                  type="checkbox"
                  checked={recordarSesion}
                  onChange={(event) =>
                    setRecordarSesion(event.target.checked)
                  }
                />

                <span>Recordar sesión</span>
              </label>

              <Link to="/recuperar-contrasena">
                ¿Olvidó su contraseña?
              </Link>
            </div>

            <button
              type="submit"
              className="login-form__submit"
            >
              <span>Ingresar al sistema</span>
              <ArrowRight size={18} />
            </button>
          </form>

          <div className="login-card__security">
            <div className="login-card__security-icon">
              <CheckCircle2 size={15} />
            </div>

            <div>
              <strong>Acceso protegido</strong>
              <span>
                Exclusivo para personal autorizado de la clínica.
              </span>
            </div>
          </div>
        </div>

        <footer className="login-access__footer">
          <span>Clínica San Juan de Dios</span>
          <span className="login-access__footer-dot" />
          <span>Sistema de apoyo clínico</span>
        </footer>
      </section>
    </main>
  );
}