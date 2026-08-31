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
  X,
} from "lucide-react";

import {
  loginRequest,
  logoutRequest,
  refreshRequest,
  verificarSegundoFactorRequest,
  type InicioLoginResponse,
} from "../api/auth.api";

import {
  tokenStorage,
  type InfoSesionLocal,
  type UsuarioSesion,
} from "./tokenStorage";

import {
  segundoFactorStorage,
} from "./segundoFactorStorage";

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
  usuario: UsuarioSesion | null;
  autenticado: boolean;
  infoSesion: InfoSesionLocal;
  eventoSesion: EventoSesion | null;

  login: (
    correo: string,
    password: string,
  ) => Promise<InicioLoginResponse>;

  verificarSegundoFactor: (
    codigo: string,
  ) => Promise<void>;

  logout: () => Promise<void>;
  renovarSesion: () => Promise<void>;

  tieneRol: (
    codigoRol: string,
  ) => boolean;

  tienePermiso: (
    codigoPermiso: string,
  ) => boolean;

  limpiarEventoSesion: () => void;
}


const AuthContext =
  createContext<AuthContextType | undefined>(
    undefined,
  );


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
    fecha: new Date().toISOString(),
  };
}


export function AuthProvider({
  children,
}: AuthProviderProps) {
  const [
    usuario,
    setUsuario,
  ] = useState<UsuarioSesion | null>(
    () => tokenStorage.obtenerUsuario(),
  );

  const [
    autenticado,
    setAutenticado,
  ] = useState<boolean>(
    () => tokenStorage.tieneSesion(),
  );

  const [
    infoSesion,
    setInfoSesion,
  ] = useState<InfoSesionLocal>(
    () => tokenStorage.obtenerInfoSesion(),
  );

  const [
    eventoSesion,
    setEventoSesion,
  ] = useState<EventoSesion | null>(
    null,
  );


  const sincronizarSesion =
    useCallback(
      () => {
        setUsuario(
          tokenStorage.obtenerUsuario(),
        );

        setInfoSesion(
          tokenStorage.obtenerInfoSesion(),
        );

        setAutenticado(
          tokenStorage.tieneSesion(),
        );
      },
      [],
    );


  const limpiarEventoSesion =
    useCallback(
      () => {
        setEventoSesion(null);
      },
      [],
    );


  useEffect(
    () => {
      if (!eventoSesion) {
        return;
      }

      if (
        eventoSesion.tipo === "RENOVADA"
        || eventoSesion.tipo === "VENCIDA"
      ) {
        return;
      }

      const temporizador =
        window.setTimeout(
          () => {
            setEventoSesion(null);
          },
          4200,
        );

      return () => {
        window.clearTimeout(
          temporizador,
        );
      };
    },
    [eventoSesion],
  );


  // ========================================================
  // PRIMER FACTOR: CORREO + CONTRASEÑA
  // NO SE GUARDA JWT TODAVÍA
  // ========================================================

  const login =
    useCallback(
      async (
        correo: string,
        password: string,
      ): Promise<InicioLoginResponse> => {
        tokenStorage.limpiar();
        segundoFactorStorage.limpiar();

        const data =
          await loginRequest({
            correo,
            password,
          });

        segundoFactorStorage.guardar(
          data,
        );

        setUsuario(null);
        setAutenticado(false);
        setInfoSesion(
          tokenStorage.obtenerInfoSesion(),
        );

        return data;
      },
      [],
    );


  // ========================================================
  // SEGUNDO FACTOR: OTP
  // AQUÍ RECIÉN SE CREA LA SESIÓN LOCAL
  // ========================================================

  const verificarSegundoFactor =
    useCallback(
      async (
        codigo: string,
      ): Promise<void> => {
        const pendiente =
          segundoFactorStorage.obtener();

        if (!pendiente) {
          throw new Error(
            "No existe una verificación pendiente. Inicie sesión nuevamente.",
          );
        }

        const data =
          await verificarSegundoFactorRequest({
            desafio_id: pendiente.desafioId,
            codigo,
          });

        tokenStorage.guardarSesion(
          data,
        );

        segundoFactorStorage.limpiar();

        setUsuario(
          data.usuario,
        );

        setInfoSesion(
          tokenStorage.obtenerInfoSesion(),
        );

        setAutenticado(true);

        setEventoSesion(
          crearEvento(
            "LOGIN",
            "Identidad verificada. Sesión iniciada correctamente.",
          ),
        );
      },
      [],
    );


  const renovarSesion =
    useCallback(
      async (): Promise<void> => {
        const refreshToken =
          tokenStorage.obtenerRefreshToken();

        if (!refreshToken) {
          tokenStorage.limpiar();
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

          tokenStorage.actualizarAccessToken(
            data,
          );

          setUsuario(
            tokenStorage.obtenerUsuario(),
          );

          setInfoSesion(
            tokenStorage.obtenerInfoSesion(),
          );

          setAutenticado(true);
        } catch (error) {
          tokenStorage.limpiar();

          setUsuario(null);

          setInfoSesion(
            tokenStorage.obtenerInfoSesion(),
          );

          setAutenticado(false);

          setEventoSesion(
            crearEvento(
              "INVALIDA",
              "La sesión expiró o dejó de ser válida. Inicie sesión nuevamente.",
            ),
          );

          throw error;
        }
      },
      [sincronizarSesion],
    );


  const logout =
    useCallback(
      async (): Promise<void> => {
        const refreshToken =
          tokenStorage.obtenerRefreshToken();

        try {
          if (refreshToken) {
            await logoutRequest(
              refreshToken,
            );
          }
        } catch {
          // Siempre limpiamos el estado local.
        } finally {
          tokenStorage.limpiar();
          segundoFactorStorage.limpiar();

          setUsuario(null);

          setInfoSesion(
            tokenStorage.obtenerInfoSesion(),
          );

          setAutenticado(false);

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


  useEffect(
    () => {
      const manejarRenovacion =
        () => {
          sincronizarSesion();
        };

      const manejarInvalidacion =
        (
          event: Event,
        ) => {
          const customEvent =
            event as CustomEvent<{
              mensaje?: string;
            }>;

          tokenStorage.limpiar();

          setUsuario(null);

          setInfoSesion(
            tokenStorage.obtenerInfoSesion(),
          );

          setAutenticado(false);

          setEventoSesion(
            crearEvento(
              "INVALIDA",
              customEvent.detail?.mensaje
                || "La sesión ya no es válida. Inicie sesión nuevamente.",
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
    [sincronizarSesion],
  );


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
        - Date.now();

      if (milisegundos <= 0) {
        void renovarSesion()
          .catch(
            () => undefined,
          );

        return;
      }

      const temporizador =
        window.setTimeout(
          () => {
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
      [usuario],
    );


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
      [usuario],
    );


  const value =
    useMemo(
      () => ({
        usuario,
        autenticado,
        infoSesion,
        eventoSesion,
        login,
        verificarSegundoFactor,
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
        verificarSegundoFactor,
        logout,
        renovarSesion,
        tieneRol,
        tienePermiso,
        limpiarEventoSesion,
      ],
    );


  const mostrarAviso =
    Boolean(
      eventoSesion
      && eventoSesion.tipo !== "RENOVADA"
      && eventoSesion.tipo !== "VENCIDA",
    );

  const iconoEvento =
    eventoSesion?.tipo === "INVALIDA"
      ? (
        <ShieldAlert size={20} />
      )
      : eventoSesion?.tipo === "CERRADA"
        ? (
          <Info size={20} />
        )
        : (
          <CheckCircle2 size={20} />
        );


  return (
    <AuthContext.Provider
      value={value}
    >
      {children}

      {mostrarAviso && eventoSesion && (
        <div
          className={`
            auth-session-notice
            auth-session-notice--${eventoSesion.tipo.toLowerCase()}
          `}
          role={
            eventoSesion.tipo === "INVALIDA"
              ? "alert"
              : "status"
          }
          aria-live={
            eventoSesion.tipo === "INVALIDA"
              ? "assertive"
              : "polite"
          }
        >
          <div className="auth-session-notice__icon">
            {iconoEvento}
          </div>

          <div className="auth-session-notice__content">
            <strong>
              {eventoSesion.tipo === "INVALIDA"
                ? "Sesión finalizada"
                : eventoSesion.tipo === "CERRADA"
                  ? "Sesión cerrada"
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
            <X size={17} />
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
