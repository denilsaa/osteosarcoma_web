import axios from "axios";

import api from "./axios";


export interface OncologoResumen {

  id_usuario: string;

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string | null;

  nombre_completo: string;

  correo: string;

  nombre_usuario: string;

  telefono: string | null;

  estado: string;

  estado_nombre: string;

  especialidad: string | null;

  subespecialidad: string | null;

  matricula_profesional: string | null;

  telefono_institucional: string | null;

  rol: string;

  fecha_creacion: string;

}


export interface PerfilOncologo {

  matricula_profesional: string | null;

  especialidad: string | null;

  subespecialidad: string | null;

  cargo: string | null;

  telefono_institucional: string | null;

}


export interface OncologoDetalle {

  id_usuario: string;

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string | null;

  nombre_completo: string;

  correo: string;

  nombre_usuario: string;

  telefono: string | null;

  estado: string;

  estado_nombre: string;

  perfil: PerfilOncologo;

  roles: string[];

  fecha_creacion: string;

  fecha_actualizacion: string;

  ultimo_acceso: string | null;

}


export interface ListadoOncologosResponse {

  total: number;

  resultados: OncologoResumen[];

}


export interface CrearOncologoPayload {

  nombres: string;

  apellido_paterno: string;

  apellido_materno?: string | null;

  correo: string;

  nombre_usuario: string;

  telefono?: string | null;

  password: string;

  matricula_profesional?: string | null;

  especialidad?: string | null;

  subespecialidad?: string | null;

  telefono_institucional?: string | null;

}


export interface EditarOncologoPayload {

  nombres?: string;

  apellido_paterno?: string;

  apellido_materno?: string | null;

  correo?: string;

  nombre_usuario?: string;

  telefono?: string | null;

  matricula_profesional?: string | null;

  especialidad?: string | null;

  subespecialidad?: string | null;

  telefono_institucional?: string | null;

}


export interface OperacionOncologoResponse {

  mensaje: string;

  id_usuario: string;

}


export interface CambiarEstadoResponse {

  mensaje: string;

  id_usuario: string;

  estado: string;

  estado_nombre: string;

  sesiones_revocadas: number;

}


export type ErroresFormulario =
  Record<string, string>;


export async function listarOncologos(
  buscar = "",
  estado = "",
): Promise<ListadoOncologosResponse> {

  const params: Record<
    string,
    string
  > = {};


  if (buscar.trim()) {

    params.buscar =
      buscar.trim();

  }


  if (estado.trim()) {

    params.estado =
      estado.trim();

  }


  const response =
    await api.get<ListadoOncologosResponse>(
      "/oncologos/",
      {
        params,
      },
    );


  return {

    total:
      Number(
        response.data?.total ??
        0
      ),

    resultados:
      Array.isArray(
        response.data?.resultados
      )
        ? response.data.resultados
        : [],

  };

}


export async function obtenerOncologo(
  idUsuario: string,
): Promise<OncologoDetalle> {

  const response =
    await api.get<OncologoDetalle>(
      `/oncologos/${idUsuario}/`,
    );


  return response.data;

}


export async function crearOncologo(
  data: CrearOncologoPayload,
): Promise<OperacionOncologoResponse> {

  const response =
    await api.post<OperacionOncologoResponse>(
      "/oncologos/",
      data,
    );


  return response.data;

}


export async function editarOncologo(
  idUsuario: string,
  data: EditarOncologoPayload,
): Promise<OperacionOncologoResponse> {

  const response =
    await api.put<OperacionOncologoResponse>(
      `/oncologos/${idUsuario}/`,
      data,
    );


  return response.data;

}


export async function cambiarEstadoOncologo(
  idUsuario: string,
  estado: "ACTIVO" | "INACTIVO",
): Promise<CambiarEstadoResponse> {

  const response =
    await api.patch<CambiarEstadoResponse>(
      `/oncologos/${idUsuario}/estado/`,
      {
        estado,
      },
    );


  return response.data;

}


export function obtenerStatusError(
  error: unknown,
): number | null {

  if (
    !axios.isAxiosError(error)
  ) {

    return null;

  }


  return (
    error.response?.status ??
    null
  );

}


export function normalizarErroresApi(
  error: unknown,
): ErroresFormulario {

  if (
    !axios.isAxiosError(error)
  ) {

    return {
      general:
        "Ocurrió un error inesperado.",
    };

  }


  const data =
    error.response?.data;


  if (!data) {

    return {
      general:
        "No fue posible comunicarse con el servidor.",
    };

  }


  if (
    typeof data === "string"
  ) {

    return {
      general: data,
    };

  }


  if (
    typeof data !== "object"
  ) {

    return {
      general:
        "No fue posible completar la operación.",
    };

  }


  const resultado:
    ErroresFormulario = {};


  Object.entries(
    data as Record<
      string,
      unknown
    >,
  ).forEach(
    ([campo, valor]) => {

      if (
        Array.isArray(valor)
      ) {

        resultado[campo] =
          valor
            .map(String)
            .join(" ");

        return;

      }


      if (
        typeof valor === "string"
      ) {

        if (
          campo === "error" ||
          campo === "detail" ||
          campo ===
            "non_field_errors"
        ) {

          resultado.general =
            valor;

        } else {

          resultado[campo] =
            valor;

        }

      }

    },
  );


  if (
    Object.keys(resultado)
      .length === 0
  ) {

    resultado.general =
      "No fue posible completar la operación.";

  }


  return resultado;

}