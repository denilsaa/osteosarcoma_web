from django.utils import timezone


from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)


from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)



class CerrarSesionUseCase:
    """
    Caso de uso encargado
    de cerrar una sesión activa.
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



        sesion = (
            self.sesion_repository
            .obtener_por_jti(
                jti
            )
        )


        if not sesion:

            raise Exception(
                "Sesión no encontrada"
            )



        if sesion.revocada:

            raise Exception(
                "La sesión ya fue cerrada"
            )



        self.sesion_repository.revocar(

            sesion,

            "Cierre de sesión manual"

        )



        return {

            "mensaje":
            "Sesión cerrada correctamente"

        }