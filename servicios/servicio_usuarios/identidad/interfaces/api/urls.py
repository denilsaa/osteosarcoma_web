from django.urls import path


# ==========================================================
# AUTENTICACIÓN
# ==========================================================

from identidad.interfaces.api.views.auth_view import (
    LoginView,
    LogoutView,
    RefreshView,
    VerificarSegundoFactorView,
    ReenviarSegundoFactorView,
)


# ==========================================================
# ONCÓLOGOS
# ==========================================================

from identidad.interfaces.api.views.oncologo_view import (
    OncologoDetailAPIView,
    OncologoEstadoAPIView,
    OncologoListCreateAPIView,
)


# ==========================================================
# RECUPERACIÓN
# ==========================================================

from identidad.interfaces.api.views.recuperacion_view import (
    CambiarPasswordRecuperacionAPIView,
    EstadoRecuperacionAPIView,
    RecuperacionesJefaturaAPIView,
    ResolverRecuperacionAPIView,
    SolicitarRecuperacionAPIView,
)


# ==========================================================
# PERFIL
# ==========================================================

from identidad.interfaces.api.views.perfil_view import (
    MiPerfilAPIView,
)


# ==========================================================
# PERMISOS
# ==========================================================

from identidad.interfaces.api.views.permisos_view import (
    PermisosOncologoJefaturaAPIView,
)


urlpatterns = [

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

    path(
        "auth/segundo-factor/verificar/",
        VerificarSegundoFactorView.as_view(),
    ),

    path(
        "auth/segundo-factor/reenviar/",
        ReenviarSegundoFactorView.as_view(),
    ),


    # ======================================================
    # RECUPERACIÓN PÚBLICA
    # ======================================================

    path(
        "auth/recuperaciones/",
        SolicitarRecuperacionAPIView.as_view(),
    ),

    path(
        "auth/recuperaciones/estado/",
        EstadoRecuperacionAPIView.as_view(),
    ),

    path(
        "auth/recuperaciones/cambiar-password/",
        CambiarPasswordRecuperacionAPIView.as_view(),
    ),


    # ======================================================
    # JEFATURA - RECUPERACIONES
    # ======================================================

    path(
        "jefatura/recuperaciones/",
        RecuperacionesJefaturaAPIView.as_view(),
    ),

    path(
        "jefatura/recuperaciones/<uuid:solicitud_id>/resolver/",
        ResolverRecuperacionAPIView.as_view(),
    ),


    # ======================================================
    # JEFATURA - PERMISOS
    # ======================================================

    path(
        "jefatura/permisos/oncologo/",
        PermisosOncologoJefaturaAPIView.as_view(),
    ),


    # ======================================================
    # ONCÓLOGOS
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
    # MI PERFIL
    # ======================================================

    path(
        "perfil/",
        MiPerfilAPIView.as_view(),
    ),

]