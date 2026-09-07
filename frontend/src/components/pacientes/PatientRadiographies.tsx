import {
  CalendarDays,
  CircleAlert,
  FileImage,
  Images,
  LoaderCircle,
  RefreshCw,
  ScanLine,
} from "lucide-react";

import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  getPatientClinicalCases,
} from "../../api/casos.api";

import {
  getCaseRadiographies,
  type RadiographicStudy,
} from "../../api/radiografias.api";

import "./PatientRadiographies.css";


interface Props {
  patientId: string;
}


interface StudyWithCase
  extends RadiographicStudy {

  caseCode: string;
}


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


function formatBytes(
  bytes: number,
): string {

  if (bytes < 1024) {
    return `${bytes} B`;
  }


  const kb =
    bytes / 1024;


  if (kb < 1024) {
    return `${kb.toFixed(1)} KB`;
  }


  return `${(kb / 1024).toFixed(1)} MB`;
}


export function PatientRadiographies(
  {
    patientId,
  }: Props,
) {

  const [
    studies,
    setStudies,
  ] = useState<
    StudyWithCase[]
  >([]);


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


  const loadRadiographies =
    useCallback(
      async () => {

        setLoading(
          true,
        );

        setError(
          null,
        );


        try {

          // ==================================================
          // 1. OBTENER CASOS DEL PACIENTE
          // ==================================================

          const casesResponse =
            await getPatientClinicalCases(
              patientId,
            );


          if (
            casesResponse.data.length ===
              0
          ) {

            setStudies(
              [],
            );

            return;
          }


          // ==================================================
          // 2. OBTENER RADIOGRAFÍAS DE CADA CASO
          // ==================================================

          const responses =
            await Promise.all(

              casesResponse.data.map(
                async (
                  clinicalCase,
                ) => {

                  const response =
                    await getCaseRadiographies(
                      clinicalCase.id_case,
                    );


                  return response.data.map(
                    (
                      study,
                    ): StudyWithCase => ({

                      ...study,

                      caseCode:
                        clinicalCase.code,

                    }),
                  );

                },
              ),
            );


          // ==================================================
          // 3. UNIFICAR
          // ==================================================

          const allStudies =
            responses.flat();


          allStudies.sort(
            (
              a,
              b,
            ) => {

              const dateA =
                new Date(
                  a.registered_at,
                ).getTime();


              const dateB =
                new Date(
                  b.registered_at,
                ).getTime();


              return dateB - dateA;

            },
          );


          setStudies(
            allStudies,
          );

        } catch {

          setStudies(
            [],
          );


          setError(
            "No fue posible cargar los estudios radiográficos del paciente.",
          );

        } finally {

          setLoading(
            false,
          );

        }

      },
      [
        patientId,
      ],
    );


  useEffect(
    () => {

      void loadRadiographies();

    },
    [
      loadRadiographies,
    ],
  );


  return (

    <article
      className="patient-radiographies-card"
    >

      <header
        className="patient-radiographies-header"
      >

        <div
          className="patient-radiographies-header__left"
        >

          <div
            className="patient-radiographies-header__icon"
          >

            <ScanLine
              size={21}
            />

          </div>


          <div>

            <h2>
              Radiografías
            </h2>


            <p>
              Estudios radiográficos asociados a los casos clínicos del paciente.
            </p>

          </div>

        </div>


        <div
          className="patient-radiographies-header__actions"
        >

          {!loading && (

            <span
              className="patient-radiographies-total"
            >
              {studies.length} estudio
              {studies.length === 1
                ? ""
                : "s"}
            </span>

          )}


          <button
            type="button"
            className="patient-radiographies-refresh"
            onClick={
              () =>
                void loadRadiographies()
            }
            title="Actualizar radiografías"
          >

            <RefreshCw
              size={17}
            />

          </button>

        </div>

      </header>


      {loading ? (

        <div
          className="patient-radiographies-state"
        >

          <LoaderCircle
            size={26}
            className="patient-radiographies-spin"
          />

          <span>
            Cargando estudios radiográficos...
          </span>

        </div>

      ) : error ? (

        <div
          className="patient-radiographies-error"
        >

          <CircleAlert
            size={19}
          />

          <span>
            {error}
          </span>

        </div>

      ) : studies.length === 0 ? (

        <div
          className="patient-radiographies-empty"
        >

          <Images
            size={31}
          />

          <strong>
            Sin radiografías
          </strong>

          <span>
            No existen estudios radiográficos asociados a los casos clínicos de este paciente.
          </span>

        </div>

      ) : (

        <div
          className="patient-radiographies-list"
        >

          {studies.map(
            (
              study,
            ) => (

              <section
                key={
                  study.id_study
                }
                className="patient-radiography"
              >

                <div
                  className="patient-radiography__top"
                >

                  <div
                    className="patient-radiography__title"
                  >

                    <FileImage
                      size={19}
                    />

                    <div>

                      <strong>
                        {
                          study
                            .study_type
                            .name
                        }
                      </strong>

                      <span>
                        {
                          study
                            .anatomical_region
                            .name
                        }
                      </span>

                    </div>

                  </div>


                  <span
                    className="patient-radiography-case"
                  >
                    {study.caseCode}
                  </span>

                </div>


                <div
                  className="patient-radiography-meta"
                >

                  <span>

                    <CalendarDays
                      size={14}
                    />

                    {
                      formatDate(
                        study.study_date,
                      )
                    }

                  </span>


                  <span>
                    {
                      study.files.length
                    } archivo
                    {
                      study.files.length === 1
                        ? ""
                        : "s"
                    }
                  </span>

                </div>


                {study.observation && (

                  <div
                    className="patient-radiography-observation"
                  >

                    <span>
                      Observación
                    </span>

                    <p>
                      {
                        study.observation
                      }
                    </p>

                  </div>

                )}


                {study.files.length > 0 && (

                  <div
                    className="patient-radiography-files"
                  >

                    {study.files.map(
                      (
                        file,
                      ) => (

                        <div
                          key={
                            file.id_file
                          }
                          className="patient-radiography-file"
                        >

                          <FileImage
                            size={16}
                          />


                          <div>

                            <strong>
                              {
                                file
                                  .original_name
                              }
                            </strong>

                            <span>
                              {
                                file
                                  .mime
                                  .extension
                                  .toUpperCase()
                              }
                              {" · "}
                              {
                                formatBytes(
                                  file
                                    .size_bytes,
                                )
                              }
                            </span>

                          </div>

                        </div>

                      ),
                    )}

                  </div>

                )}

              </section>

            ),
          )}

        </div>

      )}

    </article>

  );
}