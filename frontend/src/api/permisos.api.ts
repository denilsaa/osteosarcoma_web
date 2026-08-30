import axios from "axios";

import api from "./axios";


export interface PermisoOncologo {

  id_permiso:
    number | string;

  codigo:
    string;

  nombre:
    string;

  descripcion:
    string | null;

  modulo:
    string | null;

  asignado:
    boolean;

}


export interface RolPermisos {

  codigo:
    string;

  nombre:
    string;

  descripcion:
    string | null;

}


export interface PermisosOncologoResponse {

  rol:
    RolPermisos;

  total:
    number;

  permisos:
    PermisoOncologo[];

}


export interface ActualizarPermisosResponse
  extends PermisosOncologoResponse {

  mensaje:
    string;

}


export async function obtenerPermisosOncologo():
  Promise<PermisosOncologoResponse> {

  const response =
    await api.get<PermisosOncologoResponse>(

      "/jefatura/permisos/oncologo/",

    );


  return {

    rol:
      response.data.rol,

    total:
      Number(
        response.data.total ?? 0,
      ),

    permisos:
      Array.isArray(
        response.data.permisos,
      )
        ? response.data.permisos
        : [],

  };

}


export async function actualizarPermisosOncologo(
  permisos: string[],
): Promise<ActualizarPermisosResponse> {

  const response =
    await api.put<ActualizarPermisosResponse>(

      "/jefatura/permisos/oncologo/",

      {
        permisos,
      },

    );


  return response.data;

}


export function obtenerMensajeErrorPermisos(
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


  const primerValor =
    Object.values(
      contenido,
    )[0];


  if (
    Array.isArray(
      primerValor,
    )
  ) {

    return primerValor
      .map(String)
      .join(" ");

  }


  if (
    typeof primerValor ===
    "string"
  ) {

    return primerValor;

  }


  return (
    "No fue posible completar la operación."
  );

}