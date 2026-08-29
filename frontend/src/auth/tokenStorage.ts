const ACCESS_TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const USER_KEY = "usuario";

const ACCESS_EXPIRES_AT_KEY =
  "access_expires_at";

const REFRESH_EXPIRES_AT_KEY =
  "refresh_expires_at";

const SESSION_ID_KEY =
  "session_id";

const LAST_RENEWAL_KEY =
  "session_last_renewal";


export interface UsuarioSesion {

  id_usuario: string;

  nombre_usuario: string;

  correo: string;

  nombres?: string;

  apellido_paterno?: string | null;

  apellido_materno?: string | null;

  telefono?: string | null;

  estado?: string;

  debe_cambiar_password?: boolean;

  roles: string[];

  permisos: string[];

}


export interface SesionBackend {

  id_sesion: string;

  estado: string;

}


export interface DatosSesion {

  access_token: string;

  refresh_token: string;

  access_expires_in?: number;

  access_expires_at?: string;

  refresh_expires_in?: number;

  refresh_expires_at?: string;

  sesion?: SesionBackend;

  usuario: UsuarioSesion;

}


export interface DatosRenovacion {

  access_token: string;

  access_expires_in?: number;

  access_expires_at?: string;

  sesion?: SesionBackend;

  mensaje?: string;

}


export interface InfoSesionLocal {

  idSesion: string | null;

  accessExpiraEn: string | null;

  refreshExpiraEn: string | null;

  ultimaRenovacion: string | null;

}


function obtenerPayloadJwt(
  token: string | null,
): Record<string, unknown> | null {

  if (!token) {
    return null;
  }


  try {

    const partes =
      token.split(".");


    if (partes.length !== 3) {
      return null;
    }


    const base64 = partes[1]
      .replace(/-/g, "+")
      .replace(/_/g, "/");


    const padding =
      base64.length % 4 === 0
        ? ""
        : "=".repeat(
            4 - (base64.length % 4),
          );


    const texto = decodeURIComponent(

      Array.from(
        atob(base64 + padding),
      )
        .map(
          (caracter) =>
            `%${caracter
              .charCodeAt(0)
              .toString(16)
              .padStart(2, "0")}`,
        )
        .join(""),

    );


    return JSON.parse(texto);

  } catch {

    return null;

  }

}


function obtenerExpiracionJwt(
  token: string | null,
): string | null {

  const payload =
    obtenerPayloadJwt(token);


  const exp =
    payload?.exp;


  if (
    typeof exp !== "number"
  ) {

    return null;

  }


  return new Date(
    exp * 1000,
  ).toISOString();

}


function obtenerSidJwt(
  token: string | null,
): string | null {

  const payload =
    obtenerPayloadJwt(token);


  const sid =
    payload?.sid;


  return typeof sid === "string"
    ? sid
    : null;

}


function fechaVencida(
  fechaIso: string | null,
): boolean {

  if (!fechaIso) {
    return false;
  }


  const tiempo =
    new Date(
      fechaIso,
    ).getTime();


  if (
    Number.isNaN(tiempo)
  ) {

    return false;

  }


  return Date.now() >= tiempo;

}


