import {
  AlertCircle,
  ArrowLeft,
  BadgeCheck,
  CheckCircle2,
  CircleAlert,
  IdCard,
  LoaderCircle,
  MailCheck,
  Save,
  ShieldCheck,
  Stethoscope,
  UserRound,
} from "lucide-react";

import {
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  crearOncologo,
  normalizarErroresApi,
  verificarCiOncologo,
  verificarCorreoOncologo,
  verificarMatriculaOncologo,
  type CrearOncologoPayload,
  type ErroresFormulario,
  type ExpedicionBolivia,
  type RolOncologia,
} from "../../api/oncologos.api";

import "./UsuariosPage.css";


/* =========================================================
   TIPOS
   ========================================================= */

interface FormularioOncologo {

  nombres: string;

  apellido_paterno: string;

  apellido_materno: string;

  telefono: string;

  ci_numero: string;

  ci_complemento: string;

  ci_expedido: ExpedicionBolivia;

  correo: string;

  matricula_profesional: string;

  subespecialidad: string;

  telefono_institucional: string;

  rol_codigo: RolOncologia;

}


type CampoFormulario =
  keyof FormularioOncologo;


type EstadoVerificacion =
  | "idle"
  | "checking"
  | "available"
  | "duplicate"
  | "error";


interface Verificaciones {

  ci: EstadoVerificacion;

  matricula: EstadoVerificacion;

  correo: EstadoVerificacion;

}


/* =========================================================
   FORMULARIO INICIAL
   ========================================================= */

const formularioInicial:
  FormularioOncologo = {

  nombres: "",

  apellido_paterno: "",

  apellido_materno: "",

  telefono: "",

  ci_numero: "",

  ci_complemento: "",

  ci_expedido: "LP",

  correo: "",

  matricula_profesional: "",

  subespecialidad:
    "Oncología médica",

  telefono_institucional: "",

  rol_codigo:
    "ONCOLOGO",

};


/* =========================================================
   CATÁLOGOS
   ========================================================= */

const DEPARTAMENTOS: Array<{
  codigo: ExpedicionBolivia;
  nombre: string;
}> = [

  {
    codigo: "LP",
    nombre: "La Paz",
  },

  {
    codigo: "CB",
    nombre: "Cochabamba",
  },

  {
    codigo: "SC",
    nombre: "Santa Cruz",
  },

  {
    codigo: "OR",
    nombre: "Oruro",
  },

  {
    codigo: "PT",
    nombre: "Potosí",
  },

  {
    codigo: "CH",
    nombre: "Chuquisaca",
  },

  {
    codigo: "TJ",
    nombre: "Tarija",
  },

  {
    codigo: "BE",
    nombre: "Beni",
  },

  {
    codigo: "PD",
    nombre: "Pando",
  },

];


const SUBESPECIALIDADES = [

  "Oncología médica",

  "Oncología pediátrica",

  "Oncología quirúrgica",

  "Oncología radioterápica",

  "Oncología ortopédica",

  "Otra",

];


/* =========================================================
   PATRONES
   ========================================================= */

const PATRON_CORREO =
  /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i;


const PATRON_MATRICULA =
  /^[A-Z0-9]+(?:[./-][A-Z0-9]+)*$/;


const PATRON_TELEFONO_PERSONAL =
  /^[67]\d{7}$/;


const PATRON_TELEFONO_INSTITUCIONAL =
  /^\d{8}$/;


const PATRON_CI =
  /^\d{4,20}$/;


const PATRON_COMPLEMENTO =
  /^[A-Z0-9]{1,10}$/;


/* =========================================================
   NORMALIZADORES
   ========================================================= */

function soloDigitos(
  valor: string,
  maximo = 20,
): string {

  return valor
    .replace(
      /\D/g,
      "",
    )
    .slice(
      0,
      maximo,
    );

}


function normalizarMatricula(
  valor: string,
): string {

  return valor
    .toUpperCase()
    .replace(
      /\s+/g,
      "",
    )
    .replace(
      /[^A-Z0-9./-]/g,
      "",
    )
    .slice(
      0,
      30,
    );

}


