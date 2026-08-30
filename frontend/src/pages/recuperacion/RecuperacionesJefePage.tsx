import {
  AlertCircle,
  Check,
  CheckCircle2,
  Clock3,
  LoaderCircle,
  RefreshCw,
  RotateCcw,
  Search,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useState,
} from "react";

import {
  listarRecuperaciones,
  mensajeErrorRecuperacion,
  resolverRecuperacion,
  type RecuperacionJefatura,
} from "../../api/recuperaciones.api";

import "./RecuperacionesJefePage.css";


type Decision =
  | "APROBADA"
  | "RECHAZADA";


function fecha(
  valor: string,
): string {

  const date =
    new Date(valor);


  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {

    return "Sin registro";

  }


  return new Intl.DateTimeFormat(
    "es-BO",
    {
      dateStyle: "medium",
      timeStyle: "short",
    },
  ).format(date);
}


export function RecuperacionesJefePage() {

  const [
    solicitudes,
    setSolicitudes,
  ] = useState<
    RecuperacionJefatura[]
  >([]);


  const [
    cargando,
    setCargando,
  ] = useState(true);


  const [
    filtro,
    setFiltro,
  ] = useState("PENDIENTE");


  const [
    buscar,
    setBuscar,
  ] = useState("");


  const [
    error,
    setError,
  ] = useState("");


  const [
    exito,
    setExito,
  ] = useState("");


  const [
    seleccionada,
    setSeleccionada,
  ] = useState<
    RecuperacionJefatura | null
  >(null);


  const [
    decision,
    setDecision,
  ] = useState<
    Decision | null
  >(null);


  const [
    observacion,
    setObservacion,
  ] = useState("");


  const [
    procesando,
    setProcesando,
  ] = useState(false);


  const cargar =
    async () => {

      try {

        setCargando(true);

        setError("");


        const response =
          await listarRecuperaciones(
            filtro,
          );


        setSolicitudes(
          response.resultados,
        );

      } catch (errorActual) {

        setError(
          mensajeErrorRecuperacion(
            errorActual,
          ),
        );

      } finally {

        setCargando(false);
      }

    };


  useEffect(
    () => {

      void cargar();

    // eslint-disable-next-line react-hooks/exhaustive-deps
    },
    [
      filtro,
    ],
  );


  const abrirResolucion =
    (
      solicitud:
        RecuperacionJefatura,

      nuevaDecision:
        Decision,
    ) => {

      setSeleccionada(
        solicitud,
      );

      setDecision(
        nuevaDecision,
      );

      setObservacion("");

      setError("");
    };


  const cerrarModal =
    () => {

      if (procesando) {
        return;
      }

      setSeleccionada(null);

      setDecision(null);

      setObservacion("");
    };


  const resolver =
    async () => {

      if (
        !seleccionada ||
        !decision
      ) {
        return;
      }


      try {

        setProcesando(true);

        setError("");


        const response =
          await resolverRecuperacion(

            seleccionada
              .id_solicitud,

            decision,

            observacion,

          );


        setSeleccionada(null);

        setDecision(null);

        setObservacion("");


        setExito(
          response.mensaje,
        );


        await cargar();


        window.setTimeout(
          () =>
            setExito(""),
          3500,
        );

      } catch (errorActual) {

        setError(
          mensajeErrorRecuperacion(
            errorActual,
          ),
        );

      } finally {

        setProcesando(false);
      }

    };


  const resultados =
    solicitudes.filter(
      (solicitud) => {

        const termino =
          buscar
            .trim()
            .toLowerCase();


        if (!termino) {
          return true;
        }


        return (

          solicitud
            .usuario
            .nombre_completo
            .toLowerCase()
            .includes(
              termino,
            )

          ||

          solicitud
            .usuario
            .correo
            .toLowerCase()
            .includes(
              termino,
            )

          ||

          solicitud
            .usuario
            .nombre_usuario
            .toLowerCase()
            .includes(
              termino,
            )

        );

      },
    );


  return (

    <div className="recovery-admin-page">


      <section className="recovery-admin-header">

        <div>

          <span>
            Jefatura de Oncología
          </span>

          <h1>
            Recuperación de contraseñas
          </h1>

          <p>

            Revise y resuelva las solicitudes
            de recuperación enviadas por el
            personal médico.

          </p>

        </div>


        <div className="recovery-admin-header__badge">

          <ShieldCheck
            size={18}
          />

          Solo Jefatura

        </div>

      </section>


      {exito && (

        <div className="recovery-admin-alert recovery-admin-alert--success">

          <CheckCircle2
            size={18}
          />

          {exito}

        </div>

      )}


      {error && (

        <div className="recovery-admin-alert recovery-admin-alert--error">

          <AlertCircle
            size={18}
          />

          {error}

        </div>

      )}


      <section className="recovery-admin-card">


        <div className="recovery-admin-toolbar">


          <div className="recovery-admin-search">

            <Search
              size={18}
            />

            <input

              value={buscar}

              onChange={(event) =>
                setBuscar(
                  event.target.value,
                )
              }

              placeholder="Buscar médico..."

            />

          </div>


          <select

            value={filtro}

            onChange={(event) =>
              setFiltro(
                event.target.value,
              )
            }

          >

            <option value="PENDIENTE">
              Pendientes
            </option>

            <option value="APROBADA">
              Aprobadas
            </option>

            <option value="RECHAZADA">
              Rechazadas
            </option>

            <option value="UTILIZADA">
              Utilizadas
            </option>

            <option value="">
              Todas
            </option>

          </select>


          <button
            type="button"
            onClick={() =>
              void cargar()
            }
          >

            <RefreshCw
              size={18}
            />

          </button>

        </div>


        {cargando ? (

          <div className="recovery-admin-empty">

            <LoaderCircle
              size={28}
              className="recovery-admin-spin"
            />

            Cargando solicitudes...

          </div>

        ) : resultados.length === 0 ? (

          <div className="recovery-admin-empty">

            <Clock3
              size={30}
            />

            <strong>
              No existen solicitudes
            </strong>

            <span>

              No hay resultados para el filtro
              seleccionado.

            </span>

          </div>

        ) : (

          <div className="recovery-admin-list">

            {resultados.map(
              (solicitud) => (

                <article
                  key={
                    solicitud
                      .id_solicitud
                  }
                  className="recovery-request"
                >

                  <div className="recovery-request__avatar">

                    <UserRound
                      size={20}
                    />

                  </div>


                  <div className="recovery-request__info">

                    <strong>

                      {
                        solicitud
                          .usuario
                          .nombre_completo
                      }

                    </strong>

                    <span>

                      {
                        solicitud
                          .usuario
                          .correo
                      }

                    </span>

                    <small>

                      Solicitado:{" "}
                      {fecha(
                        solicitud
                          .fecha_solicitud,
                      )}

                    </small>

                  </div>


                  <div className="recovery-request__state">

                    {
                      solicitud
                        .estado_nombre
                    }

                  </div>


                  {solicitud.estado ===
                    "PENDIENTE" && (

                    <div className="recovery-request__actions">

                      <button

                        type="button"

                        className="recovery-request__approve"

                        onClick={() =>
                          abrirResolucion(
                            solicitud,
                            "APROBADA",
                          )
                        }

                      >

                        <Check
                          size={16}
                        />

                        Aprobar

                      </button>


                      <button

                        type="button"

                        className="recovery-request__reject"

                        onClick={() =>
                          abrirResolucion(
                            solicitud,
                            "RECHAZADA",
                          )
                        }

                      >

                        <X
                          size={16}
                        />

                        Rechazar

                      </button>

                    </div>

                  )}


                  {solicitud.resolucion && (

                    <div className="recovery-request__resolution">

                      <RotateCcw
                        size={15}
                      />

                      <span>

                        Resuelto por{" "}
                        {
                          solicitud
                            .resolucion
                            .resuelto_por
                        }

                      </span>

                    </div>

                  )}

                </article>

              ),
            )}

          </div>

        )}


      </section>


      {seleccionada && decision && (

        <div
          className="recovery-decision-backdrop"
          onMouseDown={
            cerrarModal
          }
        >

          <section

            className="recovery-decision-modal"

            onMouseDown={(event) =>
              event.stopPropagation()
            }

          >

            <button

              type="button"

              className="recovery-decision-modal__close"

              onClick={
                cerrarModal
              }

            >

              <X
                size={19}
              />

            </button>


            <div
              className={`
                recovery-decision-modal__icon
                ${
                  decision === "APROBADA"
                    ? "recovery-decision-modal__icon--approve"
                    : "recovery-decision-modal__icon--reject"
                }
              `}
            >

              {decision === "APROBADA"
                ? <Check size={27} />
                : <X size={27} />}

            </div>


            <h2>

              {decision === "APROBADA"
                ? "Aprobar recuperación"
                : "Rechazar recuperación"}

            </h2>


            <p>

              Solicitud de{" "}

              <strong>

                {
                  seleccionada
                    .usuario
                    .nombre_completo
                }

              </strong>

            </p>


            <label>

              <span>
                Observación
              </span>

              <textarea

                value={
                  observacion
                }

                onChange={(event) =>
                  setObservacion(
                    event.target.value,
                  )
                }

                rows={4}

                placeholder={
                  decision ===
                  "APROBADA"

                    ? "Observación opcional..."

                    : "Indique el motivo del rechazo..."
                }

              />

            </label>


            <div className="recovery-decision-modal__actions">

              <button

                type="button"

                className="recovery-admin-cancel"

                onClick={
                  cerrarModal
                }

                disabled={
                  procesando
                }

              >

                Cancelar

              </button>


              <button

                type="button"

                className={
                  decision ===
                  "APROBADA"

                    ? "recovery-admin-confirm recovery-admin-confirm--approve"

                    : "recovery-admin-confirm recovery-admin-confirm--reject"
                }

                onClick={() =>
                  void resolver()
                }

                disabled={
                  procesando
                }

              >

                {procesando ? (

                  <LoaderCircle
                    size={17}
                    className="recovery-admin-spin"
                  />

                ) : decision ===
                  "APROBADA" ? (

                  <Check
                    size={17}
                  />

                ) : (

                  <X
                    size={17}
                  />

                )}

                {procesando
                  ? "Procesando..."
                  : decision ===
                    "APROBADA"
                    ? "Sí, aprobar"
                    : "Sí, rechazar"}

              </button>

            </div>

          </section>

        </div>

      )}


    </div>

  );
}