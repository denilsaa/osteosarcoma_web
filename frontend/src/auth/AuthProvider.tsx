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
  CheckCircle2,
  Info,
  ShieldAlert,
  TriangleAlert,
  X,
} from "lucide-react";

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

import "./AuthProvider.css";


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
  tipo: TipoEventoSesion,
  mensaje: string,
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
  // SINCRONIZAR INFORMACIÓN LOCAL
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
  // LIMPIAR AVISO
  // ========================================================

  const limpiarEventoSesion =
    useCallback(
      () => {

        setEventoSesion(
          null,
        );

      },
      [],
    );


  // ========================================================
  // OCULTAR AVISO AUTOMÁTICAMENTE
  // ========================================================

  useEffect(
    () => {

      if (!eventoSesion) {
        return;
      }


      const temporizador =
        window.setTimeout(
          () => {

            setEventoSesion(
              null,
            );

          },
          4500,
        );


      return () => {

        window.clearTimeout(
          temporizador,
        );

      };

    },
    [
      eventoSesion,
    ],
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
  // RENOVAR SESIÓN MANUAL / INTERNA
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

              "La sesión ya no es válida. Inicie sesión nuevamente.",

            ),

          );


          throw new Error(
            "No existe una sesión válida.",
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

              "La sesión se actualizó correctamente.",

            ),

          );

        } catch (error) {

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

              "INVALIDA",

              "La sesión expiró o dejó de ser válida. Inicie sesión nuevamente.",

            ),

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

        } catch {

          // Aunque el servidor ya haya invalidado
          // la sesión, limpiamos el estado local.

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

              "La sesión venció y fue renovada automáticamente.",

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


          const mensaje =
            customEvent
              .detail
              ?.mensaje;


          setEventoSesion(

            crearEvento(

              "INVALIDA",

              mensaje
                ? "La sesión ya no es válida. Inicie sesión nuevamente."
                : "La sesión ya no es válida. Inicie sesión nuevamente.",

            ),

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
  // DETECTAR VENCIMIENTO DEL ACCESO
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

            "La sesión necesita actualizarse. Espere un momento...",

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

                "La sesión necesita actualizarse. Espere un momento...",

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


  // ========================================================
  // CONTEXTO
  // ========================================================

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


  // ========================================================
  // ICONO DEL AVISO
  // ========================================================

  const iconoEvento =
    eventoSesion?.tipo ===
      "INVALIDA"

      ? (
        <ShieldAlert
          size={20}
        />
      )

      : eventoSesion?.tipo ===
        "VENCIDA"

        ? (
          <TriangleAlert
            size={20}
          />
        )

        : eventoSesion?.tipo ===
          "CERRADA"

          ? (
            <Info
              size={20}
            />
          )

          : (
            <CheckCircle2
              size={20}
            />
          );


  return (

    <AuthContext.Provider
      value={value}
    >

      {children}


      {eventoSesion && (

        <div
          className={`
            auth-session-notice
            auth-session-notice--${eventoSesion.tipo.toLowerCase()}
          `}
          role="status"
          aria-live="polite"
        >

          <div className="auth-session-notice__icon">

            {iconoEvento}

          </div>


          <div className="auth-session-notice__content">

            <strong>

              {eventoSesion.tipo === "INVALIDA"
                ? "Sesión finalizada"
                : eventoSesion.tipo === "VENCIDA"
                  ? "Actualizando sesión"
                  : eventoSesion.tipo === "CERRADA"
                    ? "Sesión cerrada"
                    : eventoSesion.tipo === "RENOVADA"
                      ? "Sesión actualizada"
                      : "Acceso correcto"}

            </strong>


            <span>
              {eventoSesion.mensaje}
            </span>

          </div>


          <button

            type="button"

            className="auth-session-notice__close"

            onClick={
              limpiarEventoSesion
            }

            aria-label="Cerrar aviso"

          >

            <X
              size={17}
            />

          </button>

        </div>

      )}

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