from django.urls import path

from inteligencia.views import health_check


urlpatterns = [
    path("api/health/", health_check),
]