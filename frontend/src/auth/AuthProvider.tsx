import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
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


// ==========================================================
// TIPOS
// ==========================================================

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
  ) => Promise<InicioLoginResponse>;

  verificarSegundoFactor: (
    codigo: string,
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


// ==========================================================
// CONTEXTO
// ==========================================================

const AuthContext =
  createContext<
    AuthContextType | undefined
  >(undefined);


// ==========================================================
// PROPIEDADES
// ==========================================================

interface AuthProviderProps {
  children: ReactNode;
}


// ==========================================================
// CREAR EVENTO LOCAL
// ==========================================================

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


// ==========================================================
// AUTH PROVIDER
// ==========================================================

export function AuthProvider({
  children,
}: AuthProviderProps) {

  // ========================================================
  // USUARIO
  // ========================================================

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


  // ========================================================
  // ESTADO DE AUTENTICACIÓN
  // ========================================================

  const [
    autenticado,
    setAutenticado,
  ] = useState<boolean>(
    () =>
      tokenStorage
        .tieneSesion(),
  );


  // ========================================================
  // INFORMACIÓN DE LA SESIÓN
  // ========================================================

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


  // ========================================================
  // EVENTO VISUAL DE SESIÓN
  // ========================================================

  const [
    eventoSesion,
    setEventoSesion,
  ] = useState<
    EventoSesion | null
  >(null);


  // ========================================================
  // PROTECCIÓN CONTRA LOGOUT DUPLICADO
  // ========================================================
  //
  // Mientras exista una petición de logout en ejecución,
  // cualquier segundo intento simplemente se ignora.
  //
  // Esto evita:
  //
  // POST /auth/logout/
  // POST /auth/logout/
  //
  // para la misma sesión.
  // ========================================================

  const logoutEnProcesoRef =
    useRef(false);


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
  // LOGIN - PRIMER FACTOR
  // ========================================================
  //
  // Aquí solamente validamos:
  //
  // correo
  // contraseña
  //
  // Si son correctos:
  //
  // se genera desafio_id
  // se guarda temporalmente
  // se espera el OTP
  //
  // TODAVÍA NO existe una sesión autenticada.
  // ========================================================

  const login =
    useCallback(
      async (
        correo: string,
        password: string,
      ): Promise<InicioLoginResponse> => {

        const data =
          await loginRequest({
            correo,
            password,
          });


        // ====================================================
        // GUARDAR DESAFÍO DE SEGUNDO FACTOR
        // ====================================================

        segundoFactorStorage.guardar(
          data,
        );


        // ====================================================
        // NO DEBE EXISTIR SESIÓN LOCAL TODAVÍA
        // ====================================================

        tokenStorage.limpiar();


        setUsuario(
          null,
        );


        setAutenticado(
          false,
        );


        setInfoSesion(
          tokenStorage
            .obtenerInfoSesion(),
        );


        return data;

      },
      [],
    );


  // ========================================================
  // SEGUNDO FACTOR - OTP
  // ========================================================
  //
  // Aquí recién:
  //
  // OTP correcto
  //      ↓
  // access token
  // refresh token
  // usuario
  // sesión
  //      ↓
  // autenticado = true
  //
  // ========================================================

  const verificarSegundoFactor =
    useCallback(
      async (
        codigo: string,
      ): Promise<void> => {

        const pendiente =
          segundoFactorStorage
            .obtener();


        if (!pendiente) {

          throw new Error(
            "No existe una verificación pendiente. Inicie sesión nuevamente.",
          );

        }


        const data =
          await verificarSegundoFactorRequest({

            desafio_id:
              pendiente.desafioId,

            codigo,

          });


        // ====================================================
        // GUARDAR SESIÓN COMPLETA
        // ====================================================

        tokenStorage.guardarSesion(
          data,
        );


        // ====================================================
        // EL DESAFÍO OTP YA NO ES NECESARIO
        // ====================================================

        segundoFactorStorage.limpiar();


        // ====================================================
        // ACTUALIZAR ESTADO REACT
        // ====================================================

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


        // ====================================================
        // NO EXISTE REFRESH TOKEN
        // ====================================================

        if (!refreshToken) {

          tokenStorage.limpiar();

          segundoFactorStorage.limpiar();


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

          // ==================================================
          // SOLICITAR NUEVO ACCESS TOKEN
          // ==================================================

          const data =
            await refreshRequest(
              refreshToken,
            );


          // ==================================================
          // ACTUALIZAR ACCESS TOKEN LOCAL
          // ==================================================

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

        } catch (error) {

          // ==================================================
          // REFRESH INVÁLIDO / EXPIRADO
          // ==================================================

          tokenStorage.limpiar();

          segundoFactorStorage.limpiar();


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
  //
  // PROTECCIÓN IMPORTANTE:
  //
  // Si React, el usuario o algún componente intenta
  // ejecutar logout() dos veces antes de que termine
  // la primera petición:
  //
  // la segunda llamada NO envía otro POST.
  //
  // ========================================================

  const logout =
    useCallback(
      async (): Promise<void> => {

        // ====================================================
        // YA EXISTE UN LOGOUT EN EJECUCIÓN
        // ====================================================

        if (
          logoutEnProcesoRef.current
        ) {
          return;
        }


        // ====================================================
        // BLOQUEAR NUEVAS LLAMADAS
        // ====================================================

        logoutEnProcesoRef.current =
          true;


        const refreshToken =
          tokenStorage
            .obtenerRefreshToken();


        try {

          // ==================================================
          // CERRAR SESIÓN EN BACKEND
          // ==================================================

          if (refreshToken) {

            await logoutRequest(
              refreshToken,
            );

          }

        } catch {

          // ==================================================
          // IMPORTANTE
          // ==================================================
          //
          // Aunque el servidor falle o la sesión ya haya
          // sido invalidada, limpiamos el estado local.
          //
          // ==================================================

        } finally {

          // ==================================================
          // LIMPIAR TOKENS
          // ==================================================

          tokenStorage.limpiar();


          // ==================================================
          // LIMPIAR SEGUNDO FACTOR
          // ==================================================

          segundoFactorStorage.limpiar();


          // ==================================================
          // LIMPIAR USUARIO
          // ==================================================

          setUsuario(
            null,
          );


          // ==================================================
          // ACTUALIZAR INFORMACIÓN LOCAL
          // ==================================================

          setInfoSesion(
            tokenStorage
              .obtenerInfoSesion(),
          );


          // ==================================================
          // YA NO ESTÁ AUTENTICADO
          // ==================================================

          setAutenticado(
            false,
          );


          // ==================================================
          // AVISO
          // ==================================================

          setEventoSesion(

            crearEvento(

              "CERRADA",

              "Sesión cerrada correctamente.",

            ),

          );


          // ==================================================
          // LIBERAR BLOQUEO
          // ==================================================

          logoutEnProcesoRef.current =
            false;

        }

      },
      [],
    );


  // ========================================================
  // EVENTOS GENERADOS POR AXIOS
  // ========================================================

  useEffect(
    () => {

      // ======================================================
      // SESIÓN RENOVADA
      // ======================================================

      const manejarRenovacion =
        () => {

          sincronizarSesion();

        };


      // ======================================================
      // SESIÓN INVALIDADA
      // ======================================================

      const manejarInvalidacion =
        (
          event: Event,
        ) => {

          const customEvent =
            event as CustomEvent<{
              mensaje?: string;
            }>;


          tokenStorage.limpiar();

          segundoFactorStorage.limpiar();


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
  // DETECTAR VENCIMIENTO DEL ACCESS TOKEN
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


      // ======================================================
      // YA EXPIRÓ
      // ======================================================

      if (
        milisegundos <= 0
      ) {

        void renovarSesion()
          .catch(
            () => undefined,
          );


        return;
      }


      // ======================================================
      // PROGRAMAR RENOVACIÓN
      // ======================================================

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
  // VALOR DEL CONTEXTO
  // ========================================================

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


  // ========================================================
  // MOSTRAR AVISOS
  // ========================================================
  //
  // No mostramos mensajes técnicos de renovación automática.
  //
  // Sí mostramos:
  //
  // LOGIN
  // CERRADA
  // INVALIDA
  //
  // ========================================================

  const mostrarAviso =
    Boolean(
      eventoSesion
      &&
      (
        eventoSesion.tipo === "LOGIN"
        ||
        eventoSesion.tipo === "CERRADA"
        ||
        eventoSesion.tipo === "INVALIDA"
      )
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


  // ========================================================
  // RENDER
  // ========================================================

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
          role="status"
          aria-live="polite"
        >

          <div
            className="
              auth-session-notice__icon
            "
          >

            {iconoEvento}

          </div>


          <div
            className="
              auth-session-notice__content
            "
          >

            <strong>

              {
                eventoSesion.tipo ===
                  "INVALIDA"

                  ? "Sesión finalizada"

                  : eventoSesion.tipo ===
                    "CERRADA"

                    ? "Sesión cerrada"

                    : "Acceso correcto"
              }

            </strong>


            <span>

              {eventoSesion.mensaje}

            </span>

          </div>


          <button
            type="button"
            className="
              auth-session-notice__close
            "
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


// ==========================================================
// HOOK
// ==========================================================

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