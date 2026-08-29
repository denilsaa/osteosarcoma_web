import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  loginRequest,
  logoutRequest,
  refreshRequest,
} from "../api/auth.api";

import {
  tokenStorage,
  type InfoSesionLocal,
  type UsuarioSesion,
} from "./tokenStorage";


export type TipoEventoSesion =

  | "LOGIN"

  | "RENOVADA"

  | "VENCIDA"

  | "CERRADA"

  | "INVALIDA";


export interface EventoSesion {

  tipo: TipoEventoSesion;

  mensaje: string;

  fecha: string;

}


interface AuthContextType {

  usuario:
    UsuarioSesion | null;

  autenticado:
    boolean;

  infoSesion:
    InfoSesionLocal;

  eventoSesion:
    EventoSesion | null;


  login: (
    correo: string,
    password: string,
  ) => Promise<void>;


  logout:
    () => Promise<void>;


  renovarSesion:
    () => Promise<void>;


  tieneRol: (
    codigoRol: string,
  ) => boolean;


  tienePermiso: (
    codigoPermiso: string,
  ) => boolean;


  limpiarEventoSesion:
    () => void;

}


const AuthContext =
  createContext<
    AuthContextType | undefined
  >(undefined);


interface AuthProviderProps {

  children: ReactNode;

}


function crearEvento(

  tipo:
    TipoEventoSesion,

  mensaje:
    string,

): EventoSesion {

  return {

    tipo,

    mensaje,

    fecha:
      new Date()
        .toISOString(),

  };

}


