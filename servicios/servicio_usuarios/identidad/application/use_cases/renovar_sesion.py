from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)


from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)



class RenovarSesionUseCase:
    """
    Caso de uso encargado
    de renovar access tokens.
    """



    def __init__(self):

        self.sesion_repository = SesionRepository()

        self.jwt_manager = JWTManager()



    def ejecutar(
        self,
        refresh_token
    ):


        datos = (
            self.jwt_manager
            .decodificar_token(
                refresh_token
            )
        )


        if not datos:

            raise Exception(
                "Refresh token inválido"
            )



        jti = datos.get(
            "jti"
        )


        usuario_id = datos.get(
            "usuario_id"
        )



        sesion = (
            self.sesion_repository
            .obtener_sesion_valida(
                jti
            )
        )


        if not sesion:

            raise Exception(
                "Sesión expirada o cerrada"
            )



        nuevo_access = (
            self.jwt_manager
            .crear_access_token(
                sesion.usuario
            )
        )



        return {

            "access_token":
                nuevo_access,

            "mensaje":
                "Token renovado correctamente"

        }