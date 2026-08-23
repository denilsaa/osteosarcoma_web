import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


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
    "servicio_ia",
]


INSTALLED_APPS = [
    "rest_framework",
    "inteligencia.apps.InteligenciaConfig",
]


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]


ROOT_URLCONF = "config.urls"

TEMPLATES = []

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


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


LANGUAGE_CODE = "es-bo"
TIME_ZONE = "America/La_Paz"

USE_I18N = True
USE_TZ = True


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"