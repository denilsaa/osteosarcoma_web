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

export interface InicioLoginResponse {
  requiere_segundo_factor: true;
  desafio_id: string;
  correo_enmascarado: string;
  expira_en_segundos: number;
  reenvio_disponible_en: number;
  mensaje: string;
}

export interface VerificarSegundoFactorRequest {
  desafio_id: string;
  codigo: string;
}

export interface ReenviarSegundoFactorRequest {
  desafio_id: string;
}

export interface ReenviarSegundoFactorResponse {
  desafio_id: string;
  correo_enmascarado: string;
  expira_en_segundos: number;
  reenvio_disponible_en: number;
  reenvios_restantes: number;
  mensaje: string;
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
  ): Promise<InicioLoginResponse> => {
    const response =
      await apiPublic.post<InicioLoginResponse>(
        "/auth/login/",
        data,
      );

    return response.data;
  };

export const verificarSegundoFactorRequest =
  async (
    data: VerificarSegundoFactorRequest,
  ): Promise<DatosSesion> => {
    const response =
      await apiPublic.post<DatosSesion>(
        "/auth/segundo-factor/verificar/",
        data,
      );

    return response.data;
  };

export const reenviarSegundoFactorRequest =
  async (
    data: ReenviarSegundoFactorRequest,
  ): Promise<ReenviarSegundoFactorResponse> => {
    const response =
      await apiPublic.post<ReenviarSegundoFactorResponse>(
        "/auth/segundo-factor/reenviar/",
        data,
      );

    return response.data;
  };

export const logoutRequest =
  async (
    refresh_token: string,
  ): Promise<LogoutResponse> => {
    const response =
      await apiPublic.post<LogoutResponse>(
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
      await apiPublic.post<DatosRenovacion>(
        "/auth/refresh/",
        {
          refresh_token,
        },
      );

    return response.data;
  };
