import { MockupPage } from "../../components/MockupPage";

export function PacientesPage() {
  return (
    <MockupPage
      title="Pacientes"
      description="Consulta y administración de pacientes registrados."
      actionLabel="Nuevo paciente"
      actionTo="/pacientes/nuevo"
    />
  );
}