import axios from "axios";

import {
  apiPublic,
} from "./axios";

import api from "./axios";


/* =========================================================
   ESTADOS
   ========================================================= */

export type EstadoRecuperacion =
  | "PENDIENTE"
  | "APROBADA"
  | "RECHAZADA"
  | "UTILIZADA"
  | "EXPIRADA";


export type DecisionRecuperacion =
  | "APROBADA"
  | "RECHAZADA";


/* =========================================================
   SOLICITAR
   ========================================================= */

export interface SolicitarRecuperacionResponse {

  mensaje: string;

}


/* =========================================================
   CONSULTAR ESTADO
   ========================================================= */

export interface EstadoRecuperacionResponse {

  id_solicitud: string;

  estado: EstadoRecuperacion;

  puede_cambiar_password: boolean;

  mensaje: string;

  fecha_expiracion?: string;

}


/* =========================================================
   CAMBIAR CONTRASEÑA
   ========================================================= */

export interface CambiarPasswordPayload {

  token: string;

  nueva_password: string;

  confirmar_password: string;

}


export interface CambiarPasswordResponse {

  mensaje: string;

  sesiones_revocadas: number;

  estado: string;

}


/* =========================================================
   RESOLUCIÓN
   ========================================================= */

export interface ResolucionRecuperacion {

  decision: DecisionRecuperacion;

  observacion: string | null;

  resuelto_por: string;

  fecha_resolucion: string;

}


/* =========================================================
   USUARIO SOLICITANTE
   ========================================================= */

export interface UsuarioRecuperacion {

  id_usuario: string;

  nombre_completo: string;

  correo: string;

  nombre_usuario: string;

}


/* =========================================================
   RECUPERACIÓN PARA JEFATURA
   ========================================================= */

export interface RecuperacionJefatura {

  id_solicitud: string;

  usuario: UsuarioRecuperacion;

  estado: EstadoRecuperacion;

  estado_nombre: string;

  fecha_solicitud: string;

  fecha_expiracion: string;

  fecha_utilizacion: string | null;

  resolucion:
    ResolucionRecuperacion
    | null;

  /*
   * Estos campos son calculados por backend
   * según el Jefe autenticado.
   */

  es_solicitud_propia: boolean;

  puede_resolver: boolean;

}


/* =========================================================
   LISTADO
   ========================================================= */

export interface ListaRecuperacionesResponse {

  total: number;

  resultados: RecuperacionJefatura[];

}


/* =========================================================
   RESOLVER
   ========================================================= */

export interface ResolverRecuperacionResponse {

  id_solicitud: string;

  estado: EstadoRecuperacion;

  mensaje: string;

  correo_enviado?: boolean;

  revisado_por?: string;

}


/* =========================================================
   SOLICITAR RECUPERACIÓN
   ========================================================= */

export async function solicitarRecuperacion(
  correo: string,
): Promise<SolicitarRecuperacionResponse> {

  const response =
    await apiPublic.post<SolicitarRecuperacionResponse>(
      "/auth/recuperaciones/",
      {
        correo,
      },
    );


  return response.data;

}


/* =========================================================
   CONSULTAR ESTADO
   ========================================================= */

export async function consultarEstadoRecuperacion(
  token: string,
): Promise<EstadoRecuperacionResponse> {

  const response =
    await apiPublic.get<EstadoRecuperacionResponse>(
      "/auth/recuperaciones/estado/",
      {
        params: {
          token,
        },
      },
    );


  return response.data;

}


/* =========================================================
   CAMBIAR CONTRASEÑA
   ========================================================= */

export async function cambiarPasswordRecuperacion(
  data: CambiarPasswordPayload,
): Promise<CambiarPasswordResponse> {

  const response =
    await apiPublic.post<CambiarPasswordResponse>(
      "/auth/recuperaciones/cambiar-password/",
      data,
    );


  return response.data;

}


/* =========================================================
   LISTAR RECUPERACIONES
   ========================================================= */

export async function listarRecuperaciones(
  estado = "",
): Promise<ListaRecuperacionesResponse> {

  const response =
    await api.get<ListaRecuperacionesResponse>(
      "/jefatura/recuperaciones/",
      {
        params:
          estado
            ? {
                estado,
              }
            : undefined,
      },
    );


  return {

    total:
      Number(
        response.data?.total
        ??
        0,
      ),

    resultados:
      Array.isArray(
        response.data?.resultados
      )
        ? response.data.resultados
        : [],

  };

}


/* =========================================================
   RESOLVER RECUPERACIÓN
   ========================================================= */

export async function resolverRecuperacion(
  idSolicitud: string,
  decision: DecisionRecuperacion,
  observacion?: string,
): Promise<ResolverRecuperacionResponse> {

  const response =
    await api.post<ResolverRecuperacionResponse>(
      `/jefatura/recuperaciones/${idSolicitud}/resolver/`,
      {

        decision,

        observacion:
          observacion?.trim()
          ||
          null,

      },
    );


  return response.data;

}


/* =========================================================
   EXTRAER MENSAJE
   ========================================================= */

function extraerMensaje(
  valor: unknown,
): string | null {

  if (
    typeof valor === "string"
  ) {

    return valor;

  }


  if (
    Array.isArray(valor)
  ) {

    return valor
      .map(String)
      .join(" ");

  }


  if (
    valor
    &&
    typeof valor === "object"
  ) {

    for (
      const anidado
      of Object.values(
        valor as Record<
          string,
          unknown
        >
      )
    ) {

      const mensaje =
        extraerMensaje(
          anidado
        );


      if (
        mensaje
      ) {

        return mensaje;

      }

    }

  }


  return null;

}


/* =========================================================
   MENSAJE DE ERROR
   ========================================================= */

export function mensajeErrorRecuperacion(
  error: unknown,
): string {

  if (
    !axios.isAxiosError(error)
  ) {

    return (
      "Ocurrió un error inesperado."
    );

  }


  const data =
    error.response?.data;


  if (
    !data
  ) {

    return (
      "No fue posible comunicarse con el servidor."
    );

  }


  if (
    typeof data === "string"
  ) {

    return data;

  }


  if (
    typeof data === "object"
  ) {

    const objeto =
      data as Record<
        string,
        unknown
      >;


    if (
      typeof objeto.error ===
      "string"
    ) {

      return objeto.error;

    }


    if (
      typeof objeto.detail ===
      "string"
    ) {

      return objeto.detail;

    }


    const mensaje =
      extraerMensaje(
        objeto
      );


    if (
      mensaje
    ) {

      return mensaje;

    }

  }


  return (
    "No fue posible completar la operación."
  );

}