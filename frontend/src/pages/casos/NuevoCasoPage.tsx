import {
  ArrowLeft,
  CheckCircle2,
  CircleAlert,
  ClipboardPlus,
  LoaderCircle,
  Save,
  Stethoscope,
  UserRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useNavigate,
  useSearchParams,
} from "react-router-dom";

import {
  createClinicalCase,
  getClinicalCaseCatalogs,
  type ClinicalCaseCatalogs,
} from "../../api/casos.api";

import {
  listarOncologos,
  type OncologoResumen,
} from "../../api/oncologos.api";

import {
  getPatient,
} from "../../api/pacientes.api";

import { tokenStorage } from "../../auth/tokenStorage";
import {
  cacheAuthorizedCasePatient, enqueueClinicalCase, getCachedCasePatient,
  getLocalPendingPatient, isLocalPatientReference,
  subscribeClinicalQueue, type CachedAuthorizedPatient, type QueueStats,
} from "../../offline/clinicalQueue";

import "./NuevoCasoPage.css";


// ==========================================================
// FORM
// ==========================================================

type FormState = {
  priority_id:
    string;

  responsible_oncologist_uuid:
    string;

  consultation_reason:
    string;

  general_observation:
    string;
};


const initialForm:
  FormState = {

    priority_id:
      "",

    responsible_oncologist_uuid:
      "",

    consultation_reason:
      "",

    general_observation:
      "",

  };


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

    const response =
      (
        error as {
          response?: {
            data?: {
              error?: string;
              detail?: string;
            };
          };
        }
      )
        .response;


    if (
      typeof response
        ?.data
        ?.error ===
      "string"
    ) {

      return response.data.error;
    }


    if (
      typeof response
        ?.data
        ?.detail ===
      "string"
    ) {

      return response.data.detail;
    }

  }


  return (
    "No fue posible registrar el caso clínico."
  );
}


// ==========================================================
// COMPONENTE
// ==========================================================

