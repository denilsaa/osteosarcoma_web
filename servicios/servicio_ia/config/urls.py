from django.urls import path

from inteligencia.training_reports import (
    training_dashboard,
    training_evidence,
    training_experiment_detail,
)

from inteligencia.views import (
    health_check,
    ultimo_analisis_radiografia,
    validar_radiografia,
)


from inteligencia.analisis_async import (
    crear_solicitud_analisis,
    consultar_solicitud_analisis,
    ultima_solicitud_radiografia,
    obtener_gradcam_solicitud,
)

urlpatterns = [
    path("api/analisis/solicitudes/", crear_solicitud_analisis),
    path("api/analisis/solicitudes/<uuid:task_id>/gradcam/", obtener_gradcam_solicitud),
    path("api/analisis/solicitudes/<uuid:task_id>/", consultar_solicitud_analisis),
    path("api/analisis/radiografia/<uuid:radiography_uuid>/solicitud-actual/", ultima_solicitud_radiografia),
    path(
        "api/health/",
        health_check,
    ),

    path(
        "api/validaciones/radiografia/",
        validar_radiografia,
    ),


    path(
        (
            "api/analisis/radiografia/"
            "<uuid:radiografia_uuid>/"
            "ultimo/"
        ),
        ultimo_analisis_radiografia,
    ),

    path(
        "api/entrenamientos/",
        training_dashboard,
    ),

    path(
        (
            "api/entrenamientos/"
            "<str:experiment_id>/"
        ),
        training_experiment_detail,
    ),

    path(
        (
            "api/entrenamientos/"
            "<str:experiment_id>/"
            "evidencia/"
            "<str:filename>/"
        ),
        training_evidence,
    ),
]
