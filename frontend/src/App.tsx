import { Routes, Route, Navigate } from "react-router-dom";

import { MainLayout } from "./layouts/MainLayout";

import { LoginPage } from "./pages/auth/LoginPage";
import { RecuperarPasswordPage } from "./pages/auth/RecuperarPasswordPage";

import { DashboardPage } from "./pages/dashboard/DashboardPage";

import { UsuariosPage } from "./pages/usuarios/UsuariosPage";
import { NuevoUsuarioPage } from "./pages/usuarios/NuevoUsuarioPage";

import { PacientesPage } from "./pages/pacientes/PacientesPage";
import { NuevoPacientePage } from "./pages/pacientes/NuevoPacientePage";
import { PacienteDetallePage } from "./pages/pacientes/PacienteDetallePage";

import { CasosPage } from "./pages/casos/CasosPage";
import { NuevoCasoPage } from "./pages/casos/NuevoCasoPage";
import { CasoDetallePage } from "./pages/casos/CasoDetallePage";

import { SubirRadiografiaPage } from "./pages/radiografias/SubirRadiografiaPage";
import { RadiografiaDetallePage } from "./pages/radiografias/RadiografiaDetallePage";

import { AnalisisPage } from "./pages/analisis/AnalisisPage";
import { ResultadoPage } from "./pages/analisis/ResultadoPage";

import { ReportesPage } from "./pages/reportes/ReportesPage";
import { AuditoriaPage } from "./pages/auditoria/AuditoriaPage";
import { PerfilPage } from "./pages/perfil/PerfilPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />

      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/recuperar-contrasena"
        element={<RecuperarPasswordPage />}
      />

      <Route element={<MainLayout />}>
        <Route path="/dashboard" element={<DashboardPage />} />

        <Route path="/usuarios" element={<UsuariosPage />} />
        <Route path="/usuarios/nuevo" element={<NuevoUsuarioPage />} />

        <Route path="/pacientes" element={<PacientesPage />} />
        <Route path="/pacientes/nuevo" element={<NuevoPacientePage />} />
        <Route path="/pacientes/:id" element={<PacienteDetallePage />} />

        <Route path="/casos" element={<CasosPage />} />
        <Route path="/casos/nuevo" element={<NuevoCasoPage />} />
        <Route path="/casos/:id" element={<CasoDetallePage />} />

        <Route
          path="/radiografias/subir"
          element={<SubirRadiografiaPage />}
        />
        <Route
          path="/radiografias/:id"
          element={<RadiografiaDetallePage />}
        />

        <Route path="/analisis" element={<AnalisisPage />} />
        <Route path="/resultados/:id" element={<ResultadoPage />} />

        <Route path="/reportes" element={<ReportesPage />} />
        <Route path="/auditoria" element={<AuditoriaPage />} />
        <Route path="/perfil" element={<PerfilPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;