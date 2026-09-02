import json
import logging
import os

from urllib.error import (
    HTTPError,
    URLError,
)

from urllib.request import (
    Request,
    urlopen,
)


logger = logging.getLogger(__name__)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

AUDITORIA_URL = (
    os.getenv(
        "AUDITORIA_URL",
        ""
    )
    .strip()
    .rstrip("/")
)


AUDITORIA_TIMEOUT_SECONDS = float(
    os.getenv(
        "AUDITORIA_TIMEOUT_SECONDS",
        "5"
    )
)


# ==========================================================
# UTILIDADES
# ==========================================================

def _texto(valor):
    """
    Convierte valores opcionales en texto limpio.
    """

    if valor is None:
        return None

    valor = str(valor).strip()

    return valor or None


def _serializar_respuesta(response):
    """
    Intenta convertir la respuesta JSON de Auditoría
    en un diccionario de Python.
    """

    contenido = response.read().decode(
        "utf-8"
    )

    if not contenido:
        return None

    try:
        return json.loads(
            contenido
        )

    except json.JSONDecodeError:
        return {
            "contenido":
                contenido
        }


# ==========================================================
# REGISTRAR EVENTO
# ==========================================================

def registrar_evento_auditoria(
    *,
    actor_usuario_uuid=None,
    actor_nombre=None,
    actor_rol=None,

    servicio,
    modulo,
    accion,
    resultado,

    entidad_tipo=None,
    entidad_id=None,

    correlation_id=None,

    direccion_ip=None,
    user_agent=None,

    descripcion=None,
    motivo=None,

    detalle_json=None,
    cambios=None,
):
    """
    Registra una acción en el microservicio de Auditoría.

    Este cliente NO lanza excepciones hacia la operación
    principal cuando Auditoría no está disponible.

    Ejemplo:

        registrar_evento_auditoria(
            actor_usuario_uuid="...",
            actor_nombre="Dr. Carlos Pérez",
            actor_rol="Médico Oncólogo",
            servicio="CLINICO",
            modulo="PACIENTES",
            accion="EDITAR",
            resultado="EXITOSO",
        )

    Retorna:

        {
            "ok": True,
            "status": 201,
            "data": {...}
        }

    o, si Auditoría falla:

        {
            "ok": False,
            "error": "..."
        }
    """

    # ======================================================
    # AUDITORÍA NO CONFIGURADA
    # ======================================================

    if not AUDITORIA_URL:

        logger.warning(
            "AUDITORIA_URL no está configurada."
        )

        return {
            "ok": False,
            "error":
                "AUDITORIA_URL no configurada",
        }


    # ======================================================
    # PAYLOAD
    # ======================================================

    payload = {

        "actor_usuario_uuid":
            _texto(
                actor_usuario_uuid
            ),

        "actor_nombre":
            _texto(
                actor_nombre
            ),

        "actor_rol":
            _texto(
                actor_rol
            ),

        "servicio":
            _texto(
                servicio
            ),

        "modulo":
            _texto(
                modulo
            ),

        "accion":
            _texto(
                accion
            ),

        "resultado":
            _texto(
                resultado
            ),

        "entidad_tipo":
            _texto(
                entidad_tipo
            ),

        "entidad_id":
            _texto(
                entidad_id
            ),

        "correlation_id":
            _texto(
                correlation_id
            ),

        "direccion_ip":
            _texto(
                direccion_ip
            ),

        "user_agent":
            _texto(
                user_agent
            ),

        "descripcion":
            _texto(
                descripcion
            ),

        "motivo":
            _texto(
                motivo
            ),

        "detalle_json":
            detalle_json
            if isinstance(
                detalle_json,
                dict
            )
            else {},

        "cambios":
            cambios
            if isinstance(
                cambios,
                list
            )
            else [],
    }


    # ======================================================
    # NO ENVIAR NULOS INNECESARIOS
    # ======================================================

    payload = {
        clave: valor
        for clave, valor
        in payload.items()
        if valor is not None
    }


    # ======================================================
    # JSON UTF-8
    # ======================================================

    cuerpo = json.dumps(
        payload,
        ensure_ascii=False,
        default=str,
    ).encode(
        "utf-8"
    )


    # ======================================================
    # REQUEST
    # ======================================================

    request = Request(

        url=(
            f"{AUDITORIA_URL}"
            "/api/auditoria/eventos"
        ),

        data=cuerpo,

        headers={
            "Accept":
                "application/json",

            "Content-Type":
                "application/json; charset=utf-8",
        },

        method="POST",
    )


    # ======================================================
    # ENVÍO
    # ======================================================

    try:

        with urlopen(
            request,
            timeout=(
                AUDITORIA_TIMEOUT_SECONDS
            ),
        ) as response:

            status_code = (
                response.status
            )

            data = (
                _serializar_respuesta(
                    response
                )
            )

            return {
                "ok":
                    200
                    <= status_code
                    < 300,

                "status":
                    status_code,

                "data":
                    data,
            }


    # ======================================================
    # HTTP 4XX / 5XX
    # ======================================================

    except HTTPError as error:

        try:

            contenido = (
                error.read()
                .decode(
                    "utf-8"
                )
            )

        except Exception:

            contenido = ""


        logger.warning(
            "Auditoría respondió HTTP %s: %s",
            error.code,
            contenido,
        )


        return {
            "ok":
                False,

            "status":
                error.code,

            "error":
                contenido
                or
                str(
                    error
                ),
        }


    # ======================================================
    # NO SE PUDO CONECTAR
    # ======================================================

    except URLError as error:

        logger.warning(
            "No fue posible conectar "
            "con servicio_auditoria: %s",
            error,
        )


        return {
            "ok":
                False,

            "error":
                str(
                    error
                ),
        }


    # ======================================================
    # TIMEOUT / OTRO ERROR
    # ======================================================

    except Exception as error:

        logger.warning(
            "Error inesperado al registrar "
            "evento de Auditoría: %s",
            error,
        )


        return {
            "ok":
                False,

            "error":
                str(
                    error
                ),
        }