export const tokenStorage = {


  guardarSesion(
    data: DatosSesion,
  ): void {

    localStorage.setItem(
      ACCESS_TOKEN_KEY,
      data.access_token,
    );


    localStorage.setItem(
      REFRESH_TOKEN_KEY,
      data.refresh_token,
    );


    localStorage.setItem(
      USER_KEY,
      JSON.stringify({

        ...data.usuario,

        roles:
          data.usuario.roles ?? [],

        permisos:
          data.usuario.permisos ?? [],

      }),
    );


    const accessExpiraEn =

      data.access_expires_at ??

      obtenerExpiracionJwt(
        data.access_token,
      );


    const refreshExpiraEn =

      data.refresh_expires_at ??

      obtenerExpiracionJwt(
        data.refresh_token,
      );


    const idSesion =

      data.sesion?.id_sesion ??

      obtenerSidJwt(
        data.access_token,
      );


    if (accessExpiraEn) {

      localStorage.setItem(
        ACCESS_EXPIRES_AT_KEY,
        accessExpiraEn,
      );

    }


    if (refreshExpiraEn) {

      localStorage.setItem(
        REFRESH_EXPIRES_AT_KEY,
        refreshExpiraEn,
      );

    }


    if (idSesion) {

      localStorage.setItem(
        SESSION_ID_KEY,
        idSesion,
      );

    }


    localStorage.setItem(

      LAST_RENEWAL_KEY,

      new Date().toISOString(),

    );

  },


  actualizarAccessToken(
    data: DatosRenovacion,
  ): void {

    localStorage.setItem(
      ACCESS_TOKEN_KEY,
      data.access_token,
    );


    const accessExpiraEn =

      data.access_expires_at ??

      obtenerExpiracionJwt(
        data.access_token,
      );


    if (accessExpiraEn) {

      localStorage.setItem(
        ACCESS_EXPIRES_AT_KEY,
        accessExpiraEn,
      );

    }


    const idSesion =

      data.sesion?.id_sesion ??

      obtenerSidJwt(
        data.access_token,
      );


    if (idSesion) {

      localStorage.setItem(
        SESSION_ID_KEY,
        idSesion,
      );

    }


    localStorage.setItem(

      LAST_RENEWAL_KEY,

      new Date().toISOString(),

    );

  },


  obtenerAccessToken():
    string | null {

    return localStorage.getItem(
      ACCESS_TOKEN_KEY,
    );

  },


  obtenerRefreshToken():
    string | null {

    return localStorage.getItem(
      REFRESH_TOKEN_KEY,
    );

  },


  obtenerUsuario():
    UsuarioSesion | null {

    const usuario =
      localStorage.getItem(
        USER_KEY,
      );


    if (!usuario) {
      return null;
    }


    try {

      const data =
        JSON.parse(
          usuario,
        ) as UsuarioSesion;


      return {

        ...data,

        roles:
          data.roles ?? [],

        permisos:
          data.permisos ?? [],

      };

    } catch {

      return null;

    }

  },


  obtenerInfoSesion():
    InfoSesionLocal {

    return {

      idSesion:

        localStorage.getItem(
          SESSION_ID_KEY,
        ),


      accessExpiraEn:

        localStorage.getItem(
          ACCESS_EXPIRES_AT_KEY,
        ) ??

        obtenerExpiracionJwt(
          this.obtenerAccessToken(),
        ),


      refreshExpiraEn:

        localStorage.getItem(
          REFRESH_EXPIRES_AT_KEY,
        ) ??

        obtenerExpiracionJwt(
          this.obtenerRefreshToken(),
        ),


      ultimaRenovacion:

        localStorage.getItem(
          LAST_RENEWAL_KEY,
        ),

    };

  },


  accessExpirado():
    boolean {

    return fechaVencida(

      this
        .obtenerInfoSesion()
        .accessExpiraEn,

    );

  },


  refreshExpirado():
    boolean {

    return fechaVencida(

      this
        .obtenerInfoSesion()
        .refreshExpiraEn,

    );

  },


  tieneSesion():
    boolean {

    const usuario =
      this.obtenerUsuario();


    const refreshToken =
      this.obtenerRefreshToken();


    return Boolean(

      usuario &&

      refreshToken &&

      !this.refreshExpirado(),

    );

  },


  limpiar(): void {

    localStorage.removeItem(
      ACCESS_TOKEN_KEY,
    );

    localStorage.removeItem(
      REFRESH_TOKEN_KEY,
    );

    localStorage.removeItem(
      USER_KEY,
    );

    localStorage.removeItem(
      ACCESS_EXPIRES_AT_KEY,
    );

    localStorage.removeItem(
      REFRESH_EXPIRES_AT_KEY,
    );

    localStorage.removeItem(
      SESSION_ID_KEY,
    );

    localStorage.removeItem(
      LAST_RENEWAL_KEY,
    );

  },

};