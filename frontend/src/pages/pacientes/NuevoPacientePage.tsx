import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  LoaderCircle,
  Plus,
  Save,
  ShieldAlert,
  Trash2,
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
  type CreateEmergencyContactRequest,
  type CreatePatientContactRequest,
  type CreatePatientRequest,
  type PatientCatalogs,
  type PatientSummary,
} from "../../api/pacientes.api";

import "./NuevoPacientePage.css";


// ==========================================================
// FORMULARIO BASE
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

  issued_in:
    BoliviaDepartmentCode;
};


type FormErrors =
  Partial<
    Record<
      keyof FormState,
      string
    >
  >;


const initialForm:
  FormState = {

    first_names: "",

    paternal_surname: "",

    maternal_surname: "",

    birth_date: "",

    sex_id: "",

    document_type_id: "",

    document_number: "",

    complement: "",

    issued_in: "LP",

  };


// ==========================================================
// PARENTESCOS
// ==========================================================

const RELATIONSHIPS = [
  {
    code: "MADRE",
    name: "Madre",
  },
  {
    code: "PADRE",
    name: "Padre",
  },
  {
    code: "HERMANO",
    name: "Hermano",
  },
  {
    code: "HERMANA",
    name: "Hermana",
  },
  {
    code: "HIJO",
    name: "Hijo",
  },
  {
    code: "HIJA",
    name: "Hija",
  },
  {
    code: "ESPOSO",
    name: "Esposo",
  },
  {
    code: "ESPOSA",
    name: "Esposa",
  },
  {
    code: "TUTOR",
    name: "Tutor",
  },
  {
    code: "TUTORA",
    name: "Tutora",
  },
  {
    code: "ABUELO",
    name: "Abuelo",
  },
  {
    code: "ABUELA",
    name: "Abuela",
  },
  {
    code: "TIO",
    name: "Tío",
  },
  {
    code: "TIA",
    name: "Tía",
  },
  {
    code: "PRIMO",
    name: "Primo",
  },
  {
    code: "PRIMA",
    name: "Prima",
  },
  {
    code: "OTRO",
    name: "Otro",
  },
];


// ==========================================================
// HELPERS
// ==========================================================

function normalizeText(
  value:
    string,
): string {

  return value
    .trim()
    .replace(
      /\s+/g,
      " ",
    );

}


