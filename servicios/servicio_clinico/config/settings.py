import os
from pathlib import Path


# ==========================================================
# BASE
# ==========================================================

BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
    .parent
)


# ==========================================================
# SEGURIDAD
# ==========================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "unsafe-development-key",
)


DEBUG = (
    os.environ
    .get(
        "DJANGO_DEBUG",
        "False",
    )
    .lower()
    == "true"
)


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "servicio_clinico",
]


# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [

    # Django REST Framework
    "rest_framework",

    # CORS
    "corsheaders",

    # Aplicación clínica
    "clinica",

]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    # Debe estar antes de CommonMiddleware
    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",

]


# ==========================================================
# URLS / WSGI / ASGI
# ==========================================================

ROOT_URLCONF = "config.urls"


WSGI_APPLICATION = (
    "config.wsgi.application"
)


ASGI_APPLICATION = (
    "config.asgi.application"
)


# ==========================================================
# TEMPLATES
#
# Aunque este microservicio funciona como API y no utiliza
# Django Admin, mantenemos una configuración mínima válida.
# ==========================================================

TEMPLATES = [
    {
        "BACKEND":
            (
                "django.template.backends."
                "django.DjangoTemplates"
            ),

        "DIRS": [],

        "APP_DIRS": True,

        "OPTIONS": {
            "context_processors": [],
        },
    },
]


# ==========================================================
# BASE DE DATOS
# ==========================================================

DATABASES = {
    "default": {

        "ENGINE":
            "django.db.backends.postgresql",

        "NAME":
            os.environ["DB_NAME"],

        "USER":
            os.environ["DB_USER"],

        "PASSWORD":
            os.environ["DB_PASSWORD"],

        "HOST":
            os.environ["DB_HOST"],

        "PORT":
            os.environ.get(
                "DB_PORT",
                "5432",
            ),

        "CONN_MAX_AGE":
            60,
    }
}


# ==========================================================
# INTERNACIONALIZACIÓN
# ==========================================================

LANGUAGE_CODE = "es-bo"


TIME_ZONE = "America/La_Paz"


USE_I18N = True


USE_TZ = True


# ==========================================================
# DJANGO REST FRAMEWORK
# ==========================================================

REST_FRAMEWORK = {

    # La autenticación real del sistema pertenece a
    # servicio_usuarios mediante JWT.
    #
    # servicio_clinico recibe el Bearer token y utiliza
    # el contexto del request para integración/auditoría.
    "DEFAULT_AUTHENTICATION_CLASSES": [],

    "DEFAULT_PERMISSION_CLASSES": [],

    "UNAUTHENTICATED_USER": None,
}


# ==========================================================
# CAMPOS AUTOMÁTICOS
# ==========================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ==========================================================
# ARCHIVOS ESTÁTICOS
#
# Requerido por Django aunque este microservicio sea API.
# ==========================================================

STATIC_URL = "/static/"


# ==========================================================
# CORS
# ==========================================================

CORS_ALLOWED_ORIGINS = [

    "http://localhost:5173",

    "http://127.0.0.1:5173",

]


CORS_ALLOW_CREDENTIALS = True


# ==========================================================
# HEADERS CORS
#
# django-cors-headers ya permite Authorization y
# Content-Type por defecto. Se deja explícito el origen
# permitido, no habilitamos CORS global.
# ==========================================================

CORS_URLS_REGEX = r"^/api/.*$"