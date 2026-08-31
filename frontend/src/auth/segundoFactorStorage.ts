import type {
  InicioLoginResponse,
} from "../api/auth.api";

const KEY = "segundo_factor_pendiente";

export interface SegundoFactorPendiente {
  desafioId: string;
  correoEnmascarado: string;
  expiraEn: string;
  reenvioDisponibleEn: string;
}

function fechaDesdeSegundos(
  segundos: number,
): string {
  return new Date(
    Date.now() + segundos * 1000,
  ).toISOString();
}

export const segundoFactorStorage = {
  guardar(
    data: InicioLoginResponse,
  ): SegundoFactorPendiente {
    const pendiente: SegundoFactorPendiente = {
      desafioId: data.desafio_id,
      correoEnmascarado: data.correo_enmascarado,
      expiraEn: fechaDesdeSegundos(
        data.expira_en_segundos,
      ),
      reenvioDisponibleEn: fechaDesdeSegundos(
        data.reenvio_disponible_en,
      ),
    };

    sessionStorage.setItem(
      KEY,
      JSON.stringify(pendiente),
    );

    return pendiente;
  },

  obtener(): SegundoFactorPendiente | null {
    const raw = sessionStorage.getItem(KEY);

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw) as SegundoFactorPendiente;
    } catch {
      sessionStorage.removeItem(KEY);
      return null;
    }
  },

  actualizarTiempos(
    expiraEnSegundos: number,
    reenvioEnSegundos: number,
    correoEnmascarado?: string,
  ): SegundoFactorPendiente | null {
    const actual = this.obtener();
    if (!actual) {
      return null;
    }

    const actualizado: SegundoFactorPendiente = {
      ...actual,
      correoEnmascarado:
        correoEnmascarado
        || actual.correoEnmascarado,
      expiraEn: fechaDesdeSegundos(
        expiraEnSegundos,
      ),
      reenvioDisponibleEn: fechaDesdeSegundos(
        reenvioEnSegundos,
      ),
    };

    sessionStorage.setItem(
      KEY,
      JSON.stringify(actualizado),
    );

    return actualizado;
  },

  limpiar(): void {
    sessionStorage.removeItem(KEY);
  },
};
