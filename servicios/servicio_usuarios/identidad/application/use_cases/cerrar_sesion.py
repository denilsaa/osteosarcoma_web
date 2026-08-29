from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)

from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher
)


class CerrarSesionUseCase:
    """
    Caso de uso encargado de cerrar
    una sesión.

    Al revocar la sesión, también queda
    inutilizado cualquier access token
    asociado al id_sesion.
    """

    def __init__(self):

        self.sesion_repository = (
            SesionRepository()
        )

        self.jwt_manager = (
            JWTManager()
        )

        self.password_hasher = (
            PasswordHasher()
        )

    def ejecutar(
        self,
        refresh_token
    ):

        # ==================================================
        # VALIDAR REFRESH
        # ==================================================

        datos = (
            self.jwt_manager
            .validar_refresh_token(
                refresh_token
            )
        )

        jti = datos.get(
            "jti"
        )

        usuario_id = datos.get(
            "usuario_id"
        )

        # ==================================================
        # BUSCAR SESIÓN
        # ==================================================

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

        # ==================================================
        # VALIDAR PROPIETARIO
        # ==================================================

        if (
            str(
                sesion.usuario_id
            )
            !=
            str(
                usuario_id
            )
        ):

            raise Exception(
                "El token no pertenece a esta sesión"
            )

        # ==================================================
        # YA ESTABA CERRADA
        # ==================================================

        if sesion.revocada:

            return {

                "mensaje":
                    "La sesión ya se encontraba cerrada",

                "sesion": {

                    "id_sesion":
                        str(
                            sesion.id_sesion
                        ),

                    "estado":
                        "CERRADA",

                }

            }

        # ==================================================
        # VERIFICAR HASH REFRESH
        # ==================================================

        refresh_correcto = (
            self.password_hasher
            .verificar_password(

                refresh_token,

                sesion.refresh_token_hash,

            )
        )

        if not refresh_correcto:

            raise Exception(
                "Refresh token inválido"
            )

        # ==================================================
        # REVOCAR
        # ==================================================

        self.sesion_repository.revocar(

            sesion,

            "Cierre de sesión manual",

        )

        return {

            "mensaje":
                "Sesión cerrada correctamente",

            "sesion": {

                "id_sesion":
                    str(
                        sesion.id_sesion
                    ),

                "estado":
                    "CERRADA",

            }

        }