export function AuthProvider({
  children,
}: AuthProviderProps) {


  const [
    usuario,
    setUsuario,
  ] = useState<
    UsuarioSesion | null
  >(
    () =>
      tokenStorage
        .obtenerUsuario(),
  );


  const [
    autenticado,
    setAutenticado,
  ] = useState<boolean>(
    () =>
      tokenStorage
        .tieneSesion(),
  );


  const [
    infoSesion,
    setInfoSesion,
  ] = useState<
    InfoSesionLocal
  >(
    () =>
      tokenStorage
        .obtenerInfoSesion(),
  );


  const [
    eventoSesion,
    setEventoSesion,
  ] = useState<
    EventoSesion | null
  >(null);


  // ========================================================
  // SINCRONIZAR ESTADO
  // ========================================================

  const sincronizarSesion =
    useCallback(
      () => {

        setUsuario(
          tokenStorage
            .obtenerUsuario(),
        );


        setInfoSesion(
          tokenStorage
            .obtenerInfoSesion(),
        );


        setAutenticado(
          tokenStorage
            .tieneSesion(),
        );

      },
      [],
    );


  // ========================================================
  // LOGIN
  // ========================================================

  const login =
    useCallback(

      async (

        correo: string,

        password: string,

      ): Promise<void> => {

        const data =
          await loginRequest({

            correo,

            password,

          });


        tokenStorage
          .guardarSesion(
            data,
          );


        setUsuario(
          data.usuario,
        );


        setInfoSesion(
          tokenStorage
            .obtenerInfoSesion(),
        );


        setAutenticado(
          true,
        );


        setEventoSesion(

          crearEvento(

            "LOGIN",

            "Sesión iniciada correctamente.",

          ),

        );

      },

      [],

    );


  // ========================================================
  // RENOVAR SESIÓN
  // ========================================================

  const renovarSesion =
    useCallback(

      async (): Promise<void> => {

        const refreshToken =

          tokenStorage
            .obtenerRefreshToken();


        if (!refreshToken) {

          tokenStorage
            .limpiar();


          sincronizarSesion();


          setEventoSesion(

            crearEvento(

              "INVALIDA",

              "No existe una sesión válida para renovar.",

            ),

          );


          throw new Error(
            "No existe refresh token.",
          );

        }


        try {

          const data =

            await refreshRequest(
              refreshToken,
            );


          tokenStorage
            .actualizarAccessToken(
              data,
            );


          setInfoSesion(

            tokenStorage
              .obtenerInfoSesion(),

          );


          setAutenticado(
            true,
          );


          setEventoSesion(

            crearEvento(

              "RENOVADA",

              data.mensaje ??

                "Sesión renovada correctamente.",

            ),

          );

        } catch (error) {

          tokenStorage
            .limpiar();


          sincronizarSesion();


          setEventoSesion(

            crearEvento(

              "INVALIDA",

              "La sesión expiró, fue cerrada o ya no es válida.",

            ),

          );


          sessionStorage.setItem(

            "auth_message",

            "La sesión expiró, fue cerrada o ya no es válida. Inicie sesión nuevamente.",

          );


          throw error;

        }

      },

      [
        sincronizarSesion,
      ],

    );


  // ========================================================
  // LOGOUT
  // ========================================================

  const logout =
    useCallback(

      async (): Promise<void> => {

        const refreshToken =

          tokenStorage
            .obtenerRefreshToken();


        try {

          if (refreshToken) {

            await logoutRequest(
              refreshToken,
            );

          }

        } finally {

          tokenStorage
            .limpiar();


          setUsuario(
            null,
          );


          setInfoSesion(

            tokenStorage
              .obtenerInfoSesion(),

          );


          setAutenticado(
            false,
          );


          setEventoSesion(

            crearEvento(

              "CERRADA",

              "Sesión cerrada correctamente.",

            ),

          );


          sessionStorage.setItem(

            "auth_message",

            "Sesión cerrada correctamente.",

          );

        }

      },

      [],

    );


  // ========================================================
  // EVENTOS GENERADOS POR AXIOS
  // ========================================================

  useEffect(
    () => {


      const manejarRenovacion =
        () => {

          sincronizarSesion();


          setEventoSesion(

            crearEvento(

              "RENOVADA",

              "El access token venció y la sesión fue renovada automáticamente.",

            ),

          );

        };


      const manejarInvalidacion =
        (
          event: Event,
        ) => {

          const customEvent =

            event as CustomEvent<{
              mensaje?: string;
            }>;


          tokenStorage
            .limpiar();


          sincronizarSesion();


          const mensaje =

            customEvent
              .detail
              ?.mensaje ??

            "La sesión fue cerrada o ya no es válida.";


          setEventoSesion(

            crearEvento(

              "INVALIDA",

              mensaje,

            ),

          );


          sessionStorage.setItem(

            "auth_message",

            `${mensaje} Inicie sesión nuevamente.`,

          );

        };


      window.addEventListener(

        "auth:session-renewed",

        manejarRenovacion,

      );


      window.addEventListener(

        "auth:session-invalidated",

        manejarInvalidacion,

      );


      return () => {

        window.removeEventListener(

          "auth:session-renewed",

          manejarRenovacion,

        );


        window.removeEventListener(

          "auth:session-invalidated",

          manejarInvalidacion,

        );

      };

    },

    [
      sincronizarSesion,
    ],

  );


  // ========================================================
  // DETECTAR EXPIRACIÓN DEL ACCESS TOKEN
  // ========================================================

  useEffect(
    () => {


      if (!autenticado) {
        return;
      }


      const fechaExpiracion =

        tokenStorage
          .obtenerInfoSesion()
          .accessExpiraEn;


      if (!fechaExpiracion) {
        return;
      }


      const milisegundos =

        new Date(
          fechaExpiracion,
        ).getTime()

        -

        Date.now();


      if (
        milisegundos <= 0
      ) {

        setEventoSesion(

          crearEvento(

            "VENCIDA",

            "El access token venció. Renovando sesión...",

          ),

        );


        void renovarSesion()
          .catch(
            () => undefined,
          );


        return;

      }


      const temporizador =

        window.setTimeout(

          () => {

            setEventoSesion(

              crearEvento(

                "VENCIDA",

                "El access token venció. Renovando sesión...",

              ),

            );


            void renovarSesion()
              .catch(
                () => undefined,
              );

          },

          milisegundos + 250,

        );


      return () => {

        window.clearTimeout(
          temporizador,
        );

      };

    },

    [

      autenticado,

      infoSesion.accessExpiraEn,

      renovarSesion,

    ],

  );


  // ========================================================
  // ROLES
  // ========================================================

  const tieneRol =
    useCallback(

      (
        codigoRol: string,
      ): boolean => {

        return Boolean(

          usuario
            ?.roles
            ?.includes(
              codigoRol,
            ),

        );

      },

      [
        usuario,
      ],

    );


  // ========================================================
  // PERMISOS
  // ========================================================

  const tienePermiso =
    useCallback(

      (
        codigoPermiso: string,
      ): boolean => {

        return Boolean(

          usuario
            ?.permisos
            ?.includes(
              codigoPermiso,
            ),

        );

      },

      [
        usuario,
      ],

    );


  const limpiarEventoSesion =
    useCallback(
      () => {

        setEventoSesion(
          null,
        );

      },
      [],
    );


  const value =
    useMemo(

      () => ({

        usuario,

        autenticado,

        infoSesion,

        eventoSesion,

        login,

        logout,

        renovarSesion,

        tieneRol,

        tienePermiso,

        limpiarEventoSesion,

      }),

      [

        usuario,

        autenticado,

        infoSesion,

        eventoSesion,

        login,

        logout,

        renovarSesion,

        tieneRol,

        tienePermiso,

        limpiarEventoSesion,

      ],

    );


  return (

    <AuthContext.Provider
      value={value}
    >

      {children}

    </AuthContext.Provider>

  );

}


export function useAuth():
  AuthContextType {

  const context =
    useContext(
      AuthContext,
    );


  if (!context) {

    throw new Error(

      "useAuth debe utilizarse dentro de AuthProvider",

    );

  }


  return context;

}