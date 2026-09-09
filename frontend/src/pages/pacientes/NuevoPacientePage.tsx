import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  LoaderCircle,
  Save,
  ShieldAlert,
  UserPlus,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  BOLIVIA_DEPARTMENTS,
  createPatient,
  findPossibleDuplicates,
  getPatientCatalogs,
  type BoliviaDepartmentCode,
  type CatalogItem,
  type CreatePatientRequest,
  type PatientCatalogs,
  type PatientSummary,
} from "../../api/pacientes.api";

import "./NuevoPacientePage.css";


// ==========================================================
// ESTADO DEL FORMULARIO
// ==========================================================

type FormState = {
  first_names: string;

  paternal_surname: string;

  maternal_surname: string;

  birth_date: string;

  sex_id: string;

  document_type_id: string;

  document_number: string;

  complement: string;

  issued_in: BoliviaDepartmentCode;

  mobile_phone: string;

  landline_phone: string;

  email: string;

  emergency_contact_name: string;

  emergency_relationship: string;

  emergency_phone: string;

  emergency_email: string;
};


type FormErrors =
  Partial<
    Record<
      keyof FormState,
      string
    >
  >;


const initialForm: FormState = {
  first_names: "",

  paternal_surname: "",

  maternal_surname: "",

  birth_date: "",

  sex_id: "",

  document_type_id: "",

  document_number: "",

  complement: "",

  issued_in: "LP",

  mobile_phone: "",

  landline_phone: "",

  email: "",

  emergency_contact_name: "",

  emergency_relationship: "",

  emergency_phone: "",

  emergency_email: "",
};


// ==========================================================
// HELPERS
// ==========================================================

function normalizeText(
  value: string,
): string {
  return value
    .trim()
    .replace(
      /\s+/g,
      " ",
    );
}


function onlyNumbers(
  value: string,
  maxLength: number,
): string {
  return value
    .replace(
      /\D/g,
      "",
    )
    .slice(
      0,
      maxLength,
    );
}


function normalizeComplement(
  value: string,
): string {
  return value
    .toUpperCase()
    .replace(
      /[^A-Z0-9]/g,
      "",
    )
    .slice(
      0,
      20,
    );
}


