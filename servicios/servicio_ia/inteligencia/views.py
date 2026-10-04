import os
import uuid

import pika

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from inteligencia.models import AnalisisRadiografiaIA

from inteligencia.inference import (
    AnatomyImageError,
    AnatomyModelUnavailable,
    AnatomyValidator,

    OsteosarcomaDetector,
    OsteosarcomaDetectorImageError,
    OsteosarcomaDetectorUnavailable,

    OsteosarcomaImageError,
    OsteosarcomaModelUnavailable,
    OsteosarcomaValidator,

    RadiographyImageError,
    RadiographyModelUnavailable,
    RadiographyValidator,
)


MAX_FILE_BYTES = (
    20
    * 1024
    * 1024
)


ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "dcm",
}




# ==========================================================
# PERSISTENCIA DE ANALISIS CLINICO IA
# ==========================================================


def _uuid_opcional(
    value,
    field_name,
):
    if value in (
        None,
        "",
    ):
        return None

    try:
        return uuid.UUID(
            str(
                value
            )
        )

    except (
        ValueError,
        TypeError,
        AttributeError,
    ) as exc:
        raise ValueError(
            (
                f"El campo {field_name} "
                "debe contener un UUID valido."
            )
        ) from exc


def _obtener_contexto_persistencia(
    request,
):
    radiografia_uuid_raw = (
        request.POST.get(
            "radiografia_uuid"
        )
    )

    caso_uuid_raw = (
        request.POST.get(
            "caso_uuid"
        )
    )

    solicitado_por_uuid_raw = (
        request.POST.get(
            "solicitado_por_uuid"
        )
    )


    if (
        not radiografia_uuid_raw
        and
        not caso_uuid_raw
        and
        not solicitado_por_uuid_raw
    ):
        return None


    if (
        not radiografia_uuid_raw
        or
        not caso_uuid_raw
    ):
        raise ValueError(
            (
                "Para guardar el analisis "
                "debe enviar radiografia_uuid "
                "y caso_uuid."
            )
        )


    return {
        "radiografia_uuid": (
            _uuid_opcional(
                radiografia_uuid_raw,
                "radiografia_uuid",
            )
        ),

        "caso_uuid": (
            _uuid_opcional(
                caso_uuid_raw,
                "caso_uuid",
            )
        ),

        "solicitado_por_uuid": (
            _uuid_opcional(
                solicitado_por_uuid_raw,
                "solicitado_por_uuid",
            )
        ),
    }


def _guardar_analisis_clinico(
    data,
    contexto,
):
    if contexto is None:
        return data


    tumor = (
        data.get(
            "analisis_osteosarcoma"
        )
        or
        {}
    )

    localizacion = (
        data.get(
            "localizacion_osteosarcoma"
        )
        or
        {}
    )

    coordenadas = (
        localizacion.get(
            "coordenadas_normalizadas"
        )
        or
        {}
    )


    analisis = (
        AnalisisRadiografiaIA.objects.create(
            radiografia_uuid=(
                contexto[
                    "radiografia_uuid"
                ]
            ),

            caso_uuid=(
                contexto[
                    "caso_uuid"
                ]
            ),

            solicitado_por_uuid=(
                contexto[
                    "solicitado_por_uuid"
                ]
            ),

            es_radiografia=bool(
                data.get(
                    "es_radiografia",
                    False,
                )
            ),

            anatomia_evaluada=bool(
                data.get(
                    "anatomia_evaluada",
                    False,
                )
            ),

            anatomia_admitida=(
                data.get(
                    "anatomia_admitida"
                )
            ),

            analisis_osteosarcoma_evaluado=bool(
                data.get(
                    "analisis_osteosarcoma_evaluado",
                    False,
                )
            ),

            osteosarcoma_sospechoso=(
                data.get(
                    "osteosarcoma_sospechoso"
                )
            ),

            probabilidad_osteosarcoma=(
                tumor.get(
                    "probabilidad_osteosarcoma"
                )
            ),

            probabilidad_no_osteosarcoma=(
                tumor.get(
                    "probabilidad_no_osteosarcoma"
                )
            ),

            localizacion_evaluada=bool(
                localizacion.get(
                    "evaluada",
                    False,
                )
            ),

            localizacion_detectada=(
                localizacion.get(
                    "detectada"
                )
            ),

            confianza_localizacion=(
                localizacion.get(
                    "confianza"
                )
            ),

            umbral_localizacion=(
                localizacion.get(
                    "umbral"
                )
            ),

            x1=coordenadas.get(
                "x1"
            ),

            y1=coordenadas.get(
                "y1"
            ),

            x2=coordenadas.get(
                "x2"
            ),

            y2=coordenadas.get(
                "y2"
            ),

            etapa_rechazo=(
                data.get(
                    "etapa_rechazo"
                )
            ),

            mensaje=(
                data.get(
                    "mensaje"
                )
            ),

            resultado_json=data,
        )
    )


    data = dict(
        data
    )

    data[
        "persistencia"
    ] = {
        "id_analisis": str(
            analisis.id_analisis
        ),

        "fecha_analisis": (
            analisis
            .fecha_analisis
            .isoformat()
        ),
    }


    return data


