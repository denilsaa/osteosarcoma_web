import {
  CalendarDays,
  ChevronLeft,
  ChevronRight,
  CircleAlert,
  ClipboardList,
  Eye,
  Filter,
  LoaderCircle,
  RefreshCw,
  Search,
  Stethoscope,
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
  getClinicalCaseCatalogs,
  listClinicalCases,
  type ClinicalCase,
  type ClinicalCaseCatalogs,
} from "../../api/casos.api";

import {
  listarOncologos,
  type OncologoResumen,
} from "../../api/oncologos.api";

import "./CasosPage.css";


// ==========================================================
// CONSTANTES
// ==========================================================

const PAGE_SIZE =
  10;


// ==========================================================
// FECHAS
// ==========================================================

function formatDateTime(
  value?:
    string | null,
): string {

  if (!value) {

    return "—";

  }


  const date =
    new Date(
      value,
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
      day:
        "2-digit",

      month:
        "2-digit",

      year:
        "numeric",

      hour:
        "2-digit",

      minute:
        "2-digit",
    },
  ).format(
    date,
  );

}


// ==========================================================
// CLASE PRIORIDAD
// ==========================================================

function priorityClass(
  code:
    string,
): string {

  const normalized =
    code.toUpperCase();


  if (
    normalized ===
    "URGENTE"
  ) {

    return (
      "clinical-case-priority clinical-case-priority--urgent"
    );

  }


  if (
    normalized ===
    "ALTA"
  ) {

    return (
      "clinical-case-priority clinical-case-priority--high"
    );

  }


  if (
    normalized ===
    "MEDIA"
  ) {

    return (
      "clinical-case-priority clinical-case-priority--medium"
    );

  }


  return (
    "clinical-case-priority clinical-case-priority--low"
  );

}


// ==========================================================
// CLASE ESTADO
// ==========================================================

function statusClass(
  code:
    string,
): string {

  switch (
    code.toUpperCase()
  ) {

    case "REGISTRADO":
      return (
        "clinical-case-status clinical-case-status--registered"
      );


    case "PENDIENTE":
      return (
        "clinical-case-status clinical-case-status--pending"
      );


    case "EN_ANALISIS":
      return (
        "clinical-case-status clinical-case-status--analysis"
      );


    case "REVISADO":
      return (
        "clinical-case-status clinical-case-status--reviewed"
      );


    case "CERRADO":
      return (
        "clinical-case-status clinical-case-status--closed"
      );


    default:
      return (
        "clinical-case-status"
      );

  }

}


// ==========================================================
// COMPONENTE
// ==========================================================

