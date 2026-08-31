import {
  AlertCircle,
  ArrowLeft,
  BadgeCheck,
  CheckCircle2,
  Circle,
  Eye,
  EyeOff,
  LoaderCircle,
  Save,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";

import { useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  crearOncologo,
  normalizarErroresApi,
  type CrearOncologoPayload,
  type ErroresFormulario,
} from "../../api/oncologos.api";

import "./UsuariosPage.css";

interface FormularioOncologo extends CrearOncologoPayload {
  confirmar_password: string;
}

type CampoFormulario = keyof FormularioOncologo;

type RequisitoPassword = {
  texto: string;
  cumple: boolean;
};

const formularioInicial: FormularioOncologo = {
  nombres: "",
  apellido_paterno: "",
  apellido_materno: "",
  correo: "",
  nombre_usuario: "",
  telefono: "",
  password: "",
  confirmar_password: "",
  matricula_profesional: "",
  especialidad: "Oncología",
  subespecialidad: "",
  telefono_institucional: "",
};

const PATRON_CORREO = /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;
const PATRON_USUARIO = /^[A-Za-z][A-Za-z0-9._-]{2,29}$/;
const PATRON_MATRICULA = /^[A-Za-z0-9]+(?:[./-][A-Za-z0-9]+)*$/;
const PATRON_TELEFONO_PERSONAL = /^[67]\d{7}$/;
const PATRON_TELEFONO_INSTITUCIONAL = /^\d{8}$/;
const PATRON_ESPECIAL = /[!@#$%^&*()_+\-=[\]{};':"\\|,.<>/?`~]/;

const CONTRASENAS_COMUNES = new Set([
  "12345678",
  "123456789",
  "password",
  "password123",
  "qwerty123",
  "admin123",
  "oncologo123",
]);

function soloDigitos(valor: string, maximo = 8): string {
  return valor.replace(/\D/g, "").slice(0, maximo);
}

function normalizarMatricula(valor: string): string {
  return valor
    .toUpperCase()
    .replace(/\s+/g, "")
    .replace(/[^A-Z0-9./-]/g, "")
    .slice(0, 30);
}

function evaluarPassword(
  password: string,
  nombreUsuario: string,
): RequisitoPassword[] {
  const passwordMinuscula = password.toLowerCase();
  const usuarioMinuscula = nombreUsuario.trim().toLowerCase();

  return [
    {
      texto: "Entre 8 y 64 caracteres",
      cumple: password.length >= 8 && password.length <= 64,
    },
    {
      texto: "Al menos una letra mayúscula",
      cumple: /[A-Z]/.test(password),
    },
    {
      texto: "Al menos una letra minúscula",
      cumple: /[a-z]/.test(password),
    },
    {
      texto: "Al menos un número",
      cumple: /\d/.test(password),
    },
    {
      texto: "Al menos un carácter especial (!@#$...) ",
      cumple: PATRON_ESPECIAL.test(password),
    },
    {
      texto: "Sin espacios",
      cumple: password.length > 0 && !/\s/.test(password),
    },
    {
      texto: "No debe contener el nombre de usuario",
      cumple:
        password.length > 0 &&
        (usuarioMinuscula.length < 3 ||
          !passwordMinuscula.includes(usuarioMinuscula)),
    },
    {
      texto: "No debe ser una contraseña común",
      cumple:
        password.length > 0 &&
        !CONTRASENAS_COMUNES.has(passwordMinuscula),
    },
  ];
}

function validarCampo(
  campo: CampoFormulario,
  formulario: FormularioOncologo,
): string | undefined {
  const valor = formulario[campo];
  const texto = typeof valor === "string" ? valor.trim() : "";

  switch (campo) {
    case "nombres":
      if (texto.length < 2) return "Ingrese los nombres del oncólogo.";
      return undefined;

    case "apellido_paterno":
      if (texto.length < 2) return "Ingrese el apellido paterno.";
      return undefined;

    case "telefono":
      if (!texto) return undefined;
      if (!/^\d+$/.test(texto)) return "El teléfono personal solo puede contener números.";
      if (texto.length !== 8) return "El teléfono personal debe tener exactamente 8 dígitos.";
      if (!PATRON_TELEFONO_PERSONAL.test(texto)) {
        return "El teléfono personal debe comenzar con 6 o 7.";
      }
      return undefined;

    case "matricula_profesional":
      if (!texto) return "La matrícula profesional es obligatoria.";
      if (texto.length < 4 || texto.length > 30) {
        return "La matrícula debe tener entre 4 y 30 caracteres.";
      }
      if (!PATRON_MATRICULA.test(texto)) {
        return "Use solo letras, números y separadores válidos: guion (-), punto (.) o barra (/).";
      }
      return undefined;

    case "telefono_institucional":
      if (!texto) return undefined;
      if (!/^\d+$/.test(texto)) {
        return "El teléfono institucional solo puede contener números.";
      }
      if (!PATRON_TELEFONO_INSTITUCIONAL.test(texto)) {
        return "El teléfono institucional debe tener exactamente 8 dígitos.";
      }
      return undefined;

    case "correo":
      if (!texto) return "El correo institucional es obligatorio.";
      if (texto.length > 150) return "El correo no puede superar 150 caracteres.";
      if (/\s/.test(texto)) return "El correo no puede contener espacios.";
      if (texto.includes("..")) return "El correo no puede contener dos puntos consecutivos.";
      if (!PATRON_CORREO.test(texto)) return "Ingrese un correo electrónico válido.";
      return undefined;

    case "nombre_usuario":
      if (!texto) return "El nombre de usuario es obligatorio.";
      if (texto.length < 3 || texto.length > 30) {
        return "El nombre de usuario debe tener entre 3 y 30 caracteres.";
      }
      if (/\s/.test(texto)) return "El nombre de usuario no puede contener espacios.";
      if (!/^[A-Za-z]/.test(texto)) return "El nombre de usuario debe comenzar con una letra.";
      if (!PATRON_USUARIO.test(texto)) {
        return "Use solo letras, números, punto (.), guion (-) o guion bajo (_).";
      }
      return undefined;

    case "password": {
      if (!formulario.password) return "La contraseña temporal es obligatoria.";
      const requisitos = evaluarPassword(
        formulario.password,
        formulario.nombre_usuario,
      );
      if (!requisitos.every((requisito) => requisito.cumple)) {
        return "La contraseña todavía no cumple todos los requisitos de seguridad.";
      }
      return undefined;
    }

    case "confirmar_password":
      if (!formulario.confirmar_password) return "Confirme la contraseña temporal.";
      if (formulario.password !== formulario.confirmar_password) {
        return "Las contraseñas no coinciden.";
      }
      return undefined;

    default:
      return undefined;
  }
}

export function NuevoUsuarioPage() {
  const navigate = useNavigate();

  const [formulario, setFormulario] = useState<FormularioOncologo>(formularioInicial);
  const [errores, setErrores] = useState<ErroresFormulario>({});
  const [guardando, setGuardando] = useState(false);
  const [mostrarPassword, setMostrarPassword] = useState(false);
  const [mensajeExito, setMensajeExito] = useState("");
  const [camposTocados, setCamposTocados] = useState<Partial<Record<CampoFormulario, boolean>>>({});

  const requisitosPassword = useMemo(
    () => evaluarPassword(formulario.password, formulario.nombre_usuario),
    [formulario.password, formulario.nombre_usuario],
  );

  const passwordSegura = requisitosPassword.every((requisito) => requisito.cumple);

  const actualizarCampo = (campo: CampoFormulario, valorOriginal: string) => {
    let valor = valorOriginal;

    if (campo === "telefono" || campo === "telefono_institucional") {
      valor = soloDigitos(valorOriginal);
    }

    if (campo === "matricula_profesional") {
      valor = normalizarMatricula(valorOriginal);
    }

    if (campo === "correo" || campo === "nombre_usuario") {
      valor = valorOriginal.toLowerCase();
    }

    const siguienteFormulario: FormularioOncologo = {
      ...formulario,
      [campo]: valor,
    };

    setFormulario(siguienteFormulario);

    setErrores((actual) => {
      const nuevo = { ...actual };
      delete nuevo.general;

      if (camposTocados[campo]) {
        const errorCampo = validarCampo(campo, siguienteFormulario);
        if (errorCampo) nuevo[campo] = errorCampo;
        else delete nuevo[campo];
      } else {
        delete nuevo[campo];
      }

      if (
        campo === "password" ||
        (campo === "confirmar_password" && camposTocados.confirmar_password)
      ) {
        const errorConfirmacion = validarCampo("confirmar_password", siguienteFormulario);
        if (siguienteFormulario.confirmar_password && errorConfirmacion) {
          nuevo.confirmar_password = errorConfirmacion;
        } else if (siguienteFormulario.confirmar_password) {
          delete nuevo.confirmar_password;
        }
      }

      if (campo === "nombre_usuario" && camposTocados.password && siguienteFormulario.password) {
        const errorPassword = validarCampo("password", siguienteFormulario);
        if (errorPassword) nuevo.password = errorPassword;
        else delete nuevo.password;
      }

      return nuevo;
    });
  };

  const tocarCampo = (campo: CampoFormulario) => {
    setCamposTocados((actual) => ({ ...actual, [campo]: true }));

    const errorCampo = validarCampo(campo, formulario);
    setErrores((actual) => {
      const nuevo = { ...actual };
      if (errorCampo) nuevo[campo] = errorCampo;
      else delete nuevo[campo];
      return nuevo;
    });
  };

  const validarFormulario = (): ErroresFormulario => {
    const nuevos: ErroresFormulario = {};
    const camposAValidar: CampoFormulario[] = [
      "nombres",
      "apellido_paterno",
      "telefono",
      "matricula_profesional",
      "telefono_institucional",
      "correo",
      "nombre_usuario",
      "password",
      "confirmar_password",
    ];

    camposAValidar.forEach((campo) => {
      const errorCampo = validarCampo(campo, formulario);
      if (errorCampo) nuevos[campo] = errorCampo;
    });

    return nuevos;
  };

  const registrar = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    setCamposTocados({
      nombres: true,
      apellido_paterno: true,
      telefono: true,
      matricula_profesional: true,
      telefono_institucional: true,
      correo: true,
      nombre_usuario: true,
      password: true,
      confirmar_password: true,
    });

    const erroresLocales = validarFormulario();

    if (Object.keys(erroresLocales).length > 0) {
      setErrores(erroresLocales);
      return;
    }

    try {
      setGuardando(true);
      setErrores({});
      setMensajeExito("");

      const { confirmar_password: _confirmarPassword, ...payload } = formulario;

      const response = await crearOncologo({
        ...payload,
        nombres: payload.nombres.trim(),
        apellido_paterno: payload.apellido_paterno.trim(),
        apellido_materno: payload.apellido_materno?.trim() || null,
        correo: payload.correo.trim().toLowerCase(),
        nombre_usuario: payload.nombre_usuario.trim().toLowerCase(),
        telefono: payload.telefono?.trim() || null,
        matricula_profesional: payload.matricula_profesional?.trim().toUpperCase() || null,
        especialidad: payload.especialidad?.trim() || null,
        subespecialidad: payload.subespecialidad?.trim() || null,
        telefono_institucional: payload.telefono_institucional?.trim() || null,
      });

      setMensajeExito(response.mensaje);

      window.setTimeout(() => {
        navigate("/usuarios", { replace: true });
      }, 900);
    } catch (error) {
      setErrores(normalizarErroresApi(error));
    } finally {
      setGuardando(false);
    }
  };

  return (
    <div className="oncologists-page">
      <button
        type="button"
        className="oncologist-form-back"
        onClick={() => navigate("/usuarios")}
      >
        <ArrowLeft size={17} />
        Volver a oncólogos
      </button>

      <section className="oncologists-header">
        <div>
          <span className="oncologists-header__eyebrow">Administración</span>
          <h1>Registrar oncólogo</h1>
          <p>Cree una cuenta institucional para un nuevo médico oncólogo.</p>
        </div>
      </section>

      {mensajeExito && (
        <div className="oncologists-alert oncologists-alert--success">
          <BadgeCheck size={18} />
          {mensajeExito}
        </div>
      )}

      {errores.general && (
        <div className="oncologists-alert oncologists-alert--error">
          <AlertCircle size={18} />
          {errores.general}
        </div>
      )}

      <form className="oncologist-form-card" onSubmit={registrar} noValidate>
        <div className="oncologist-form-section-title">
          <div><UserRound size={19} /></div>
          <span>
            <strong>Datos personales</strong>
            <small>Información básica de identificación.</small>
          </span>
        </div>

        <div className="oncologist-form-grid">
          <label>
            <span>Nombres *</span>
            <input
              value={formulario.nombres}
              onChange={(event) => actualizarCampo("nombres", event.target.value)}
              onBlur={() => tocarCampo("nombres")}
              placeholder="Ej. Andrea María"
              maxLength={100}
              aria-invalid={Boolean(errores.nombres)}
            />
            {errores.nombres && <small>{errores.nombres}</small>}
          </label>

          <label>
            <span>Apellido paterno *</span>
            <input
              value={formulario.apellido_paterno}
              onChange={(event) => actualizarCampo("apellido_paterno", event.target.value)}
              onBlur={() => tocarCampo("apellido_paterno")}
              placeholder="Ej. López"
              maxLength={80}
              aria-invalid={Boolean(errores.apellido_paterno)}
            />
            {errores.apellido_paterno && <small>{errores.apellido_paterno}</small>}
          </label>

          <label>
            <span>Apellido materno</span>
            <input
              value={formulario.apellido_materno ?? ""}
              onChange={(event) => actualizarCampo("apellido_materno", event.target.value)}
              placeholder="Ej. Vargas"
              maxLength={80}
            />
          </label>

          <label>
            <span>Teléfono personal</span>
            <input
              value={formulario.telefono ?? ""}
              onChange={(event) => actualizarCampo("telefono", event.target.value)}
              onBlur={() => tocarCampo("telefono")}
              placeholder="Ej. 71234567"
              inputMode="numeric"
              autoComplete="tel"
              maxLength={8}
              aria-invalid={Boolean(errores.telefono)}
            />
            {!errores.telefono && (
              <small className="oncologist-field-help">
                Opcional. 8 dígitos y debe comenzar con 6 o 7.
              </small>
            )}
            {errores.telefono && <small>{errores.telefono}</small>}
          </label>
        </div>

        <div className="oncologist-form-divider" />

        <div className="oncologist-form-section-title">
          <div><Stethoscope size={19} /></div>
          <span>
            <strong>Información profesional</strong>
            <small>Datos institucionales del especialista.</small>
          </span>
        </div>

        <div className="oncologist-form-grid">
          <label>
            <span>Matrícula profesional *</span>
            <input
              value={formulario.matricula_profesional ?? ""}
              onChange={(event) => actualizarCampo("matricula_profesional", event.target.value)}
              onBlur={() => tocarCampo("matricula_profesional")}
              placeholder="Ej. MED-5487"
              maxLength={30}
              autoCapitalize="characters"
              aria-invalid={Boolean(errores.matricula_profesional)}
            />
            {!errores.matricula_profesional && (
              <small className="oncologist-field-help">
                Entre 4 y 30 caracteres. Letras, números, -, . o /.
              </small>
            )}
            {errores.matricula_profesional && <small>{errores.matricula_profesional}</small>}
          </label>

          <label>
            <span>Especialidad</span>
            <input
              value={formulario.especialidad ?? ""}
              onChange={(event) => actualizarCampo("especialidad", event.target.value)}
              placeholder="Oncología"
              maxLength={120}
            />
          </label>

          <label>
            <span>Subespecialidad</span>
            <input
              value={formulario.subespecialidad ?? ""}
              onChange={(event) => actualizarCampo("subespecialidad", event.target.value)}
              placeholder="Opcional"
              maxLength={120}
            />
          </label>

          <label>
            <span>Teléfono institucional</span>
            <input
              value={formulario.telefono_institucional ?? ""}
              onChange={(event) => actualizarCampo("telefono_institucional", event.target.value)}
              onBlur={() => tocarCampo("telefono_institucional")}
              placeholder="Ej. 22123456"
              inputMode="numeric"
              autoComplete="tel"
              maxLength={8}
              aria-invalid={Boolean(errores.telefono_institucional)}
            />
            {!errores.telefono_institucional && (
              <small className="oncologist-field-help">
                Opcional. Debe contener exactamente 8 dígitos.
              </small>
            )}
            {errores.telefono_institucional && <small>{errores.telefono_institucional}</small>}
          </label>
        </div>

        <div className="oncologist-form-divider" />

        <div className="oncologist-form-section-title">
          <div><ShieldCheck size={19} /></div>
          <span>
            <strong>Acceso al sistema</strong>
            <small>Credenciales institucionales del nuevo oncólogo.</small>
          </span>
        </div>

        <div className="oncologist-form-grid">
          <label>
            <span>Correo institucional *</span>
            <input
              type="email"
              value={formulario.correo}
              onChange={(event) => actualizarCampo("correo", event.target.value)}
              onBlur={() => tocarCampo("correo")}
              placeholder="oncologo@hospital.com"
              maxLength={150}
              autoComplete="email"
              aria-invalid={Boolean(errores.correo)}
            />
            {!errores.correo && (
              <small className="oncologist-field-help">
                Debe tener un formato válido, por ejemplo nombre@institucion.com.
              </small>
            )}
            {errores.correo && <small>{errores.correo}</small>}
          </label>

          <label>
            <span>Nombre de usuario *</span>
            <input
              value={formulario.nombre_usuario}
              onChange={(event) => actualizarCampo("nombre_usuario", event.target.value)}
              onBlur={() => tocarCampo("nombre_usuario")}
              placeholder="Ej. alopez"
              maxLength={30}
              autoComplete="username"
              aria-invalid={Boolean(errores.nombre_usuario)}
            />
            {!errores.nombre_usuario && (
              <small className="oncologist-field-help">
                3 a 30 caracteres. Debe iniciar con letra; admite . _ y -.
              </small>
            )}
            {errores.nombre_usuario && <small>{errores.nombre_usuario}</small>}
          </label>

          <label className="oncologist-password-field">
            <span>Contraseña temporal *</span>
            <div className="oncologist-password">
              <input
                type={mostrarPassword ? "text" : "password"}
                value={formulario.password}
                onChange={(event) => actualizarCampo("password", event.target.value)}
                onBlur={() => tocarCampo("password")}
                placeholder="Cree una contraseña segura"
                maxLength={64}
                autoComplete="new-password"
                aria-invalid={Boolean(errores.password)}
              />
              <button
                type="button"
                onClick={() => setMostrarPassword((actual) => !actual)}
                aria-label={mostrarPassword ? "Ocultar contraseña" : "Mostrar contraseña"}
              >
                {mostrarPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>

            <div className="oncologist-password-rules" aria-live="polite">
              <div className="oncologist-password-rules__header">
                <strong>Seguridad de la contraseña</strong>
                <span className={passwordSegura ? "is-valid" : ""}>
                  {passwordSegura ? "Segura" : "Requisitos pendientes"}
                </span>
              </div>

              <div className="oncologist-password-rules__grid">
                {requisitosPassword.map((requisito) => (
                  <span
                    key={requisito.texto}
                    className={requisito.cumple ? "is-valid" : ""}
                  >
                    {requisito.cumple ? <CheckCircle2 size={14} /> : <Circle size={14} />}
                    {requisito.texto}
                  </span>
                ))}
              </div>
            </div>

            {errores.password && <small>{errores.password}</small>}
          </label>

          <label>
            <span>Confirmar contraseña *</span>
            <input
              type={mostrarPassword ? "text" : "password"}
              value={formulario.confirmar_password}
              onChange={(event) => actualizarCampo("confirmar_password", event.target.value)}
              onBlur={() => tocarCampo("confirmar_password")}
              placeholder="Repita la contraseña"
              maxLength={64}
              autoComplete="new-password"
              aria-invalid={Boolean(errores.confirmar_password)}
            />
            {formulario.confirmar_password && !errores.confirmar_password && formulario.password === formulario.confirmar_password && (
              <small className="oncologist-field-success">Las contraseñas coinciden.</small>
            )}
            {errores.confirmar_password && <small>{errores.confirmar_password}</small>}
          </label>
        </div>

        <div className="oncologist-form-note">
          <ShieldCheck size={18} />
          <div>
            <strong>Contraseña temporal</strong>
            <span>
              La cuenta se registrará como oncólogo activo. La contraseña se almacena mediante hash en el servidor y el usuario quedará marcado para realizar su cambio posterior.
            </span>
          </div>
        </div>

        <footer className="oncologist-form-footer">
          <button
            type="button"
            className="oncologists-secondary-button"
            onClick={() => navigate("/usuarios")}
            disabled={guardando}
          >
            Cancelar
          </button>

          <button
            type="submit"
            className="oncologists-primary-button"
            disabled={guardando}
          >
            <span className="oncologists-button-icon" aria-hidden="true">
              {guardando ? (
                <LoaderCircle size={17} className="oncologists-spin" />
              ) : (
                <Save size={17} />
              )}
            </span>
            <span>{guardando ? "Registrando..." : "Registrar oncólogo"}</span>
          </button>
        </footer>
      </form>
    </div>
  );
}
