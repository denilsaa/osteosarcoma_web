from django.urls import (
    include,
    path,
)

from clinica.interfaces.api.views import (
    health_view,
)


urlpatterns = [
    path(
        "api/health/",
        health_view,
        name="health",
    ),

    path(
        "api/",
        include(
            "clinica.interfaces.api.urls"
        ),
    ),
]