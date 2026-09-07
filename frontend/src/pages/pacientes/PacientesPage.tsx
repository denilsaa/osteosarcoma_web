import {
  Activity,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  Eye,
  Filter,
  LoaderCircle,
  Plus,
  RefreshCw,
  Search,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
} from "react-router-dom";

import {
  getPatientCatalogs,
  listPatients,
  type PatientCatalogs,
  type PatientSummary,
} from "../../api/pacientes.api";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./PacientesPage.css";


// ==========================================================
// CONSTANTES
// ==========================================================

const PAGE_SIZE = 10;


// ==========================================================
// HELPERS
// ==========================================================

function formatDate(
  value?: string | null,
): string {

  if (!value) {

    return "—";

  }


  const date =
    new Date(
      `${value}T00:00:00`,
    );


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {

    return value;

  }


  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    },
  ).format(
    date,
  );

}


function formatDateTime(
  value?: string | null,
): string {

  if (!value) {

    return "—";

  }


  const date =
    new Date(value);


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {

    return value;

  }


  return new Intl.DateTimeFormat(
    "es-BO",
    {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    },
  ).format(
    date,
  );

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function PacientesPage() {

  const navigate =
    useNavigate();


  const {
    tieneRol,
    tienePermiso,
  } = useAuth();


  // ========================================================
  // PERMISOS VISUALES
  // ========================================================

  const puedeRegistrar =
    tieneRol(
      "JEFE_ONCOLOGIA",
    )
    ||
    tieneRol(
      "ONCOLOGO",
    )
    ||
    tienePermiso(
      "PACIENTES_CREAR",
    );


  // ========================================================
  // ESTADO
  // ========================================================

  const [
    patients,
    setPatients,
  ] = useState<
    PatientSummary[]
  >([]);


  const [
    catalogs,
    setCatalogs,
  ] = useState<
    PatientCatalogs | null
  >(null);


  const [
    searchInput,
    setSearchInput,
  ] = useState(
    "",
  );


  const [
    appliedSearch,
    setAppliedSearch,
  ] = useState(
    "",
  );


  const [
    sexCode,
    setSexCode,
  ] = useState(
    "",
  );


  const [
    documentTypeCode,
    setDocumentTypeCode,
  ] = useState(
    "",
  );


  const [
    activeFilter,
    setActiveFilter,
  ] = useState(
    "",
  );


  const [
    page,
    setPage,
  ] = useState(
    1,
  );


  const [
    total,
    setTotal,
  ] = useState(
    0,
  );


  const [
    totalPages,
    setTotalPages,
  ] = useState(
    1,
  );


  const [
    loading,
    setLoading,
  ] = useState(
    true,
  );


  const [
    error,
    setError,
  ] = useState<
    string | null
  >(null);


  // ========================================================
  // CARGAR CATÁLOGOS
  // ========================================================

  useEffect(
    () => {

      let mounted = true;


      async function loadCatalogs() {

        try {

          const data =
            await getPatientCatalogs();


          if (mounted) {

            setCatalogs(
              data,
            );

          }

        } catch {

          if (mounted) {

            setError(
              "No fue posible cargar los catálogos de pacientes.",
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
  // CARGAR PACIENTES
  // ========================================================

  const loadPatients =
    useCallback(
      async () => {

        setLoading(
          true,
        );

        setError(
          null,
        );


        try {

          const active =
            activeFilter ===
              "true"

              ? true

              : activeFilter ===
                "false"

                ? false

                : undefined;


          const response =
            await listPatients(
              {
                search:
                  appliedSearch ||
                  undefined,

                sex_code:
                  sexCode ||
                  undefined,

                active,

                document_type_code:
                  documentTypeCode ||
                  undefined,

                page,

                page_size:
                  PAGE_SIZE,
              },
            );


          setPatients(
            response.data,
          );


          setTotal(
            response
              .pagination
              .total,
          );


          setTotalPages(
            response
              .pagination
              .total_pages,
          );

        } catch {

          setPatients(
            [],
          );


          setTotal(
            0,
          );


          setTotalPages(
            1,
          );


          setError(
            "No fue posible cargar los pacientes. Verifique la conexión con el servicio clínico.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        activeFilter,
        appliedSearch,
        documentTypeCode,
        page,
        sexCode,
      ],
    );


  useEffect(
    () => {

      void loadPatients();

    },
    [
      loadPatients,
    ],
  );


  // ========================================================
  // MÉTRICAS
  // ========================================================

  const activePatients =
    useMemo(
      () =>
        patients.filter(
          (patient) =>
            patient.active,
        ).length,
      [
        patients,
      ],
    );


  const casesInPage =
    useMemo(
      () =>
        patients.reduce(
          (
            totalCases,
            patient,
          ) =>
            totalCases
            +
            patient
              .clinical_cases_count,
          0,
        ),
      [
        patients,
      ],
    );


  // ========================================================
  // ACCIONES
  // ========================================================

  function handleSearchSubmit(
    event:
      React.FormEvent,
  ) {

    event.preventDefault();


    setPage(
      1,
    );


    setAppliedSearch(
      searchInput.trim(),
    );

  }


  function clearFilters() {

    setSearchInput(
      "",
    );

    setAppliedSearch(
      "",
    );

    setSexCode(
      "",
    );

    setDocumentTypeCode(
      "",
    );

    setActiveFilter(
      "",
    );

    setPage(
      1,
    );

  }


  const hasFilters =
    Boolean(
      appliedSearch
      ||
      sexCode
      ||
      documentTypeCode
      ||
      activeFilter,
    );


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="patients-page"
    >


      {/* ==================================================
          ENCABEZADO
          ================================================== */}

      <header
        className="patients-header"
      >

        <div>

          <span
            className="patients-header__eyebrow"
          >
            Gestión clínica
          </span>


          <h1>
            Pacientes
          </h1>


          <p>
            Consulta, búsqueda y seguimiento de pacientes registrados en el sistema.
          </p>

        </div>


        {puedeRegistrar && (

          <button
            type="button"
            className="patients-primary-button"
            onClick={
              () =>
                navigate(
                  "/pacientes/nuevo",
                )
            }
          >

            <Plus
              size={18}
              strokeWidth={2.2}
            />

            Registrar paciente

          </button>

        )}

      </header>


      {/* ==================================================
          KPIS
          ================================================== */}

      <div
        className="patients-kpis"
      >

        <article
          className="patients-kpi-card"
        >

          <div
            className="patients-kpi-card__icon"
          >
            <UsersRound
              size={22}
            />
          </div>


          <div>

            <span>
              Pacientes encontrados
            </span>

            <strong>
              {total}
            </strong>

          </div>

        </article>


        <article
          className="patients-kpi-card"
        >

          <div
            className="patients-kpi-card__icon"
          >
            <UserRound
              size={22}
            />
          </div>


          <div>

            <span>
              Activos en esta página
            </span>

            <strong>
              {activePatients}
            </strong>

          </div>

        </article>


        <article
          className="patients-kpi-card"
        >

          <div
            className="patients-kpi-card__icon"
          >
            <Activity
              size={22}
            />
          </div>


          <div>

            <span>
              Casos en esta página
            </span>

            <strong>
              {casesInPage}
            </strong>

          </div>

        </article>

      </div>


      {/* ==================================================
          BUSCADOR Y FILTROS
          ================================================== */}

      <div
        className="patients-toolbar"
      >

        <form
          className="patients-search"
          onSubmit={
            handleSearchSubmit
          }
        >

          <Search
            size={19}
            className="patients-search__icon"
          />


          <input
            type="search"
            value={
              searchInput
            }
            onChange={
              (event) =>
                setSearchInput(
                  event.target.value,
                )
            }
            placeholder="Buscar por nombre, apellido, documento o contacto..."
          />


          <button
            type="submit"
          >
            Buscar
          </button>

        </form>


        <button
          type="button"
          className="patients-refresh-button"
          onClick={
            () =>
              void loadPatients()
          }
          title="Actualizar listado"
          aria-label="Actualizar listado"
        >

          <RefreshCw
            size={18}
          />

        </button>

      </div>


      <div
        className="patients-filter-card"
      >

        <div
          className="patients-filter-card__title"
        >

          <Filter
            size={18}
          />

          <span>
            Filtros
          </span>

        </div>


        <div
          className="patients-filters"
        >

          <label>

            <span>
              Sexo
            </span>

            <select
              value={
                sexCode
              }
              onChange={
                (event) => {

                  setSexCode(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option value="">
                Todos
              </option>


              {catalogs
                ?.sexes
                .map(
                  (item) => (

                    <option
                      key={
                        item.id
                      }
                      value={
                        item.code
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
              Documento
            </span>

            <select
              value={
                documentTypeCode
              }
              onChange={
                (event) => {

                  setDocumentTypeCode(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option value="">
                Todos
              </option>


              {catalogs
                ?.document_types
                .map(
                  (item) => (

                    <option
                      key={
                        item.id
                      }
                      value={
                        item.code
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
              Estado
            </span>

            <select
              value={
                activeFilter
              }
              onChange={
                (event) => {

                  setActiveFilter(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option value="">
                Todos
              </option>

              <option value="true">
                Activos
              </option>

              <option value="false">
                Inactivos
              </option>

            </select>

          </label>


          {hasFilters && (

            <button
              type="button"
              className="patients-clear-button"
              onClick={
                clearFilters
              }
            >

              <X
                size={17}
              />

              Limpiar

            </button>

          )}

        </div>

      </div>


      {/* ==================================================
          ERROR
          ================================================== */}

      {error && (

        <div
          className="patients-message patients-message--error"
        >

          <CircleAlert
            size={19}
          />

          <span>
            {error}
          </span>

        </div>

      )}


      {/* ==================================================
          TABLA
          ================================================== */}

      <div
        className="patients-table-card"
      >

        <div
          className="patients-table-card__header"
        >

          <div>

            <h2>
              Listado de pacientes
            </h2>

            <p>
              {total === 1
                ? "1 registro encontrado."
                : `${total} registros encontrados.`}
            </p>

          </div>

        </div>


        {loading ? (

          <div
            className="patients-loading"
          >

            <LoaderCircle
              size={28}
              className="patients-spin"
            />

            <span>
              Cargando pacientes...
            </span>

          </div>

        ) : patients.length === 0 ? (

          <div
            className="patients-empty"
          >

            <UsersRound
              size={38}
            />

            <h3>
              No se encontraron pacientes
            </h3>

            <p>
              Cambie los criterios de búsqueda o registre un nuevo paciente.
            </p>

          </div>

        ) : (

          <div
            className="patients-table-wrapper"
          >

            <table
              className="patients-table"
            >

              <thead>

                <tr>

                  <th>
                    Paciente
                  </th>

                  <th>
                    Documento
                  </th>

                  <th>
                    Contacto
                  </th>

                  <th>
                    Nacimiento
                  </th>

                  <th>
                    Estado
                  </th>

                  <th>
                    Casos
                  </th>

                  <th>
                    Registro
                  </th>

                  <th
                    aria-label="Acciones"
                  />

                </tr>

              </thead>


              <tbody>

                {patients.map(
                  (patient) => (

                    <tr
                      key={
                        patient.id_patient
                      }
                    >

                      <td>

                        <div
                          className="patients-person"
                        >

                          <div
                            className="patients-person__avatar"
                          >
                            {patient
                              .full_name
                              .charAt(0)
                              .toUpperCase()}
                          </div>


                          <div>

                            <strong>
                              {patient.full_name}
                            </strong>

                            <span>
                              {patient.sex.name}
                            </span>

                          </div>

                        </div>

                      </td>


                      <td>

                        {patient
                          .primary_document

                          ? (

                            <div
                              className="patients-cell-stack"
                            >

                              <strong>
                                {
                                  patient
                                    .primary_document
                                    .document_number
                                }
                              </strong>

                              <span>
                                {
                                  patient
                                    .primary_document
                                    .document_type_code
                                }
                              </span>

                            </div>

                          )

                          : "—"}

                      </td>


                      <td>

                        {patient
                          .primary_contact

                          ? (

                            <div
                              className="patients-cell-stack"
                            >

                              <strong>
                                {
                                  patient
                                    .primary_contact
                                    .value
                                }
                              </strong>

                              <span>
                                {
                                  patient
                                    .primary_contact
                                    .contact_type_name
                                }
                              </span>

                            </div>

                          )

                          : "—"}

                      </td>


                      <td>
                        {
                          formatDate(
                            patient.birth_date,
                          )
                        }
                      </td>


                      <td>

                        <span
                          className={
                            patient.active
                              ? "patients-status patients-status--active"
                              : "patients-status patients-status--inactive"
                          }
                        >
                          {patient.active
                            ? "Activo"
                            : "Inactivo"}
                        </span>

                      </td>


                      <td>

                        <span
                          className="patients-case-count"
                        >
                          {
                            patient
                              .clinical_cases_count
                          }
                        </span>

                      </td>


                      <td>
                        {
                          formatDateTime(
                            patient
                              .registration_date,
                          )
                        }
                      </td>


                      <td>

                        <button
                          type="button"
                          className="patients-open-button"
                          onClick={
                            () =>
                              navigate(
                                `/pacientes/${patient.id_patient}`,
                              )
                          }
                          title="Abrir ficha"
                        >

                          <Eye
                            size={17}
                          />

                          Ver ficha

                        </button>

                      </td>

                    </tr>

                  ),
                )}

              </tbody>

            </table>

          </div>

        )}


        {/* ================================================
            PAGINACIÓN
            ================================================ */}

        {!loading
          &&
          total > 0
          &&
          (

            <footer
              className="patients-pagination"
            >

              <span>
                Página {page} de {totalPages}
              </span>


              <div>

                <button
                  type="button"
                  disabled={
                    page <= 1
                  }
                  onClick={
                    () =>
                      setPage(
                        (
                          current,
                        ) =>
                          Math.max(
                            1,
                            current - 1,
                          ),
                      )
                  }
                >

                  <ChevronLeft
                    size={17}
                  />

                  Anterior

                </button>


                <button
                  type="button"
                  disabled={
                    page >=
                    totalPages
                  }
                  onClick={
                    () =>
                      setPage(
                        (
                          current,
                        ) =>
                          Math.min(
                            totalPages,
                            current + 1,
                          ),
                      )
                  }
                >

                  Siguiente

                  <ChevronRight
                    size={17}
                  />

                </button>

              </div>

            </footer>

          )}

      </div>

    </section>

  );

}