function normalizarComplemento(
  valor: string,
): string {

  return valor
    .toUpperCase()
    .replace(
      /\s+/g,
      "",
    )
    .replace(
      /[^A-Z0-9]/g,
      "",
    )
    .slice(
      0,
      10,
    );

}


/* =========================================================
   VALIDACIÓN LOCAL
   ========================================================= */

function validarCampo(
  campo: CampoFormulario,
  formulario: FormularioOncologo,
): string | undefined {

  const valor =
    formulario[
      campo
    ];


  const texto =
    typeof valor === "string"
      ? valor.trim()
      : "";


  switch (
    campo
  ) {

    case "nombres":

      if (
        texto.length < 2
      ) {

        return (
          "Ingrese los nombres del oncólogo."
        );

      }

      return undefined;


    case "apellido_paterno":

      if (
        texto.length < 2
      ) {

        return (
          "Ingrese el apellido paterno."
        );

      }

      return undefined;


    case "telefono":

      if (!texto) {

        return undefined;

      }

      if (
        !PATRON_TELEFONO_PERSONAL
          .test(
            texto
          )
      ) {

        return (
          "Debe tener 8 dígitos y comenzar con 6 o 7."
        );

      }

      return undefined;


    case "ci_numero":

      if (!texto) {

        return (
          "La cédula de identidad es obligatoria."
        );

      }

      if (
        !PATRON_CI
          .test(
            texto
          )
      ) {

        return (
          "Ingrese únicamente números, entre 4 y 20 dígitos."
        );

      }

      return undefined;


    case "ci_complemento":

      if (!texto) {

        return undefined;

      }

      if (
        !PATRON_COMPLEMENTO
          .test(
            texto
          )
      ) {

        return (
          "El complemento solo puede contener letras y números."
        );

      }

      return undefined;


    case "ci_expedido":

      if (!texto) {

        return (
          "Seleccione el departamento de expedición."
        );

      }

      return undefined;


    case "matricula_profesional":

      if (!texto) {

        return (
          "La matrícula profesional es obligatoria."
        );

      }

      if (
        texto.length < 4
        ||
        texto.length > 30
      ) {

        return (
          "La matrícula debe tener entre 4 y 30 caracteres."
        );

      }

      if (
        !PATRON_MATRICULA
          .test(
            texto
          )
      ) {

        return (
          "Use letras, números, guion (-), punto (.) o barra (/)."
        );

      }

      return undefined;


    case "subespecialidad":

      if (!texto) {

        return (
          "Seleccione una subespecialidad."
        );

      }

      return undefined;


    case "telefono_institucional":

      if (!texto) {

        return undefined;

      }

      if (
        !PATRON_TELEFONO_INSTITUCIONAL
          .test(
            texto
          )
      ) {

        return (
          "El teléfono institucional debe tener exactamente 8 dígitos."
        );

      }

      return undefined;


    case "correo":

      if (!texto) {

        return (
          "El correo institucional es obligatorio."
        );

      }

      if (
        texto.length > 150
      ) {

        return (
          "El correo no puede superar 150 caracteres."
        );

      }

      if (
        /\s/.test(
          texto
        )
      ) {

        return (
          "El correo no puede contener espacios."
        );

      }

      if (
        texto.includes(
          ".."
        )
      ) {

        return (
          "El correo no puede contener dos puntos consecutivos."
        );

      }

      if (
        !PATRON_CORREO
          .test(
            texto
          )
      ) {

        return (
          "Ingrese un correo electrónico válido."
        );

      }

      return undefined;


    case "rol_codigo":

      if (
        texto !== "ONCOLOGO"
        &&
        texto !== "JEFE_ONCOLOGIA"
      ) {

        return (
          "Seleccione un rol válido."
        );

      }

      return undefined;


    default:

      return undefined;

  }

}


/* =========================================================
   COMPONENTE
   ========================================================= */

