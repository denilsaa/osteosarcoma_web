from django.urls import path


from identidad.interfaces.api.views.oncologo_view import (
    OncologoDetailAPIView,
    OncologoEstadoAPIView,
    OncologoListCreateAPIView,
)


from identidad.interfaces.api.views.auth_view import (
    LoginView,
    LogoutView,
    RefreshView,
)


urlpatterns = [

    # ======================================================
    # GESTIÓN DE ONCÓLOGOS
    # ======================================================

    path(
        "oncologos/",
        OncologoListCreateAPIView.as_view(),
    ),

    path(
        "oncologos/<uuid:usuario_id>/",
        OncologoDetailAPIView.as_view(),
    ),

    path(
        "oncologos/<uuid:usuario_id>/estado/",
        OncologoEstadoAPIView.as_view(),
    ),


    # ======================================================
    # AUTENTICACIÓN
    # ======================================================

    path(
        "auth/login/",
        LoginView.as_view(),
    ),

    path(
        "auth/logout/",
        LogoutView.as_view(),
    ),

    path(
        "auth/refresh/",
        RefreshView.as_view(),
    ),

]