def _respuesta_con_persistencia(
    data,
    contexto,
):
    try:
        data = (
            _guardar_analisis_clinico(
                data,
                contexto,
            )
        )

    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "AI_ANALYSIS_"
                        "PERSISTENCE_ERROR"
                    ),

                    "message": (
                        "El analisis fue ejecutado, "
                        "pero no pudo guardarse "
                        "para trazabilidad."
                    ),
                }
            },

            status=500,
        )


    return JsonResponse(
        {
            "data": data
        },

        status=200,
    )


@require_GET
def ultimo_analisis_radiografia(
    request,
    radiografia_uuid,
):
    queryset = (
        AnalisisRadiografiaIA
        .objects
        .filter(
            radiografia_uuid=(
                radiografia_uuid
            )
        )
    )


    caso_uuid_raw = (
        request.GET.get(
            "caso_uuid"
        )
    )


    if caso_uuid_raw:
        try:
            caso_uuid = (
                _uuid_opcional(
                    caso_uuid_raw,
                    "caso_uuid",
                )
            )

        except ValueError as exc:
            return JsonResponse(
                {
                    "error": {
                        "code": (
                            "AI_ANALYSIS_"
                            "INVALID_CASE_UUID"
                        ),

                        "message": (
                            str(
                                exc
                            )
                        ),
                    }
                },

                status=422,
            )


        queryset = (
            queryset.filter(
                caso_uuid=(
                    caso_uuid
                )
            )
        )


    analisis = (
        queryset
        .order_by(
            "-fecha_analisis"
        )
        .first()
    )


    if analisis is None:
        return JsonResponse(
            {
                "data": None
            },

            status=200,
        )


    data = dict(
        analisis.resultado_json
        or
        {}
    )


    data[
        "persistencia"
    ] = {
        "id_analisis": str(
            analisis.id_analisis
        ),

        "fecha_analisis": (
            analisis
            .fecha_analisis
            .isoformat()
        ),
    }


    return JsonResponse(
        {
            "data": data
        },

        status=200,
    )


# ==========================================================
# POSTGRESQL
# ==========================================================


def comprobar_postgresql():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1;"
        )

        cursor.fetchone()


# ==========================================================
# RABBITMQ
# ==========================================================


def comprobar_rabbitmq():
    credenciales = (
        pika.PlainCredentials(
            os.environ[
                "RABBITMQ_USER"
            ],
            os.environ[
                "RABBITMQ_PASSWORD"
            ],
        )
    )

    parametros = (
        pika.ConnectionParameters(
            host=os.environ[
                "RABBITMQ_HOST"
            ],
            port=int(
                os.environ.get(
                    "RABBITMQ_PORT",
                    "5672",
                )
            ),
            credentials=(
                credenciales
            ),
            connection_attempts=3,
            retry_delay=1,
        )
    )

    conexion = (
        pika.BlockingConnection(
            parametros
        )
    )

    canal = (
        conexion.channel()
    )

    canal.queue_declare(
        queue=(
            "analisis_radiografia"
        ),
        durable=True,
    )

    conexion.close()


# ==========================================================
# HEALTH
# ==========================================================


