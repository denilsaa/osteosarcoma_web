import axios from "axios";

import api from "./axios";


/* =========================================================
   TIPOS GENERALES
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
   RESUMEN DE ONCÓLOGO
   ========================================================= */

export interface OncologoResumen {

  id_usuario: string;

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string | null;

  nombre_completo: string;

  ci_numero: string | null;

  ci_complemento: string | null;

  ci_expedido: ExpedicionBolivia | null;

  ci_completo: string | null;

  correo: string;

  nombre_usuario: string;

  telefono: string | null;

  estado: string;

  estado_nombre: string;

  especialidad: string | null;

  subespecialidad: string | null;

  area_clinica: string | null;

  matricula_profesional: string | null;

  telefono_institucional: string | null;

  rol: string;

  rol_codigo: RolOncologia;

  roles: string[];

  fecha_creacion: string;

}


/* =========================================================
   PERFIL PROFESIONAL
   ========================================================= */

export interface PerfilOncologo {

  matricula_profesional: string | null;

  especialidad: string | null;

  subespecialidad: string | null;

  area_clinica: string | null;

  cargo: string | null;

  telefono_institucional: string | null;

}


/* =========================================================
   DETALLE
   ========================================================= */

export interface OncologoDetalle {

  id_usuario: string;

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string | null;

  nombre_completo: string;

  telefono: string | null;

  ci_numero: string | null;

  ci_complemento: string | null;

  ci_expedido: ExpedicionBolivia | null;

  ci_completo: string | null;

  correo: string;

  nombre_usuario: string;

  estado: string;

  estado_nombre: string;

  rol_codigo: RolOncologia;

  rol_nombre: string;

  perfil: PerfilOncologo;

  roles: string[];

  fecha_creacion: string;

  fecha_actualizacion: string;

  ultimo_acceso: string | null;

}


/* =========================================================
   LISTADO
   ========================================================= */

export interface ListadoOncologosResponse {

  total: number;

  resultados: OncologoResumen[];

}


/* =========================================================
   CREAR ONCÓLOGO
   ========================================================= */

export interface CrearOncologoPayload {

  nombres: string;

  apellido_paterno: string;

  apellido_materno?: string | null;

  telefono?: string | null;

  ci_numero: string;

  ci_complemento?: string | null;

  ci_expedido: ExpedicionBolivia;

  correo: string;

  matricula_profesional: string;

  subespecialidad: string;

  telefono_institucional?: string | null;

  rol_codigo: RolOncologia;

}


/* =========================================================
   EDITAR ONCÓLOGO
   ========================================================= */

export interface EditarOncologoPayload {

  nombres?: string;

  apellido_paterno?: string;

  apellido_materno?: string | null;

  telefono?: string | null;

  ci_numero?: string;

  ci_complemento?: string | null;

  ci_expedido?: ExpedicionBolivia;

  correo?: string;

  matricula_profesional?: string;

  subespecialidad?: string;

  telefono_institucional?: string | null;

  rol_codigo?: RolOncologia;

  /*
   * Compatibilidad temporal con la pantalla
   * de edición existente.
   *
   * Más adelante la actualizaremos para que
   * nombre_usuario y especialidad tampoco
   * puedan editarse manualmente.
   */
  nombre_usuario?: string;

  especialidad?: string | null;

  area_clinica?: string | null;

}


/* =========================================================
   RESPUESTA DE CREACIÓN
   ========================================================= */

export interface CrearOncologoResponse {

  mensaje: string;

  oncologo: {

    id_usuario: string;

    nombre_usuario: string;

    correo: string;

    rol_codigo: RolOncologia;

    nombre_completo: string;

  };

  correo_credenciales_enviado: boolean;

}


/* =========================================================
   RESPUESTA DE EDICIÓN
   ========================================================= */

export interface OperacionOncologoResponse {

  mensaje: string;

  id_usuario: string;

}


/* =========================================================
   CAMBIO DE ESTADO
   ========================================================= */

export interface CambiarEstadoResponse {

  mensaje: string;

  id_usuario: string;

  estado: string;

