import { lazy, Suspense } from "react";

import {
  Navigate,
  Route,
  Routes,
} from "react-router-dom";

import {
  ProtectedRoute,
} from "./auth/ProtectedRoute";

import {
  MainLayout,
} from "./layouts/MainLayout";


// ==========================================================
// AUTENTICACIÓN
// ==========================================================

import {
  LoginPage,
} from "./pages/auth/LoginPage";

import {
  VerificarSegundoFactorPage,
} from "./pages/auth/VerificarSegundoFactorPage";


// ==========================================================
// RECUPERACIÓN
// ==========================================================

import {
  RecuperacionPage,
} from "./pages/recuperacion/RecuperacionPage";

import {
  CambiarPasswordRecuperacionPage,
} from "./pages/recuperacion/CambiarPasswordRecuperacionPage";

const RecuperacionesJefePage = lazy(() =>
  import("./pages/recuperacion/RecuperacionesJefePage").then((module) => ({ default: module.RecuperacionesJefePage })),
);


// ==========================================================
// PERMISOS
// ==========================================================

const PermisosJefePage = lazy(() =>
  import("./pages/permisos/PermisosJefePage").then((module) => ({ default: module.PermisosJefePage })),
);


// ==========================================================
// DASHBOARD
// ==========================================================

import {
  DashboardPage,
} from "./pages/dashboard/DashboardPage";


// ==========================================================
// USUARIOS / ONCÓLOGOS
// ==========================================================

const UsuariosPage = lazy(() =>
  import("./pages/usuarios/UsuariosPage").then((module) => ({ default: module.UsuariosPage })),
);

const NuevoUsuarioPage = lazy(() =>
  import("./pages/usuarios/NuevoUsuarioPage").then((module) => ({ default: module.NuevoUsuarioPage })),
);


// ==========================================================
// PACIENTES
// ==========================================================

import {
  PacientesPage,
} from "./pages/pacientes/PacientesPage";

import {
  NuevoPacientePage,
} from "./pages/pacientes/NuevoPacientePage";

import {
  PacienteDetallePage,
} from "./pages/pacientes/PacienteDetallePage";


// ==========================================================
// CASOS CLÍNICOS
// ==========================================================

import {
  CasosPage,
} from "./pages/casos/CasosPage";

import {
  NuevoCasoPage,
} from "./pages/casos/NuevoCasoPage";

const CasoDetallePage = lazy(() =>
  import("./pages/casos/CasoDetallePage").then((module) => ({
    default: module.CasoDetallePage,
  })),
);


// ==========================================================
// RADIOGRAFÍAS
// ==========================================================

import {
  SubirRadiografiaPage,
} from "./pages/radiografias/SubirRadiografiaPage";

import {
  RadiografiaDetallePage,
} from "./pages/radiografias/RadiografiaDetallePage";


// ==========================================================
// ANÁLISIS IA
// ==========================================================

import {
  AnalisisPage,
} from "./pages/analisis/AnalisisPage";

import {
  ResultadoPage,
} from "./pages/analisis/ResultadoPage";



// ==========================================================
// AUDITORÍA
// ==========================================================

const AuditoriaPage = lazy(() =>
  import("./pages/auditoria/AuditoriaPage").then((module) => ({ default: module.AuditoriaPage })),
);


// ==========================================================
// PERFIL
// ==========================================================

import {
  PerfilPage,
} from "./pages/perfil/PerfilPage";


function App() {

  return (

    <Routes>


      {/* ==================================================
          RUTA INICIAL
          ================================================== */}

      <Route
        path="/"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />


      {/* ==================================================
          RUTAS PÚBLICAS
          ================================================== */}

      <Route
        path="/login"
        element={
          <LoginPage />
        }
      />


      <Route
        path="/verificar-acceso"
        element={
          <VerificarSegundoFactorPage />
        }
      />


      {/* ==================================================
          RECUPERACIÓN DE CONTRASEÑA
          ================================================== */}

      <Route
        path="/recuperar-contrasena"
        element={
          <RecuperacionPage />
        }
      />


      <Route
        path="/recuperar-contrasena/cambiar"
        element={
          <CambiarPasswordRecuperacionPage />
        }
      />


      {/* Alias */}

      <Route
        path="/recuperar"
        element={
          <Navigate
            to="/recuperar-contrasena"
            replace
          />
        }
      />


      {/* ==================================================
          RUTAS PROTEGIDAS
          ================================================== */}

      <Route
        element={
          <ProtectedRoute />
        }
      >


        <Route
          element={
            <MainLayout />
          }
        >


          {/* ================================================
              DASHBOARD
              ================================================ */}

          <Route
            path="/dashboard"
            element={
              <DashboardPage />
            }
          />


          {/* ================================================
              GESTIÓN DE ONCÓLOGOS
              ================================================ */}

          <Route
            path="/usuarios"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando módulo...</div>}>
                <UsuariosPage />
              </Suspense>
            }
          />


          <Route
            path="/usuarios/nuevo"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando módulo...</div>}>
                <NuevoUsuarioPage />
              </Suspense>
            }
          />


          {/* ================================================
              RECUPERACIONES
              SOLO JEFE A NIVEL BACKEND
              ================================================ */}

          <Route
            path="/recuperaciones"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando módulo...</div>}>
                <RecuperacionesJefePage />
              </Suspense>
            }
          />


          {/* ================================================
              ADMINISTRACIÓN DE PERMISOS
              SOLO JEFE A NIVEL BACKEND
              ================================================ */}

          <Route
            path="/permisos"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando módulo...</div>}>
                <PermisosJefePage />
              </Suspense>
            }
          />


          {/* ================================================
              PACIENTES
              ================================================ */}

          <Route
            path="/pacientes"
            element={
              <PacientesPage />
            }
          />


          <Route
            path="/pacientes/nuevo"
            element={
              <NuevoPacientePage />
            }
          />


          <Route
            path="/pacientes/:id"
            element={
              <PacienteDetallePage />
            }
          />


          {/* ================================================
              CASOS CLÍNICOS
              ================================================ */}

          <Route
            path="/casos"
            element={
              <CasosPage />
            }
          />


          <Route
            path="/casos/nuevo"
            element={
              <NuevoCasoPage />
            }
          />


          <Route
            path="/casos/:id"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando detalle del caso...</div>}>
                <CasoDetallePage />
              </Suspense>
            }
          />


          {/* ================================================
              RADIOGRAFÍAS
              ================================================ */}

          <Route
            path="/radiografias/subir"
            element={
              <SubirRadiografiaPage />
            }
          />


          <Route
            path="/radiografias/:id"
            element={
              <RadiografiaDetallePage />
            }
          />


          {/* ================================================
              ANÁLISIS IA
              ================================================ */}

          <Route
            path="/analisis"
            element={
              <AnalisisPage />
            }
          />


          <Route
            path="/resultados/:id"
            element={
              <ResultadoPage />
            }
          />



          {/* ================================================
              AUDITORÍA
              ================================================ */}

          <Route
            path="/auditoria"
            element={
              <Suspense fallback={<div role="status" aria-live="polite" style={{ padding: 16 }}>Cargando módulo...</div>}>
                <AuditoriaPage />
              </Suspense>
            }
          />


          {/* ================================================
              MI PERFIL
              ================================================ */}

          <Route
            path="/perfil"
            element={
              <PerfilPage />
            }
          />


        </Route>


      </Route>


      {/* ==================================================
          RUTA DESCONOCIDA
          ================================================== */}

      <Route
        path="*"
        element={
          <Navigate
            to="/login"
            replace
          />
        }
      />


    </Routes>

  );

}


export default App;