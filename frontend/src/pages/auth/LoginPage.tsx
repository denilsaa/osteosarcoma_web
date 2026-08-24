import {
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  LockKeyhole,
  Mail,
  ShieldCheck,
  Sparkles,
  Stethoscope,
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
      <section className="login-visual">
        <div className="login-visual__glow login-visual__glow--one" />
        <div className="login-visual__glow login-visual__glow--two" />

        <div className="login-visual__orb login-visual__orb--one" />
        <div className="login-visual__orb login-visual__orb--two" />
        <div className="login-visual__orb login-visual__orb--three" />

        <div className="login-visual__grid" />

        <div className="login-visual__content">
          <div className="login-visual__badge">
            <ShieldCheck size={17} />
            <span>Entorno clínico seguro</span>
          </div>

          <div className="login-visual__heading">
            <span className="login-visual__eyebrow">
              Clínica San Juan de Dios
            </span>

            <h1>
              Tecnología que acompaña
              <span> decisiones clínicas.</span>
            </h1>

            <p>
              Plataforma especializada para la gestión clínica,
              radiográfica y el apoyo al análisis de imágenes mediante
              inteligencia artificial.
            </p>
          </div>

          <div className="login-visual__features">
            <article className="login-visual__feature">
              <div className="login-visual__feature-icon">
                <Stethoscope size={21} />
              </div>

              <div>
                <strong>Gestión clínica integrada</strong>
                <span>
                  Pacientes, casos y radiografías centralizados.
                </span>
              </div>
            </article>

            <article className="login-visual__feature">
              <div className="login-visual__feature-icon">
                <Sparkles size={21} />
              </div>

              <div>
                <strong>Apoyo mediante IA</strong>
                <span>
                  Herramientas orientadas al análisis radiográfico.
                </span>
              </div>
            </article>
          </div>

          <div className="login-visual__status">
            <div className="login-visual__status-dot" />

            <span>Sistema operativo</span>

            <div className="login-visual__status-separator" />

            <span>Acceso institucional</span>
          </div>
        </div>
      </section>

      <section className="login-access">
        <div className="login-access__decor login-access__decor--one" />
        <div className="login-access__decor login-access__decor--two" />

        <div className="login-card">
          <div className="login-card__logo">
            <img
              src="/branding/logo-san-juan.png"
              alt="Clínica San Juan de Dios"
            />
          </div>

          <div className="login-card__heading">
            <div className="login-card__tag">
              <CheckCircle2 size={14} />
              <span>Portal clínico</span>
            </div>

            <h2>Bienvenido</h2>

            <p>
              Ingrese sus credenciales institucionales para acceder
              al sistema.
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
            <ShieldCheck size={16} />

            <span>
              Acceso exclusivo para personal autorizado
            </span>
          </div>
        </div>

        <footer className="login-access__footer">
          <span>Clínica San Juan de Dios</span>
          <span>•</span>
          <span>Sistema de apoyo clínico</span>
        </footer>
      </section>
    </main>
  );
}