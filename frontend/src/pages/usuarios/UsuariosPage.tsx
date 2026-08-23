import { MockupPage } from "../../components/MockupPage";

export function UsuariosPage() {
  return (
    <MockupPage
      title="Usuarios"
      description="Gestión de oncólogos, responsables y permisos del sistema."
      actionLabel="Nuevo usuario"
      actionTo="/usuarios/nuevo"
    />
  );
}