import { Link } from "react-router-dom";

import "./Auth.css";

export function RecuperarPasswordPage() {
  return (
    <div className="auth-page auth-page--center">
      <div className="auth-card auth-card--standalone">
        <span className="auth-card__eyebrow">
          Recuperación de acceso
        </span>

        <h2>Recuperar contraseña</h2>

        <p>
          Ingrese su correo institucional para iniciar el
          proceso de recuperación.
        </p>

        <label>
          Correo
          <input
            type="email"
            placeholder="usuario@clinica.com"
          />
        </label>

        <button type="button">
          Solicitar recuperación
        </button>

        <Link to="/login">
          Volver al inicio de sesión
        </Link>
      </div>
    </div>
  );
}