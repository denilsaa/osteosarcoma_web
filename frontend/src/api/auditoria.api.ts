// ==========================================================
// CONFIGURACIÓN
// ==========================================================

const AUDITORIA_API_URL =
  (
    import.meta.env.VITE_AUDITORIA_API_URL ||
    "http://localhost:8004/api"
  ).replace(/\/$/, "");


// ==========================================================
// TIPOS
// ==========================================================

export type ServicioAuditoria = {
  codigo: string;
  nombre: string;
};


export type ModuloAuditoria = {
  servicio: string;
  codigo: string;
  nombre: string;
};


export type AccionAuditoria = {
  codigo: string;
  nombre: string;
};


export type ResultadoAuditoria = {
  codigo: string;
  nombre: string;
};


export type CatalogosAuditoria = {
  servicios: ServicioAuditoria[];
  modulos: ModuloAuditoria[];
  acciones: AccionAuditoria[];
  resultados: ResultadoAuditoria[];
};


export type DetalleJsonAuditoria = {
  actor_nombre?: string | null;
  actor_rol?: string | null;

  descripcion?: string | null;
  motivo?: string | null;

  [key: string]: unknown;
};


export type EventoAuditoria = {
  id_evento: string;

  actor_usuario_uuid:
    | string
    | null;

  servicio: string;

  servicio_nombre?:
    | string
    | null;

  modulo: string;

  modulo_nombre?:
    | string
    | null;

  accion: string;

  accion_nombre?:
    | string
    | null;

  resultado: string;

  resultado_nombre?:
    | string
    | null;

  entidad_tipo:
    | string
    | null;

  entidad_id:
    | string
    | null;

  correlation_id:
    | string
    | null;

  direccion_ip:
    | string
    | null;

  user_agent?:
    | string
    | null;

  detalle_json:
    | DetalleJsonAuditoria
    | null;

  fecha_evento: string;

  cantidad_cambios: number;
};


export type CambioAuditoria = {
  id_cambio: number;

  campo: string;

  valor_anterior:
    | string
    | null;

  valor_nuevo:
    | string
    | null;
};


export type DetalleEventoAuditoria = {
  evento: EventoAuditoria;
  cambios: CambioAuditoria[];
};


export type RespuestaPaginadaAuditoria = {
  current_page: number;

  data: EventoAuditoria[];

  from:
    | number
    | null;

  last_page: number;

  next_page_url:
    | string
    | null;

  per_page: number;

  prev_page_url:
    | string
    | null;

  to:
    | number
    | null;

  total: number;
};


export type FiltrosAuditoria = {
  page?: number;
  per_page?: number;

  servicio?: string;
  modulo?: string;
  accion?: string;
  resultado?: string;

  entidad?: string;
};


// ==========================================================
// ERROR
// ==========================================================

export class AuditoriaApiError
  extends Error {

  status: number;

  constructor(
    message: string,
    status: number,
  ) {

    super(message);

    this.name =
      "AuditoriaApiError";

    this.status =
      status;
  }
}


// ==========================================================
// REQUEST
// ==========================================================

async function requestJson<T>(
  ruta: string,
  signal?: AbortSignal,
): Promise<T> {

  const response =
    await fetch(
      `${AUDITORIA_API_URL}${ruta}`,
      {
        method:
          "GET",

        headers: {
          Accept:
            "application/json",
        },

        signal,
      },
    );


  if (
    !response.ok
  ) {

    let mensaje =
      `Auditoría respondió HTTP ${response.status}.`;


    try {

      const data =
        await response.json();

      mensaje =
        data?.mensaje ||
        data?.error ||
        mensaje;

    } catch {

      // Se mantiene el mensaje
      // HTTP genérico.
    }


    throw new AuditoriaApiError(
      mensaje,
      response.status,
    );
  }


  return (
    await response.json()
  ) as T;
}


// ==========================================================
// CATÁLOGOS
// ==========================================================

export async function obtenerCatalogosAuditoria(
  signal?: AbortSignal,
): Promise<CatalogosAuditoria> {

  return requestJson<CatalogosAuditoria>(
    "/auditoria/catalogos",
    signal,
  );
}


// ==========================================================
// LISTAR EVENTOS
// ==========================================================

export async function listarEventosAuditoria(
  filtros: FiltrosAuditoria = {},
  signal?: AbortSignal,
): Promise<RespuestaPaginadaAuditoria> {

  const params =
    new URLSearchParams();


  if (
    filtros.page
  ) {
    params.set(
      "page",
      String(
        filtros.page,
      ),
    );
  }


  if (
    filtros.per_page
  ) {
    params.set(
      "per_page",
      String(
        filtros.per_page,
      ),
    );
  }


  if (
    filtros.servicio?.trim()
  ) {

    params.set(
      "servicio",
      filtros.servicio.trim(),
    );
  }


  if (
    filtros.modulo?.trim()
  ) {

    params.set(
      "modulo",
      filtros.modulo.trim(),
    );
  }


  if (
    filtros.accion?.trim()
  ) {

    params.set(
      "accion",
      filtros.accion.trim(),
    );
  }


  if (
    filtros.resultado?.trim()
  ) {

    params.set(
      "resultado",
      filtros.resultado.trim(),
    );
  }


  if (
    filtros.entidad?.trim()
  ) {

    params.set(
      "entidad",
      filtros.entidad.trim(),
    );
  }


  const query =
    params.toString();


  return requestJson<RespuestaPaginadaAuditoria>(
    `/auditoria/eventos${query ? `?${query}` : ""}`,
    signal,
  );
}


// ==========================================================
// DETALLE
// ==========================================================

export async function obtenerEventoAuditoria(
  idEvento: string,
  signal?: AbortSignal,
): Promise<DetalleEventoAuditoria> {

  return requestJson<DetalleEventoAuditoria>(
    `/auditoria/eventos/${encodeURIComponent(idEvento)}`,
    signal,
  );
}


// ==========================================================
// MENSAJE ERROR
// ==========================================================

export function mensajeErrorAuditoria(
  error: unknown,
): string {

  if (
    error instanceof
    AuditoriaApiError
  ) {

    return error.message;
  }


  if (
    error instanceof
    Error
  ) {

    if (
      error.name ===
      "AbortError"
    ) {

      return "";
    }


    return error.message;
  }


  return (
    "No fue posible comunicarse " +
    "con el servicio de Auditoría."
  );
}