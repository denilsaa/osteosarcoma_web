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
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "identidad",
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

    "DEFAULT_AUTHENTICATION_CLASSES": [

        "identidad.infrastructure.security.jwt_authentication.JWTAuthentication",

    ],


    "DEFAULT_PERMISSION_CLASSES": [

        "rest_framework.permissions.IsAuthenticated",

    ],


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

# ==========================================================
# CORREO ELECTRÓNICO - RECUPERACIÓN DE CONTRASEÑA
# ==========================================================

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.smtp.EmailBackend",
)

EMAIL_HOST = os.environ.get(
    "EMAIL_HOST",
    "smtp.gmail.com",
)

EMAIL_PORT = int(
    os.environ.get(
        "EMAIL_PORT",
        "587",
    )
)

EMAIL_USE_TLS = os.environ.get(
    "EMAIL_USE_TLS",
    "True",
).lower() == "true"

EMAIL_USE_SSL = os.environ.get(
    "EMAIL_USE_SSL",
    "False",
).lower() == "true"

EMAIL_HOST_USER = os.environ.get(
    "EMAIL_HOST_USER",
    "",
)

EMAIL_HOST_PASSWORD = os.environ.get(
    "EMAIL_HOST_PASSWORD",
    "",
)

DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    EMAIL_HOST_USER or "no-reply@localhost",
)

FRONTEND_BASE_URL = os.environ.get(
    "FRONTEND_BASE_URL",
    "http://localhost:5173",
)

RECOVERY_LINK_MINUTES = int(
    os.environ.get(
        "RECOVERY_LINK_MINUTES",
        "15",
    )
)
