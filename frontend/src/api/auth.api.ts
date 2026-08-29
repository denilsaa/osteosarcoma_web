import {
  apiPublic,
} from "./axios";

import type {
  DatosRenovacion,
  DatosSesion,
} from "../auth/tokenStorage";


export interface LoginRequest {

  correo: string;

  password: string;

}


export interface LogoutResponse {

  mensaje: string;

  sesion?: {

    id_sesion: string;

    estado: string;

  };

}


export const loginRequest =
  async (
    data: LoginRequest,
  ): Promise<DatosSesion> => {

    const response =
      await apiPublic
        .post<DatosSesion>(

          "/auth/login/",

          data,

        );


    return response.data;

  };


export const logoutRequest =
  async (
    refresh_token: string,
  ): Promise<LogoutResponse> => {

    const response =
      await apiPublic
        .post<LogoutResponse>(

          "/auth/logout/",

          {

            refresh_token,

          },

        );


    return response.data;

  };


export const refreshRequest =
  async (
    refresh_token: string,
  ): Promise<DatosRenovacion> => {

    const response =
      await apiPublic
        .post<DatosRenovacion>(

          "/auth/refresh/",

          {

            refresh_token,

          },

        );


    return response.data;

  };