export function NuevoUsuarioPage() {

  const navigate =
    useNavigate();


  const [
    formulario,
    setFormulario,
  ] = useState<FormularioOncologo>(
    formularioInicial
  );


  const [
    errores,
    setErrores,
  ] = useState<ErroresFormulario>(
    {}
  );


  const [
    guardando,
    setGuardando,
  ] = useState(
    false
  );


  const [
    mensajeExito,
    setMensajeExito,
  ] = useState(
    ""
  );


  const [
    usuarioGenerado,
    setUsuarioGenerado,
  ] = useState(
    ""
  );


  const [
    verificaciones,
    setVerificaciones,
  ] = useState<Verificaciones>(
    {
      ci: "idle",
      matricula: "idle",
      correo: "idle",
    }
  );


  const [
    camposTocados,
    setCamposTocados,
  ] = useState<
    Partial<
      Record<
        CampoFormulario,
        boolean
      >
    >
  >(
    {}
  );


  /* =======================================================
     ACTUALIZAR CAMPO
     ======================================================= */

  const actualizarCampo = (
    campo: CampoFormulario,
    valorOriginal: string,
  ) => {

    let valor =
      valorOriginal;


    if (
      campo === "telefono"
    ) {

      valor =
        soloDigitos(
          valorOriginal,
          8,
        );

    }


    if (
      campo ===
      "telefono_institucional"
    ) {

      valor =
        soloDigitos(
          valorOriginal,
          8,
        );

    }


    if (
      campo === "ci_numero"
    ) {

      valor =
        soloDigitos(
          valorOriginal,
          20,
        );


      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          ci: "idle",
        })
      );

    }


    if (
      campo === "ci_complemento"
    ) {

      valor =
        normalizarComplemento(
          valorOriginal
        );


      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          ci: "idle",
        })
      );

    }


    if (
      campo ===
      "matricula_profesional"
    ) {

      valor =
        normalizarMatricula(
          valorOriginal
        );


      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          matricula: "idle",
        })
      );

    }


    if (
      campo === "correo"
    ) {

      valor =
        valorOriginal
          .toLowerCase();


      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          correo: "idle",
        })
      );

    }


    const siguienteFormulario:
      FormularioOncologo = {

      ...formulario,

      [campo]:
        valor,

    };


    setFormulario(
      siguienteFormulario
    );


    setErrores(
      (
        actual
      ) => {

        const nuevo = {
          ...actual,
        };


        delete nuevo.general;


        if (
          camposTocados[
            campo
          ]
        ) {

          const errorCampo =
            validarCampo(
              campo,
              siguienteFormulario,
            );


          if (
            errorCampo
          ) {

            nuevo[
              campo
            ] = errorCampo;

          } else {

            delete nuevo[
              campo
            ];

          }

        } else {

          delete nuevo[
            campo
          ];

        }


        return nuevo;

      }
    );

  };


  /* =======================================================
     TOCAR CAMPO
     ======================================================= */

  const tocarCampo = (
    campo: CampoFormulario,
  ) => {

    setCamposTocados(
      (
        actual
      ) => ({
        ...actual,
        [campo]: true,
      })
    );


    const errorCampo =
      validarCampo(
        campo,
        formulario,
      );


    setErrores(
      (
        actual
      ) => {

        const nuevo = {
          ...actual,
        };


        if (
          errorCampo
        ) {

          nuevo[
            campo
          ] = errorCampo;

        } else {

          delete nuevo[
            campo
          ];

        }


        return nuevo;

      }
    );

  };


  /* =======================================================
     VERIFICAR CI
     ======================================================= */

  const verificarCi = async () => {

    const error =
      validarCampo(
        "ci_numero",
        formulario,
      );


    if (
      error
    ) {

      setErrores(
        (
          actual
        ) => ({
          ...actual,
          ci_numero:
            error,
        })
      );

      return;

    }


    try {

      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          ci: "checking",
        })
      );


      const disponible =
        await verificarCiOncologo(
          formulario.ci_numero,
          formulario.ci_complemento
            || null,
        );


      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          ci:
            disponible
              ? "available"
              : "duplicate",
        })
      );


      if (
        !disponible
      ) {

        setErrores(
          (
            actual
          ) => ({
            ...actual,
            ci_numero:
              "Ya existe un profesional registrado con esta cédula de identidad.",
          })
        );

      } else {

        setErrores(
          (
            actual
          ) => {

            const nuevo = {
              ...actual,
            };

            delete nuevo.ci_numero;

            return nuevo;

          }
        );

      }

    } catch {

      setVerificaciones(
        (
          actual
        ) => ({
          ...actual,
          ci: "error",
        })
      );

    }

  };


  /* =======================================================
     VERIFICAR MATRÍCULA
     ======================================================= */

  const verificarMatricula =
    async () => {

      const error =
        validarCampo(
          "matricula_profesional",
          formulario,
        );


      if (
        error
      ) {

        setErrores(
          (
            actual
          ) => ({
            ...actual,
            matricula_profesional:
              error,
          })
        );

        return;

      }


      try {

        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            matricula: "checking",
          })
        );


        const disponible =
          await verificarMatriculaOncologo(
            formulario
              .matricula_profesional
          );


        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            matricula:
              disponible
                ? "available"
                : "duplicate",
          })
        );


        if (
          !disponible
        ) {

          setErrores(
            (
              actual
            ) => ({
              ...actual,
              matricula_profesional:
                "Esta matrícula profesional ya se encuentra registrada.",
            })
          );

        } else {

          setErrores(
            (
              actual
            ) => {

              const nuevo = {
                ...actual,
              };

              delete nuevo
                .matricula_profesional;

              return nuevo;

            }
          );

        }

      } catch {

        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            matricula:
              "error",
          })
        );

      }

    };


  /* =======================================================
     VERIFICAR CORREO
     ======================================================= */

  const verificarCorreo =
    async () => {

      const error =
        validarCampo(
          "correo",
          formulario,
        );


      if (
        error
      ) {

        setErrores(
          (
            actual
          ) => ({
            ...actual,
            correo:
              error,
          })
        );

        return;

      }


      try {

        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            correo: "checking",
          })
        );


        const disponible =
          await verificarCorreoOncologo(
            formulario.correo
          );


        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            correo:
              disponible
                ? "available"
                : "duplicate",
          })
        );


        if (
          !disponible
        ) {

          setErrores(
            (
              actual
            ) => ({
              ...actual,
              correo:
                "Este correo ya se encuentra registrado.",
            })
          );

        } else {

          setErrores(
            (
              actual
            ) => {

              const nuevo = {
                ...actual,
              };

              delete nuevo.correo;

              return nuevo;

            }
          );

        }

      } catch {

        setVerificaciones(
          (
            actual
          ) => ({
            ...actual,
            correo: "error",
          })
        );

      }

    };


  /* =======================================================
     VALIDAR FORMULARIO
     ======================================================= */

  const validarFormulario =
    (): ErroresFormulario => {

      const nuevos:
        ErroresFormulario = {};


      const campos:
        CampoFormulario[] = [

        "nombres",

        "apellido_paterno",

        "telefono",

        "ci_numero",

        "ci_complemento",

        "ci_expedido",

        "correo",

        "matricula_profesional",

        "subespecialidad",

        "telefono_institucional",

        "rol_codigo",

      ];


      campos.forEach(
        (
          campo
        ) => {

          const error =
            validarCampo(
              campo,
              formulario,
            );


          if (
            error
          ) {

            nuevos[
              campo
            ] = error;

          }

        }
      );


      if (
        verificaciones.ci ===
        "duplicate"
      ) {

        nuevos.ci_numero =
          "Ya existe un profesional con esta cédula.";

      }


      if (
        verificaciones.matricula ===
        "duplicate"
      ) {

        nuevos.matricula_profesional =
          "Esta matrícula ya se encuentra registrada.";

      }


      if (
        verificaciones.correo ===
        "duplicate"
      ) {

        nuevos.correo =
          "Este correo ya se encuentra registrado.";

      }


      return nuevos;

    };


  /* =======================================================
     REGISTRAR
     ======================================================= */

  const registrar = async (
    event:
      React.FormEvent<HTMLFormElement>,
  ) => {

    event.preventDefault();


    const todosTocados:
      Partial<
        Record<
          CampoFormulario,
          boolean
        >
      > = {};


    (
      Object.keys(
        formulario
      ) as CampoFormulario[]
    ).forEach(
      (
        campo
      ) => {

        todosTocados[
          campo
        ] = true;

      }
    );


    setCamposTocados(
      todosTocados
    );


    const erroresLocales =
      validarFormulario();


    if (
      Object.keys(
        erroresLocales
      ).length > 0
    ) {

      setErrores(
        erroresLocales
      );

      return;

    }


    try {

      setGuardando(
        true
      );

      setErrores(
        {}
      );

      setMensajeExito(
        ""
      );

      setUsuarioGenerado(
        ""
      );


      const payload:
        CrearOncologoPayload = {

        nombres:
          formulario
            .nombres
            .trim(),

        apellido_paterno:
          formulario
            .apellido_paterno
            .trim(),

        apellido_materno:
          formulario
            .apellido_materno
            .trim()
          || null,

        telefono:
          formulario
            .telefono
            .trim()
          || null,

        ci_numero:
          formulario
            .ci_numero
            .trim(),

        ci_complemento:
          formulario
            .ci_complemento
            .trim()
          || null,

        ci_expedido:
          formulario
            .ci_expedido,

        correo:
          formulario
            .correo
            .trim()
            .toLowerCase(),

        matricula_profesional:
          formulario
            .matricula_profesional
            .trim()
            .toUpperCase(),

        subespecialidad:
          formulario
            .subespecialidad,

        telefono_institucional:
          formulario
            .telefono_institucional
            .trim()
          || null,

        rol_codigo:
          formulario
            .rol_codigo,

      };


      const response =
        await crearOncologo(
          payload
        );


      setMensajeExito(
        response.mensaje
      );


      setUsuarioGenerado(
        response
          .oncologo
          .nombre_usuario
      );


      window.setTimeout(
        () => {

          navigate(
            "/usuarios",
            {
              replace: true,
            },
          );

        },
        2400,
      );

    } catch (
      error
    ) {

      setErrores(
        normalizarErroresApi(
          error
        )
      );

    } finally {

      setGuardando(
        false
      );

    }

  };


  /* =======================================================
     INDICADOR DE VERIFICACIÓN
     ======================================================= */

  const indicadorVerificacion = (
    estado: EstadoVerificacion,
    mensajeDisponible: string,
  ) => {

    if (
      estado === "checking"
    ) {

      return (
        <small className="oncologist-field-check oncologist-field-check--checking">
          <LoaderCircle
            size={13}
            className="oncologists-spin"
          />
          Verificando...
        </small>
      );

    }


    if (
      estado === "available"
    ) {

      return (
        <small className="oncologist-field-check oncologist-field-check--success">
          <CheckCircle2 size={13} />
          {mensajeDisponible}
        </small>
      );

    }


    if (
      estado === "error"
    ) {

      return (
        <small className="oncologist-field-check oncologist-field-check--warning">
          <CircleAlert size={13} />
          No fue posible verificar ahora. El servidor validará al registrar.
        </small>
      );

    }


    return null;

  };


  /* =======================================================
     VISTA
     ======================================================= */

  return (

    <div
      className="oncologists-page"
    >

      <button
        type="button"
        className="oncologist-form-back"
        onClick={
          () =>
            navigate(
              "/usuarios"
            )
        }
      >

        <ArrowLeft
          size={17}
        />

        Volver a oncólogos

      </button>


      <section
        className="oncologists-header"
      >

        <div>

          <span
            className="oncologists-header__eyebrow"
          >
            Administración
          </span>

          <h1>
            Registrar profesional
          </h1>

          <p>
            Registre un oncólogo o Jefe de Oncología.
            El sistema generará automáticamente sus credenciales.
          </p>

        </div>

      </section>


      {
        mensajeExito
        &&
        (
          <div
            className="oncologist-created-card"
          >

            <div
              className="oncologist-created-card__icon"
            >
              <BadgeCheck
                size={24}
              />
            </div>

            <div>

              <strong>
                {mensajeExito}
              </strong>

              {
                usuarioGenerado
                &&
                (
                  <span>
                    Usuario generado:
                    {" "}
                    <b>
                      {usuarioGenerado}
                    </b>
                    . Las credenciales temporales fueron enviadas al correo institucional.
                  </span>
                )
              }

            </div>

          </div>
        )
      }


      {
        errores.general
        &&
        (
          <div
            className="oncologists-alert oncologists-alert--error"
          >

            <AlertCircle
              size={18}
            />

            {errores.general}

          </div>
        )
      }


      <form
        className="oncologist-form-card"
        onSubmit={
          registrar
        }
        noValidate
      >

        {/* =================================================
            DATOS PERSONALES
            ================================================= */}

        <div
          className="oncologist-form-section-title"
        >

          <div>
            <UserRound
              size={19}
            />
          </div>

          <span>

            <strong>
              Datos personales
            </strong>

            <small>
              Información básica del profesional.
            </small>

          </span>

        </div>


        <div
          className="oncologist-form-grid"
        >

          <label>

            <span>
              Nombres *
            </span>

            <input
              value={
                formulario.nombres
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "nombres",
                    event.target.value,
                  )
              }
              onBlur={
                () =>
                  tocarCampo(
                    "nombres"
                  )
              }
              placeholder="Ej. Andrea María"
              maxLength={100}
              aria-invalid={
                Boolean(
                  errores.nombres
                )
              }
            />

            {
              errores.nombres
              &&
              (
                <small>
                  {errores.nombres}
                </small>
              )
            }

          </label>


          <label>

            <span>
              Apellido paterno *
            </span>

            <input
              value={
                formulario
                  .apellido_paterno
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "apellido_paterno",
                    event.target.value,
                  )
              }
              onBlur={
                () =>
                  tocarCampo(
                    "apellido_paterno"
                  )
              }
              placeholder="Ej. López"
              maxLength={80}
              aria-invalid={
                Boolean(
                  errores
                    .apellido_paterno
                )
              }
            />

            {
              errores
                .apellido_paterno
              &&
              (
                <small>
                  {
                    errores
                      .apellido_paterno
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Apellido materno
            </span>

            <input
              value={
                formulario
                  .apellido_materno
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "apellido_materno",
                    event.target.value,
                  )
              }
              placeholder="Ej. Vargas"
              maxLength={80}
            />

          </label>


          <label>

            <span>
              Teléfono personal
            </span>

            <input
              value={
                formulario.telefono
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "telefono",
                    event.target.value,
                  )
              }
              onBlur={
                () =>
                  tocarCampo(
                    "telefono"
                  )
              }
              placeholder="Ej. 71234567"
              inputMode="numeric"
              maxLength={8}
              aria-invalid={
                Boolean(
                  errores.telefono
                )
              }
            />

            {
              !errores.telefono
              &&
              (
                <small
                  className="oncologist-field-help"
                >
                  Opcional. 8 dígitos y debe comenzar con 6 o 7.
                </small>
              )
            }

            {
              errores.telefono
              &&
              (
                <small>
                  {errores.telefono}
                </small>
              )
            }

          </label>

        </div>


        <div
          className="oncologist-form-divider"
        />


        {/* =================================================
            IDENTIFICACIÓN
            ================================================= */}

        <div
          className="oncologist-form-section-title"
        >

          <div>
            <IdCard
              size={19}
            />
          </div>

          <span>

            <strong>
              Identificación
            </strong>

            <small>
              Cédula de identidad y departamento de expedición.
            </small>

          </span>

        </div>


        <div
          className="oncologist-form-grid"
        >

          <label>

            <span>
              Cédula de identidad *
            </span>

            <input
              value={
                formulario.ci_numero
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "ci_numero",
                    event.target.value,
                  )
              }
              onBlur={
                async () => {

                  tocarCampo(
                    "ci_numero"
                  );

                  await verificarCi();

                }
              }
              placeholder="Ej. 8459217"
              inputMode="numeric"
              maxLength={20}
              aria-invalid={
                Boolean(
                  errores.ci_numero
                )
              }
            />

            {
              indicadorVerificacion(
                verificaciones.ci,
                "Documento disponible.",
              )
            }

            {
              errores.ci_numero
              &&
              (
                <small>
                  {errores.ci_numero}
                </small>
              )
            }

          </label>


          <label>

            <span>
              Complemento
            </span>

            <input
              value={
                formulario
                  .ci_complemento
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "ci_complemento",
                    event.target.value,
                  )
              }
              onBlur={
                async () => {

                  tocarCampo(
                    "ci_complemento"
                  );

                  if (
                    formulario
                      .ci_numero
                  ) {

                    await verificarCi();

                  }

                }
              }
              placeholder="Ej. 1A"
              maxLength={10}
              aria-invalid={
                Boolean(
                  errores
                    .ci_complemento
                )
              }
            />

            {
              !errores
                .ci_complemento
              &&
              (
                <small
                  className="oncologist-field-help"
                >
                  Opcional.
                </small>
              )
            }

            {
              errores
                .ci_complemento
              &&
              (
                <small>
                  {
                    errores
                      .ci_complemento
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Expedido en *
            </span>

            <select
              value={
                formulario
                  .ci_expedido
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "ci_expedido",
                    event.target.value,
                  )
              }
            >

              {
                DEPARTAMENTOS
                  .map(
                    (
                      departamento
                    ) => (

                      <option
                        key={
                          departamento.codigo
                        }
                        value={
                          departamento.codigo
                        }
                      >
                        {
                          departamento.nombre
                        }
                        {" "}
                        (
                        {
                          departamento.codigo
                        }
                        )
                      </option>

                    )
                  )
              }

            </select>

          </label>

        </div>


        <div
          className="oncologist-form-divider"
        />


        {/* =================================================
            PROFESIONAL
            ================================================= */}

        <div
          className="oncologist-form-section-title"
        >

          <div>
            <Stethoscope
              size={19}
            />
          </div>

          <span>

            <strong>
              Información profesional
            </strong>

            <small>
              Datos médicos e institucionales.
            </small>

          </span>

        </div>


        <div
          className="oncologist-form-grid"
        >

          <label>

            <span>
              Matrícula profesional *
            </span>

            <input
              value={
                formulario
                  .matricula_profesional
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "matricula_profesional",
                    event.target.value,
                  )
              }
              onBlur={
                async () => {

                  tocarCampo(
                    "matricula_profesional"
                  );

                  await verificarMatricula();

                }
              }
              placeholder="Ej. MED-5487"
              maxLength={30}
              aria-invalid={
                Boolean(
                  errores
                    .matricula_profesional
                )
              }
            />

            {
              indicadorVerificacion(
                verificaciones
                  .matricula,
                "Matrícula disponible.",
              )
            }

            {
              errores
                .matricula_profesional
              &&
              (
                <small>
                  {
                    errores
                      .matricula_profesional
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Especialidad
            </span>

            <div
              className="oncologist-readonly-field"
            >

              <Stethoscope
                size={16}
              />

              Oncología

              <BadgeCheck
                size={15}
              />

            </div>

            <small
              className="oncologist-field-help"
            >
              Definida automáticamente por el sistema.
            </small>

          </label>


          <label>

            <span>
              Subespecialidad *
            </span>

            <select
              value={
                formulario
                  .subespecialidad
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "subespecialidad",
                    event.target.value,
                  )
              }
              aria-invalid={
                Boolean(
                  errores
                    .subespecialidad
                )
              }
            >

              {
                SUBESPECIALIDADES
                  .map(
                    (
                      opcion
                    ) => (

                      <option
                        key={
                          opcion
                        }
                        value={
                          opcion
                        }
                      >
                        {opcion}
                      </option>

                    )
                  )
              }

            </select>

            {
              errores
                .subespecialidad
              &&
              (
                <small>
                  {
                    errores
                      .subespecialidad
                  }
                </small>
              )
            }

          </label>


          <label>

            <span>
              Área clínica
            </span>

            <div
              className="oncologist-readonly-field oncologist-readonly-field--accent"
            >

              <BadgeCheck
                size={16}
              />

              Tumores óseos / Osteosarcoma

            </div>

            <small
              className="oncologist-field-help"
            >
              Enfoque clínico definido automáticamente.
            </small>

          </label>


          <label>

            <span>
              Teléfono institucional
            </span>

            <input
              value={
                formulario
                  .telefono_institucional
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "telefono_institucional",
                    event.target.value,
                  )
              }
              onBlur={
                () =>
                  tocarCampo(
                    "telefono_institucional"
                  )
              }
              placeholder="Ej. 22123456"
              inputMode="numeric"
              maxLength={8}
              aria-invalid={
                Boolean(
                  errores
                    .telefono_institucional
                )
              }
            />

            {
              !errores
                .telefono_institucional
              &&
              (
                <small
                  className="oncologist-field-help"
                >
                  Opcional. Debe tener 8 dígitos.
                </small>
              )
            }

            {
              errores
                .telefono_institucional
              &&
              (
                <small>
                  {
                    errores
                      .telefono_institucional
                  }
                </small>
              )
            }

          </label>

        </div>


        <div
          className="oncologist-form-divider"
        />


        {/* =================================================
            ACCESO
            ================================================= */}

        <div
          className="oncologist-form-section-title"
        >

          <div>
            <ShieldCheck
              size={19}
            />
          </div>

          <span>

            <strong>
              Acceso al sistema
            </strong>

            <small>
              Rol y correo institucional del profesional.
            </small>

          </span>

        </div>


        <div
          className="oncologist-form-grid"
        >

          <label>

            <span>
              Correo institucional *
            </span>

            <input
              type="email"
              value={
                formulario.correo
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "correo",
                    event.target.value,
                  )
              }
              onBlur={
                async () => {

                  tocarCampo(
                    "correo"
                  );

                  await verificarCorreo();

                }
              }
              placeholder="oncologo@hospital.com"
              maxLength={150}
              aria-invalid={
                Boolean(
                  errores.correo
                )
              }
            />

            {
              indicadorVerificacion(
                verificaciones.correo,
                "Correo disponible.",
              )
            }

            {
              errores.correo
              &&
              (
                <small>
                  {errores.correo}
                </small>
              )
            }

          </label>


          <label>

            <span>
              Rol *
            </span>

            <select
              value={
                formulario
                  .rol_codigo
              }
              onChange={
                (
                  event
                ) =>
                  actualizarCampo(
                    "rol_codigo",
                    event.target.value,
                  )
              }
            >

              <option
                value="ONCOLOGO"
              >
                Oncólogo
              </option>

              <option
                value="JEFE_ONCOLOGIA"
              >
                Jefe de Oncología
              </option>

            </select>

            <small
              className="oncologist-field-help"
            >
              El rol define los permisos que tendrá dentro del sistema.
            </small>

          </label>

        </div>


        {/* =================================================
            NOTA CREDENCIALES
            ================================================= */}

        <div
          className="oncologist-form-note"
        >

          <MailCheck
            size={20}
          />

          <div>

            <strong>
              Credenciales automáticas
            </strong>

            <span>
              El nombre de usuario y una contraseña temporal segura serán generados automáticamente. Las credenciales se enviarán únicamente al correo institucional registrado y el profesional deberá cambiar su contraseña posteriormente.
            </span>

          </div>

        </div>


        {/* =================================================
            FOOTER
            ================================================= */}

        <footer
          className="oncologist-form-footer"
        >

          <button
            type="button"
            className="oncologists-secondary-button"
            onClick={
              () =>
                navigate(
                  "/usuarios"
                )
            }
            disabled={
              guardando
            }
          >
            Cancelar
          </button>


          <button
            type="submit"
            className="oncologists-primary-button"
            disabled={
              guardando
              ||
              verificaciones.ci === "checking"
              ||
              verificaciones.matricula === "checking"
              ||
              verificaciones.correo === "checking"
            }
          >

            <span
              className="oncologists-button-icon"
            >

              {
                guardando
                  ? (
                    <LoaderCircle
                      size={17}
                      className="oncologists-spin"
                    />
                  )
                  : (
                    <Save
                      size={17}
                    />
                  )
              }

            </span>

            <span>
              {
                guardando
                  ? "Registrando..."
                  : "Registrar profesional"
              }
            </span>

          </button>

        </footer>

      </form>

    </div>

  );

}