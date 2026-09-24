import os

import pika
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from inteligencia.inference import (
    RadiographyImageError,
    RadiographyModelUnavailable,
    RadiographyValidator,
)


MAX_FILE_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "dcm"}


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
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        credentials=credenciales,
        connection_attempts=3,
        retry_delay=1,
    )

    conexion = pika.BlockingConnection(parametros)
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

    validador = RadiographyValidator()

    correcto = (
        estado_bd == "conectada"
        and estado_rabbitmq == "conectado"
    )

    return JsonResponse(
        {
            "servicio": "servicio_ia",
            "estado": "ok" if correcto else "error",
            "base_datos": estado_bd,
            "rabbitmq": estado_rabbitmq,
            "validador_radiografia": {
                "modelo": "EfficientNet",
                "disponible": validador.available,
            },
        },
        status=200 if correcto else 503,
    )


@require_POST
def validar_radiografia(request):
    archivo = request.FILES.get("file")

    if archivo is None:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_FILE_REQUIRED",
                    "message": "Debe adjuntar una imagen para validarla.",
                }
            },
            status=422,
        )

    nombre = str(getattr(archivo, "name", "imagen"))
    extension = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""

    if extension not in ALLOWED_EXTENSIONS:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_FILE_FORMAT",
                    "message": "Solo se permiten archivos JPG, PNG o DICOM.",
                }
            },
            status=422,
        )

    size = int(getattr(archivo, "size", 0) or 0)
    if size <= 0:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_FILE_EMPTY",
                    "message": "El archivo recibido está vacío.",
                }
            },
            status=422,
        )

    if size > MAX_FILE_BYTES:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_FILE_TOO_LARGE",
                    "message": "La imagen no puede superar los 20 MB.",
                }
            },
            status=422,
        )

    raw = archivo.read()

    try:
        prediction = RadiographyValidator().predict(raw, nombre)
    except RadiographyModelUnavailable as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_MODEL_UNAVAILABLE",
                    "message": str(exc),
                }
            },
            status=503,
        )
    except RadiographyImageError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_IMAGE_INVALID",
                    "message": str(exc),
                }
            },
            status=422,
        )
    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": "RADIOGRAPHY_VALIDATION_ERROR",
                    "message": "No fue posible ejecutar la validación EfficientNet.",
                }
            },
            status=500,
        )

    message = (
        "La imagen fue identificada como radiografía."
        if prediction.is_radiography
        else "La imagen subida no fue identificada como una radiografía. Seleccione una radiografía válida para continuar."
    )

    return JsonResponse(
        {
            "data": {
                "es_radiografia": prediction.is_radiography,
                "confianza": round(prediction.confidence, 6),
                "probabilidad_radiografia": round(
                    prediction.radiography_probability,
                    6,
                ),
                "probabilidad_no_radiografia": round(
                    prediction.non_radiography_probability,
                    6,
                ),
                "umbral": prediction.threshold,
                "arquitectura": prediction.architecture,
                "familia_modelo": "EfficientNet",
                "mensaje": message,
            }
        },
        status=200,
    )
