import {
  Activity,
  Bell,
  ChevronDown,
  ClipboardList,
  FileText,
  HeartPulse,
  KeyRound,
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

import type {
  ComponentType,
} from "react";

import {
  NavLink,
  Outlet,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  useAuth,
} from "../auth/AuthProvider";

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
    label: "Informes",
    path: "/reportes",
    icon: FileText,
  },

];


const adminMenu: MenuItem[] = [

  {
    label: "Oncólogos",
    path: "/usuarios",
    icon: UserRound,
  },

  {
    label: "Recuperaciones",
    path: "/recuperaciones",
    icon: KeyRound,
  },

  {
    label: "Permisos",
    path: "/permisos",
    icon: ShieldCheck,
  },

];


function getPageTitle(
  pathname: string,
): string {

  if (
    pathname.startsWith(
      "/pacientes",
    )
  ) {
    return "Pacientes";
  }


  if (
    pathname.startsWith(
      "/casos",
    )
  ) {
    return "Casos clínicos";
  }


  if (
    pathname.startsWith(
      "/radiografias",
    )
  ) {
    return "Radiografías";
  }


  if (
    pathname.startsWith(
      "/analisis",
    )
  ) {
    return "Análisis IA";
  }


  if (
    pathname.startsWith(
      "/resultados",
    )
  ) {
    return "Resultados";
  }


  if (
    pathname.startsWith(
      "/reportes",
    )
  ) {
    return "Informes";
  }


  if (
    pathname.startsWith(
      "/auditoria",
    )
  ) {
    return "Auditoría";
  }


  if (
    pathname.startsWith(
      "/usuarios",
    )
  ) {
    return "Gestión de oncólogos";
  }


  if (
    pathname.startsWith(
      "/recuperaciones",
    )
  ) {
    return "Recuperaciones";
  }


  if (
    pathname.startsWith(
      "/permisos",
    )
  ) {
    return "Administración de permisos";
  }


  if (
    pathname.startsWith(
      "/perfil",
    )
  ) {
    return "Mi perfil";
  }


  return "Panel clínico";
}


function obtenerNombreVisible(

  nombres?: string,

  apellidoPaterno?: string | null,

  nombreUsuario?: string,

): string {

  const nombre =
    nombres?.trim();


  const apellido =
    apellidoPaterno?.trim();


  if (
    nombre &&
    apellido
  ) {

    return `${nombre} ${apellido}`;

  }


  if (nombre) {
    return nombre;
  }


  if (
    nombreUsuario?.trim()
  ) {

    return nombreUsuario.trim();

  }


  return "Usuario";
}


