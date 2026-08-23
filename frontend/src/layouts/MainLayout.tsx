import { NavLink, Outlet, useNavigate } from "react-router-dom";

import "./MainLayout.css";

export function MainLayout() {
  const navigate = useNavigate();

  const cerrarSesion = () => {
    navigate("/login");
  };

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar__brand">
          <div className="sidebar__brand-icon">OS</div>

          <div>
            <strong>OsteoSupport</strong>
            <span>Apoyo radiográfico</span>
          </div>
        </div>

        <nav className="sidebar__nav">
          <NavLink to="/dashboard">Inicio</NavLink>

          <NavLink to="/pacientes">Pacientes</NavLink>

          <NavLink to="/casos">Casos clínicos</NavLink>

          <NavLink to="/radiografias/subir">
            Radiografías
          </NavLink>

          <NavLink to="/analisis">
            Análisis IA
          </NavLink>

          <NavLink to="/reportes">
            Reportes
          </NavLink>

          <NavLink to="/usuarios">
            Usuarios
          </NavLink>

          <NavLink to="/auditoria">
            Auditoría
          </NavLink>
        </nav>

        <div className="sidebar__bottom">
          <NavLink to="/perfil">Mi perfil</NavLink>

          <button type="button" onClick={cerrarSesion}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div>
            <span className="topbar__clinic">
              Clínica San Juan de Dios
            </span>
          </div>

          <div className="topbar__user">
            <div className="topbar__avatar">DR</div>

            <div>
              <strong>Dr. Usuario</strong>
              <span>Oncología</span>
            </div>
          </div>
        </header>

        <section className="content">
          <Outlet />
        </section>
      </main>
    </div>
  );
}