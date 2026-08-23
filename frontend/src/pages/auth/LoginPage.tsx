import { Link, useNavigate } from "react-router-dom";

import "./Auth.css";

export function LoginPage() {
  const navigate = useNavigate();

  const iniciarSesion = () => {
    navigate("/dashboard");
  };

  return (
    <div className="auth-page">
      <div className="auth-panel">
        <div className="auth-brand">
          <div className="auth-brand__logo">OS</div>

          <div>
            <h1>OsteoSupport</h1>
            <p>Sistema de apoyo radiográfico</p>
          </div>
        </div>

        <div className="auth-card">
          <span className="auth-card__eyebrow">
            Acceso profesional
          </span>

          <h2>Iniciar sesión</h2>

          <p>
            Ingrese sus credenciales para acceder al sistema.
          </p>

          <label>
            Correo o usuario
            <input
              type="text"
              placeholder="usuario@clinica.com"
            />
          </label>

          <label>
            Contraseña
            <input
              type="password"
              placeholder="••••••••"
            />
          </label>

          <button type="button" onClick={iniciarSesion}>
            Ingresar
          </button>

          <Link to="/recuperar-contrasena">
            ¿Olvidó su contraseña?
          </Link>
        </div>
      </div>

      <aside className="auth-info">
        <div>
          <span>Clínica San Juan de Dios</span>

          <h2>
            Apoyo inteligente para el análisis radiográfico
          </h2>

          <p>
            Plataforma orientada al apoyo del especialista en
            la revisión de radiografías óseas.
          </p>
        </div>
      </aside>
    </div>
  );
}