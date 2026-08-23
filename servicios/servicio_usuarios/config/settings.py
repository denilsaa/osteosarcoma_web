import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "unsafe-development-key",
)

DEBUG = os.environ.get(
    "DJANGO_DEBUG",
    "False",
).lower() == "true"

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "servicio_usuarios",
]


# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [
    "rest_framework",
    "identidad",
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]


# ==========================================================
# URLS
# ==========================================================

ROOT_URLCONF = "config.urls"


# ==========================================================
# TEMPLATES
# ==========================================================

# Este microservicio funciona únicamente como API REST.
TEMPLATES = []


# ==========================================================
# WSGI / ASGI
# ==========================================================

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# ==========================================================
# BASE DE DATOS
# ==========================================================

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ["DB_HOST"],
        "PORT": os.environ.get("DB_PORT", "5432"),
        "CONN_MAX_AGE": 60,
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

# Todavía NO usamos autenticación propia de Django.
# Más adelante implementaremos JWT de nuestro dominio.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}


# ==========================================================
# MODELOS
# ==========================================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"