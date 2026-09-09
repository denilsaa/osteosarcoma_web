import axios from "axios";

import api from "./axios";


/* =========================================================
   TIPOS
   ========================================================= */

export type RolOncologia =
  | "ONCOLOGO"
  | "JEFE_ONCOLOGIA";


export type ExpedicionBolivia =
  | "LP"
  | "CB"
  | "SC"
  | "OR"
  | "PT"
  | "CH"
  | "TJ"
  | "BE"
  | "PD";


/* =========================================================
   PERFIL PROFESIONAL
   ========================================================= */

export interface PerfilProfesional {

  matricula_profesional:
    string | null;

  especialidad:
    string | null;

  subespecialidad:
    string | null;

  area_clinica:
    string | null;

  cargo:
    string | null;

  telefono_institucional:
    string | null;

}


/* =========================================================
   MI PERFIL
   ========================================================= */

export interface MiPerfil {

  id_usuario: string;

  /* -------------------------------------------------------
     DATOS PERSONALES
     ------------------------------------------------------- */

  nombres: string;

  apellido_paterno: string;

  apellido_materno:
    string | null;

  nombre_completo: string;

  telefono:
    string | null;

  /* -------------------------------------------------------
     IDENTIFICACIÓN
     ------------------------------------------------------- */

  ci_numero:
    string | null;

  ci_complemento:
    string | null;

  ci_expedido:
    ExpedicionBolivia | null;

  ci_completo:
    string | null;

  /* -------------------------------------------------------
     CUENTA
     ------------------------------------------------------- */

  correo: string;

  nombre_usuario: string;

  estado: string;

  estado_nombre: string;

  /* -------------------------------------------------------
     ROL
     ------------------------------------------------------- */

  rol_codigo:
    RolOncologia | string | null;

  rol_nombre:
    string | null;

  roles:
    string[];

  /* -------------------------------------------------------
     PROFESIONAL
     ------------------------------------------------------- */

  perfil_profesional:
    PerfilProfesional;

  /* -------------------------------------------------------
     FECHAS
     ------------------------------------------------------- */

  fecha_creacion: string;

  fecha_actualizacion: string;

  ultimo_acceso:
    string | null;

}


/* =========================================================
   ACTUALIZACIÓN
   ========================================================= */

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


/* =========================================================
   OBTENER MI PERFIL
   ========================================================= */

export async function obtenerMiPerfil():
  Promise<MiPerfil> {

  const response =
    await api.get<MiPerfil>(
      "/perfil/",
    );


  return response.data;

}


/* =========================================================
   ACTUALIZAR MI PERFIL
   ========================================================= */

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


/* =========================================================
   EXTRAER MENSAJES DE ERROR
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
      const elemento
      of Object.values(
        valor as Record<
          string,
          unknown
        >
      )
    ) {

      const mensaje =
        extraerMensaje(
          elemento
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


  const mensaje =
    extraerMensaje(
      contenido
    );


  if (
    mensaje
  ) {

    return mensaje;

  }


  return (
    "No fue posible completar la operación."
  );

}