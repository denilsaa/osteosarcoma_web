import {
  CheckCircle2,
  Clock3,
  KeyRound,
  RefreshCw,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  useAuth,
} from "../../auth/AuthProvider";

import "./PerfilPage.css";


function formatearFecha(
  fechaIso: string | null,
): string {

  if (!fechaIso) {
    return "No disponible";
  }


  const fecha =
    new Date(fechaIso);


  if (
    Number.isNaN(
      fecha.getTime(),
    )
  ) {

    return "No disponible";

  }


  return new Intl.DateTimeFormat(

    "es-BO",

    {

      dateStyle:
        "medium",

      timeStyle:
        "medium",

    },

  ).format(fecha);

}


function cuentaRegresiva(

  fechaIso: string | null,

  ahora: number,

): string {

  if (!fechaIso) {

    return "No disponible";

  }


  const diferencia =

    new Date(
      fechaIso,
    ).getTime()

    -

    ahora;


  if (
    diferencia <= 0
  ) {

    return "Vencido";

  }


  const totalSegundos =
    Math.floor(
      diferencia / 1000,
    );


  const horas =
    Math.floor(
      totalSegundos / 3600,
    );


  const minutos =
    Math.floor(
      (
        totalSegundos % 3600
      ) / 60,
    );


  const segundos =
    totalSegundos % 60;


  if (horas > 0) {

    return (
      `${horas} h ` +
      `${minutos} min ` +
      `${segundos} s`
    );

  }


  return (
    `${minutos} min ` +
    `${segundos} s`
  );

}


export function PerfilPage() {

  const {

    usuario,

    infoSesion,

    eventoSesion,

    renovarSesion,

  } = useAuth();


  const [
    ahora,
    setAhora,
  ] = useState(
    Date.now(),
  );


  const [
    renovando,
    setRenovando,
  ] = useState(false);


  const [
    errorRenovacion,
    setErrorRenovacion,
  ] = useState("");


  useEffect(
    () => {

      const intervalo =
        window.setInterval(

          () => {

            setAhora(
              Date.now(),
            );

          },

          1000,

        );


      return () => {

        window.clearInterval(
          intervalo,
        );

      };

    },
    [],
  );


  const nombreCompleto =
    useMemo(
      () => {

        if (!usuario) {

          return "Usuario";

        }


        const partes = [

          usuario.nombres,

          usuario
            .apellido_paterno,

          usuario
            .apellido_materno,

        ].filter(Boolean);


        if (
          partes.length > 0
        ) {

          return partes.join(
            " ",
          );

        }


        return usuario
          .nombre_usuario;

      },
      [
        usuario,
      ],
    );


  const rolVisible =

    usuario
      ?.roles
      ?.includes(
        "JEFE_ONCOLOGIA",
      )

      ? "Jefe de Oncología"

      : "Médico Oncólogo";


  const accessRestante =

    cuentaRegresiva(

      infoSesion
        .accessExpiraEn,

      ahora,

    );


  const renovar =
    async () => {

      try {

        setRenovando(
          true,
        );

        setErrorRenovacion(
          "",
        );


        await renovarSesion();

      } catch {

        setErrorRenovacion(

          "No fue posible renovar la sesión. Inicie sesión nuevamente.",

        );

      } finally {

        setRenovando(
          false,
        );

      }

    };


  return (

    <div className="profile-page">


      <section className="profile-hero">


        <div>

          <span className="profile-hero__eyebrow">
            Cuenta institucional
          </span>


          <h1>
            Mi perfil
          </h1>


          <p>

            Consulte la información de su cuenta y
            el estado de seguridad de la sesión activa.

          </p>

        </div>


        <div className="profile-hero__badge">

          <ShieldCheck
            size={18}
          />

          Sesión protegida con JWT

        </div>


      </section>


      <div className="profile-grid">


        <section className="profile-card">


          <div className="profile-card__heading">

            <div className="profile-card__icon">

              <UserRound
                size={20}
              />

            </div>


            <div>

              <h2>
                Información de la cuenta
              </h2>

              <p>
                Usuario autenticado actualmente.
              </p>

            </div>

          </div>


          <div className="profile-account">

            <div className="profile-account__avatar">

              {nombreCompleto
                .substring(
                  0,
                  2,
                )
                .toUpperCase()}

            </div>


            <div>

              <strong>
                {nombreCompleto}
              </strong>

              <span>
                {rolVisible}
              </span>

            </div>

          </div>


          <div className="profile-data-grid">


            <div className="profile-data-item">

              <span>
                Usuario
              </span>

              <strong>
                {usuario
                  ?.nombre_usuario ??
                  "—"}
              </strong>

            </div>


            <div className="profile-data-item">

              <span>
                Correo
              </span>

              <strong>
                {usuario
                  ?.correo ??
                  "—"}
              </strong>

            </div>


            <div className="profile-data-item">

              <span>
                Estado
              </span>

              <strong className="profile-state">

                <CheckCircle2
                  size={15}
                />

                {usuario
                  ?.estado ??
                  "ACTIVO"}

              </strong>

            </div>


            <div className="profile-data-item">

              <span>
                Rol
              </span>

              <strong>
                {rolVisible}
              </strong>

            </div>


          </div>


        </section>


        <section className="profile-card">


          <div className="profile-card__heading">

            <div className="profile-card__icon">

              <KeyRound
                size={20}
              />

            </div>


            <div>

              <h2>
                Seguridad de la sesión
              </h2>

              <p>
                Estado del access y refresh token.
              </p>

            </div>

          </div>


          <div className="session-status">

            <span className="session-status__dot" />


            <div>

              <strong>
                Sesión activa
              </strong>

              <span>

                ID:{" "}

                {infoSesion
                  .idSesion ??
                  "No disponible"}

              </span>

            </div>

          </div>


          <div className="session-metrics">


            <div className="session-metric">

              <Clock3
                size={18}
              />


              <div>

                <span>
                  Access token vence en
                </span>

                <strong>
                  {accessRestante}
                </strong>

              </div>

            </div>


            <div className="session-metric">

              <ShieldCheck
                size={18}
              />


              <div>

                <span>
                  Refresh válido hasta
                </span>

                <strong>

                  {formatearFecha(

                    infoSesion
                      .refreshExpiraEn,

                  )}

                </strong>

              </div>

            </div>


            <div className="session-metric">

              <RefreshCw
                size={18}
              />


              <div>

                <span>
                  Última renovación
                </span>

                <strong>

                  {formatearFecha(

                    infoSesion
                      .ultimaRenovacion,

                  )}

                </strong>

              </div>

            </div>


          </div>


          {eventoSesion && (

            <div
              className={`
                session-event
                session-event--${eventoSesion.tipo.toLowerCase()}
              `}
            >

              <strong>
                {eventoSesion.mensaje}
              </strong>


              <span>

                {formatearFecha(
                  eventoSesion.fecha,
                )}

              </span>

            </div>

          )}


          {errorRenovacion && (

            <div className="session-error">

              {errorRenovacion}

            </div>

          )}


          <button

            type="button"

            className="session-renew-button"

            onClick={renovar}

            disabled={renovando}

          >

            <RefreshCw
              size={17}
            />


            {renovando

              ? "Renovando sesión..."

              : "Renovar access token"}

          </button>


        </section>


      </div>


    </div>

  );

}