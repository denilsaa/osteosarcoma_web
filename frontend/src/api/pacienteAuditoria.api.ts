import {
  apiAuditoria,
} from "./axios";


// ==========================================================
// CAMBIO DE AUDITORÍA
// ==========================================================

export interface PatientAuditChange {

  id_cambio:
    number;

  campo:
    string;

  valor_anterior:
    string | null;

  valor_nuevo:
    string | null;

}


// ==========================================================
// EVENTO
// ==========================================================

export interface PatientAuditEvent {

  id_evento:
    string;

  actor_usuario_uuid:
    string | null;

  servicio:
    string;

  servicio_nombre:
    string;

  modulo:
    string;

  modulo_nombre:
    string;

  accion:
    string;

  accion_nombre:
    string;

  resultado:
    string;

  resultado_nombre:
    string;

  entidad_tipo:
    string | null;

  entidad_id:
    string | null;

  correlation_id:
    string | null;

  direccion_ip:
    string | null;

  user_agent:
    string | null;

  detalle_json:
    Record<
      string,
      unknown
    > | null;

  fecha_evento:
    string;

  cantidad_cambios?:
    number;

}


// ==========================================================
// LISTADO PAGINADO
// ==========================================================

interface PatientAuditListResponse {

  current_page:
    number;

  data:
    PatientAuditEvent[];

  last_page:
    number;

  per_page:
    number;

  total:
    number;

}


// ==========================================================
// DETALLE
// ==========================================================

export interface PatientAuditEventDetail {

  evento:
    PatientAuditEvent;

  cambios:
    PatientAuditChange[];

}


// ==========================================================
// NORMALIZAR RESPUESTA
// ==========================================================

function normalizeResponse<T>(
  data:
    T | string,
): T {

  if (
    typeof data ===
      "string"
  ) {

    return JSON.parse(
      data,
    ) as T;

  }


  return data;

}


// ==========================================================
// HISTORIAL DEL PACIENTE
// ==========================================================

export async function getPatientAuditHistory(
  patientId: string,
  limit = 15,
): Promise<
  PatientAuditEvent[]
> {

  const response =
    await apiAuditoria
      .get<
        PatientAuditListResponse
        |
        string
      >(
        "/auditoria/eventos",
        {
          params: {

            servicio:
              "CLINICO",

            modulo:
              "PACIENTES",

            page:
              1,

            per_page:
              limit,

          },
        },
      );


  const result =
    normalizeResponse<
      PatientAuditListResponse
    >(
      response.data,
    );


  /*
   * Defensa adicional:
   * filtramos por entidad_id también en frontend.
   */
  return result
    .data
    .filter(
      (
        event,
      ) =>
        event.entidad_id ===
        patientId,
    );

}


// ==========================================================
// DETALLE DEL EVENTO
// ==========================================================

export async function getPatientAuditEventDetail(
  eventId: string,
): Promise<
  PatientAuditEventDetail
> {

  const response =
    await apiAuditoria
      .get<
        PatientAuditEventDetail
        |
        string
      >(
        `/auditoria/eventos/${eventId}`,
      );


  return normalizeResponse<
    PatientAuditEventDetail
  >(
    response.data,
  );

}