import uuid

from datetime import (
    datetime,
    timedelta,
    timezone,
)

import jwt

from django.conf import settings


class JWTManager:
    """
    Servicio encargado de crear y validar
    tokens JWT del microservicio de identidad.

    El access token queda relacionado con una
    sesión almacenada en la tabla sesiones
    mediante el claim 'sid'.
    """

    def __init__(self):

        self.secret_key = settings.SECRET_KEY

        self.algorithm = "HS256"

        self.access_expiration = timedelta(
            minutes=15
        )

        self.refresh_expiration = timedelta(
            days=7
        )

    # ======================================================
    # ACCESS TOKEN
    # ======================================================

    def crear_access_token(
        self,
        usuario,
        sesion_id
    ):

        ahora = datetime.now(
            timezone.utc
        )

        fecha_expiracion = (
            ahora
            +
            self.access_expiration
        )

        payload = {

            "type":
                "access",

            "usuario_id":
                str(
                    usuario.id_usuario
                ),

            "correo":
                usuario.correo,

            # Identificador de la sesión real
            # almacenada en PostgreSQL.
            "sid":
                str(
                    sesion_id
                ),

            "iat":
                ahora,

            "exp":
                fecha_expiracion,

        }

        token = jwt.encode(

            payload,

            self.secret_key,

            algorithm=self.algorithm,

        )

        return {

            "token":
                token,

            "expira":
                fecha_expiracion,

            "expires_in":
                int(
                    self.access_expiration.total_seconds()
                ),

        }

    # ======================================================
    # REFRESH TOKEN
    # ======================================================

    def crear_refresh_token(
        self,
        usuario
    ):

        ahora = datetime.now(
            timezone.utc
        )

        fecha_expiracion = (
            ahora
            +
            self.refresh_expiration
        )

        jti = str(
            uuid.uuid4()
        )

        payload = {

            "type":
                "refresh",

            "usuario_id":
                str(
                    usuario.id_usuario
                ),

            "jti":
                jti,

            "iat":
                ahora,

            "exp":
                fecha_expiracion,

        }

        token = jwt.encode(

            payload,

            self.secret_key,

            algorithm=self.algorithm,

        )

        return {

            "token":
                token,

            "jti":
                jti,

            "expira":
                fecha_expiracion,

            "expires_in":
                int(
                    self.refresh_expiration.total_seconds()
                ),

        }

    # ======================================================
    # VALIDACIÓN GENERAL
    # ======================================================

    def validar_token(
        self,
        token
    ):

        try:

            return jwt.decode(

                token,

                self.secret_key,

                algorithms=[
                    self.algorithm
                ],

            )

        except jwt.ExpiredSignatureError:

            raise Exception(
                "Token expirado"
            )

        except jwt.InvalidTokenError:

            raise Exception(
                "Token inválido"
            )

    # ======================================================
    # VALIDAR ACCESS
    # ======================================================

    def validar_access_token(
        self,
        token
    ):

        payload = self.validar_token(
            token
        )

        if payload.get("type") != "access":

            raise Exception(
                "El token proporcionado no es un access token"
            )

        if not payload.get(
            "usuario_id"
        ):

            raise Exception(
                "Access token sin usuario"
            )

        if not payload.get(
            "sid"
        ):

            raise Exception(
                "Access token sin identificador de sesión"
            )

        return payload

    # ======================================================
    # VALIDAR REFRESH
    # ======================================================

    def validar_refresh_token(
        self,
        token
    ):

        payload = self.validar_token(
            token
        )

        if payload.get("type") != "refresh":

            raise Exception(
                "El token proporcionado no es un refresh token"
            )

        if not payload.get(
            "usuario_id"
        ):

            raise Exception(
                "Refresh token sin usuario"
            )

        if not payload.get(
            "jti"
        ):

            raise Exception(
                "Refresh token sin identificador"
            )

        return payload

    # ======================================================
    # COMPATIBILIDAD
    # ======================================================

    def decodificar_token(
        self,
        token
    ):

        return self.validar_token(
            token
        )