function extractErrorMessage(
  error: unknown,
): string {
  if (
    typeof error === "object"
    &&
    error !== null
    &&
    "response" in error
  ) {
    const maybeAxios =
      error as {
        response?: {
          data?: unknown;
        };
      };


    const data =
      maybeAxios
        .response
        ?.data;


    if (
      data
      &&
      typeof data === "object"
    ) {
      const object =
        data as Record<
          string,
          unknown
        >;


      if (
        typeof object.detail ===
        "string"
      ) {
        return object.detail;
      }


      if (
        typeof object.error ===
        "string"
      ) {
        return object.error;
      }


      if (
        object.error
        &&
        typeof object.error ===
        "object"
      ) {
        const nested =
          object.error as Record<
            string,
            unknown
          >;


        if (
          typeof nested.message ===
          "string"
        ) {
          return nested.message;
        }
      }


      for (
        const value
        of Object.values(
          object,
        )
      ) {
        if (
          Array.isArray(
            value,
          )
        ) {
          return value
            .map(String)
            .join(" ");
        }


        if (
          typeof value ===
          "string"
        ) {
          return value;
        }


        if (
          value
          &&
          typeof value ===
          "object"
        ) {
          const nestedValues =
            Object.values(
              value as Record<
                string,
                unknown
              >,
            );


          const first =
            nestedValues[0];


          if (
            Array.isArray(
              first,
            )
          ) {
            return first
              .map(String)
              .join(" ");
          }


          if (
            typeof first ===
            "string"
          ) {
            return first;
          }
        }
      }
    }
  }


  return (
    "No fue posible registrar el paciente."
  );
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function NuevoPacientePage() {
  const navigate =
    useNavigate();


  const [
    catalogs,
    setCatalogs,
  ] = useState<
    PatientCatalogs | null
  >(
    null,
  );


  const [
    form,
    setForm,
  ] = useState<FormState>(
    initialForm,
  );


  const [
    formErrors,
    setFormErrors,
  ] = useState<FormErrors>(
    {},
  );


  const [
    loadingCatalogs,
    setLoadingCatalogs,
  ] = useState(
    true,
  );


  const [
    saving,
    setSaving,
  ] = useState(
    false,
  );


  const [
    checkingDuplicates,
    setCheckingDuplicates,
  ] = useState(
    false,
  );


  const [
    duplicates,
    setDuplicates,
  ] = useState<
    PatientSummary[]
  >(
    [],
  );


  const [
    duplicateChecked,
    setDuplicateChecked,
  ] = useState(
    false,
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(
    null,
  );


  const [
    success,
    setSuccess,
  ] = useState<
    string | null
  >(
    null,
  );


  // ========================================================
  // CATÁLOGOS
  // ========================================================

  useEffect(
    () => {
      let mounted = true;


      async function loadCatalogs() {
        setLoadingCatalogs(
          true,
        );


        try {
          const data =
            await getPatientCatalogs();


          if (
            !mounted
          ) {
            return;
          }


          setCatalogs(
            data,
          );


          const defaultSex =
            data.sexes[0];


          const defaultDocument =
            data.document_types[0];


          setForm(
            (
              current,
            ) => ({
              ...current,

              sex_id:
                current.sex_id
                ||
                (
                  defaultSex
                    ? String(
                        defaultSex.id,
                      )
                    : ""
                ),

              document_type_id:
                current.document_type_id
                ||
                (
                  defaultDocument
                    ? String(
                        defaultDocument.id,
                      )
                    : ""
                ),
            }),
          );
        } catch {
          if (
            mounted
          ) {
            setError(
              "No fue posible cargar los catálogos de pacientes.",
            );
          }
        } finally {
          if (
            mounted
          ) {
            setLoadingCatalogs(
              false,
            );
          }
        }
      }


      void loadCatalogs();


      return () => {
        mounted = false;
      };
    },
    [],
  );


  // ========================================================
  // ACTUALIZAR CAMPO
  // ========================================================

  function updateField(
    field:
      keyof FormState,

    originalValue:
      string,
  ) {
    let value =
      originalValue;


    if (
      field ===
      "mobile_phone"
      ||
      field ===
      "emergency_phone"
    ) {
      value =
        onlyNumbers(
          originalValue,
          8,
        );
    }


    if (
      field ===
      "landline_phone"
    ) {
      value =
        onlyNumbers(
          originalValue,
          8,
        );
    }


    if (
      field ===
      "document_number"
    ) {
      value =
        originalValue
          .toUpperCase()
          .replace(
            /\s+/g,
            "",
          )
          .slice(
            0,
            50,
          );
    }


    if (
      field ===
      "complement"
    ) {
      value =
        normalizeComplement(
          originalValue,
        );
    }


    if (
      field ===
      "email"
      ||
      field ===
      "emergency_email"
    ) {
      value =
        originalValue
          .toLowerCase()
          .trimStart();
    }


    setForm(
      (
        current,
      ) => ({
        ...current,
        [field]:
          value,
      }),
    );


    setSuccess(
      null,
    );


    setError(
      null,
    );


    setFormErrors(
      (
        current,
      ) => {
        const next = {
          ...current,
        };


        delete next[
          field
        ];


        return next;
      },
    );


    if (
      field ===
      "document_number"
      ||
      field ===
      "document_type_id"
      ||
      field ===
      "first_names"
      ||
      field ===
      "paternal_surname"
      ||
      field ===
      "maternal_surname"
      ||
      field ===
      "birth_date"
    ) {
      setDuplicateChecked(
        false,
      );

      setDuplicates(
        [],
      );
    }
  }


  // ========================================================
  // VALIDACIONES
  // ========================================================

  function validateForm():
    FormErrors {

    const errors:
      FormErrors = {};


    if (
      normalizeText(
        form.first_names,
      ).length < 2
    ) {
      errors.first_names =
        "Ingrese los nombres del paciente.";
    }


    if (
      normalizeText(
        form.paternal_surname,
      ).length < 2
    ) {
      errors.paternal_surname =
        "Ingrese el apellido paterno.";
    }


    if (
      !form.birth_date
    ) {
      errors.birth_date =
        "Seleccione la fecha de nacimiento.";
    } else {
      const birthDate =
        new Date(
          `${form.birth_date}T00:00:00`,
        );


      const today =
        new Date();


      if (
        Number.isNaN(
          birthDate.getTime(),
        )
        ||
        birthDate >
        today
      ) {
        errors.birth_date =
          "La fecha de nacimiento no es válida.";
      }
    }


    if (
      !form.sex_id
    ) {
      errors.sex_id =
        "Seleccione el sexo.";
    }


    if (
      !form.document_type_id
    ) {
      errors.document_type_id =
        "Seleccione el tipo de documento.";
    }


    if (
      normalizeText(
        form.document_number,
      ).length < 4
    ) {
      errors.document_number =
        "Ingrese un número de documento válido.";
    }


    if (
      !form.issued_in
    ) {
      errors.issued_in =
        "Seleccione el departamento de expedición.";
    }


    if (
      form.mobile_phone
      &&
      !/^[67]\d{7}$/.test(
        form.mobile_phone,
      )
    ) {
      errors.mobile_phone =
        (
          "El celular debe tener 8 dígitos " +
          "y comenzar con 6 o 7."
        );
    }


    if (
      form.landline_phone
      &&
      !/^\d{7,8}$/.test(
        form.landline_phone,
      )
    ) {
      errors.landline_phone =
        (
          "El teléfono fijo debe tener " +
          "entre 7 y 8 dígitos."
        );
    }


    if (
      form.email
      &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        form.email,
      )
    ) {
      errors.email =
        "Ingrese un correo válido.";
    }


    const hasEmergencyData =
      Boolean(
        normalizeText(
          form.emergency_contact_name,
        )
        ||
        normalizeText(
          form.emergency_relationship,
        )
        ||
        form.emergency_phone
        ||
        normalizeText(
          form.emergency_email,
        )
      );


    if (
      hasEmergencyData
    ) {
      if (
        normalizeText(
          form.emergency_contact_name,
        ).length < 3
      ) {
        errors.emergency_contact_name =
          "Ingrese el nombre del familiar o responsable.";
      }


      if (
        normalizeText(
          form.emergency_relationship,
        ).length < 2
      ) {
        errors.emergency_relationship =
          "Ingrese el parentesco.";
      }


      if (
        !/^[67]\d{7}$/.test(
          form.emergency_phone,
        )
      ) {
        errors.emergency_phone =
          (
            "El teléfono de emergencia debe tener " +
            "8 dígitos y comenzar con 6 o 7."
          );
      }


      if (
        form.emergency_email
        &&
        !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
          form.emergency_email,
        )
      ) {
        errors.emergency_email =
          "Ingrese un correo válido.";
      }
    }


    return errors;
  }


  const formValid =
    useMemo(
      () =>
        Object.keys(
          validateForm(),
        ).length === 0,
      [
        form,
      ],
    );


  // ========================================================
  // DUPLICADOS AUTOMÁTICOS
  // ========================================================

  useEffect(
    () => {
      if (
        loadingCatalogs
      ) {
        return;
      }


      const documentNumber =
        normalizeText(
          form.document_number,
        );


      const firstNames =
        normalizeText(
          form.first_names,
        );


      const paternalSurname =
        normalizeText(
          form.paternal_surname,
        );


      const canCheckByDocument =
        Boolean(
          form.document_type_id
          &&
          documentNumber.length >= 4
        );


      const canCheckByIdentity =
        Boolean(
          firstNames.length >= 2
          &&
          paternalSurname.length >= 2
          &&
          form.birth_date
        );


      if (
        !canCheckByDocument
        &&
        !canCheckByIdentity
      ) {
        setCheckingDuplicates(
          false,
        );

        setDuplicateChecked(
          false,
        );

        setDuplicates(
          [],
        );

        return;
      }


      let cancelled =
        false;


      const timer =
        window.setTimeout(
          async () => {
            try {
              setCheckingDuplicates(
                true,
              );


              setDuplicateChecked(
                false,
              );


              const response =
                await findPossibleDuplicates(
                  {
                    document_type_id:
                      form.document_type_id
                        ? Number(
                            form.document_type_id,
                          )
                        : undefined,

                    document_number:
                      documentNumber
                      ||
                      undefined,

                    first_names:
                      firstNames
                      ||
                      undefined,

                    paternal_surname:
                      paternalSurname
                      ||
                      undefined,

                    maternal_surname:
                      normalizeText(
                        form.maternal_surname,
                      )
                      ||
                      undefined,

                    birth_date:
                      form.birth_date
                      ||
                      undefined,
                  },
                );


              if (
                cancelled
              ) {
                return;
              }


              setDuplicates(
                Array.isArray(
                  response.data,
                )
                  ? response.data
                  : [],
              );


              setDuplicateChecked(
                true,
              );
            } catch {
              if (
                cancelled
              ) {
                return;
              }


              setDuplicateChecked(
                false,
              );


              setDuplicates(
                [],
              );


              setError(
                "No fue posible verificar automáticamente posibles duplicados.",
              );
            } finally {
              if (
                !cancelled
              ) {
                setCheckingDuplicates(
                  false,
                );
              }
            }
          },
          650,
        );


      return () => {
        cancelled = true;

        window.clearTimeout(
          timer,
        );
      };
    },
    [
      form.document_type_id,
      form.document_number,
      form.first_names,
      form.paternal_surname,
      form.maternal_surname,
      form.birth_date,
      loadingCatalogs,
    ],
  );


  // ========================================================
  // GUARDAR
  // ========================================================

  async function handleSubmit(
    event:
      React.FormEvent,
  ) {
    event.preventDefault();


    setError(
      null,
    );


    setSuccess(
      null,
    );


    const errors =
      validateForm();


    if (
      Object.keys(
        errors,
      ).length > 0
    ) {
      setFormErrors(
        errors,
      );


      setError(
        "Revise los campos marcados antes de registrar al paciente.",
      );

      return;
    }


    if (
      checkingDuplicates
    ) {
      setError(
        "Espere a que termine la verificación automática de duplicados.",
      );

      return;
    }


    if (
      !duplicateChecked
    ) {
      setError(
        "El sistema aún no terminó de verificar posibles duplicados.",
      );

      return;
    }


    if (
      duplicates.length > 0
    ) {
      setError(
        (
          "Se encontraron posibles pacientes duplicados. " +
          "Revise las coincidencias antes de continuar."
        ),
      );

      return;
    }


    const payload:
      CreatePatientRequest = {

      first_names:
        normalizeText(
          form.first_names,
        ),

      paternal_surname:
        normalizeText(
          form.paternal_surname,
        ),

      maternal_surname:
        normalizeText(
          form.maternal_surname,
        )
        ||
        null,

      birth_date:
        form.birth_date,

      sex_id:
        Number(
          form.sex_id,
        ),

      document_type_id:
        Number(
          form.document_type_id,
        ),

      document_number:
        normalizeText(
          form.document_number,
        ),

      complement:
        normalizeText(
          form.complement,
        )
        ||
        null,

      issued_in:
        form.issued_in,

      mobile_phone:
        form.mobile_phone
        ||
        null,

      landline_phone:
        form.landline_phone
        ||
        null,

      email:
        normalizeText(
          form.email,
        )
          .toLowerCase()
        ||
        null,

      emergency_contact_name:
        normalizeText(
          form.emergency_contact_name,
        )
        ||
        null,

      emergency_relationship:
        normalizeText(
          form.emergency_relationship,
        )
        ||
        null,

      emergency_phone:
        form.emergency_phone
        ||
        null,

      emergency_email:
        normalizeText(
          form.emergency_email,
        )
          .toLowerCase()
        ||
        null,
    };


    setSaving(
      true,
    );


    try {
      const response =
        await createPatient(
          payload,
        );


      setSuccess(
        response.message,
      );


      window.setTimeout(
        () => {
          navigate(
            `/pacientes/${response.data.id_patient}`,
          );
        },
        500,
      );
    } catch (
      requestError
    ) {
      setError(
        extractErrorMessage(
          requestError,
        ),
      );
    } finally {
      setSaving(
        false,
      );
    }
  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="new-patient-page"
    >

      {/* ==================================================
          HEADER
          ================================================== */}

      <header
        className="new-patient-header"
      >

        <div
          className="new-patient-header__main"
        >

          <button
            type="button"
            className="new-patient-back"
            onClick={
              () =>
                navigate(
                  "/pacientes",
                )
            }
          >

            <ArrowLeft
              size={18}
            />

          </button>


          <div>

            <span
              className="new-patient-eyebrow"
            >
              Gestión clínica
            </span>


            <h1>
              Registrar paciente
            </h1>


            <p>
              Registre la identificación, medios de contacto
              y un familiar o responsable para emergencias.
            </p>

          </div>

        </div>


        <div
          className="new-patient-header__icon"
        >

          <UserPlus
            size={26}
          />

        </div>

      </header>


      {/* ==================================================
          MENSAJES
          ================================================== */}

      {
        error
        &&
        (
          <div
            className="new-patient-message new-patient-message--error"
          >

            <CircleAlert
              size={19}
            />

            <span>
              {error}
            </span>

          </div>
        )
      }


      {
        success
        &&
        (
          <div
            className="new-patient-message new-patient-message--success"
          >

            <CheckCircle2
              size={19}
            />

            <span>
              {success}
            </span>

          </div>
        )
      }


      {
        loadingCatalogs
          ? (
              <div
                className="new-patient-loading"
              >

                <LoaderCircle
                  size={28}
                  className="new-patient-spin"
                />

                <span>
                  Cargando formulario...
                </span>

              </div>
            )
          : (
              <form
                className="new-patient-form"
                onSubmit={
                  handleSubmit
                }
              >

                {/* ==========================================
                    DATOS PERSONALES
                    ========================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header"
                  >

                    <div>

                      <h2>
                        Datos personales
                      </h2>

                      <p>
                        Información principal de identificación del paciente.
                      </p>

                    </div>

                  </div>


                  <div
                    className="new-patient-grid new-patient-grid--3"
                  >

                    <label>

                      <span>
                        Nombres *
                      </span>

                      <input
                        type="text"
                        value={
                          form.first_names
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "first_names",
                              event.target.value,
                            )
                        }
                        maxLength={100}
                        placeholder="Ej. María Fernanda"
                        autoComplete="off"
                        aria-invalid={
                          Boolean(
                            formErrors.first_names,
                          )
                        }
                      />

                      {
                        formErrors.first_names
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.first_names
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Apellido paterno *
                      </span>

                      <input
                        type="text"
                        value={
                          form.paternal_surname
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "paternal_surname",
                              event.target.value,
                            )
                        }
                        maxLength={80}
                        placeholder="Ej. López"
                        autoComplete="off"
                        aria-invalid={
                          Boolean(
                            formErrors.paternal_surname,
                          )
                        }
                      />

                      {
                        formErrors.paternal_surname
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.paternal_surname
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
                        type="text"
                        value={
                          form.maternal_surname
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "maternal_surname",
                              event.target.value,
                            )
                        }
                        maxLength={80}
                        placeholder="Ej. Flores"
                        autoComplete="off"
                      />

                    </label>


                    <label>

                      <span>
                        Fecha de nacimiento *
                      </span>

                      <input
                        type="date"
                        value={
                          form.birth_date
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "birth_date",
                              event.target.value,
                            )
                        }
                        aria-invalid={
                          Boolean(
                            formErrors.birth_date,
                          )
                        }
                      />

                      {
                        formErrors.birth_date
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.birth_date
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Sexo *
                      </span>

                      <select
                        value={
                          form.sex_id
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "sex_id",
                              event.target.value,
                            )
                        }
                      >

                        {
                          catalogs
                            ?.sexes
                            .map(
                              (
                                item:
                                  CatalogItem,
                              ) => (

                                <option
                                  key={
                                    item.id
                                  }
                                  value={
                                    item.id
                                  }
                                >
                                  {item.name}
                                </option>

                              ),
                            )
                        }

                      </select>

                    </label>

                  </div>

                </article>


                {/* ==========================================
                    DOCUMENTO
                    ========================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header"
                  >

                    <div>

                      <h2>
                        Documento de identidad
                      </h2>

                      <p>
                        El sistema verifica automáticamente posibles registros duplicados.
                      </p>

                    </div>

                  </div>


                  <div
                    className="new-patient-grid new-patient-grid--4"
                  >

                    <label>

                      <span>
                        Tipo *
                      </span>

                      <select
                        value={
                          form.document_type_id
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "document_type_id",
                              event.target.value,
                            )
                        }
                      >

                        {
                          catalogs
                            ?.document_types
                            .map(
                              (
                                item:
                                  CatalogItem,
                              ) => (

                                <option
                                  key={
                                    item.id
                                  }
                                  value={
                                    item.id
                                  }
                                >
                                  {item.name}
                                </option>

                              ),
                            )
                        }

                      </select>

                    </label>


                    <label>

                      <span>
                        Número *
                      </span>

                      <input
                        type="text"
                        value={
                          form.document_number
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "document_number",
                              event.target.value,
                            )
                        }
                        maxLength={50}
                        placeholder="Número de documento"
                        autoComplete="off"
                        aria-invalid={
                          Boolean(
                            formErrors.document_number,
                          )
                        }
                      />

                      {
                        formErrors.document_number
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.document_number
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Complemento
                      </span>

                      <input
                        type="text"
                        value={
                          form.complement
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "complement",
                              event.target.value,
                            )
                        }
                        maxLength={20}
                        placeholder="Ej. 1A"
                        autoComplete="off"
                      />

                    </label>


                    <label>

                      <span>
                        Expedido en *
                      </span>

                      <select
                        value={
                          form.issued_in
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "issued_in",
                              event.target.value,
                            )
                        }
                      >

                        {
                          BOLIVIA_DEPARTMENTS.map(
                            (
                              department
                            ) => (

                              <option
                                key={
                                  department.code
                                }
                                value={
                                  department.code
                                }
                              >
                                {department.name}
                              </option>

                            ),
                          )
                        }

                      </select>

                    </label>

                  </div>


                  <div
                    className="new-patient-auto-check"
                  >

                    {
                      checkingDuplicates
                        ? (
                            <>
                              <LoaderCircle
                                size={17}
                                className="new-patient-spin"
                              />

                              <span>
                                Verificando posibles duplicados...
                              </span>
                            </>
                          )
                        : duplicateChecked
                          &&
                          duplicates.length === 0
                          ? (
                              <>
                                <CheckCircle2
                                  size={17}
                                />

                                <span>
                                  Sin coincidencias detectadas
                                </span>
                              </>
                            )
                          : duplicateChecked
                            &&
                            duplicates.length > 0
                            ? (
                                <>
                                  <ShieldAlert
                                    size={17}
                                  />

                                  <span>
                                    Se encontraron posibles coincidencias
                                  </span>
                                </>
                              )
                            : (
                                <>
                                  <ShieldAlert
                                    size={17}
                                  />

                                  <span>
                                    La comprobación se realizará automáticamente.
                                  </span>
                                </>
                              )
                    }

                  </div>


                  {
                    duplicateChecked
                    &&
                    duplicates.length > 0
                    &&
                    (
                      <div
                        className="new-patient-duplicates"
                      >

                        <div
                          className="new-patient-duplicates__header"
                        >

                          <ShieldAlert
                            size={20}
                          />

                          <div>

                            <strong>
                              Posibles pacientes duplicados
                            </strong>

                            <span>
                              Revise las coincidencias antes de crear un nuevo registro.
                            </span>

                          </div>

                        </div>


                        <div
                          className="new-patient-duplicates__list"
                        >

                          {
                            duplicates.map(
                              (
                                patient
                              ) => (

                                <button
                                  key={
                                    patient.id_patient
                                  }
                                  type="button"
                                  onClick={
                                    () =>
                                      navigate(
                                        `/pacientes/${patient.id_patient}`,
                                      )
                                  }
                                >

                                  <div>

                                    <strong>
                                      {patient.full_name}
                                    </strong>

                                    <span>
                                      {
                                        patient
                                          .primary_document
                                          ?.document_number
                                        ??
                                        "Sin documento"
                                      }
                                    </span>

                                  </div>


                                  <span>
                                    Ver ficha
                                  </span>

                                </button>

                              ),
                            )
                          }

                        </div>

                      </div>
                    )
                  }

                </article>


                {/* ==========================================
                    CONTACTOS DEL PACIENTE
                    ========================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header"
                  >

                    <div>

                      <h2>
                        Contacto del paciente
                      </h2>

                      <p>
                        Registre los medios disponibles. Todos son opcionales.
                      </p>

                    </div>

                  </div>


                  <div
                    className="new-patient-grid new-patient-grid--3"
                  >

                    <label>

                      <span>
                        Celular
                      </span>

                      <input
                        type="text"
                        inputMode="numeric"
                        value={
                          form.mobile_phone
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "mobile_phone",
                              event.target.value,
                            )
                        }
                        maxLength={8}
                        placeholder="Ej. 71234567"
                        aria-invalid={
                          Boolean(
                            formErrors.mobile_phone,
                          )
                        }
                      />

                      {
                        formErrors.mobile_phone
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.mobile_phone
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Teléfono fijo
                      </span>

                      <input
                        type="text"
                        inputMode="numeric"
                        value={
                          form.landline_phone
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "landline_phone",
                              event.target.value,
                            )
                        }
                        maxLength={8}
                        placeholder="Ej. 22123456"
                        aria-invalid={
                          Boolean(
                            formErrors.landline_phone,
                          )
                        }
                      />

                      {
                        formErrors.landline_phone
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.landline_phone
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Correo
                      </span>

                      <input
                        type="email"
                        value={
                          form.email
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "email",
                              event.target.value,
                            )
                        }
                        maxLength={150}
                        placeholder="paciente@correo.com"
                        aria-invalid={
                          Boolean(
                            formErrors.email,
                          )
                        }
                      />

                      {
                        formErrors.email
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.email
                            }
                          </small>
                        )
                      }

                    </label>

                  </div>

                </article>


                {/* ==========================================
                    CONTACTO DE EMERGENCIA
                    ========================================== */}

                <article
                  className="new-patient-card new-patient-card--emergency"
                >

                  <div
                    className="new-patient-card__header"
                  >

                    <div>

                      <h2>
                        Contacto de emergencia
                      </h2>

                      <p>
                        Familiar, tutor o responsable que pueda ser contactado en caso necesario.
                      </p>

                    </div>

                  </div>


                  <div
                    className="new-patient-grid new-patient-grid--4"
                  >

                    <label>

                      <span>
                        Nombre completo
                      </span>

                      <input
                        type="text"
                        value={
                          form.emergency_contact_name
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "emergency_contact_name",
                              event.target.value,
                            )
                        }
                        maxLength={180}
                        placeholder="Ej. María Quispe"
                        aria-invalid={
                          Boolean(
                            formErrors.emergency_contact_name,
                          )
                        }
                      />

                      {
                        formErrors.emergency_contact_name
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.emergency_contact_name
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Parentesco
                      </span>

                      <input
                        type="text"
                        value={
                          form.emergency_relationship
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "emergency_relationship",
                              event.target.value,
                            )
                        }
                        maxLength={80}
                        placeholder="Ej. Madre"
                        aria-invalid={
                          Boolean(
                            formErrors.emergency_relationship,
                          )
                        }
                      />

                      {
                        formErrors.emergency_relationship
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.emergency_relationship
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Teléfono
                      </span>

                      <input
                        type="text"
                        inputMode="numeric"
                        value={
                          form.emergency_phone
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "emergency_phone",
                              event.target.value,
                            )
                        }
                        maxLength={8}
                        placeholder="Ej. 76543210"
                        aria-invalid={
                          Boolean(
                            formErrors.emergency_phone,
                          )
                        }
                      />

                      {
                        formErrors.emergency_phone
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.emergency_phone
                            }
                          </small>
                        )
                      }

                    </label>


                    <label>

                      <span>
                        Correo
                      </span>

                      <input
                        type="email"
                        value={
                          form.emergency_email
                        }
                        onChange={
                          (
                            event
                          ) =>
                            updateField(
                              "emergency_email",
                              event.target.value,
                            )
                        }
                        maxLength={150}
                        placeholder="familiar@correo.com"
                        aria-invalid={
                          Boolean(
                            formErrors.emergency_email,
                          )
                        }
                      />

                      {
                        formErrors.emergency_email
                        &&
                        (
                          <small
                            className="new-patient-field-error"
                          >
                            {
                              formErrors.emergency_email
                            }
                          </small>
                        )
                      }

                    </label>

                  </div>


                  <div
                    className="new-patient-emergency-note"
                  >
                    Si registra algún dato de emergencia,
                    el nombre, parentesco y teléfono serán obligatorios.
                  </div>

                </article>


                {/* ==========================================
                    FOOTER
                    ========================================== */}

                <footer
                  className="new-patient-footer"
                >

                  <button
                    type="button"
                    className="new-patient-cancel"
                    disabled={
                      saving
                    }
                    onClick={
                      () =>
                        navigate(
                          "/pacientes",
                        )
                    }
                  >

                    <X
                      size={17}
                    />

                    Cancelar

                  </button>


                  <button
                    type="submit"
                    className="new-patient-save"
                    disabled={
                      saving
                      ||
                      !formValid
                      ||
                      checkingDuplicates
                      ||
                      !duplicateChecked
                      ||
                      duplicates.length > 0
                    }
                  >

                    {
                      saving
                        ? (
                            <LoaderCircle
                              size={18}
                              className="new-patient-spin"
                            />
                          )
                        : (
                            <Save
                              size={18}
                            />
                          )
                    }

                    {
                      saving
                        ? "Guardando..."
                        : "Registrar paciente"
                    }

                  </button>

                </footer>

              </form>
            )
      }

    </section>

  );
}