  estado_nombre: string;

  sesiones_revocadas: number;

}


/* =========================================================
   ERRORES
   ========================================================= */

export type ErroresFormulario =
  Record<string, string>;


/* =========================================================
   LISTAR
   ========================================================= */

export async function listarOncologos(
  buscar = "",
  estado = "",
  rol = "",
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


  if (rol.trim()) {

    params.rol =
      rol.trim();

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


/* =========================================================
   OBTENER
   ========================================================= */

export async function obtenerOncologo(
  idUsuario: string,
): Promise<OncologoDetalle> {

  const response =
    await api.get<OncologoDetalle>(
      `/oncologos/${idUsuario}/`,
    );


  return response.data;

}


/* =========================================================
   CREAR
   ========================================================= */

export async function crearOncologo(
  data: CrearOncologoPayload,
): Promise<CrearOncologoResponse> {

  const response =
    await api.post<CrearOncologoResponse>(
      "/oncologos/",
      data,
    );


  return response.data;

}


/* =========================================================
   EDITAR
   ========================================================= */

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


/* =========================================================
   CAMBIAR ESTADO
   ========================================================= */

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


/* =========================================================
   VERIFICACIÓN AUTOMÁTICA DE CI
   ========================================================= */

export async function verificarCiOncologo(
  ciNumero: string,
  ciComplemento?: string | null,
): Promise<boolean> {

  const numero =
    ciNumero.trim();

  const complemento =
    ciComplemento
      ?.trim()
      .toUpperCase() || null;


  if (!numero) {

    return true;

  }


  const response =
    await listarOncologos(
      numero,
    );


  return !response.resultados.some(
    (oncologo) =>
      oncologo.ci_numero === numero
      &&
      (
        oncologo.ci_complemento
          ?.trim()
          .toUpperCase() || null
      ) === complemento,
  );

}


/* =========================================================
   VERIFICACIÓN AUTOMÁTICA DE MATRÍCULA
   ========================================================= */

export async function verificarMatriculaOncologo(
  matricula: string,
): Promise<boolean> {

  const valor =
    matricula
      .trim()
      .toUpperCase();


  if (!valor) {

    return true;

  }


  const response =
    await listarOncologos(
      valor,
    );


  return !response.resultados.some(
    (oncologo) =>
      oncologo
        .matricula_profesional
        ?.trim()
        .toUpperCase() === valor,
  );

}


/* =========================================================
   VERIFICACIÓN AUTOMÁTICA DE CORREO
   ========================================================= */

export async function verificarCorreoOncologo(
  correo: string,
): Promise<boolean> {

  const valor =
    correo
      .trim()
      .toLowerCase();


  if (!valor) {

    return true;

  }


  const response =
    await listarOncologos(
      valor,
    );


  return !response.resultados.some(
    (oncologo) =>
      oncologo
        .correo
        .trim()
        .toLowerCase() === valor,
  );

}


/* =========================================================
   STATUS DE ERROR
   ========================================================= */

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


/* =========================================================
   OBTENER TEXTO DE ERROR
   ========================================================= */

function obtenerTextoError(
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

    const mensajes =
      Object.values(
        valor as Record<
          string,
          unknown
        >
      )
        .map(
          obtenerTextoError
        )
        .filter(
          (
            mensaje,
          ): mensaje is string =>
            Boolean(mensaje),
        );


    if (
      mensajes.length > 0
    ) {

      return mensajes.join(" ");

    }

  }


  return null;

}


/* =========================================================
   NORMALIZAR ERRORES DE API
   ========================================================= */

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
      general:
        data,
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

      const mensaje =
        obtenerTextoError(
          valor
        );


      if (!mensaje) {

        return;

      }


      if (
        campo === "error"
        ||
        campo === "detail"
        ||
        campo === "non_field_errors"
      ) {

        resultado.general =
          mensaje;

        return;

      }


      resultado[campo] =
        mensaje;

    },
  );


  if (
    Object.keys(
      resultado
    ).length === 0
  ) {

    resultado.general =
      "No fue posible completar la operación.";

  }


  return resultado;

}