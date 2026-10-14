import { apiClinico } from "./axios";

export interface AsignacionPaciente {
  id_asignacion: string;
  oncologo_uuid: string;
  activa: boolean;
  motivo: string;
  fecha_asignacion: string;
  fecha_revocacion: string | null;
  motivo_revocacion: string;
}

export async function listarAsignacionesPaciente(patientId: string): Promise<AsignacionPaciente[]> {
  const { data } = await apiClinico.get<{data: AsignacionPaciente[]}>(
    `/pacientes/${patientId}/asignaciones/`,
  );
  return data.data;
}

export async function asignarPaciente(
  patientId: string,
  oncologoUuid: string,
  motivo: string,
): Promise<void> {
  await apiClinico.post(`/pacientes/${patientId}/asignaciones/`, {
    oncologo_uuid: oncologoUuid,
    motivo,
  });
}

export async function revocarPaciente(
  patientId: string,
  oncologoUuid: string,
  motivo: string,
): Promise<void> {
  await apiClinico.post(
    `/pacientes/${patientId}/asignaciones/${oncologoUuid}/revocar/`,
    { motivo },
  );
}
