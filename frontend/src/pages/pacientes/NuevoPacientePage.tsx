import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  LoaderCircle,
  Save,
  Search,
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
  createPatient,
  findPossibleDuplicates,
  getPatientCatalogs,
  type CatalogItem,
  type CreatePatientRequest,
  type PatientCatalogs,
  type PatientSummary,
} from "../../api/pacientes.api";

import "./NuevoPacientePage.css";


// ==========================================================
// ESTADO INICIAL
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

  issued_in: string;

  contact_type_id: string;

  contact_value: string;

};


const initialForm: FormState = {

  first_names: "",

  paternal_surname: "",

  maternal_surname: "",

  birth_date: "",

  sex_id: "",

  document_type_id: "",

  document_number: "",

  complement: "",

  issued_in: "",

  contact_type_id: "",

  contact_value: "",

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
          data?: {
            error?: {
              message?: string;
            };
            detail?: string;
          };
        };
      };


    return (
      maybeAxios
        .response
        ?.data
        ?.error
        ?.message
      ??
      maybeAxios
        .response
        ?.data
        ?.detail
      ??
      "No fue posible registrar el paciente."
    );

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
  >(null);


  const [
    form,
    setForm,
  ] = useState<FormState>(
    initialForm,
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
  >([]);


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
  >(null);


  const [
    success,
    setSuccess,
  ] = useState<
    string | null
  >(null);


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


          if (!mounted) {

            return;

          }


          setCatalogs(
            data,
          );


          const defaultSex =
            data.sexes[0];


          const defaultDocument =
            data.document_types[0];


          const defaultContact =
            data.contact_types[0];


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

              contact_type_id:
                current.contact_type_id
                ||
                (
                  defaultContact
                    ? String(
                        defaultContact.id,
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
  // VALIDACIONES
  // ========================================================

  const formValid =
    useMemo(
      () => {

        return Boolean(

          normalizeText(
            form.first_names,
          ).length >= 2

          &&

          normalizeText(
            form.paternal_surname,
          ).length >= 2

          &&

          form.birth_date

          &&

          form.sex_id

          &&

          form.document_type_id

          &&

          normalizeText(
            form.document_number,
          )

        );

      },
      [
        form,
      ],
    );


  // ========================================================
  // CAMBIOS DE INPUT
  // ========================================================

  function updateField(
    field: keyof FormState,
    value: string,
  ) {

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
  // DUPLICADOS
  // ========================================================

  async function checkDuplicates() {

    setError(
      null,
    );


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


    if (
      !documentNumber
      &&
      (
        !firstNames
        ||
        !paternalSurname
      )
    ) {

      setError(
        "Ingrese documento o nombres y apellido paterno para buscar posibles duplicados.",
      );

      return;

    }


    setCheckingDuplicates(
      true,
    );


    try {

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
                || undefined,

            first_names:
              firstNames
                || undefined,

            paternal_surname:
              paternalSurname
                || undefined,

            maternal_surname:
              normalizeText(
                form.maternal_surname,
              )
                || undefined,

            birth_date:
              form.birth_date
                || undefined,

          },
        );


      setDuplicates(
        response.data,
      );


      setDuplicateChecked(
        true,
      );

    } catch {

      setError(
        "No fue posible verificar posibles duplicados.",
      );

    } finally {

      setCheckingDuplicates(
        false,
      );

    }

  }


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


    if (
      !formValid
    ) {

      setError(
        "Complete correctamente los campos obligatorios.",
      );

      return;

    }


    if (
      !duplicateChecked
    ) {

      setError(
        "Antes de guardar, verifique si existen posibles pacientes duplicados.",
      );

      return;

    }


    if (
      duplicates.length > 0
    ) {

      setError(
        "Se encontraron posibles duplicados. Revise las coincidencias antes de continuar.",
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
          || null,

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
          || null,

      issued_in:
        normalizeText(
          form.issued_in,
        )
          || null,

      contact_type_id:
        form.contact_type_id
          ? Number(
              form.contact_type_id,
            )
          : null,

      contact_value:
        normalizeText(
          form.contact_value,
        )
          || null,

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
              Registre los datos personales, documento y contacto principal del paciente.
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

      {error && (

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

      )}


      {success && (

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

      )}


      {loadingCatalogs ? (

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

      ) : (

        <form
          className="new-patient-form"
          onSubmit={
            handleSubmit
          }
        >


          {/* ==============================================
              DATOS PERSONALES
              ============================================== */}

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
                    (event) =>
                      updateField(
                        "first_names",
                        event.target.value,
                      )
                  }
                  maxLength={100}
                  placeholder="Ej. Maria Fernanda"
                  autoComplete="off"
                />
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
                    (event) =>
                      updateField(
                        "paternal_surname",
                        event.target.value,
                      )
                  }
                  maxLength={80}
                  placeholder="Ej. López"
                  autoComplete="off"
                />
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
                    (event) =>
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
                    (event) =>
                      updateField(
                        "birth_date",
                        event.target.value,
                      )
                  }
                />
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
                    (event) =>
                      updateField(
                        "sex_id",
                        event.target.value,
                      )
                  }
                >

                  {catalogs
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
                    )}

                </select>
              </label>

            </div>

          </article>


          {/* ==============================================
              DOCUMENTO
              ============================================== */}

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
                  El documento será utilizado para prevenir registros duplicados.
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
                    (event) =>
                      updateField(
                        "document_type_id",
                        event.target.value,
                      )
                  }
                >

                  {catalogs
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
                    )}

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
                    (event) =>
                      updateField(
                        "document_number",
                        event.target.value,
                      )
                  }
                  maxLength={50}
                  placeholder="Número de documento"
                  autoComplete="off"
                />
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
                    (event) =>
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
                  Expedido en
                </span>

                <input
                  type="text"
                  value={
                    form.issued_in
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "issued_in",
                        event.target.value,
                      )
                  }
                  maxLength={40}
                  placeholder="Ej. LP"
                  autoComplete="off"
                />
              </label>

            </div>


            <div
              className="new-patient-duplicate-actions"
            >

              <button
                type="button"
                className="new-patient-check-button"
                disabled={
                  checkingDuplicates
                }
                onClick={
                  () =>
                    void checkDuplicates()
                }
              >

                {checkingDuplicates
                  ? (
                    <LoaderCircle
                      size={17}
                      className="new-patient-spin"
                    />
                  )
                  : (
                    <Search
                      size={17}
                    />
                  )}

                Verificar duplicados

              </button>


              {duplicateChecked
                &&
                duplicates.length === 0
                &&
                (

                  <span
                    className="new-patient-check-ok"
                  >
                    <CheckCircle2
                      size={17}
                    />

                    Sin coincidencias detectadas
                  </span>

                )}

            </div>


            {duplicateChecked
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
                        Se encontraron posibles duplicados
                      </strong>

                      <span>
                        Revise los registros antes de crear un nuevo paciente.
                      </span>
                    </div>
                  </div>


                  <div
                    className="new-patient-duplicates__list"
                  >

                    {duplicates.map(
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
                    )}

                  </div>

                </div>

              )}

          </article>


          {/* ==============================================
              CONTACTO
              ============================================== */}

          <article
            className="new-patient-card"
          >

            <div
              className="new-patient-card__header"
            >
              <div>
                <h2>
                  Contacto principal
                </h2>

                <p>
                  Información de contacto del paciente.
                </p>
              </div>
            </div>


            <div
              className="new-patient-grid new-patient-grid--2"
            >

              <label>
                <span>
                  Tipo de contacto
                </span>

                <select
                  value={
                    form.contact_type_id
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "contact_type_id",
                        event.target.value,
                      )
                  }
                >

                  <option value="">
                    Sin contacto
                  </option>


                  {catalogs
                    ?.contact_types
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
                    )}

                </select>
              </label>


              <label>
                <span>
                  Valor
                </span>

                <input
                  type="text"
                  value={
                    form.contact_value
                  }
                  onChange={
                    (event) =>
                      updateField(
                        "contact_value",
                        event.target.value,
                      )
                  }
                  maxLength={150}
                  placeholder="Teléfono o correo"
                  autoComplete="off"
                />
              </label>

            </div>

          </article>


          {/* ==============================================
              FOOTER
              ============================================== */}

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
              }
            >

              {saving
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
                )}

              {saving
                ? "Guardando..."
                : "Registrar paciente"}

            </button>

          </footer>


        </form>

      )}

    </section>

  );

}