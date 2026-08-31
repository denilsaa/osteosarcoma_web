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


// ==========================================================
// RECUPERACIÓN
// ==========================================================

import {
  RecuperacionPage,
} from "./pages/recuperacion/RecuperacionPage";

import {
  CambiarPasswordRecuperacionPage,
} from "./pages/recuperacion/CambiarPasswordRecuperacionPage";

import {
  RecuperacionesJefePage,
} from "./pages/recuperacion/RecuperacionesJefePage";


// ==========================================================
// PERMISOS
// ==========================================================

import {
  PermisosJefePage,
} from "./pages/permisos/PermisosJefePage";


// ==========================================================
// DASHBOARD
// ==========================================================

import {
  DashboardPage,
} from "./pages/dashboard/DashboardPage";


// ==========================================================
// USUARIOS / ONCÓLOGOS
// ==========================================================

import {
  UsuariosPage,
} from "./pages/usuarios/UsuariosPage";

import {
  NuevoUsuarioPage,
} from "./pages/usuarios/NuevoUsuarioPage";


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

import {
  CasoDetallePage,
} from "./pages/casos/CasoDetallePage";


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

import {
  AuditoriaPage,
} from "./pages/auditoria/AuditoriaPage";


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
              <UsuariosPage />
            }
          />


          <Route
            path="/usuarios/nuevo"
            element={
              <NuevoUsuarioPage />
            }
          />


          {/* ================================================
              RECUPERACIONES
              SOLO JEFE A NIVEL BACKEND
              ================================================ */}

          <Route
            path="/recuperaciones"
            element={
              <RecuperacionesJefePage />
            }
          />


          {/* ================================================
              ADMINISTRACIÓN DE PERMISOS
              SOLO JEFE A NIVEL BACKEND
              ================================================ */}

          <Route
            path="/permisos"
            element={
              <PermisosJefePage />
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
              <CasoDetallePage />
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
              <AuditoriaPage />
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