def health_check(
    request,
):
    estado_bd = (
        "desconectada"
    )

    estado_rabbitmq = (
        "desconectado"
    )


    try:
        comprobar_postgresql()

        estado_bd = (
            "conectada"
        )

    except Exception:
        pass


    try:
        comprobar_rabbitmq()

        estado_rabbitmq = (
            "conectado"
        )

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

    osteosarcoma_detector = (
        OsteosarcomaDetector()
    )


    correcto = (
        estado_bd
        == "conectada"
        and
        estado_rabbitmq
        == "conectado"
    )


    return JsonResponse(
        {
            "servicio": (
                "servicio_ia"
            ),

            "estado": (
                "ok"
                if correcto
                else "error"
            ),

            "base_datos": (
                estado_bd
            ),

            "rabbitmq": (
                estado_rabbitmq
            ),

            "validador_radiografia": {
                "modelo": (
                    "EfficientNetB0"
                ),

                "version": "V3",

                "disponible": (
                    radiography_validator
                    .available
                ),
            },

            "validador_anatomico": {
                "modelo": (
                    "EfficientNetB0"
                ),

                "version": "V2",

                "disponible": (
                    anatomy_validator
                    .available
                ),
            },

            "analizador_osteosarcoma": {
                "modelo": (
                    "EfficientNetB0"
                ),

                "version": (
                    "Fine-tuned V1"
                ),

                "disponible": (
                    osteosarcoma_validator
                    .available
                ),
            },

            "localizador_osteosarcoma": {
                "modelo": (
                    "Faster R-CNN "
                    "ResNet50 FPN"
                ),

                "version": "V2",

                "umbral": (
                    osteosarcoma_detector
                    .threshold
                ),

                "disponible": (
                    osteosarcoma_detector
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


# ==========================================================
# VALIDAR / ANALIZAR RADIOGRAF?A
# ==========================================================


@require_POST
def validar_radiografia(
    request,
):
    archivo = (
        request.FILES.get(
            "file"
        )
    )


    # ======================================================
    # ARCHIVO OBLIGATORIO
    # ======================================================

    if archivo is None:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "FILE_REQUIRED"
                    ),

                    "message": (
                        "Debe adjuntar "
                        "una imagen para "
                        "analizarla."
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
        nombre
        .rsplit(
            ".",
            1,
        )[-1]
        .lower()
        if "." in nombre
        else ""
    )


    # ======================================================
    # FORMATO
    # ======================================================

    if (
        extension
        not in
        ALLOWED_EXTENSIONS
    ):
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "FILE_FORMAT"
                    ),

                    "message": (
                        "Solo se permiten "
                        "archivos JPG, PNG "
                        "o DICOM."
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


    # ======================================================
    # ARCHIVO VAC?O
    # ======================================================

    if size <= 0:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "FILE_EMPTY"
                    ),

                    "message": (
                        "El archivo recibido "
                        "está vacío."
                    ),
                }
            },

            status=422,
        )


    # ======================================================
    # TAMA?O M?XIMO
    # ======================================================

    if (
        size
        >
        MAX_FILE_BYTES
    ):
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "FILE_TOO_LARGE"
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


    # ======================================================
    # CONTEXTO OPCIONAL DE PERSISTENCIA
    # ======================================================

    try:
        contexto_persistencia = (
            _obtener_contexto_persistencia(
                request
            )
        )

    except ValueError as exc:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "AI_ANALYSIS_"
                        "INVALID_CONTEXT"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=422,
        )


    # ======================================================
    # ETAPA 1
    # VALIDACI?N DE RADIOGRAF?A
    # ======================================================

    try:
        radiography_prediction = (
            RadiographyValidator()
            .predict(
                raw,
                nombre,
            )
        )


    except (
        RadiographyModelUnavailable
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "MODEL_UNAVAILABLE"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=503,
        )


    except (
        RadiographyImageError
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "IMAGE_INVALID"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=422,
        )


    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "RADIOGRAPHY_"
                        "VALIDATION_ERROR"
                    ),

                    "message": (
                        "No fue posible "
                        "ejecutar la "
                        "validación "
                        "radiográfica."
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

        "probabilidad_radiografia": (
            round(
                radiography_prediction
                .radiography_probability,
                6,
            )
        ),

        "probabilidad_no_radiografia": (
            round(
                radiography_prediction
                .non_radiography_probability,
                6,
            )
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


    # ======================================================
    # RECHAZO ETAPA 1
    # ======================================================

    if not (
        radiography_prediction
        .is_radiography
    ):
        response_data = {
            "es_radiografia": (
                False
            ),

            "anatomia_evaluada": (
                False
            ),

            "anatomia_admitida": (
                None
            ),

            "analisis_osteosarcoma_evaluado": (
                False
            ),

            "osteosarcoma_sospechoso": (
                None
            ),

            "localizacion_osteosarcoma": (
                None
            ),

            "puede_continuar": (
                False
            ),

            "etapa_rechazo": (
                "validacion_"
                "radiografia"
            ),

            "mensaje": (
                "La imagen no fue "
                "identificada como "
                "una radiografía."
            ),

            # Compatibilidad
            # frontend existente.
            **radiography_data,

            "validacion_radiografia": (
                radiography_data
            ),

            "familia_modelo": (
                "EfficientNet"
            ),
        }

        return (
            _respuesta_con_persistencia(
                response_data,
                contexto_persistencia,
            )
        )


    # ======================================================
    # ETAPA 2
    # VALIDACIÓN ANATÓMICA
    # ======================================================

    try:
        anatomy_prediction = (
            AnatomyValidator()
            .predict(
                raw,
                nombre,
            )
        )


    except (
        AnatomyModelUnavailable
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_"
                        "MODEL_UNAVAILABLE"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=503,
        )


    except (
        AnatomyImageError
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_"
                        "IMAGE_INVALID"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=422,
        )


    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "ANATOMY_"
                        "VALIDATION_ERROR"
                    ),

                    "message": (
                        "No fue posible "
                        "ejecutar la "
                        "validación "
                        "anatómica."
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

        "probabilidad_admitida": (
            round(
                anatomy_prediction
                .admitted_probability,
                6,
            )
        ),

        "probabilidad_no_admitida": (
            round(
                anatomy_prediction
                .non_admitted_probability,
                6,
            )
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


    # ======================================================
    # RECHAZO ETAPA 2
    # ======================================================

    if not (
        anatomy_prediction
        .is_admitted
    ):
        response_data = {
            "es_radiografia": (
                True
            ),

            "anatomia_evaluada": (
                True
            ),

            "anatomia_admitida": (
                False
            ),

            "analisis_osteosarcoma_evaluado": (
                False
            ),

            "osteosarcoma_sospechoso": (
                None
            ),

            "localizacion_osteosarcoma": (
                None
            ),

            "puede_continuar": (
                False
            ),

            "etapa_rechazo": (
                "validacion_anatomica"
            ),

            "mensaje": (
                "La imagen corresponde "
                "a una radiografía, "
                "pero la región "
                "anatómica no está "
                "admitida para el "
                "análisis."
            ),

            # Compatibilidad
            # frontend actual.
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

        return (
            _respuesta_con_persistencia(
                response_data,
                contexto_persistencia,
            )
        )


    # ======================================================
    # ETAPA 3
    # CLASIFICACIÓN DE OSTEOSARCOMA
    # ======================================================

    try:
        tumor_prediction = (
            OsteosarcomaValidator()
            .predict(
                raw,
                nombre,
            )
        )


    except (
        OsteosarcomaModelUnavailable
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_"
                        "MODEL_UNAVAILABLE"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=503,
        )


    except (
        OsteosarcomaImageError
    ) as exc:

        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_"
                        "IMAGE_INVALID"
                    ),

                    "message": (
                        str(
                            exc
                        )
                    ),
                }
            },

            status=422,
        )


    except Exception:
        return JsonResponse(
            {
                "error": {
                    "code": (
                        "OSTEOSARCOMA_"
                        "ANALYSIS_ERROR"
                    ),

                    "message": (
                        "No fue posible "
                        "ejecutar el análisis "
                        "de osteosarcoma."
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

        "probabilidad_osteosarcoma": (
            round(
                tumor_prediction
                .osteosarcoma_probability,
                6,
            )
        ),

        "probabilidad_no_osteosarcoma": (
            round(
                tumor_prediction
                .non_osteosarcoma_probability,
                6,
            )
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


    # ======================================================
    # ETAPA 4
    # LOCALIZACIÓN
    #
    # Solo se ejecuta cuando el clasificador considera
    # sospechosa la radiografía.
    # ======================================================

    localization_data = {
        "evaluada": False,

        "detectada": None,

        "confianza": None,

        "umbral": 0.70,

        "coordenadas_normalizadas": (
            None
        ),

        "mensaje": (
            "La localización no "
            "corresponde porque la "
            "imagen no fue clasificada "
            "como sospechosa."
        ),
    }


    if (
        tumor_prediction
        .is_suspicious
    ):
        try:
            localization_prediction = (
                OsteosarcomaDetector()
                .predict(
                    raw,
                    nombre,
                )
            )


            coordinates = None


            if (
                localization_prediction
                .detected
            ):
                coordinates = {
                    "x1": round(
                        float(
                            localization_prediction
                            .x1
                        ),
                        6,
                    ),

                    "y1": round(
                        float(
                            localization_prediction
                            .y1
                        ),
                        6,
                    ),

                    "x2": round(
                        float(
                            localization_prediction
                            .x2
                        ),
                        6,
                    ),

                    "y2": round(
                        float(
                            localization_prediction
                            .y2
                        ),
                        6,
                    ),
                }


            localization_data = {
                "evaluada": True,

                "detectada": (
                    localization_prediction
                    .detected
                ),

                "confianza": round(
                    localization_prediction
                    .confidence,
                    6,
                ),

                "umbral": (
                    localization_prediction
                    .threshold
                ),

                "coordenadas_normalizadas": (
                    coordinates
                ),

                "mensaje": (
                    (
                        "Se identificó una "
                        "región sospechosa "
                        "con suficiente "
                        "confianza."
                    )
                    if (
                        localization_prediction
                        .detected
                    )
                    else (
                        "El análisis fue "
                        "sospechoso, pero "
                        "no se obtuvo una "
                        "localización con "
                        "confianza suficiente."
                    )
                ),
            }


        # ==================================================
        # La localización es complementaria.
        #
        # Si falla, NO descartamos la clasificación
        # obtenida por EfficientNetB0.
        # ==================================================

        except (
            OsteosarcomaDetectorUnavailable
        ):

            localization_data = {
                "evaluada": False,

                "detectada": None,

                "confianza": None,

                "umbral": 0.70,

                "coordenadas_normalizadas": (
                    None
                ),

                "mensaje": (
                    "El análisis fue "
                    "sospechoso, pero el "
                    "localizador no está "
                    "disponible."
                ),
            }


        except (
            OsteosarcomaDetectorImageError
        ):

            localization_data = {
                "evaluada": False,

                "detectada": None,

                "confianza": None,

                "umbral": 0.70,

                "coordenadas_normalizadas": (
                    None
                ),

                "mensaje": (
                    "No fue posible "
                    "preparar la imagen "
                    "para localizar la "
                    "región sospechosa."
                ),
            }


        except Exception:

            localization_data = {
                "evaluada": False,

                "detectada": None,

                "confianza": None,

                "umbral": 0.70,

                "coordenadas_normalizadas": (
                    None
                ),

                "mensaje": (
                    "No fue posible "
                    "ejecutar la "
                    "localización de la "
                    "región sospechosa."
                ),
            }


    # ======================================================
    # MENSAJE CL?NICO
    # ======================================================

    if (
        tumor_prediction
        .is_suspicious
    ):

        if (
            localization_data[
                "detectada"
            ]
            is True
        ):
            message = (
                "El modelo identificó "
                "características "
                "radiográficas compatibles "
                "con un resultado "
                "sospechoso de "
                "osteosarcoma y estimó "
                "una región sospechosa. "
                "El resultado requiere "
                "revisión clínica."
            )

        else:
            message = (
                "El modelo identificó "
                "características "
                "radiográficas compatibles "
                "con un resultado "
                "sospechoso de "
                "osteosarcoma. No se "
                "obtuvo una localización "
                "con suficiente confianza. "
                "El resultado requiere "
                "revisión clínica."
            )

    else:
        message = (
            "El modelo no identificó "
            "suficientes características "
            "radiográficas para "
            "clasificar la imagen como "
            "sospechosa de osteosarcoma. "
            "El resultado no sustituye "
            "la valoración clínica."
        )


    # ======================================================
    # RESPUESTA FINAL
    # ======================================================

    response_data = {
        "es_radiografia": (
            True
        ),

        "anatomia_evaluada": (
            True
        ),

        "anatomia_admitida": (
            True
        ),

        "analisis_osteosarcoma_evaluado": (
            True
        ),

        "osteosarcoma_sospechoso": (
            tumor_prediction
            .is_suspicious
        ),

        "localizacion_osteosarcoma": (
            localization_data
        ),

        "puede_continuar": (
            True
        ),

        "etapa_rechazo": (
            None
        ),

        "mensaje": (
            message
        ),

        # Compatibilidad frontend actual.
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

    return (
        _respuesta_con_persistencia(
            response_data,
            contexto_persistencia,
        )
    )
