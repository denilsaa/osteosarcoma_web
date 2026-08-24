import {
  Activity,
  Bell,
  ChevronDown,
  ClipboardList,
  FileText,
  HeartPulse,
  LayoutDashboard,
  LogOut,
  ScanLine,
  Search,
  Settings,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  UserRound,
  UsersRound,
} from "lucide-react";
import type { ComponentType } from "react";
import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import "./MainLayout.css";

type MenuItem = {
  label: string;
  path: string;
  icon: ComponentType<{
    size?: number;
    strokeWidth?: number;
  }>;
};

const mainMenu: MenuItem[] = [
  {
    label: "Inicio",
    path: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Pacientes",
    path: "/pacientes",
    icon: UsersRound,
  },
  {
    label: "Casos clínicos",
    path: "/casos",
    icon: ClipboardList,
  },
  {
    label: "Radiografías",
    path: "/radiografias/subir",
    icon: ScanLine,
  },
  {
    label: "Análisis IA",
    path: "/analisis",
    icon: Sparkles,
  },
  {
    label: "Reportes",
    path: "/reportes",
    icon: FileText,
  },
];

const adminMenu: MenuItem[] = [
  {
    label: "Usuarios",
    path: "/usuarios",
    icon: UserRound,
  },
  {
    label: "Auditoría",
    path: "/auditoria",
    icon: ShieldCheck,
  },
];

function getPageTitle(pathname: string) {
  if (pathname.startsWith("/pacientes")) return "Pacientes";
  if (pathname.startsWith("/casos")) return "Casos clínicos";
  if (pathname.startsWith("/radiografias")) return "Radiografías";
  if (pathname.startsWith("/analisis")) return "Análisis IA";
  if (pathname.startsWith("/resultados")) return "Resultados";
  if (pathname.startsWith("/reportes")) return "Reportes";
  if (pathname.startsWith("/usuarios")) return "Usuarios";
  if (pathname.startsWith("/auditoria")) return "Auditoría";
  if (pathname.startsWith("/perfil")) return "Mi perfil";

  return "Panel clínico";
}

export function MainLayout() {
  const navigate = useNavigate();
  const location = useLocation();

  const pageTitle = getPageTitle(location.pathname);

  const cerrarSesion = () => {
    navigate("/login");
  };

  return (
    <div className="clinical-layout">
      <aside className="clinical-sidebar">
        <div className="clinical-sidebar__header">
          <img
            src="/branding/logo-san-juan.png"
            alt="Clínica San Juan de Dios"
            className="clinical-sidebar__logo"
          />

          <div className="clinical-sidebar__system">
            <span className="clinical-sidebar__system-name">
              OSTEOSARCOMA
            </span>

            <span className="clinical-sidebar__system-description">
              SAN JUAN DE DIOS  
            </span>
          </div>
        </div>

        <div className="clinical-sidebar__scroll">
          <div className="clinical-sidebar__section">
            <span className="clinical-sidebar__section-label">
              Principal
            </span>

            <nav className="clinical-sidebar__navigation">
              {mainMenu.map((item) => {
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      [
                        "clinical-sidebar__link",
                        isActive
                          ? "clinical-sidebar__link--active"
                          : "",
                      ].join(" ")
                    }
                  >
                    <Icon size={19} strokeWidth={1.9} />

                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="clinical-sidebar__section">
            <span className="clinical-sidebar__section-label">
              Administración
            </span>

            <nav className="clinical-sidebar__navigation">
              {adminMenu.map((item) => {
                const Icon = item.icon;

                return (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) =>
                      [
                        "clinical-sidebar__link",
                        isActive
                          ? "clinical-sidebar__link--active"
                          : "",
                      ].join(" ")
                    }
                  >
                    <Icon size={19} strokeWidth={1.9} />

                    <span>{item.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          </div>

          <div className="clinical-sidebar__status">
            <div className="clinical-sidebar__status-icon">
              <HeartPulse size={21} />
            </div>

            <div>
              <strong>Sistema operativo</strong>
              <span>Servicios disponibles</span>
            </div>

            <span className="clinical-sidebar__status-dot" />
          </div>
        </div>

        <div className="clinical-sidebar__footer">
          <button
            type="button"
            className="clinical-sidebar__profile"
            onClick={() => navigate("/perfil")}
          >
            <div className="clinical-sidebar__avatar">
              DS
            </div>

            <div className="clinical-sidebar__profile-text">
              <strong>Dr. Samuel</strong>
              <span>Médico Oncólogo</span>
            </div>

            <ChevronDown
              className="clinical-sidebar__profile-chevron"
              size={17}
            />
          </button>

          <button
            type="button"
            className="clinical-sidebar__logout"
            onClick={cerrarSesion}
          >
            <LogOut size={18} />

            <span>Cerrar sesión</span>
          </button>
        </div>
      </aside>

      <div className="clinical-main">
        <header className="clinical-topbar">
          <div className="clinical-topbar__left">
            <div className="clinical-topbar__context">
              <span>Clínica San Juan de Dios</span>

              <strong>{pageTitle}</strong>
            </div>
          </div>

          <div className="clinical-topbar__right">
            <div className="clinical-topbar__search">
              <Search size={18} />

              <input
                type="search"
                placeholder="Buscar paciente o caso..."
              />

              <span>⌘ K</span>
            </div>

            <button
              type="button"
              className="clinical-topbar__icon-button"
              aria-label="Actividad"
            >
              <Activity size={19} />
            </button>

            <button
              type="button"
              className="clinical-topbar__icon-button clinical-topbar__notification"
              aria-label="Notificaciones"
            >
              <Bell size={19} />

              <span />
            </button>

            <button
              type="button"
              className="clinical-topbar__icon-button"
              aria-label="Configuración"
            >
              <Settings size={19} />
            </button>

            <div className="clinical-topbar__divider" />

            <div className="clinical-topbar__doctor">
              <div className="clinical-topbar__doctor-icon">
                <Stethoscope size={17} />
              </div>

              <div>
                <strong>Dr. Samuel</strong>
                <span>Oncología</span>
              </div>
            </div>
          </div>
        </header>

        <main className="clinical-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}