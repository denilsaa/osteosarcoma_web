import axios, {
  type AxiosError,
  type AxiosInstance,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  tokenStorage,
  type DatosRenovacion,
} from "../auth/tokenStorage";


// ==========================================================
// URLS DE MICROSERVICIOS
// ==========================================================

const API_USUARIOS_URL =
  import.meta.env
    .VITE_API_USUARIOS_URL ??
  "http://localhost:8000";


const API_CLINICO_URL =
  import.meta.env
    .VITE_API_CLINICO_URL ??
  "http://localhost:8001";

const API_RADIOGRAFIAS_URL =
  import.meta.env
    .VITE_API_RADIOGRAFIAS_URL ??
  "/radiografias-api";

const API_AUDITORIA_URL =
  import.meta.env
    .VITE_API_AUDITORIA_URL ??
  "/auditoria-api";

// ==========================================================
// BASE URLS
// ==========================================================

const USUARIOS_BASE_URL =
  `${API_USUARIOS_URL}/api`;


const CLINICO_BASE_URL =
  `${API_CLINICO_URL}/api`;

const RADIOGRAFIAS_BASE_URL =
  `${API_RADIOGRAFIAS_URL}/api`;


const AUDITORIA_BASE_URL =
  `${API_AUDITORIA_URL}/api`;


// ==========================================================
// CLIENTE PÚBLICO - USUARIOS
// ==========================================================

export const apiPublic =
  axios.create({
    baseURL:
      USUARIOS_BASE_URL,

    headers: {
      "Content-Type":
        "application/json",
    },
  });


// ==========================================================
// CONTROL GLOBAL DE RENOVACIÓN
// ==========================================================

let renovacionEnCurso:
  Promise<string> | null = null;


// ==========================================================
// RENOVAR ACCESS TOKEN
// ==========================================================

async function renovarAccessToken():
  Promise<string> {

  if (renovacionEnCurso) {
    return renovacionEnCurso;
  }


  const refreshToken =
    tokenStorage
      .obtenerRefreshToken();


  if (!refreshToken) {
    throw new Error(
      "No existe refresh token.",
    );
  }


  renovacionEnCurso =
    apiPublic
      .post<DatosRenovacion>(
        "/auth/refresh/",
        {
          refresh_token:
            refreshToken,
        },
      )

      .then(
        (response) => {

          tokenStorage
            .actualizarAccessToken(
              response.data,
            );


          window.dispatchEvent(
            new CustomEvent(
              "auth:session-renewed",
              {
                detail:
                  response.data,
              },
            ),
          );


          return response
            .data
            .access_token;
        },
      )

      .catch(
        (error) => {

          tokenStorage.limpiar();


          window.dispatchEvent(
            new CustomEvent(
              "auth:session-invalidated",
              {
                detail: {
                  mensaje:
                    "La sesión expiró, fue cerrada o ya no es válida.",
                },
              },
            ),
          );


          throw error;
        },
      )

      .finally(
        () => {
          renovacionEnCurso =
            null;
        },
      );


  return renovacionEnCurso;
}


// ==========================================================
// CONFIGURACIÓN REUTILIZABLE
// ==========================================================

type ConfigConReintento =
  InternalAxiosRequestConfig & {
    _retry?: boolean;
  };


function configurarClienteAutenticado(
  cliente: AxiosInstance,
  rutasPublicas: string[] = [],
): AxiosInstance {

  const esRutaPublica =
    (
      url?: string,
    ): boolean => {

      if (!url) {
        return false;
      }


      return rutasPublicas.some(
        (ruta) =>
          url.includes(ruta),
      );
    };


  // ========================================================
  // REQUEST
  // ========================================================

  cliente.interceptors
    .request
    .use(

      (
        config:
          InternalAxiosRequestConfig,
      ) => {

        if (
          esRutaPublica(
            config.url,
          )
        ) {
          return config;
        }


        const token =
          tokenStorage
            .obtenerAccessToken();


        if (token) {
          config
            .headers
            .Authorization =
              `Bearer ${token}`;
        }


        return config;
      },


      (error) =>
        Promise.reject(
          error,
        ),
    );


  // ========================================================
  // RESPONSE
  // ========================================================

  cliente.interceptors
    .response
    .use(

      (response) =>
        response,


      async (
        error: AxiosError,
      ) => {

        const originalRequest =
          error.config as
            | ConfigConReintento
            | undefined;


        if (
          !originalRequest
          ||
          error.response?.status !==
            401
          ||
          originalRequest._retry
          ||
          esRutaPublica(
            originalRequest.url,
          )
        ) {
          return Promise.reject(
            error,
          );
        }


        originalRequest._retry =
          true;


        try {

          const nuevoAccess =
            await renovarAccessToken();


          originalRequest
            .headers
            .Authorization =
              `Bearer ${nuevoAccess}`;


          return cliente(
            originalRequest,
          );

        } catch (
          refreshError
        ) {

          return Promise.reject(
            refreshError,
          );
        }
      },
    );


  return cliente;
}


// ==========================================================
// USUARIOS
// ==========================================================

const api =
  configurarClienteAutenticado(

    axios.create({
      baseURL:
        USUARIOS_BASE_URL,

      headers: {
        "Content-Type":
          "application/json",
      },
    }),

    [
      "/auth/login/",
      "/auth/refresh/",
      "/auth/logout/",
      "/auth/recuperaciones/",
    ],
  );


// ==========================================================
// CLÍNICO
// ==========================================================

export const apiClinico =
  configurarClienteAutenticado(

    axios.create({
      baseURL:
        CLINICO_BASE_URL,

      headers: {
        "Content-Type":
          "application/json",
      },
    }),
  );


// ==========================================================
// RADIOGRAFÍAS
// ==========================================================

export const apiRadiografias =
  configurarClienteAutenticado(

    axios.create({
      baseURL:
        RADIOGRAFIAS_BASE_URL,

      headers: {
        "Content-Type":
          "application/json",
      },
    }),
  );


// ==========================================================
// AUDITORÍA
// ==========================================================

export const apiAuditoria =
  configurarClienteAutenticado(

    axios.create({
      baseURL:
        AUDITORIA_BASE_URL,

      headers: {
        "Content-Type":
          "application/json",
      },
    }),
  );


// ==========================================================
// DEFAULT
// ==========================================================

export default api;