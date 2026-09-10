from django.conf import (
    settings,
)

from django.conf.urls.static import (
    static,
)

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


# ==========================================================
# MEDIA LOCAL
# ==========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,

        document_root=
            settings.MEDIA_ROOT,
    )