import {
  AlertCircle,
  BadgeCheck,
  BrainCircuit,
  Check,
  CheckCircle2,
  ClipboardList,
  FileText,
  LoaderCircle,
  LockKeyhole,
  RefreshCw,
  Save,
  ScanLine,
  ShieldCheck,
  UserRound,
  UsersRound,
  X,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
  type ComponentType,
} from "react";

import {
  actualizarPermisosOncologo,
  obtenerMensajeErrorPermisos,
  obtenerPermisosOncologo,
  type PermisoOncologo,
} from "../../api/permisos.api";

import "./PermisosJefePage.css";


interface IconoPermisoProps {
  size?: number;
}


function obtenerIconoPermiso(
  codigo: string,
): ComponentType<IconoPermisoProps> {

  switch (
    codigo
  ) {

    case "PACIENTE_GESTIONAR":
      return UsersRound;

    case "CASO_CLINICO_GESTIONAR":
      return ClipboardList;

    case "RADIOGRAFIA_GESTIONAR":
      return ScanLine;

    case "ANALISIS_IA_USAR":
      return BrainCircuit;

    case "INFORME_CONSULTAR":
      return FileText;

    case "PERFIL_EDITAR":
      return UserRound;

    default:
      return ShieldCheck;

  }

}


function obtenerNombreModulo(
  permiso: PermisoOncologo,
): string {

  if (
    permiso.modulo
  ) {

    return permiso.modulo
      .replaceAll(
        "_",
        " ",
      );

  }


  return "SISTEMA";

}


