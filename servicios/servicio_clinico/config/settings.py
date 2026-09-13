import os

from pathlib import (
    Path,
)


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
    ==
    "true"
)


ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "servicio-clinico",
]


# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [

    "rest_framework",

    "corsheaders",

    "clinica",

]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [

    "django.middleware.security.SecurityMiddleware",

    "corsheaders.middleware.CorsMiddleware",

    "django.middleware.common.CommonMiddleware",

]


# ==========================================================
# URLS / WSGI / ASGI
# ==========================================================

ROOT_URLCONF = (
    "config.urls"
)


WSGI_APPLICATION = (
    "config.wsgi.application"
)


ASGI_APPLICATION = (
    "config.asgi.application"
)


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        "BACKEND":
            (
                "django.template.backends."
                "django.DjangoTemplates"
            ),

        "DIRS": [],

        "APP_DIRS":
            True,

        "OPTIONS": {
            "context_processors":
                [],
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
            os.environ[
                "DB_NAME"
            ],

        "USER":
            os.environ[
                "DB_USER"
            ],

        "PASSWORD":
            os.environ[
                "DB_PASSWORD"
            ],

        "HOST":
            os.environ[
                "DB_HOST"
            ],

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

LANGUAGE_CODE = (
    "es-bo"
)


TIME_ZONE = (
    "America/La_Paz"
)


USE_I18N = True

USE_TZ = True


# ==========================================================
# DJANGO REST FRAMEWORK
# ==========================================================

REST_FRAMEWORK = {

    "DEFAULT_AUTHENTICATION_CLASSES":
        [],

    "DEFAULT_PERMISSION_CLASSES":
        [],

    "UNAUTHENTICATED_USER":
        None,
}


# ==========================================================
# CAMPOS AUTOMÁTICOS
# ==========================================================

DEFAULT_AUTO_FIELD = (
    "django.db.models.BigAutoField"
)


# ==========================================================
# ARCHIVOS ESTÁTICOS
# ==========================================================

STATIC_URL = (
    "/static/"
)


# ==========================================================
# ARCHIVOS MULTIMEDIA
# ==========================================================

MEDIA_URL = (
    "/media/"
)


MEDIA_ROOT = (
    BASE_DIR
    /
    "media"
)


# ==========================================================
# LÍMITE DE SUBIDA
# ==========================================================

DATA_UPLOAD_MAX_MEMORY_SIZE = (
    6
    *
    1024
    *
    1024
)


# ==========================================================
# CORS
# ==========================================================

CORS_ALLOWED_ORIGINS = [

    "http://localhost:5173",

    "http://127.0.0.1:5173",

]


CORS_ALLOW_CREDENTIALS = (
    True
)


CORS_URLS_REGEX = (
    r"^/api/.*$"
)