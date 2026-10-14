import { apiClinico } from "./axios";

export interface NotificacionClinica {
  id: string;
  type: "ASIGNACION" | "PRIORIDAD";
  title: string;
  message: string;
  case_id: string;
  created_at: string;
  read_at: string | null;
}

export interface ListaNotificacionesClinicas {
  data: NotificacionClinica[];
  unread: number;
}

export async function listarNotificacionesClinicas(): Promise<ListaNotificacionesClinicas> {
  const { data } = await apiClinico.get<ListaNotificacionesClinicas>("/notificaciones/");
  return data;
}

export async function marcarNotificacionLeida(id: string): Promise<void> {
  await apiClinico.patch(`/notificaciones/${encodeURIComponent(id)}/leer/`, {});
}
