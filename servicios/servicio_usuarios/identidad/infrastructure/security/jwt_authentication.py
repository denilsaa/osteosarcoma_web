from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)



class JWTAuthentication(BaseAuthentication):
    """
    Autenticación JWT personalizada
    para el microservicio identidad.
    """



    def __init__(self):

        self.jwt_manager = JWTManager()

        self.usuario_repository = UsuarioRepository()



    def authenticate(
        self,
        request
    ):


        auth_header = request.headers.get(
            "Authorization"
        )


        if not auth_header:

            return None



        try:

            esquema, token = auth_header.split(
                " "
            )


        except ValueError:

            raise AuthenticationFailed(
                "Formato de autorización inválido"
            )



        if esquema.lower() != "bearer":

            raise AuthenticationFailed(
                "Debe utilizar Bearer Token"
            )



        try:

            payload = (
                self.jwt_manager
                .validar_token(
                    token
                )
            )


        except Exception as error:

            raise AuthenticationFailed(
                str(error)
            )



        if payload.get("type") != "access":

            raise AuthenticationFailed(
                "Token incorrecto"
            )



        usuario_id = payload.get(
            "usuario_id"
        )


        usuario = (
            self.usuario_repository
            .obtener_por_id(
                usuario_id
            )
        )



        if not usuario:

            raise AuthenticationFailed(
                "Usuario no encontrado"
            )



        return (
            usuario,
            token
        )