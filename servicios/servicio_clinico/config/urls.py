from django.urls import path

from clinica.views import health_check


urlpatterns = [
    path("api/health/", health_check),
]