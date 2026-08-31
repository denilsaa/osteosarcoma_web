import axios from "axios";

import {
  ArrowLeft,
  CheckCircle2,
  LoaderCircle,
  LockKeyhole,
  MailCheck,
  RefreshCw,
  ShieldCheck,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  Link,
  Navigate,
  useLocation,
  useNavigate,
} from "react-router-dom";

import {
  reenviarSegundoFactorRequest,
} from "../../api/auth.api";

import {
  useAuth,
} from "../../auth/AuthProvider";

import {
  segundoFactorStorage,
  type SegundoFactorPendiente,
} from "../../auth/segundoFactorStorage";

import "./Auth.css";


interface LocationState {
  from?: string;
}


function obtenerMensajeError(
  error: unknown,
  fallback: string,
): string {
  if (
    axios.isAxiosError(error)
    && typeof error.response?.data?.error === "string"
  ) {
    return error.response.data.error;
  }

  if (
    error instanceof Error
    && error.message
  ) {
    return error.message;
  }

  return fallback;
}


function segundosRestantes(
  fechaIso: string,
): number {
  return Math.max(
    0,
    Math.ceil(
      (
        new Date(fechaIso).getTime()
        - Date.now()
      ) / 1000,
    ),
  );
}


function formatoTiempo(
  segundos: number,
): string {
  const minutos =
    Math.floor(segundos / 60);

  const resto =
    segundos % 60;

  return `${String(minutos).padStart(2, "0")}:${String(resto).padStart(2, "0")}`;
}


