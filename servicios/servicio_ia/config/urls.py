from django.urls import path

from inteligencia.views import health_check, validar_radiografia


urlpatterns = [
    path("api/health/", health_check),
    path("api/validaciones/radiografia/", validar_radiografia),
]