export function NuevoCasoPage() {

  const navigate =
    useNavigate();


  const [
    searchParams,
  ] =
    useSearchParams();


  const patientId =
    searchParams.get(
      "paciente",
    )
    ??
    "";
  const temporaryPatient = isLocalPatientReference(patientId);

  // ========================================================
  // DATOS
  // ========================================================

  const [
    patient,
    setPatient,
  ] =
    useState<
      CachedAuthorizedPatient | null
    >(
      null,
    );


  const [
    catalogs,
    setCatalogs,
  ] =
    useState<
      ClinicalCaseCatalogs | null
    >(
      null,
    );


  const [
    oncologists,
    setOncologists,
  ] =
    useState<
      OncologoResumen[]
    >(
      [],
    );


  const [
    form,
    setForm,
  ] =
    useState<FormState>(
      initialForm,
    );


  // ========================================================
  // ESTADOS
  // ========================================================

  const [
    loading,
    setLoading,
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


  const [queueState, setQueueState] = useState<QueueStats>({
    ready: false, pending: 0, patientPending: 0, casePending: 0,
    review: 0, syncing: false, lastError: null,
  });
  const [offlineQueued, setOfflineQueued] = useState(false);
  const [localPatientVerified, setLocalPatientVerified] = useState(false);

  useEffect(() => subscribeClinicalQueue(setQueueState), []);

  // ========================================================
  // CARGA INICIAL
  // ========================================================

  useEffect(() => {
    if (!patientId) {
      setError("Debe registrar el caso desde la ficha de un paciente.");
      setLoading(false);
      return;
    }
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      // Solamente la jefatura consulta el directorio de oncólogos.
      const isHead = tokenStorage.obtenerUsuario()?.roles.some(r => r.toUpperCase() === "JEFE_ONCOLOGIA") ?? false;
      try {
        const patientPromise = temporaryPatient ? getLocalPendingPatient(patientId).then(p => {
          if (!p) throw new Error("No existe un paciente pendiente accesible para esta cuenta y bandeja. Desbloquea la bandeja desde Inicio.");
          return { data: p, stored: true };
        }) : getPatient(patientId).then(async (p) => {
          // Una autorización obtenida del servidor puede guardarse cifrada
          // para contingencia, si la bandeja está desbloqueada.
          let stored = false;
          try { await cacheAuthorizedCasePatient(p); stored = true; } catch { /* bandeja cerrada */ }
          return { data: p as CachedAuthorizedPatient, stored };
        }).catch(async (err: unknown) => {
          if (typeof err === "object" && err !== null && "response" in err && (err as { response?: unknown }).response) throw err;
          const local = await getCachedCasePatient(patientId);
          if (!local) throw new Error("No hay una ficha previamente autorizada y cifrada para este paciente. Conecta el servidor y abre este formulario con la bandeja desbloqueada.");
          return { data: local, stored: true };
        });
        const catalogPromise = getClinicalCaseCatalogs();
        const directoryPromise = isHead
          && !temporaryPatient ? listarOncologos("", "ACTIVO", "").catch(() => null)
          : Promise.resolve(null);
        const [patientResult, catalogData, oncologistData] = await Promise.all([
          patientPromise, catalogPromise, directoryPromise,
        ]);
        if (!mounted) return;
        setPatient(patientResult.data);
        setLocalPatientVerified(patientResult.stored);
        setCatalogs(catalogData);
        setOncologists(oncologistData?.resultados || []);
        const priority = catalogData.priorities.find(x => x.code === "MEDIA") || catalogData.priorities[0];
        setForm(current => ({ ...current, priority_id: priority ? String(priority.id) : "" }));
      } catch (err: unknown) {
        if (mounted) setError(err instanceof Error ? err.message : extractErrorMessage(err));
      } finally {
        if (mounted) setLoading(false);
      }
    }
    void load();
    return () => { mounted = false; };
  }, [patientId, temporaryPatient]);

  // ========================================================
  // VALIDACIÓN
  // ========================================================

  const formValid =
    useMemo(
      () => {

        return Boolean(
          patientId
          &&
          form.priority_id
          &&
          normalizeText(
            form.consultation_reason,
          ).length >= 10
        );

      },
      [
        patientId,
        form.priority_id,
        form.consultation_reason,
      ],
    );


  // ========================================================
  // CAMPO
  // ========================================================

  function updateField(
    field:
      keyof FormState,

    value:
      string,
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


    setError(
      null,
    );


    setSuccess(
      null,
    );
  }


  async function handleSaveOffline() {
    if (!formValid || offlineQueued || !queueState.ready || !localPatientVerified) {
      setError("Prepara y desbloquea la bandeja desde Inicio; consulta antes la ficha autorizada del paciente.");
      return;
    }
    setSaving(true); setError(null); setSuccess(null);
    try {
      await enqueueClinicalCase(patientId, {
        priority_id: Number(form.priority_id),
        responsible_oncologist_uuid: form.responsible_oncologist_uuid || null,
        consultation_reason: normalizeText(form.consultation_reason),
        general_observation: normalizeText(form.general_observation) || null,
      });
      setOfflineQueued(true);
      setSuccess("Caso guardado cifrado en este equipo como PENDIENTE. No existe aún en el servidor. Se sincronizará al recuperar la conexión y validar permisos.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "No fue posible guardar el caso pendiente.");
    } finally { setSaving(false); }
  }

  // ========================================================
  // GUARDAR
  // ========================================================

  async function handleSubmit(
    event:
      React.FormEvent,
  ) {

    event.preventDefault();

    if (offlineQueued) {
      setError("Este caso ya está pendiente en la bandeja local. Evita duplicarlo.");
      return;
    }
    if (temporaryPatient) {
      setError("El paciente todavía utiliza una referencia temporal. Guarda el caso como pendiente offline; el servidor recibirá primero el paciente y después el caso.");
      return;
    }

    if (
      !patientId
    ) {

      setError(
        "No se identificó al paciente.",
      );


      return;
    }


    const consultationReason =
      normalizeText(
        form.consultation_reason,
      );


    if (
      !form.priority_id
    ) {

      setError(
        "Seleccione la prioridad del caso.",
      );


      return;
    }


    if (
      consultationReason.length <
      10
    ) {

      setError(
        "El motivo de consulta debe contener al menos 10 caracteres.",
      );


      return;
    }


    setSaving(
      true,
    );


    setError(
      null,
    );


    setSuccess(
      null,
    );


    try {

      const response =
        await createClinicalCase(
          patientId,
          {
            priority_id:
              Number(
                form.priority_id,
              ),

            responsible_oncologist_uuid:
              form
                .responsible_oncologist_uuid
              ||
              null,

            consultation_reason:
              consultationReason,

            general_observation:
              normalizeText(
                form.general_observation,
              )
              ||
              null,
          },
        );


      setSuccess(
        response.message,
      );


      window.setTimeout(
        () => {

          navigate(
            `/casos/${response.data.id_case}`,
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
  // LOADING
  // ========================================================

  if (
    loading
  ) {

    return (

      <div
        className="new-case-loading"
      >

        <LoaderCircle
          size={30}
          className="new-case-spin"
        />

        <span>
          Cargando formulario...
        </span>

      </div>

    );
  }


  // ========================================================
  // SIN PACIENTE
  // ========================================================

  if (
    !patientId
    ||
    !patient
  ) {

    return (

      <section
        className="new-case-page"
      >

        <div
          className="new-case-message new-case-message--error"
        >

          <CircleAlert
            size={19}
          />

          <span>
            {
              error
              ??
              "Debe registrar el caso desde la ficha de un paciente."
            }
          </span>

        </div>


        <button
          type="button"
          className="new-case-back-list"
          onClick={
            () =>
              navigate(
                "/pacientes",
              )
          }
        >

          <ArrowLeft
            size={17}
          />

          Volver a pacientes
        </button>

      </section>

    );
  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <section
      className="new-case-page"
    >

      <header
        className="new-case-header"
      >

        <div
          className="new-case-header__main"
        >

          <button
            type="button"
            className="new-case-back"
            onClick={
              () =>
                navigate(
                  temporaryPatient ? "/dashboard" : `/pacientes/${patient.id_patient}`,
                )
            }
          >
            <ArrowLeft
              size={18}
            />
          </button>


          <div>

            <span
              className="new-case-eyebrow"
            >
              Gestión clínica
            </span>


            <h1>
              Registrar caso clínico
            </h1>


            <p>
              Registre la información inicial
              para la evaluación clínica del paciente.
            </p>

          </div>

        </div>


        <div
          className="new-case-header__icon"
        >
          <ClipboardPlus
            size={26}
          />
        </div>

      </header>


      {
        error
        &&
        (

          <div
            className="new-case-message new-case-message--error"
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
            className="new-case-message new-case-message--success"
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


      {!localPatientVerified && (
        <div className="new-case-message new-case-message--warning" role="status">
          <CircleAlert size={19}/>
          Para crear casos sin conexión, desbloquea la bandeja cifrada desde Inicio y prepara la
          referencia del paciente mientras el servidor esté disponible.
        </div>
      )}

      {temporaryPatient && (
        <div className="new-case-message new-case-message--warning" role="status">
          <CircleAlert size={19}/>
          Paciente creado en este equipo, todavía pendiente. Este caso se guardará vinculado a
          su referencia temporal. Al sincronizar, el servidor registrará primero el paciente
          y luego el caso. No utilices el botón de registro central.
        </div>
      )}
      <form
        className="new-case-form"
        onSubmit={
          handleSubmit
        }
      >

        {/* ================================================
            PACIENTE
            ================================================ */}

        <article
          className="new-case-card"
        >

          <div
            className="new-case-card__header"
          >

            <div
              className="new-case-card__icon"
            >
              <UserRound
                size={20}
              />
            </div>


            <div>
              <h2>
                Paciente
              </h2>

              <p>
                El caso quedará asociado permanentemente
                a esta ficha clínica.
              </p>
            </div>

          </div>


          <div
            className="new-case-patient"
          >

            <div
              className="new-case-patient__avatar"
            >
              {
                patient
                  .first_names
                  .charAt(
                    0,
                  )
                  .toUpperCase()
              }
            </div>


            <div>

              <strong>
                {patient.full_name}
              </strong>


              <span>
                {
                  patient
                    .documents[0]
                    ?.document_type_name
                  ??
                  "Documento"
                }
                {": "}
                {
                  temporaryPatient ? "Alta local pendiente" : "Consulta autorizada"
                }
              </span>


              <small>
                UUID: {patient.id_patient}
              </small>

            </div>

          </div>

        </article>


        {/* ================================================
            INFORMACIÓN DEL CASO
            ================================================ */}

        <article
          className="new-case-card"
        >

          <div
            className="new-case-card__header"
          >

            <div
              className="new-case-card__icon"
            >
              <Stethoscope
                size={20}
              />
            </div>


            <div>
              <h2>
                Información inicial del caso
              </h2>

              <p>
                Defina prioridad, médico responsable
                y motivo de consulta.
              </p>
            </div>

          </div>


          <div
            className="new-case-grid new-case-grid--2"
          >

            <label>

              <span>
                Prioridad *
              </span>

              <select
                value={
                  form.priority_id
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "priority_id",
                      event.target.value,
                    )
                }
              >

                {
                  catalogs
                    ?.priorities
                    .map(
                      (
                        priority,
                      ) => (

                        <option
                          key={
                            priority.id
                          }
                          value={
                            priority.id
                          }
                        >
                          {priority.name}
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
                  form.responsible_oncologist_uuid
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "responsible_oncologist_uuid",
                      event.target.value,
                    )
                }
              >

                <option
                  value=""
                >
                  Asignar al usuario actual
                </option>


                {
                  oncologists.map(
                    (
                      oncologist,
                    ) => (

                      <option
                        key={
                          oncologist.id_usuario
                        }
                        value={
                          oncologist.id_usuario
                        }
                      >
                        {
                          oncologist.nombre_completo
                        }
                        {" — "}
                        {
                          oncologist.rol
                        }
                      </option>

                    ),
                  )
                }

              </select>


              <small
                className="new-case-help"
              >
                Si no selecciona un profesional,
                el backend asignará al usuario autenticado.
              </small>

            </label>

          </div>


          <div
            className="new-case-grid new-case-grid--1"
          >

            <label>

              <span>
                Motivo de consulta *
              </span>

              <textarea
                value={
                  form.consultation_reason
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "consultation_reason",
                      event.target.value,
                    )
                }
                maxLength={1000}
                rows={4}
                placeholder="Ej. Dolor óseo persistente, aumento de volumen y limitación funcional."
              />

              <small
                className="new-case-counter"
              >
                {
                  form
                    .consultation_reason
                    .length
                }
                /1000
              </small>

            </label>


            <label>

              <span>
                Observación general
              </span>

              <textarea
                value={
                  form.general_observation
                }
                onChange={
                  (
                    event,
                  ) =>
                    updateField(
                      "general_observation",
                      event.target.value,
                    )
                }
                maxLength={2000}
                rows={5}
                placeholder="Información complementaria relevante para la apertura del caso."
              />

              <small
                className="new-case-counter"
              >
                {
                  form
                    .general_observation
                    .length
                }
                /2000
              </small>

            </label>

          </div>

        </article>


        {/* ================================================
            ESTADO INICIAL
            ================================================ */}

        <article
          className="new-case-state-card"
        >

          <div>

            <span>
              Estado inicial
            </span>

            <strong>
              Registrado
            </strong>

          </div>


          <p>
            El sistema generará automáticamente
            el código del caso y registrará el primer
            evento del historial de estados.
          </p>

        </article>


        {/* ================================================
            ACCIONES
            ================================================ */}

        <footer
          className="new-case-footer"
        >

          <button
            type="button"
            className="new-case-cancel"
            disabled={
              saving
            }
            onClick={
              () =>
                navigate(
                  temporaryPatient ? "/dashboard" : `/pacientes/${patient.id_patient}`,
                )
            }
          >

            <X
              size={17}
            />

            Cancelar

          </button>


          <button
            type="button"
            className="new-case-offline"
            disabled={saving || !formValid || !queueState.ready || !localPatientVerified || offlineQueued}
            onClick={() => void handleSaveOffline()}
            title="Guarda una operación cifrada pendiente; el servidor validará permisos al sincronizar"
          >
            <Save size={17} />
            {offlineQueued ? "Pendiente guardado" : "Guardar pendiente offline"}
          </button>

          <button
            type="submit"
            className="new-case-save"
            disabled={
              saving
              ||
              !formValid
              ||
              offlineQueued
              ||
              temporaryPatient
            }
          >

            {
              saving
                ? (
                    <LoaderCircle
                      size={18}
                      className="new-case-spin"
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
                ? "Registrando..."
                : "Registrar caso clínico"
            }

          </button>

        </footer>

      </form>

    </section>

  );
}