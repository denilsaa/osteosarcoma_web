import axios from "axios";

import {
  apiPublic,
} from "./axios";

import api from "./axios";


export interface SolicitarRecuperacionResponse {
  mensaje: string;
}


export interface EstadoRecuperacionResponse {
  id_solicitud: string;

  estado:
    | "PENDIENTE"
    | "APROBADA"
    | "RECHAZADA"
    | "UTILIZADA"
    | "EXPIRADA";

  puede_cambiar_password: boolean;

  mensaje: string;

  fecha_expiracion?: string;
}


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


export interface RecuperacionJefatura {
  id_solicitud: string;

  usuario: {
    id_usuario: string;

    nombre_completo: string;

    correo: string;

    nombre_usuario: string;
  };

  estado: string;

  estado_nombre: string;

  fecha_solicitud: string;

  fecha_expiracion: string;

  fecha_utilizacion: string | null;

  resolucion: {
    decision: string;

    observacion: string | null;

    resuelto_por: string;

    fecha_resolucion: string;
  } | null;
}


export interface ListaRecuperacionesResponse {
  total: number;

  resultados: RecuperacionJefatura[];
}


export interface ResolverRecuperacionResponse {
  id_solicitud: string;

  estado: string;

  mensaje: string;

  correo_enviado?: boolean;
}


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


export async function listarRecuperaciones(
  estado = "",
): Promise<ListaRecuperacionesResponse> {
  const response =
    await api.get<ListaRecuperacionesResponse>(
      "/jefatura/recuperaciones/",
      {
        params:
          estado
            ? { estado }
            : undefined,
      },
    );

  return {
    total:
      Number(
        response.data?.total ?? 0,
      ),

    resultados:
      Array.isArray(
        response.data?.resultados,
      )
        ? response.data.resultados
        : [],
  };
}


export async function resolverRecuperacion(
  idSolicitud: string,
  decision:
    | "APROBADA"
    | "RECHAZADA",
  observacion?: string,
): Promise<ResolverRecuperacionResponse> {
  const response =
    await api.post<ResolverRecuperacionResponse>(
      `/jefatura/recuperaciones/${idSolicitud}/resolver/`,
      {
        decision,

        observacion:
          observacion?.trim() || null,
      },
    );

  return response.data;
}


export function mensajeErrorRecuperacion(
  error: unknown,
): string {
  if (
    !axios.isAxiosError(error)
  ) {
    return "Ocurrió un error inesperado.";
  }

  const data =
    error.response?.data;

  if (
    data &&
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

    for (
      const valor of
      Object.values(objeto)
    ) {
      if (
        Array.isArray(valor)
      ) {
        return valor
          .map(String)
          .join(" ");
      }

      if (
        typeof valor ===
        "string"
      ) {
        return valor;
      }

      if (
        valor &&
        typeof valor === "object"
      ) {
        const anidado =
          Object.values(
            valor as Record<
              string,
              unknown
            >,
          )[0];

        if (
          Array.isArray(anidado)
        ) {
          return anidado
            .map(String)
            .join(" ");
        }
      }
    }
  }

  return (
    "No fue posible completar la operación."
  );
}
