import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "osteosarcoma_microservicio_seguridad_jwt_2026_clave_super_segura"
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

# ==========================================================
# BASE DE DATOS
# ==========================================================

DATABASES = {

    "default": {

        "ENGINE":
            "django.db.backends.postgresql",


        "NAME":
            os.environ.get(
                "DB_NAME"
            ),


        "USER":
            os.environ.get(
                "DB_USER"
            ),


        "PASSWORD":
            os.environ.get(
                "DB_PASSWORD"
            ),


        "HOST":
            os.environ.get(
                "DB_HOST"
            ),


        "PORT":
            os.environ.get(
                "DB_PORT",
                "5432"
            ),

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

# ==========================================================
# SEGURIDAD DE CONTRASEÑAS
# ==========================================================

PASSWORD_HASHERS = [

    "django.contrib.auth.hashers.Argon2PasswordHasher",

    "django.contrib.auth.hashers.PBKDF2PasswordHasher",

]