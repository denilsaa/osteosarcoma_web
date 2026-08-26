import jwt
import uuid

from datetime import datetime, timedelta, timezone

from django.conf import settings



class JWTManager:
    """
    Servicio encargado de crear,
    validar y renovar tokens JWT.
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



    def crear_access_token(
        self,
        usuario
    ):

        ahora = datetime.now(
            timezone.utc
        )


        payload = {

            "type": "access",

            "usuario_id": str(
                usuario.id_usuario
            ),

            "correo": usuario.correo,

            "iat": ahora,

            "exp": ahora + self.access_expiration

        }


        return jwt.encode(

            payload,

            self.secret_key,

            algorithm=self.algorithm

        )



    def crear_refresh_token(
        self,
        usuario
    ):

        ahora = datetime.now(
            timezone.utc
        )


        jti = str(
            uuid.uuid4()
        )


        payload = {

            "type": "refresh",

            "usuario_id": str(
                usuario.id_usuario
            ),

            "jti": jti,

            "iat": ahora,

            "exp": ahora + self.refresh_expiration

        }


        token = jwt.encode(

            payload,

            self.secret_key,

            algorithm=self.algorithm

        )


        return {

            "token": token,

            "jti": jti,

            "expira": ahora + self.refresh_expiration

        }



    def validar_token(
        self,
        token
    ):

        try:

            payload = jwt.decode(

                token,

                self.secret_key,

                algorithms=[
                    self.algorithm
                ]

            )


            return payload


        except jwt.ExpiredSignatureError:

            raise Exception(
                "Token expirado"
            )


        except jwt.InvalidTokenError:

            raise Exception(
                "Token inválido"
            )