export function CasosPage() {

  const navigate =
    useNavigate();


  // ========================================================
  // DATOS
  // ========================================================

  const [
    cases,
    setCases,
  ] = useState<
    ClinicalCase[]
  >(
    [],
  );


  const [
    catalogs,
    setCatalogs,
  ] = useState<
    ClinicalCaseCatalogs | null
  >(
    null,
  );


  const [
    oncologists,
    setOncologists,
  ] = useState<
    OncologoResumen[]
  >(
    [],
  );


  // ========================================================
  // FILTROS
  // ========================================================

  const [
    search,
    setSearch,
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
    statusCode,
    setStatusCode,
  ] = useState(
    "",
  );


  const [
    priorityCode,
    setPriorityCode,
  ] = useState(
    "",
  );


  const [
    oncologistUuid,
    setOncologistUuid,
  ] = useState(
    "",
  );


  const [
    openingDate,
    setOpeningDate,
  ] = useState(
    "",
  );


  const [
    page,
    setPage,
  ] = useState(
    1,
  );


  // ========================================================
  // PAGINACIÓN
  // ========================================================

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
    0,
  );


  // ========================================================
  // ESTADO
  // ========================================================

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
  >(
    null,
  );


  // ========================================================
  // MAPA DE MÉDICOS
  // ========================================================

  const oncologistMap =
    useMemo(
      () => {

        const map =
          new Map<
            string,
            string
          >();


        oncologists.forEach(
          (
            oncologist,
          ) => {

            map.set(
              oncologist.id_usuario,
              oncologist.nombre_completo,
            );

          },
        );


        return map;

      },
      [
        oncologists,
      ],
    );


  // ========================================================
  // CARGAR CATÁLOGOS Y MÉDICOS
  // ========================================================

  useEffect(
    () => {

      let mounted =
        true;


      async function loadInitialData() {

        try {

          const [
            catalogResponse,
            oncologistResponse,
          ] =
            await Promise.all(
              [
                getClinicalCaseCatalogs(),

                listarOncologos(
                  "",
                  "ACTIVO",
                  "",
                ),
              ],
            );


          if (!mounted) {

            return;

          }


          setCatalogs(
            catalogResponse,
          );


          setOncologists(
            oncologistResponse
              .resultados,
          );

        } catch {

          if (
            mounted
          ) {

            setError(
              "No fue posible cargar los catálogos de casos clínicos.",
            );

          }

        }

      }


      void loadInitialData();


      return () => {

        mounted =
          false;

      };

    },
    [],
  );


  // ========================================================
  // CARGAR CASOS
  // ========================================================

  const loadCases =
    useCallback(
      async () => {

        setLoading(
          true,
        );


        setError(
          null,
        );


        try {

          const response =
            await listClinicalCases(
              {
                search:
                  appliedSearch
                  ||
                  undefined,

                status_code:
                  statusCode
                  ||
                  undefined,

                priority_code:
                  priorityCode
                  ||
                  undefined,

                responsible_oncologist_uuid:
                  oncologistUuid
                  ||
                  undefined,

                opening_date:
                  openingDate
                  ||
                  undefined,

                page:
                  page,

                page_size:
                  PAGE_SIZE,
              },
            );


          setCases(
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

          setCases(
            [],
          );


          setTotal(
            0,
          );


          setTotalPages(
            0,
          );


          setError(
            "No fue posible cargar los casos clínicos.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        appliedSearch,
        statusCode,
        priorityCode,
        oncologistUuid,
        openingDate,
        page,
      ],
    );


  useEffect(
    () => {

      void loadCases();

    },
    [
      loadCases,
    ],
  );


  // ========================================================
  // BUSCAR
  // ========================================================

  function handleSearch(
    event:
      React.FormEvent,
  ) {

    event.preventDefault();


    setPage(
      1,
    );


    setAppliedSearch(
      search.trim(),
    );

  }


  // ========================================================
  // LIMPIAR FILTROS
  // ========================================================

  function clearFilters() {

    setSearch(
      "",
    );


    setAppliedSearch(
      "",
    );


    setStatusCode(
      "",
    );


    setPriorityCode(
      "",
    );


    setOncologistUuid(
      "",
    );


    setOpeningDate(
      "",
    );


    setPage(
      1,
    );

  }


  // ========================================================
  // NOMBRE MÉDICO
  // ========================================================

  function responsibleName(
    clinicalCase:
      ClinicalCase,
  ): string {

    if (
      !clinicalCase
        .responsible_oncologist_uuid
    ) {

      return (
        "Sin asignar"
      );

    }


    return (
      oncologistMap.get(
        clinicalCase
          .responsible_oncologist_uuid,
      )
      ??
      "Profesional asignado"
    );

  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="clinical-cases-page"
    >

      {/* ==================================================
          HEADER
          ================================================== */}

      <header
        className="clinical-cases-header"
      >

        <div>

          <span
            className="clinical-cases-eyebrow"
          >
            Gestión clínica
          </span>


          <h1>
            Casos clínicos
          </h1>


          <p>
            Consulta y seguimiento de casos registrados
            para pacientes de Oncología.
          </p>

        </div>

      </header>


      {/* ==================================================
          RESUMEN
          ================================================== */}

      <div
        className="clinical-cases-summary"
      >

        <article>

          <div>
            <ClipboardList
              size={21}
            />
          </div>

          <span>
            Casos encontrados
          </span>

          <strong>
            {total}
          </strong>

        </article>


        <article>

          <div>
            <Stethoscope
              size={21}
            />
          </div>

          <span>
            En esta página
          </span>

          <strong>
            {cases.length}
          </strong>

        </article>


        <article>

          <div>
            <CalendarDays
              size={21}
            />
          </div>

          <span>
            Página actual
          </span>

          <strong>
            {page}
          </strong>

        </article>

      </div>


      {/* ==================================================
          BÚSQUEDA
          ================================================== */}

      <form
        className="clinical-cases-search"
        onSubmit={
          handleSearch
        }
      >

        <div
          className="clinical-cases-search__field"
        >

          <Search
            size={18}
          />


          <input
            type="text"
            value={
              search
            }
            onChange={
              (
                event,
              ) =>
                setSearch(
                  event.target.value,
                )
            }
            placeholder="Buscar por código o paciente..."
          />

        </div>


        <button
          type="submit"
          className="clinical-cases-search__button"
        >
          Buscar
        </button>


        <button
          type="button"
          className="clinical-cases-refresh"
          onClick={
            () =>
              void loadCases()
          }
          title="Actualizar"
        >
          <RefreshCw
            size={17}
          />
        </button>

      </form>


      {/* ==================================================
          FILTROS
          ================================================== */}

      <section
        className="clinical-cases-filters"
      >

        <div
          className="clinical-cases-filters__title"
        >
          <Filter
            size={16}
          />

          <strong>
            Filtros
          </strong>
        </div>


        <div
          className="clinical-cases-filters__grid"
        >

          <label>

            <span>
              Estado
            </span>

            <select
              value={
                statusCode
              }
              onChange={
                (
                  event,
                ) => {

                  setStatusCode(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option
                value=""
              >
                Todos
              </option>


              {
                catalogs
                  ?.statuses
                  .map(
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
              Prioridad
            </span>

            <select
              value={
                priorityCode
              }
              onChange={
                (
                  event,
                ) => {

                  setPriorityCode(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option
                value=""
              >
                Todas
              </option>


              {
                catalogs
                  ?.priorities
                  .map(
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
              Médico responsable
            </span>

            <select
              value={
                oncologistUuid
              }
              onChange={
                (
                  event,
                ) => {

                  setOncologistUuid(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            >

              <option
                value=""
              >
                Todos
              </option>


              {
                oncologists.map(
                  (
                    oncologist,
                  ) => (

                    <option
                      key={
                        oncologist
                          .id_usuario
                      }
                      value={
                        oncologist
                          .id_usuario
                      }
                    >
                      {
                        oncologist
                          .nombre_completo
                      }
                    </option>

                  ),
                )
              }

            </select>

          </label>


          <label>

            <span>
              Fecha de apertura
            </span>

            <input
              type="date"
              value={
                openingDate
              }
              onChange={
                (
                  event,
                ) => {

                  setOpeningDate(
                    event.target.value,
                  );

                  setPage(
                    1,
                  );

                }
              }
            />

          </label>

        </div>


        <button
          type="button"
          className="clinical-cases-clear"
          onClick={
            clearFilters
          }
        >
          Limpiar filtros
        </button>

      </section>


      {/* ==================================================
          ERROR
          ================================================== */}

      {
        error
        &&
        (

          <div
            className="clinical-cases-error"
          >

            <CircleAlert
              size={18}
            />

            <span>
              {error}
            </span>

          </div>

        )
      }


      {/* ==================================================
          LISTADO
          ================================================== */}

      <section
        className="clinical-cases-card"
      >

        <header
          className="clinical-cases-card__header"
        >

          <div>

            <h2>
              Listado de casos
            </h2>

            <p>
              {total} caso(s) encontrado(s).
            </p>

          </div>

        </header>


        {
          loading
            ? (

                <div
                  className="clinical-cases-loading"
                >

                  <LoaderCircle
                    size={28}
                    className="clinical-cases-spin"
                  />

                  <span>
                    Cargando casos clínicos...
                  </span>

                </div>

              )
            : cases.length === 0
              ? (

                  <div
                    className="clinical-cases-empty"
                  >

                    <ClipboardList
                      size={31}
                    />

                    <strong>
                      No se encontraron casos clínicos
                    </strong>

                    <span>
                      Cambie los filtros o registre un caso
                      desde la ficha de un paciente.
                    </span>

                  </div>

                )
              : (

                  <div
                    className="clinical-cases-table-wrap"
                  >

                    <table
                      className="clinical-cases-table"
                    >

                      <thead>

                        <tr>

                          <th>
                            Código
                          </th>

                          <th>
                            Paciente
                          </th>

                          <th>
                            Médico responsable
                          </th>

                          <th>
                            Prioridad
                          </th>

                          <th>
                            Estado
                          </th>

                          <th>
                            Apertura
                          </th>

                          <th>
                            Acciones
                          </th>

                        </tr>

                      </thead>


                      <tbody>

                        {
                          cases.map(
                            (
                              clinicalCase,
                            ) => (

                              <tr
                                key={
                                  clinicalCase
                                    .id_case
                                }
                              >

                                <td>

                                  <strong
                                    className="clinical-case-code"
                                  >
                                    {
                                      clinicalCase
                                        .code
                                    }
                                  </strong>

                                </td>


                                <td>

                                  <div
                                    className="clinical-case-patient"
                                  >

                                    <strong>
                                      {
                                        clinicalCase
                                          .patient_name
                                        ??
                                        "Paciente"
                                      }
                                    </strong>

                                    <span>
                                      {
                                        clinicalCase
                                          .patient_id
                                      }
                                    </span>

                                  </div>

                                </td>


                                <td>

                                  <span
                                    className="clinical-case-doctor"
                                  >
                                    {
                                      responsibleName(
                                        clinicalCase,
                                      )
                                    }
                                  </span>

                                </td>


                                <td>

                                  <span
                                    className={
                                      priorityClass(
                                        clinicalCase
                                          .priority
                                          .code,
                                      )
                                    }
                                  >
                                    {
                                      clinicalCase
                                        .priority
                                        .name
                                    }
                                  </span>

                                </td>


                                <td>

                                  <span
                                    className={
                                      statusClass(
                                        clinicalCase
                                          .status
                                          .code,
                                      )
                                    }
                                  >
                                    {
                                      clinicalCase
                                        .status
                                        .name
                                    }
                                  </span>

                                </td>


                                <td>

                                  <span
                                    className="clinical-case-date"
                                  >
                                    {
                                      formatDateTime(
                                        clinicalCase
                                          .opening_date,
                                      )
                                    }
                                  </span>

                                </td>


                                <td>

                                  <button
                                    type="button"
                                    className="clinical-case-view"
                                    onClick={
                                      () =>
                                        navigate(
                                          `/casos/${clinicalCase.id_case}`,
                                        )
                                    }
                                  >

                                    <Eye
                                      size={16}
                                    />

                                    Ver caso

                                  </button>

                                </td>

                              </tr>

                            ),
                          )
                        }

                      </tbody>

                    </table>

                  </div>

                )
        }


        {/* ==================================================
            PAGINACIÓN
            ================================================== */}

        <footer
          className="clinical-cases-pagination"
        >

          <span>
            {
              totalPages > 0
                ? `Página ${page} de ${totalPages}`
                : "Sin resultados"
            }
          </span>


          <div>

            <button
              type="button"
              disabled={
                page <= 1
                ||
                loading
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
                size={16}
              />

              Anterior

            </button>


            <button
              type="button"
              disabled={
                page >=
                  totalPages
                ||
                totalPages === 0
                ||
                loading
              }
              onClick={
                () =>
                  setPage(
                    (
                      current,
                    ) =>
                      current + 1,
                  )
              }
            >

              Siguiente

              <ChevronRight
                size={16}
              />

            </button>

          </div>

        </footer>

      </section>

    </section>

  );

}