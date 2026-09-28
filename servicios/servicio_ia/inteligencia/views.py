import os

import pika
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from inteligencia.inference import (
    AnatomyImageError,
    AnatomyModelUnavailable,
    AnatomyValidator,
    OsteosarcomaImageError,
    OsteosarcomaModelUnavailable,
    OsteosarcomaValidator,
    RadiographyImageError,
    RadiographyModelUnavailable,
    RadiographyValidator,
)


MAX_FILE_BYTES = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "dcm",
}


def comprobar_postgresql():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        cursor.fetchone()


def comprobar_rabbitmq():
    credenciales = pika.PlainCredentials(
        os.environ["RABBITMQ_USER"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    parametros = pika.ConnectionParameters(
        host=os.environ["RABBITMQ_HOST"],
        port=int(
            os.environ.get(
                "RABBITMQ_PORT",
                "5672",
            )
        ),
        credentials=credenciales,
        connection_attempts=3,
        retry_delay=1,
    )

    conexion = pika.BlockingConnection(
        parametros
    )

    canal = conexion.channel()

    canal.queue_declare(
        queue="analisis_radiografia",
        durable=True,
    )

    conexion.close()


def health_check(request):
    estado_bd = "desconectada"
    estado_rabbitmq = "desconectado"

    try:
        comprobar_postgresql()
        estado_bd = "conectada"
    except Exception:
        pass

    try:
        comprobar_rabbitmq()
        estado_rabbitmq = "conectado"
    except Exception:
        pass

    radiography_validator = (
        RadiographyValidator()
    )

    anatomy_validator = (
        AnatomyValidator()
    )

    osteosarcoma_validator = (
        OsteosarcomaValidator()
    )

    correcto = (
        estado_bd == "conectada"
        and estado_rabbitmq == "conectado"
    )

    return JsonResponse(
        {
            "servicio": "servicio_ia",
            "estado": (
                "ok"
                if correcto
                else "error"
            ),
            "base_datos": estado_bd,
            "rabbitmq": estado_rabbitmq,
            "validador_radiografia": {
                "modelo": "EfficientNetB0",
                "version": "V3",
                "disponible": (
                    radiography_validator
                    .available
                ),
            },
            "validador_anatomico": {
                "modelo": "EfficientNetB0",
                "version": "V1",
                "disponible": (
                    anatomy_validator
                    .available
                ),
            },
            "analizador_osteosarcoma": {
                "modelo": "EfficientNetB0",
                "version": (
                    "Fine-tuned V1"
                ),
                "disponible": (
                    osteosarcoma_validator
                    .available
                ),
            },
        },
        status=(
            200
            if correcto
            else 503
        ),
    )


@require_POST
def validar_radiografia(request):
    archivo = request.FILES.get(
        "file"
    )

    if archivo is None:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_FILE_REQUIRED"
                    ),
                    "message": (
                        "Debe adjuntar una imagen "
                        "para analizarla."
                    ),
                }
            },
            status=422,
        )

    nombre = str(
        getattr(
            archivo,
            "name",
            "imagen",
        )
    )

    extension = (
        nombre.rsplit(
            ".",
            1,
        )[-1].lower()
        if "." in nombre
        else ""
    )

    if extension not in ALLOWED_EXTENSIONS:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_FILE_FORMAT"
                    ),
                    "message": (
                        "Solo se permiten archivos "
                        "JPG, PNG o DICOM."
                    ),
                }
            },
            status=422,
        )

    size = int(
        getattr(
            archivo,
            "size",
            0,
        )
        or 0
    )

    if size <= 0:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_FILE_EMPTY"
                    ),
                    "message": (
                        "El archivo recibido "
                        "está vacío."
                    ),
                }
            },
            status=422,
        )

    if size > MAX_FILE_BYTES:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_FILE_TOO_LARGE"
                    ),
                    "message": (
                        "La imagen no puede "
                        "superar los 20 MB."
                    ),
                }
            },
            status=422,
        )

    raw = archivo.read()

    # =========================================================
    # ETAPA 1 - RADIOGRAFÍA
    # =========================================================

    try:
        radiography_prediction = (
            RadiographyValidator()
            .predict(
                raw,
                nombre,
            )
        )

    except RadiographyModelUnavailable as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_MODEL_UNAVAILABLE"
                    ),
                    "message": str(exc),
                }
            },
            status=503,
        )

    except RadiographyImageError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_IMAGE_INVALID"
                    ),
                    "message": str(exc),
                }
            },
            status=422,
        )

    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_VALIDATION_ERROR"
                    ),
                    "message": (
                        "No fue posible ejecutar "
                        "la validación radiográfica."
                    ),
                }
            },
            status=500,
        )

    radiography_data = {
        "confianza": round(
            radiography_prediction
            .confidence,
            6,
        ),
        "probabilidad_radiografia": round(
            radiography_prediction
            .radiography_probability,
            6,
        ),
        "probabilidad_no_radiografia": round(
            radiography_prediction
            .non_radiography_probability,
            6,
        ),
        "umbral": (
            radiography_prediction
            .threshold
        ),
        "arquitectura": (
            radiography_prediction
            .architecture
        ),
        "version": "V3",
    }

    if not (
        radiography_prediction
        .is_radiography
    ):
        return JsonResponse(
            {
                "data": {
                    "es_radiografia": False,
                    "anatomia_evaluada": False,
                    "anatomia_admitida": None,
                    "analisis_osteosarcoma_evaluado": False,
                    "osteosarcoma_sospechoso": None,
                    "puede_continuar": False,
                    "etapa_rechazo": (
                        "validacion_radiografia"
                    ),
                    "mensaje": (
                        "La imagen no fue "
                        "identificada como una "
                        "radiografía."
                    ),

                    # Compatibilidad frontend.
                    **radiography_data,

                    "validacion_radiografia": (
                        radiography_data
                    ),
                    "familia_modelo": (
                        "EfficientNet"
                    ),
                }
            },
            status=200,
        )

    # =========================================================
    # ETAPA 2 - ANATOMÍA
    # =========================================================

    try:
        anatomy_prediction = (
            AnatomyValidator()
            .predict(
                raw,
                nombre,
            )
        )

    except AnatomyModelUnavailable as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_MODEL_UNAVAILABLE"
                    ),
                    "message": str(exc),
                }
            },
            status=503,
        )

    except AnatomyImageError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_IMAGE_INVALID"
                    ),
                    "message": str(exc),
                }
            },
            status=422,
        )

    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_VALIDATION_ERROR"
                    ),
                    "message": (
                        "No fue posible ejecutar "
                        "la validación anatómica."
                    ),
                }
            },
            status=500,
        )

    anatomy_data = {
        "confianza": round(
            anatomy_prediction
            .confidence,
            6,
        ),
        "probabilidad_admitida": round(
            anatomy_prediction
            .admitted_probability,
            6,
        ),
        "probabilidad_no_admitida": round(
            anatomy_prediction
            .non_admitted_probability,
            6,
        ),
        "umbral": (
            anatomy_prediction
            .threshold
        ),
        "arquitectura": (
            anatomy_prediction
            .architecture
        ),
        "version": (
            anatomy_prediction
            .version
        ),
        "huesos_admitidos": [
            "húmero",
            "radio",
            "cúbito",
            "fémur",
            "tibia",
            "peroné",
        ],
    }

    if not anatomy_prediction.is_admitted:
        return JsonResponse(
            {
                "data": {
                    "es_radiografia": True,
                    "anatomia_evaluada": True,
                    "anatomia_admitida": False,
                    "analisis_osteosarcoma_evaluado": False,
                    "osteosarcoma_sospechoso": None,
                    "puede_continuar": False,
                    "etapa_rechazo": (
                        "validacion_anatomica"
                    ),
                    "mensaje": (
                        "La imagen corresponde a "
                        "una radiografía, pero la "
                        "región anatómica no está "
                        "admitida para el análisis."
                    ),

                    # Compatibilidad frontend.
                    **radiography_data,

                    "validacion_radiografia": (
                        radiography_data
                    ),
                    "validacion_anatomica": (
                        anatomy_data
                    ),
                    "familia_modelo": (
                        "EfficientNet"
                    ),
                }
            },
            status=200,
        )

    # =========================================================
    # ETAPA 3 - OSTEOSARCOMA
    # =========================================================

    try:
        tumor_prediction = (
            OsteosarcomaValidator()
            .predict(
                raw,
                nombre,
            )
        )

    except OsteosarcomaModelUnavailable as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_MODEL_UNAVAILABLE"
                    ),
                    "message": str(exc),
                }
            },
            status=503,
        )

    except OsteosarcomaImageError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_IMAGE_INVALID"
                    ),
                    "message": str(exc),
                }
            },
            status=422,
        )

    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_ANALYSIS_ERROR"
                    ),
                    "message": (
                        "No fue posible ejecutar "
                        "el análisis de osteosarcoma."
                    ),
                }
            },
            status=500,
        )

    tumor_data = {
        "sospechoso": (
            tumor_prediction
            .is_suspicious
        ),
        "confianza": round(
            tumor_prediction
            .confidence,
            6,
        ),
        "probabilidad_osteosarcoma": round(
            tumor_prediction
            .osteosarcoma_probability,
            6,
        ),
        "probabilidad_no_osteosarcoma": round(
            tumor_prediction
            .non_osteosarcoma_probability,
            6,
        ),
        "umbral": (
            tumor_prediction
            .threshold
        ),
        "arquitectura": (
            tumor_prediction
            .architecture
        ),
        "version": (
            tumor_prediction
            .version
        ),
    }

    if tumor_prediction.is_suspicious:
        message = (
            "El modelo identificó características "
            "radiográficas compatibles con un "
            "resultado sospechoso de osteosarcoma. "
            "El resultado requiere revisión clínica."
        )
    else:
        message = (
            "El modelo no identificó suficientes "
            "características radiográficas para "
            "clasificar la imagen como sospechosa "
            "de osteosarcoma. El resultado no "
            "sustituye la valoración clínica."
        )

    return JsonResponse(
        {
            "data": {
                "es_radiografia": True,
                "anatomia_evaluada": True,
                "anatomia_admitida": True,

                "analisis_osteosarcoma_evaluado": (
                    True
                ),

                "osteosarcoma_sospechoso": (
                    tumor_prediction
                    .is_suspicious
                ),

                "puede_continuar": True,
                "etapa_rechazo": None,
                "mensaje": message,

                # Compatibilidad con frontend actual.
                **radiography_data,

                "validacion_radiografia": (
                    radiography_data
                ),

                "validacion_anatomica": (
                    anatomy_data
                ),

                "analisis_osteosarcoma": (
                    tumor_data
                ),

                "familia_modelo": (
                    "EfficientNet"
                ),
            }
        },
        status=200,
    )