export function VerificarSegundoFactorPage() {
  const navigate = useNavigate();
  const location = useLocation();

  const {
    autenticado,
    verificarSegundoFactor,
  } = useAuth();

  const [
    pendiente,
    setPendiente,
  ] = useState<SegundoFactorPendiente | null>(
    () => segundoFactorStorage.obtener(),
  );

  const [
    digitos,
    setDigitos,
  ] = useState<string[]>(
    ["", "", "", "", "", ""],
  );

  const [
    verificando,
    setVerificando,
  ] = useState(false);

  const [
    reenviando,
    setReenviando,
  ] = useState(false);

  const [
    error,
    setError,
  ] = useState("");

  const [
    mensaje,
    setMensaje,
  ] = useState("");

  const [
    ahora,
    setAhora,
  ] = useState(Date.now());

  const inputsRef =
    useRef<Array<HTMLInputElement | null>>([]);


  useEffect(
    () => {
      const timer =
        window.setInterval(
          () => {
            setAhora(Date.now());
          },
          1000,
        );

      return () => {
        window.clearInterval(timer);
      };
    },
    [],
  );


  const expiracionSegundos =
    useMemo(
      () => pendiente
        ? segundosRestantes(
            pendiente.expiraEn,
          )
        : 0,
      [
        pendiente,
        ahora,
      ],
    );

  const reenvioSegundos =
    useMemo(
      () => pendiente
        ? segundosRestantes(
            pendiente.reenvioDisponibleEn,
          )
        : 0,
      [
        pendiente,
        ahora,
      ],
    );

  const codigo =
    digitos.join("");

  const codigoCompleto =
    /^\d{6}$/.test(codigo);


  if (autenticado) {
    return (
      <Navigate
        to="/dashboard"
        replace
      />
    );
  }

  if (!pendiente) {
    return (
      <Navigate
        to="/login"
        replace
      />
    );
  }


  const cambiarDigito = (
    indice: number,
    valor: string,
  ) => {
    const soloNumero =
      valor.replace(/\D/g, "").slice(-1);

    const nuevos = [...digitos];
    nuevos[indice] = soloNumero;
    setDigitos(nuevos);
    setError("");
    setMensaje("");

    if (
      soloNumero
      && indice < 5
    ) {
      inputsRef.current[indice + 1]?.focus();
    }
  };


  const manejarTecla = (
    indice: number,
    event: React.KeyboardEvent<HTMLInputElement>,
  ) => {
    if (
      event.key === "Backspace"
      && !digitos[indice]
      && indice > 0
    ) {
      inputsRef.current[indice - 1]?.focus();
    }

    if (
      event.key === "ArrowLeft"
      && indice > 0
    ) {
      inputsRef.current[indice - 1]?.focus();
    }

    if (
      event.key === "ArrowRight"
      && indice < 5
    ) {
      inputsRef.current[indice + 1]?.focus();
    }
  };


  const manejarPegado = (
    event: React.ClipboardEvent<HTMLDivElement>,
  ) => {
    const texto =
      event.clipboardData
        .getData("text")
        .replace(/\D/g, "")
        .slice(0, 6);

    if (!texto) {
      return;
    }

    event.preventDefault();

    const nuevos =
      Array.from(
        { length: 6 },
        (_, indice) => texto[indice] || "",
      );

    setDigitos(nuevos);
    setError("");

    inputsRef.current[
      Math.min(texto.length, 6) - 1
    ]?.focus();
  };


  const verificar =
    async (
      event: React.FormEvent<HTMLFormElement>,
    ) => {
      event.preventDefault();
      setError("");
      setMensaje("");

      if (expiracionSegundos <= 0) {
        setError(
          "El código expiró. Solicite uno nuevo o vuelva a iniciar sesión.",
        );
        return;
      }

      if (!codigoCompleto) {
        setError(
          "Ingrese los 6 dígitos del código de verificación.",
        );
        return;
      }

      try {
        setVerificando(true);

        await verificarSegundoFactor(
          codigo,
        );

        const state =
          location.state as LocationState | null;

        navigate(
          state?.from || "/dashboard",
          {
            replace: true,
          },
        );
      } catch (errorActual) {
        setError(
          obtenerMensajeError(
            errorActual,
            "No fue posible verificar el código.",
          ),
        );

        setDigitos(
          ["", "", "", "", "", ""],
        );

        window.setTimeout(
          () => {
            inputsRef.current[0]?.focus();
          },
          50,
        );
      } finally {
        setVerificando(false);
      }
    };


  const reenviar =
    async () => {
      if (
        reenviando
        || reenvioSegundos > 0
      ) {
        return;
      }

      try {
        setReenviando(true);
        setError("");
        setMensaje("");

        const data =
          await reenviarSegundoFactorRequest({
            desafio_id: pendiente.desafioId,
          });

        const actualizado =
          segundoFactorStorage.actualizarTiempos(
            data.expira_en_segundos,
            data.reenvio_disponible_en,
            data.correo_enmascarado,
          );

        setPendiente(actualizado);
        setAhora(Date.now());
        setDigitos(
          ["", "", "", "", "", ""],
        );
        setMensaje(
          "Se envió un nuevo código a su correo institucional.",
        );

        window.setTimeout(
          () => {
            inputsRef.current[0]?.focus();
          },
          50,
        );
      } catch (errorActual) {
        setError(
          obtenerMensajeError(
            errorActual,
            "No fue posible reenviar el código.",
          ),
        );
      } finally {
        setReenviando(false);
      }
    };


  const volverLogin = () => {
    segundoFactorStorage.limpiar();
    navigate(
      "/login",
      {
        replace: true,
      },
    );
  };


  return (
    <main className="twofactor-page">
      <section className="twofactor-shell">
        <button
          type="button"
          className="twofactor-back"
          onClick={volverLogin}
        >
          <ArrowLeft size={17} />
          <span>Volver al inicio de sesión</span>
        </button>

        <div className="twofactor-brand">
          <img
            src="/branding/logo-san-juan.png"
            alt="Clínica San Juan de Dios"
          />
          <div>
            <strong>Verificación de seguridad</strong>
            <span>Clínica San Juan de Dios</span>
          </div>
        </div>

        <div className="twofactor-hero">
          <div className="twofactor-hero__icon">
            <ShieldCheck size={30} />
          </div>

          <span className="twofactor-eyebrow">
            SEGUNDO FACTOR
          </span>

          <h1>Confirme su identidad</h1>

          <p>
            Enviamos un código de 6 dígitos al correo institucional
            <strong> {pendiente.correoEnmascarado}</strong>.
          </p>
        </div>

        {error && (
          <div
            className="twofactor-message twofactor-message--error"
            role="alert"
          >
            <LockKeyhole size={18} />
            <span>{error}</span>
          </div>
        )}

        {mensaje && (
          <div
            className="twofactor-message twofactor-message--success"
            role="status"
          >
            <CheckCircle2 size={18} />
            <span>{mensaje}</span>
          </div>
        )}

        <form
          className="twofactor-form"
          onSubmit={verificar}
        >
          <div
            className="twofactor-code"
            onPaste={manejarPegado}
          >
            {digitos.map(
              (
                digito,
                indice,
              ) => (
                <input
                  key={indice}
                  ref={(elemento) => {
                    inputsRef.current[indice] = elemento;
                  }}
                  type="text"
                  inputMode="numeric"
                  autoComplete={
                    indice === 0
                      ? "one-time-code"
                      : "off"
                  }
                  maxLength={1}
                  value={digito}
                  onChange={(event) =>
                    cambiarDigito(
                      indice,
                      event.target.value,
                    )
                  }
                  onKeyDown={(event) =>
                    manejarTecla(
                      indice,
                      event,
                    )
                  }
                  aria-label={`Dígito ${indice + 1}`}
                  autoFocus={indice === 0}
                />
              ),
            )}
          </div>

          <div className="twofactor-meta">
            <div>
              <span>Código válido por</span>
              <strong
                className={
                  expiracionSegundos <= 60
                    ? "twofactor-time--warning"
                    : ""
                }
              >
                {formatoTiempo(expiracionSegundos)}
              </strong>
            </div>

            <div>
              <span>Destino</span>
              <strong>
                <MailCheck size={14} />
                Correo institucional
              </strong>
            </div>
          </div>

          <button
            type="submit"
            className="twofactor-submit"
            disabled={
              verificando
              || !codigoCompleto
              || expiracionSegundos <= 0
            }
          >
            <span className="twofactor-submit__icon">
              {verificando
                ? (
                  <LoaderCircle
                    size={19}
                    className="login-spinner"
                  />
                )
                : (
                  <ShieldCheck size={19} />
                )}
            </span>

            <span>
              {verificando
                ? "Verificando identidad..."
                : "Verificar y acceder"}
            </span>
          </button>
        </form>

        <div className="twofactor-resend">
          <span>¿No recibió el código?</span>

          <button
            type="button"
            onClick={reenviar}
            disabled={
              reenviando
              || reenvioSegundos > 0
            }
          >
            {reenviando
              ? (
                <LoaderCircle
                  size={15}
                  className="login-spinner"
                />
              )
              : (
                <RefreshCw size={15} />
              )}

            <span>
              {reenvioSegundos > 0
                ? `Reenviar en ${reenvioSegundos}s`
                : "Reenviar código"}
            </span>
          </button>
        </div>

        <div className="twofactor-security">
          <ShieldCheck size={17} />
          <p>
            El JWT de acceso se genera únicamente después de verificar
            correctamente este segundo factor.
          </p>
        </div>

        <Link
          to="/recuperar-contrasena"
          className="twofactor-help"
        >
          ¿Tiene problemas para acceder?
        </Link>
      </section>
    </main>
  );
}