export function PermisosJefePage() {

  const [
    permisos,
    setPermisos,
  ] = useState<
    PermisoOncologo[]
  >([]);


  const [
    seleccionados,
    setSeleccionados,
  ] = useState<
    Set<string>
  >(
    new Set(),
  );


  const [
    seleccionadosIniciales,
    setSeleccionadosIniciales,
  ] = useState<
    Set<string>
  >(
    new Set(),
  );


  const [
    nombreRol,
    setNombreRol,
  ] = useState(
    "Oncólogo",
  );


  const [
    cargando,
    setCargando,
  ] = useState(
    true,
  );


  const [
    guardando,
    setGuardando,
  ] = useState(
    false,
  );


  const [
    error,
    setError,
  ] = useState(
    "",
  );


  const [
    exito,
    setExito,
  ] = useState(
    "",
  );


  const [
    confirmarGuardar,
    setConfirmarGuardar,
  ] = useState(
    false,
  );


  // ========================================================
  // CARGAR
  // ========================================================

  const cargar =
    async () => {

      try {

        setCargando(
          true,
        );

        setError("");


        const response =
          await obtenerPermisosOncologo();


        setNombreRol(
          response.rol?.nombre
          ??
          "Oncólogo",
        );


        setPermisos(
          response.permisos,
        );


        const activos =
          new Set(

            response.permisos
              .filter(
                (permiso) =>
                  permiso.asignado,
              )
              .map(
                (permiso) =>
                  permiso.codigo,
              ),

          );


        setSeleccionados(
          new Set(
            activos,
          ),
        );


        setSeleccionadosIniciales(
          new Set(
            activos,
          ),
        );

      } catch (
        errorActual
      ) {

        setError(
          obtenerMensajeErrorPermisos(
            errorActual,
          ),
        );

      } finally {

        setCargando(
          false,
        );

      }

    };


  useEffect(
    () => {

      void cargar();

    },
    [],
  );


  // ========================================================
  // CAMBIOS
  // ========================================================

  const alternarPermiso =
    (
      codigo: string,
    ) => {

      setSeleccionados(
        (actuales) => {

          const nuevos =
            new Set(
              actuales,
            );


          if (
            nuevos.has(
              codigo,
            )
          ) {

            nuevos.delete(
              codigo,
            );

          } else {

            nuevos.add(
              codigo,
            );

          }


          return nuevos;

        },
      );


      setError("");

      setExito("");

    };


  const seleccionarTodos =
    () => {

      setSeleccionados(

        new Set(

          permisos.map(
            (permiso) =>
              permiso.codigo,
          ),

        ),

      );

    };


  const quitarTodos =
    () => {

      setSeleccionados(
        new Set(),
      );

    };


  const restaurar =
    () => {

      setSeleccionados(

        new Set(
          seleccionadosIniciales,
        ),

      );

      setError("");

      setExito("");

    };


  // ========================================================
  // DETECTAR CAMBIOS
  // ========================================================

  const hayCambios =
    useMemo(
      () => {

        if (
          seleccionados.size
          !==
          seleccionadosIniciales.size
        ) {

          return true;

        }


        for (
          const codigo
          of seleccionados
        ) {

          if (
            !seleccionadosIniciales.has(
              codigo,
            )
          ) {

            return true;

          }

        }


        return false;

      },
      [
        seleccionados,
        seleccionadosIniciales,
      ],
    );


  // ========================================================
  // GUARDAR
  // ========================================================

  const guardar =
    async () => {

      try {

        setGuardando(
          true,
        );

        setError("");

        setExito("");


        const codigos =
          Array.from(
            seleccionados,
          );


        const response =
          await actualizarPermisosOncologo(
            codigos,
          );


        const nuevosActivos =
          new Set(

            response.permisos
              .filter(
                (permiso) =>
                  permiso.asignado,
              )
              .map(
                (permiso) =>
                  permiso.codigo,
              ),

          );


        setPermisos(
          response.permisos,
        );


        setSeleccionados(
          new Set(
            nuevosActivos,
          ),
        );


        setSeleccionadosIniciales(
          new Set(
            nuevosActivos,
          ),
        );


        setConfirmarGuardar(
          false,
        );


        setExito(
          response.mensaje,
        );


        window.setTimeout(
          () => {

            setExito("");

          },
          4000,
        );

      } catch (
        errorActual
      ) {

        setConfirmarGuardar(
          false,
        );


        setError(
          obtenerMensajeErrorPermisos(
            errorActual,
          ),
        );

      } finally {

        setGuardando(
          false,
        );

      }

    };


  // ========================================================
  // LOADING
  // ========================================================

  if (
    cargando
  ) {

    return (

      <div className="permissions-page">

        <div className="permissions-loading">

          <LoaderCircle
            size={30}
            className="permissions-spin"
          />

          <strong>
            Cargando permisos...
          </strong>

          <span>
            Consultando configuración del rol Oncólogo.
          </span>

        </div>

      </div>

    );

  }


  // ========================================================
  // RENDER
  // ========================================================

  return (

    <div className="permissions-page">


      {/* ====================================================
          CABECERA
          ==================================================== */}

      <section className="permissions-header">


        <div>

          <span className="permissions-header__eyebrow">

            Jefatura de Oncología

          </span>


          <h1>
            Administración de permisos
          </h1>


          <p>

            Configure las funcionalidades que
            estarán disponibles para el personal
            con rol de médico oncólogo.

          </p>

        </div>


        <div className="permissions-header__badge">

          <ShieldCheck
            size={18}
          />

          Solo Jefatura

        </div>


      </section>


      {/* ====================================================
          MENSAJES
          ==================================================== */}

      {exito && (

        <div className="permissions-alert permissions-alert--success">

          <CheckCircle2
            size={18}
          />

          {exito}

        </div>

      )}


      {error && (

        <div className="permissions-alert permissions-alert--error">

          <AlertCircle
            size={18}
          />

          {error}

        </div>

      )}


      {/* ====================================================
          INFORMACIÓN ROL
          ==================================================== */}

      <section className="permissions-role-card">


        <div className="permissions-role-card__icon">

          <UserRound
            size={25}
          />

        </div>


        <div className="permissions-role-card__info">

          <span>
            Rol administrado
          </span>

          <strong>
            {nombreRol}
          </strong>

          <small>

            Los cambios se aplicarán a las
            cuentas que utilizan este rol.

          </small>

        </div>


        <div className="permissions-role-card__counter">

          <strong>

            {
              seleccionados
                .size
            }

          </strong>

          <span>

            de {
              permisos.length
            } habilitados

          </span>

        </div>


      </section>


      {/* ====================================================
          CONTROLES
          ==================================================== */}

      <section className="permissions-card">


        <header className="permissions-card__header">


          <div>

            <h2>
              Permisos disponibles
            </h2>

            <p>

              Active o desactive las
              funcionalidades autorizadas.

            </p>

          </div>


          <div className="permissions-tools">


            <button

              type="button"

              onClick={
                seleccionarTodos
              }

            >

              <Check
                size={15}
              />

              Habilitar todos

            </button>


            <button

              type="button"

              onClick={
                quitarTodos
              }

            >

              <X
                size={15}
              />

              Deshabilitar todos

            </button>


            <button

              type="button"

              onClick={
                restaurar
              }

              disabled={
                !hayCambios
              }

            >

              <RefreshCw
                size={15}
              />

              Restaurar

            </button>


          </div>


        </header>


        {/* ==================================================
            PERMISOS
            ================================================== */}

        <div className="permissions-grid">


          {permisos.map(
            (permiso) => {

              const activo =
                seleccionados.has(
                  permiso.codigo,
                );


              const Icon =
                obtenerIconoPermiso(
                  permiso.codigo,
                );


              return (

                <button

                  type="button"

                  key={
                    permiso.codigo
                  }

                  className={`
                    permission-item
                    ${
                      activo
                        ? "permission-item--active"
                        : ""
                    }
                  `}

                  onClick={() =>
                    alternarPermiso(
                      permiso.codigo,
                    )
                  }

                >


                  <div className="permission-item__top">


                    <div className="permission-item__icon">

                      <Icon
                        size={21}
                      />

                    </div>


                    <div
                      className={`
                        permission-switch
                        ${
                          activo
                            ? "permission-switch--active"
                            : ""
                        }
                      `}
                    >

                      <span />

                    </div>


                  </div>


                  <div className="permission-item__content">


                    <span className="permission-item__module">

                      {obtenerNombreModulo(
                        permiso,
                      )}

                    </span>


                    <strong>

                      {
                        permiso.nombre
                      }

                    </strong>


                    <p>

                      {
                        permiso.descripcion
                        ||
                        "Permiso del sistema."
                      }

                    </p>


                  </div>


                  <div className="permission-item__state">


                    {activo ? (

                      <>

                        <BadgeCheck
                          size={15}
                        />

                        Habilitado

                      </>

                    ) : (

                      <>

                        <LockKeyhole
                          size={15}
                        />

                        Deshabilitado

                      </>

                    )}


                  </div>


                </button>

              );

            },
          )}


        </div>


        {/* ==================================================
            FOOTER
            ================================================== */}

        <footer className="permissions-card__footer">


          <div
            className={`
              permissions-change-state
              ${
                hayCambios
                  ? "permissions-change-state--changed"
                  : ""
              }
            `}
          >

            {hayCambios ? (

              <>

                <AlertCircle
                  size={17}
                />

                Existen cambios pendientes de guardar.

              </>

            ) : (

              <>

                <CheckCircle2
                  size={17}
                />

                La configuración está actualizada.

              </>

            )}

          </div>


          <button

            type="button"

            className="permissions-save-button"

            disabled={
              !hayCambios
              ||
              guardando
            }

            onClick={() =>
              setConfirmarGuardar(
                true,
              )
            }

          >

            <Save
              size={17}
            />

            Guardar permisos

          </button>


        </footer>


      </section>


      {/* ====================================================
          NOTA
          ==================================================== */}

      <section className="permissions-security-note">

        <ShieldCheck
          size={20}
        />

        <div>

          <strong>
            Control de acceso basado en roles
          </strong>

          <span>

            Esta configuración modifica los permisos
            asociados al rol Oncólogo. Los permisos
            administrativos de Jefatura no pueden
            modificarse desde esta pantalla.

          </span>

        </div>

      </section>


      {/* ====================================================
          MODAL CONFIRMACIÓN
          ==================================================== */}

      {confirmarGuardar && (

        <div
          className="permissions-modal-backdrop"
          onMouseDown={() => {

            if (
              !guardando
            ) {

              setConfirmarGuardar(
                false,
              );

            }

          }}
        >

          <section

            className="permissions-modal"

            onMouseDown={(event) =>
              event.stopPropagation()
            }

          >


            <button

              type="button"

              className="permissions-modal__close"

              disabled={
                guardando
              }

              onClick={() =>
                setConfirmarGuardar(
                  false,
                )
              }

            >

              <X
                size={19}
              />

            </button>


            <div className="permissions-modal__icon">

              <ShieldCheck
                size={28}
              />

            </div>


            <h2>
              Guardar permisos
            </h2>


            <p>

              ¿Desea aplicar esta configuración
              al rol{" "}

              <strong>
                {nombreRol}
              </strong>

              ?

            </p>


            <div className="permissions-modal__summary">

              <div>

                <span>
                  Habilitados
                </span>

                <strong>
                  {seleccionados.size}
                </strong>

              </div>


              <div>

                <span>
                  Deshabilitados
                </span>

                <strong>

                  {
                    permisos.length
                    -
                    seleccionados.size
                  }

                </strong>

              </div>

            </div>


            <div className="permissions-modal__notice">

              <AlertCircle
                size={18}
              />

              <span>

                Los cambios afectarán las
                funcionalidades disponibles para
                los médicos oncólogos.

              </span>

            </div>


            <div className="permissions-modal__actions">


              <button

                type="button"

                className="permissions-cancel-button"

                disabled={
                  guardando
                }

                onClick={() =>
                  setConfirmarGuardar(
                    false,
                  )
                }

              >

                Cancelar

              </button>


              <button

                type="button"

                className="permissions-confirm-button"

                disabled={
                  guardando
                }

                onClick={() =>
                  void guardar()
                }

              >

                {guardando ? (

                  <LoaderCircle
                    size={17}
                    className="permissions-spin"
                  />

                ) : (

                  <Save
                    size={17}
                  />

                )}


                {guardando
                  ? "Guardando..."
                  : "Sí, guardar"}

              </button>


            </div>


          </section>

        </div>

      )}


    </div>

  );

}