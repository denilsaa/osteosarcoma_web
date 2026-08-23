import { MockupPage } from "../../components/MockupPage";

export function CasosPage() {
  return (
    <MockupPage
      title="Casos clínicos"
      description="Seguimiento de casos abiertos, en evaluación y analizados."
      actionLabel="Nuevo caso"
      actionTo="/casos/nuevo"
    />
  );
}