export function MainLayout() {

  const navigate =
    useNavigate();


  const location =
    useLocation();


  const {
    usuario,
    logout,
    tieneRol,
  } = useAuth();


  const pageTitle =
    getPageTitle(
      location.pathname,
    );


  const nombreUsuario =
    obtenerNombreVisible(

      usuario?.nombres,

      usuario?.apellido_paterno,

      usuario?.nombre_usuario,

    );


  const esJefeOncologia =
    tieneRol(
      "JEFE_ONCOLOGIA",
    );


  const rolVisible =
    esJefeOncologia

      ? "Jefe de Oncología"

      : "Médico Oncólogo";


  const iniciales =
    nombreUsuario
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map(
        (parte) =>
          parte.charAt(0),
      )
      .join("")
      .toUpperCase()
    ||
    "US";


  const cerrarSesion =
    async () => {

      try {

        await logout();

      } finally {

        navigate(
          "/login",
          {
            replace: true,
          },
        );

      }

    };


  return (

    <div className="clinical-layout">


      {/* ==================================================
          SIDEBAR
          ================================================== */}

      <aside className="clinical-sidebar">


        {/* ==================================================
            LOGO
            ================================================== */}

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


          {/* ==================================================
              PRINCIPAL
              ================================================== */}

          <div className="clinical-sidebar__section">


            <span className="clinical-sidebar__section-label">

              Principal

            </span>


            <nav className="clinical-sidebar__navigation">


              {mainMenu.map(
                (item) => {

                  const Icon =
                    item.icon;


                  return (

                    <NavLink

                      key={item.path}

                      to={item.path}

                      className={({
                        isActive,
                      }) =>
                        [
                          "clinical-sidebar__link",

                          isActive
                            ? "clinical-sidebar__link--active"
                            : "",
                        ].join(" ")
                      }

                    >

                      <Icon
                        size={19}
                        strokeWidth={1.9}
                      />


                      <span>
                        {item.label}
                      </span>


                    </NavLink>

                  );

                },
              )}


            </nav>


          </div>


          {/* ==================================================
              ADMINISTRACIÓN
              SOLO JEFE DE ONCOLOGÍA
              ================================================== */}

          {esJefeOncologia && (

            <div className="clinical-sidebar__section">


              <span className="clinical-sidebar__section-label">

                Administración

              </span>


              <nav className="clinical-sidebar__navigation">


                {adminMenu.map(
                  (item) => {

                    const Icon =
                      item.icon;


                    return (

                      <NavLink

                        key={item.path}

                        to={item.path}

                        className={({
                          isActive,
                        }) =>
                          [
                            "clinical-sidebar__link",

                            isActive
                              ? "clinical-sidebar__link--active"
                              : "",
                          ].join(" ")
                        }

                      >

                        <Icon
                          size={19}
                          strokeWidth={1.9}
                        />


                        <span>
                          {item.label}
                        </span>


                      </NavLink>

                    );

                  },
                )}


              </nav>


            </div>

          )}


          {/* ==================================================
              ESTADO DEL SISTEMA
              ================================================== */}

          <div className="clinical-sidebar__status">


            <div className="clinical-sidebar__status-icon">

              <HeartPulse
                size={21}
              />

            </div>


            <div>

              <strong>
                Sistema operativo
              </strong>

              <span>
                Servicios disponibles
              </span>

            </div>


            <span className="clinical-sidebar__status-dot" />


          </div>


        </div>


        {/* ==================================================
            USUARIO
            ================================================== */}

        <div className="clinical-sidebar__footer">


          <button

            type="button"

            className="clinical-sidebar__profile"

            onClick={() =>
              navigate(
                "/perfil",
              )
            }

          >


            <div className="clinical-sidebar__avatar">

              {iniciales}

            </div>


            <div className="clinical-sidebar__profile-text">


              <strong>
                {nombreUsuario}
              </strong>


              <span>
                {rolVisible}
              </span>


            </div>


            <ChevronDown
              className="clinical-sidebar__profile-chevron"
              size={17}
            />


          </button>


          <button

            type="button"

            className="clinical-sidebar__logout"

            onClick={() =>
              void cerrarSesion()
            }

          >

            <LogOut
              size={18}
            />

            <span>
              Cerrar sesión
            </span>

          </button>


        </div>


      </aside>


      {/* ==================================================
          CONTENIDO
          ================================================== */}

      <div className="clinical-main">


        {/* ==================================================
            TOPBAR
            ================================================== */}

        <header className="clinical-topbar">


          <div className="clinical-topbar__left">


            <div className="clinical-topbar__context">


              <span>
                Clínica San Juan de Dios
              </span>


              <strong>
                {pageTitle}
              </strong>


            </div>


          </div>


          <div className="clinical-topbar__right">


            <div className="clinical-topbar__search">

              <Search
                size={18}
              />

              <input

                type="search"

                placeholder="Buscar paciente o caso..."

              />

              <span>
                ⌘ K
              </span>

            </div>


            <button

              type="button"

              className="clinical-topbar__icon-button"

              aria-label="Actividad"

            >

              <Activity
                size={19}
              />

            </button>


            <button

              type="button"

              className="
                clinical-topbar__icon-button
                clinical-topbar__notification
              "

              aria-label="Notificaciones"

            >

              <Bell
                size={19}
              />

              <span />

            </button>


            <button

              type="button"

              className="clinical-topbar__icon-button"

              aria-label="Configuración"

            >

              <Settings
                size={19}
              />

            </button>


            <div className="clinical-topbar__divider" />


            <button

              type="button"

              className="clinical-topbar__doctor"

              onClick={() =>
                navigate(
                  "/perfil",
                )
              }

            >


              <div className="clinical-topbar__doctor-icon">

                <Stethoscope
                  size={17}
                />

              </div>


              <div>

                <strong>
                  {nombreUsuario}
                </strong>

                <span>
                  {rolVisible}
                </span>

              </div>


            </button>


          </div>


        </header>


        {/* ==================================================
            PÁGINA ACTUAL
            ================================================== */}

        <main className="clinical-content">

          <Outlet />

        </main>


      </div>


    </div>

  );

}