function onlyNumbers(
  value:
    string,

  maxLength:
    number,
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
  value:
    string,
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
  error:
    unknown,
): string {

  if (
    typeof error ===
    "object"
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
      typeof data ===
      "object"
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
            .map(
              String,
            )
            .join(
              " ",
            );

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

          const nested =
            Object.values(
              value as Record<
                string,
                unknown
              >,
            );


          const first =
            nested[0];


          if (
            Array.isArray(
              first,
            )
          ) {

            return first
              .map(
                String,
              )
              .join(
                " ",
              );

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


  // ========================================================
  // CATÁLOGOS
  // ========================================================

  const [
    catalogs,
    setCatalogs,
  ] =
    useState<
      PatientCatalogs | null
    >(
      null,
    );


  // ========================================================
  // FORMULARIO BASE
  // ========================================================

  const [
    form,
    setForm,
  ] =
    useState<FormState>(
      initialForm,
    );


  const [
    formErrors,
    setFormErrors,
  ] =
    useState<FormErrors>(
      {},
    );


  // ========================================================
  // CONTACTOS
  // ========================================================

  const [
    contacts,
    setContacts,
  ] =
    useState<
      CreatePatientContactRequest[]
    >([
      {
        contact_type_id:
          1,

        value:
          "",

        primary:
          true,
      },
    ]);


  // ========================================================
  // EMERGENCIA
  // ========================================================

  const [
    emergencyContacts,
    setEmergencyContacts,
  ] =
    useState<
      CreateEmergencyContactRequest[]
    >(
      [],
    );


  // ========================================================
  // ESTADOS
  // ========================================================

  const [
    loadingCatalogs,
    setLoadingCatalogs,
  ] =
    useState(
      true,
    );


  const [
    saving,
    setSaving,
  ] =
    useState(
      false,
    );


  const [
    checkingDuplicates,
    setCheckingDuplicates,
  ] =
    useState(
      false,
    );


  const [
    duplicates,
    setDuplicates,
  ] =
    useState<
      PatientSummary[]
    >(
      [],
    );


  const [
    duplicateChecked,
    setDuplicateChecked,
  ] =
    useState(
      false,
    );


  const [
    error,
    setError,
  ] =
    useState<
      string | null
    >(
      null,
    );


  const [
    success,
    setSuccess,
  ] =
    useState<
      string | null
    >(
      null,
    );


  // ========================================================
  // CATÁLOGOS
  // ========================================================

  useEffect(
    () => {

      let mounted =
        true;


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


          // Solo Masculino / Femenino.

          const filteredCatalogs:
            PatientCatalogs = {

              ...data,

              sexes:
                data.sexes.filter(
                  (
                    item,
                  ) =>
                    item.code === "M"
                    ||
                    item.code === "F",
                ),

            };


          setCatalogs(
            filteredCatalogs,
          );


          const defaultSex =
            filteredCatalogs
              .sexes[0];


          const defaultDocument =
            filteredCatalogs
              .document_types[0];


          const defaultContact =
            filteredCatalogs
              .contact_types[0];


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


          if (
            defaultContact
          ) {

            setContacts(
              (
                current,
              ) =>
                current.map(
                  (
                    item,
                  ) => ({
                    ...item,

                    contact_type_id:
                      defaultContact.id,
                  }),
                ),
            );

          }

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

        mounted =
          false;

      };

    },
    [],
  );


  // ========================================================
  // ACTUALIZAR CAMPO BASE
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
      field === "document_number"
      ||
      field === "document_type_id"
      ||
      field === "first_names"
      ||
      field === "paternal_surname"
      ||
      field === "maternal_surname"
      ||
      field === "birth_date"
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
  // CONTACTOS - AGREGAR
  // ========================================================

  function addContact() {

    const defaultType =
      catalogs
        ?.contact_types[0]
        ?.id
      ??
      1;


    setContacts(
      (
        current,
      ) => [

        ...current,

        {
          contact_type_id:
            defaultType,

          value:
            "",

          primary:
            current.length === 0,
        },

      ],
    );

  }


  // ========================================================
  // CONTACTOS - MODIFICAR
  // ========================================================

  function updateContact(
    index:
      number,

    field:
      keyof CreatePatientContactRequest,

    value:
      string | number | boolean,
  ) {

    setContacts(
      (
        current,
      ) =>
        current.map(
          (
            item,
            itemIndex,
          ) => {

            if (
              itemIndex !==
              index
            ) {

              return item;

            }


            return {

              ...item,

              [field]:
                value,

            };

          },
        ),
    );


    setError(
      null,
    );

  }


  // ========================================================
  // CONTACTOS - PRINCIPAL
  // ========================================================

  function setPrimaryContact(
    index:
      number,
  ) {

    setContacts(
      (
        current,
      ) =>
        current.map(
          (
            item,
            itemIndex,
          ) => ({

            ...item,

            primary:
              itemIndex ===
              index,

          }),
        ),
    );

  }


  // ========================================================
  // CONTACTOS - ELIMINAR
  // ========================================================

  function removeContact(
    index:
      number,
  ) {

    setContacts(
      (
        current,
      ) => {

        const next =
          current.filter(
            (
              _,
              itemIndex,
            ) =>
              itemIndex !==
              index,
          );


        if (
          next.length > 0
          &&
          !next.some(
            (
              item,
            ) =>
              item.primary,
          )
        ) {

          next[0] = {

            ...next[0],

            primary:
              true,

          };

        }


        return next;

      },
    );

  }


  // ========================================================
  // CONTACTOS - NORMALIZAR VALOR
  // ========================================================

  function updateContactValue(
    index:
      number,

    value:
      string,
  ) {

    const contact =
      contacts[
        index
      ];


    const type =
      catalogs
        ?.contact_types
        .find(
          (
            item,
          ) =>
            item.id ===
            contact
              ?.contact_type_id,
        );


    let normalized =
      value;


    if (
      type?.code ===
      "CELULAR"
    ) {

      normalized =
        onlyNumbers(
          value,
          8,
        );

    }


    if (
      type?.code ===
      "TELEFONO"
    ) {

      normalized =
        onlyNumbers(
          value,
          8,
        );

    }


    if (
      type?.code ===
      "CORREO"
    ) {

      normalized =
        value
          .toLowerCase()
          .trimStart();

    }


    updateContact(
      index,
      "value",
      normalized,
    );

  }


  // ========================================================
  // EMERGENCIA - AGREGAR
  // ========================================================

  function addEmergencyContact() {

    setEmergencyContacts(
      (
        current,
      ) => [

        ...current,

        {
          full_name:
            "",

          relationship:
            "MADRE",

          phone:
            "",

          email:
            "",

          primary:
            current.length === 0,
        },

      ],
    );

  }


  // ========================================================
  // EMERGENCIA - MODIFICAR
  // ========================================================

  function updateEmergencyContact(
    index:
      number,

    field:
      keyof CreateEmergencyContactRequest,

    value:
      string | boolean,
  ) {

    setEmergencyContacts(
      (
        current,
      ) =>
        current.map(
          (
            item,
            itemIndex,
          ) => {

            if (
              itemIndex !==
              index
            ) {

              return item;

            }


            return {

              ...item,

              [field]:
                value,

            };

          },
        ),
    );


    setError(
      null,
    );

  }


  // ========================================================
  // EMERGENCIA - PRINCIPAL
  // ========================================================

  function setPrimaryEmergencyContact(
    index:
      number,
  ) {

    setEmergencyContacts(
      (
        current,
      ) =>
        current.map(
          (
            item,
            itemIndex,
          ) => ({

            ...item,

            primary:
              itemIndex ===
              index,

          }),
        ),
    );

  }


  // ========================================================
  // EMERGENCIA - ELIMINAR
  // ========================================================

  function removeEmergencyContact(
    index:
      number,
  ) {

    setEmergencyContacts(
      (
        current,
      ) => {

        const next =
          current.filter(
            (
              _,
              itemIndex,
            ) =>
              itemIndex !==
              index,
          );


        if (
          next.length > 0
          &&
          !next.some(
            (
              item,
            ) =>
              item.primary,
          )
        ) {

          next[0] = {

            ...next[0],

            primary:
              true,

          };

        }


        return next;

      },
    );

  }


  // ========================================================
  // ERROR DE UN CONTACTO
  // ========================================================

  function getContactError(
    contact:
      CreatePatientContactRequest,
  ): string | null {

    if (
      !contact.value.trim()
    ) {

      return null;

    }


    const type =
      catalogs
        ?.contact_types
        .find(
          (
            item,
          ) =>
            item.id ===
            contact.contact_type_id,
        );


    if (
      type?.code ===
      "CELULAR"
      &&
      !/^[67]\d{7}$/.test(
        contact.value,
      )
    ) {

      return (
        "El celular debe tener 8 dígitos y comenzar con 6 o 7."
      );

    }


    if (
      type?.code ===
      "TELEFONO"
      &&
      !/^\d{7,8}$/.test(
        contact.value,
      )
    ) {

      return (
        "El teléfono fijo debe tener entre 7 y 8 dígitos."
      );

    }


    if (
      type?.code ===
      "CORREO"
      &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        contact.value,
      )
    ) {

      return (
        "Ingrese un correo válido."
      );

    }


    return null;

  }


  // ========================================================
  // ERROR DE EMERGENCIA
  // ========================================================

  function getEmergencyError(
    contact:
      CreateEmergencyContactRequest,
  ): string | null {

    if (
      normalizeText(
        contact.full_name,
      ).length < 3
    ) {

      return (
        "Ingrese el nombre completo."
      );

    }


    if (
      !contact.relationship
    ) {

      return (
        "Seleccione el parentesco."
      );

    }


    if (
      !/^[67]\d{7}$/.test(
        contact.phone,
      )
    ) {

      return (
        "El teléfono debe tener 8 dígitos y comenzar con 6 o 7."
      );

    }


    if (
      contact.email
      &&
      !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(
        contact.email,
      )
    ) {

      return (
        "Ingrese un correo válido."
      );

    }


    return null;

  }


  // ========================================================
  // VALIDACIONES GENERALES
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


    return errors;

  }


  // ========================================================
  // VALIDACIÓN COMPLETA
  // ========================================================

  const dynamicValid =
    useMemo(
      () => {

        const contactsValid =
          contacts.every(
            (
              item,
            ) =>
              !getContactError(
                item,
              ),
          );


        const emergencyValid =
          emergencyContacts.every(
            (
              item,
            ) =>
              !getEmergencyError(
                item,
              ),
          );


        return (
          contactsValid
          &&
          emergencyValid
        );

      },
      [
        contacts,
        emergencyContacts,
        catalogs,
      ],
    );


  const formValid =
    useMemo(
      () =>
        Object.keys(
          validateForm(),
        ).length === 0
        &&
        dynamicValid,
      [
        form,
        dynamicValid,
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
          documentNumber.length >= 4,
        );


      const canCheckByIdentity =
        Boolean(
          firstNames.length >= 2
          &&
          paternalSurname.length >= 2
          &&
          form.birth_date,
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

        cancelled =
          true;


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


    const contactError =
      contacts
        .map(
          getContactError,
        )
        .find(
          Boolean,
        );


    if (
      contactError
    ) {

      setError(
        contactError,
      );


      return;

    }


    const emergencyError =
      emergencyContacts
        .map(
          getEmergencyError,
        )
        .find(
          Boolean,
        );


    if (
      emergencyError
    ) {

      setError(
        emergencyError,
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
        "Se encontraron posibles pacientes duplicados. Revise las coincidencias antes de continuar.",
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

      contacts:
        contacts
          .filter(
            (
              item,
            ) =>
              item.value.trim(),
          )
          .map(
            (
              item,
            ) => ({

              contact_type_id:
                item.contact_type_id,

              value:
                item.value.trim(),

              primary:
                item.primary,

            }),
          ),

      emergency_contacts:
        emergencyContacts.map(
          (
            item,
          ) => ({

            full_name:
              normalizeText(
                item.full_name,
              ),

            relationship:
              item.relationship,

            phone:
              item.phone,

            email:
              normalizeText(
                item.email
                ??
                "",
              )
                .toLowerCase()
              ||
              null,

            primary:
              item.primary,

          }),
        ),

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
              y responsables para emergencias.
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

                {/* ========================================
                    DATOS PERSONALES
                    ======================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header"
                  >
                    <h2>
                      Datos personales
                    </h2>

                    <p>
                      Información principal de identificación.
                    </p>
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
                            event,
                          ) =>
                            updateField(
                              "first_names",
                              event.target.value,
                            )
                        }
                        maxLength={100}
                        placeholder="Ej. María Fernanda"
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
                            {formErrors.first_names}
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
                            event,
                          ) =>
                            updateField(
                              "paternal_surname",
                              event.target.value,
                            )
                        }
                        maxLength={80}
                        placeholder="Ej. López"
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
                            {formErrors.paternal_surname}
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
                            event,
                          ) =>
                            updateField(
                              "maternal_surname",
                              event.target.value,
                            )
                        }
                        maxLength={80}
                        placeholder="Ej. Flores"
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
                            event,
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
                            {formErrors.birth_date}
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
                            event,
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


                {/* ========================================
                    DOCUMENTO
                    ======================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header"
                  >
                    <h2>
                      Documento de identidad
                    </h2>

                    <p>
                      Se verifican automáticamente posibles duplicados.
                    </p>
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
                            event,
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
                                item,
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
                            event,
                          ) =>
                            updateField(
                              "document_number",
                              event.target.value,
                            )
                        }
                        maxLength={50}
                        placeholder="Número de documento"
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
                            {formErrors.document_number}
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
                            event,
                          ) =>
                            updateField(
                              "complement",
                              event.target.value,
                            )
                        }
                        maxLength={20}
                        placeholder="Ej. 1A"
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
                            event,
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
                              department,
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
                              Verificando posibles duplicados...
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
                                Sin coincidencias detectadas
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
                                  Se encontraron posibles coincidencias
                                </>
                              )
                            : (
                                <>
                                  <ShieldAlert
                                    size={17}
                                  />
                                  La comprobación se realizará automáticamente.
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
                              Revise las coincidencias antes de continuar.
                            </span>
                          </div>
                        </div>


                        <div
                          className="new-patient-duplicates__list"
                        >
                          {
                            duplicates.map(
                              (
                                patient,
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


                {/* ========================================
                    CONTACTOS DEL PACIENTE
                    ======================================== */}

                <article
                  className="new-patient-card"
                >

                  <div
                    className="new-patient-card__header new-patient-card__header--actions"
                  >
                    <div>
                      <h2>
                        Contactos del paciente
                      </h2>

                      <p>
                        Puede registrar varios celulares, teléfonos o correos.
                      </p>
                    </div>


                    <button
                      type="button"
                      className="new-patient-add-button"
                      onClick={
                        addContact
                      }
                    >
                      <Plus
                        size={16}
                      />

                      Agregar contacto
                    </button>
                  </div>


                  {
                    contacts.length === 0
                      ? (
                          <div
                            className="new-patient-dynamic-empty"
                          >
                            No se registraron medios de contacto.
                          </div>
                        )
                      : (
                          <div
                            className="new-patient-dynamic-list"
                          >
                            {
                              contacts.map(
                                (
                                  contact,
                                  index,
                                ) => {

                                  const rowError =
                                    getContactError(
                                      contact,
                                    );


                                  const currentType =
                                    catalogs
                                      ?.contact_types
                                      .find(
                                        (
                                          item,
                                        ) =>
                                          item.id ===
                                          contact.contact_type_id,
                                      );


                                  return (
                                    <div
                                      className="new-patient-dynamic-row new-patient-dynamic-row--contact"
                                      key={
                                        index
                                      }
                                    >

                                      <label>
                                        <span>
                                          Tipo
                                        </span>

                                        <select
                                          value={
                                            contact.contact_type_id
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) => {
                                              updateContact(
                                                index,
                                                "contact_type_id",
                                                Number(
                                                  event.target.value,
                                                ),
                                              );

                                              updateContact(
                                                index,
                                                "value",
                                                "",
                                              );
                                            }
                                          }
                                        >
                                          {
                                            catalogs
                                              ?.contact_types
                                              .map(
                                                (
                                                  item,
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
                                          {
                                            currentType?.code === "CORREO"
                                              ? "Correo"
                                              : "Número"
                                          }
                                        </span>

                                        <input
                                          type={
                                            currentType?.code === "CORREO"
                                              ? "email"
                                              : "text"
                                          }
                                          inputMode={
                                            currentType?.code === "CORREO"
                                              ? undefined
                                              : "numeric"
                                          }
                                          value={
                                            contact.value
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) =>
                                              updateContactValue(
                                                index,
                                                event.target.value,
                                              )
                                          }
                                          placeholder={
                                            currentType?.code === "CORREO"
                                              ? "paciente@correo.com"
                                              : currentType?.code === "TELEFONO"
                                                ? "22123456"
                                                : "71234567"
                                          }
                                          aria-invalid={
                                            Boolean(
                                              rowError,
                                            )
                                          }
                                        />

                                        {
                                          rowError
                                          &&
                                          (
                                            <small
                                              className="new-patient-field-error"
                                            >
                                              {rowError}
                                            </small>
                                          )
                                        }
                                      </label>


                                      <label
                                        className="new-patient-primary-option"
                                      >
                                        <span>
                                          Principal
                                        </span>

                                        <input
                                          type="radio"
                                          name="primary-contact"
                                          checked={
                                            contact.primary
                                          }
                                          onChange={
                                            () =>
                                              setPrimaryContact(
                                                index,
                                              )
                                          }
                                        />
                                      </label>


                                      <button
                                        type="button"
                                        className="new-patient-remove-button"
                                        onClick={
                                          () =>
                                            removeContact(
                                              index,
                                            )
                                        }
                                        title="Eliminar contacto"
                                      >
                                        <Trash2
                                          size={17}
                                        />
                                      </button>

                                    </div>
                                  );
                                },
                              )
                            }
                          </div>
                        )
                  }

                </article>


                {/* ========================================
                    CONTACTOS DE EMERGENCIA
                    ======================================== */}

                <article
                  className="new-patient-card new-patient-card--emergency"
                >

                  <div
                    className="new-patient-card__header new-patient-card__header--actions"
                  >
                    <div>
                      <h2>
                        Contactos de emergencia
                      </h2>

                      <p>
                        Registre familiares, tutores o responsables.
                      </p>
                    </div>


                    <button
                      type="button"
                      className="new-patient-add-button"
                      onClick={
                        addEmergencyContact
                      }
                    >
                      <Plus
                        size={16}
                      />

                      Agregar contacto de emergencia
                    </button>
                  </div>


                  {
                    emergencyContacts.length === 0
                      ? (
                          <div
                            className="new-patient-dynamic-empty"
                          >
                            No se registraron contactos de emergencia.
                          </div>
                        )
                      : (
                          <div
                            className="new-patient-dynamic-list"
                          >
                            {
                              emergencyContacts.map(
                                (
                                  contact,
                                  index,
                                ) => {

                                  const rowError =
                                    getEmergencyError(
                                      contact,
                                    );


                                  return (
                                    <div
                                      className="new-patient-dynamic-row new-patient-dynamic-row--emergency"
                                      key={
                                        index
                                      }
                                    >

                                      <label>
                                        <span>
                                          Nombre completo *
                                        </span>

                                        <input
                                          type="text"
                                          value={
                                            contact.full_name
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) =>
                                              updateEmergencyContact(
                                                index,
                                                "full_name",
                                                event.target.value,
                                              )
                                          }
                                          placeholder="Ej. María Quispe"
                                        />
                                      </label>


                                      <label>
                                        <span>
                                          Parentesco *
                                        </span>

                                        <select
                                          value={
                                            contact.relationship
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) =>
                                              updateEmergencyContact(
                                                index,
                                                "relationship",
                                                event.target.value,
                                              )
                                          }
                                        >
                                          {
                                            RELATIONSHIPS.map(
                                              (
                                                item,
                                              ) => (
                                                <option
                                                  key={
                                                    item.code
                                                  }
                                                  value={
                                                    item.code
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
                                          Teléfono *
                                        </span>

                                        <input
                                          type="text"
                                          inputMode="numeric"
                                          value={
                                            contact.phone
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) =>
                                              updateEmergencyContact(
                                                index,
                                                "phone",
                                                onlyNumbers(
                                                  event.target.value,
                                                  8,
                                                ),
                                              )
                                          }
                                          maxLength={8}
                                          placeholder="76543210"
                                        />
                                      </label>


                                      <label>
                                        <span>
                                          Correo
                                        </span>

                                        <input
                                          type="email"
                                          value={
                                            contact.email
                                            ??
                                            ""
                                          }
                                          onChange={
                                            (
                                              event,
                                            ) =>
                                              updateEmergencyContact(
                                                index,
                                                "email",
                                                event.target.value
                                                  .toLowerCase(),
                                              )
                                          }
                                          placeholder="familiar@correo.com"
                                        />

                                        {
                                          rowError
                                          &&
                                          (
                                            <small
                                              className="new-patient-field-error"
                                            >
                                              {rowError}
                                            </small>
                                          )
                                        }
                                      </label>


                                      <label
                                        className="new-patient-primary-option"
                                      >
                                        <span>
                                          Principal
                                        </span>

                                        <input
                                          type="radio"
                                          name="primary-emergency"
                                          checked={
                                            contact.primary
                                          }
                                          onChange={
                                            () =>
                                              setPrimaryEmergencyContact(
                                                index,
                                              )
                                          }
                                        />
                                      </label>


                                      <button
                                        type="button"
                                        className="new-patient-remove-button"
                                        onClick={
                                          () =>
                                            removeEmergencyContact(
                                              index,
                                            )
                                        }
                                        title="Eliminar contacto"
                                      >
                                        <Trash2
                                          size={17}
                                        />
                                      </button>

                                    </div>
                                  );
                                },
                              )
                            }
                          </div>
                        )
                  }


                  <div
                    className="new-patient-emergency-note"
                  >
                    Si agrega un contacto de emergencia,
                    nombre, parentesco y teléfono son obligatorios.
                    Solo uno puede estar marcado como principal.
                  </div>

                </article>


                {/* ========================================
                    BOTONES
                    ======================================== */}

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