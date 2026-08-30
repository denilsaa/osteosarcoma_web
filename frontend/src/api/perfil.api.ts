import axios from "axios";

import api from "./axios";


export interface PerfilProfesional {

  matricula_profesional:
    string | null;

  especialidad:
    string | null;

  subespecialidad:
    string | null;

  cargo:
    string | null;

  telefono_institucional:
    string | null;

}


export interface MiPerfil {

  id_usuario: string;

  nombres: string;

  apellido_paterno: string;

  apellido_materno:
    string | null;

  nombre_completo: string;

  correo: string;

  nombre_usuario: string;

  telefono:
    string | null;

  estado: string;

  estado_nombre: string;

  roles: string[];

  perfil_profesional:
    PerfilProfesional;

  fecha_creacion: string;

  ultimo_acceso:
    string | null;

}


export interface ActualizarPerfilPayload {

  nombres?: string;

  apellido_paterno?: string;

  apellido_materno?:
    string | null;

  telefono?:
    string | null;

}


export interface ActualizarPerfilResponse {

  mensaje: string;

  perfil: MiPerfil;

}


export async function obtenerMiPerfil():
  Promise<MiPerfil> {

  const response =
    await api.get<MiPerfil>(
      "/perfil/",
    );


  return response.data;

}


export async function actualizarMiPerfil(
  data: ActualizarPerfilPayload,
): Promise<ActualizarPerfilResponse> {

  const response =
    await api.patch<ActualizarPerfilResponse>(
      "/perfil/",
      data,
    );


  return response.data;

}


export function obtenerMensajeErrorPerfil(
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
    !data ||
    typeof data !== "object"
  ) {

    return (
      "No fue posible completar la operación."
    );

  }


  const contenido =
    data as Record<
      string,
      unknown
    >;


  if (
    typeof contenido.error ===
    "string"
  ) {

    return contenido.error;

  }


  if (
    typeof contenido.detail ===
    "string"
  ) {

    return contenido.detail;

  }


  const primerError =
    Object.values(
      contenido,
    )[0];


  if (
    Array.isArray(
      primerError,
    )
  ) {

    return primerError
      .map(String)
      .join(" ");

  }


  if (
    typeof primerError ===
    "string"
  ) {

    return primerError;

  }


  return (
    "No fue posible completar la operación."
  );

}