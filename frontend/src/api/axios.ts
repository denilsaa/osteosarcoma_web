import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  tokenStorage,
  type DatosRenovacion,
} from "../auth/tokenStorage";


const API_USUARIOS_URL =

  import.meta.env
    .VITE_API_USUARIOS_URL ??

  "http://localhost:8000";


const BASE_URL =
  `${API_USUARIOS_URL}/api`;


// ==========================================================
// CLIENTE PÚBLICO
// ==========================================================

export const apiPublic =
  axios.create({

    baseURL: BASE_URL,

    headers: {

      "Content-Type":
        "application/json",

    },

  });


// ==========================================================
// CLIENTE AUTENTICADO
// ==========================================================

const api =
  axios.create({

    baseURL: BASE_URL,

    headers: {

      "Content-Type":
        "application/json",

    },

  });


// ==========================================================
// RUTAS QUE NO DEBEN RECIBIR ACCESS TOKEN
// ==========================================================

const rutasPublicas = [

  "/auth/login/",

  "/auth/refresh/",

  "/auth/logout/",

  "/auth/recuperaciones/",

];


function esRutaPublica(
  url?: string,
): boolean {

  if (!url) {
    return false;
  }


  return rutasPublicas.some(
    (ruta) =>
      url.includes(ruta),
  );

}


// ==========================================================
// REQUEST INTERCEPTOR
// ==========================================================

api.interceptors.request.use(

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

      config.headers.Authorization =
        `Bearer ${token}`;

    }


    return config;

  },


  (error) =>
    Promise.reject(error),

);


// ==========================================================
// CONTROL DE RENOVACIÓN
// ==========================================================

let renovacionEnCurso:
  Promise<string> | null = null;


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
// RESPONSE INTERCEPTOR
// ==========================================================

type ConfigConReintento =
  InternalAxiosRequestConfig & {

    _retry?: boolean;

  };


api.interceptors.response.use(

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

      !originalRequest ||

      error.response?.status !==
        401 ||

      originalRequest._retry ||

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


      return api(
        originalRequest,
      );

    } catch (refreshError) {

      return Promise.reject(
        refreshError,
      );

    }

  },

);


export default api;