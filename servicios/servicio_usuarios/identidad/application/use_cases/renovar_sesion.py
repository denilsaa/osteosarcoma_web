from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)

from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher
)


class RenovarSesionUseCase:
    """
    Renueva únicamente el access token
    cuando el refresh pertenece a una
    sesión activa y válida.
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
        # VALIDAR REFRESH JWT
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
            .obtener_sesion_valida(
                jti
            )
        )

        if not sesion:

            raise Exception(
                "Sesión expirada, inválida o cerrada"
            )

        # ==================================================
        # COMPROBAR USUARIO DEL TOKEN
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
                "El refresh token no pertenece a esta sesión"
            )

        # ==================================================
        # COMPROBAR REFRESH CONTRA SU HASH
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
        # USUARIO ACTIVO
        # ==================================================

        if (
            not
            sesion.usuario
            .estado_usuario
            .es_operativo
        ):

            raise Exception(
                "Usuario deshabilitado"
            )

        # ==================================================
        # NUEVO ACCESS
        # ==================================================

        access_data = (
            self.jwt_manager
            .crear_access_token(

                sesion.usuario,

                sesion.id_sesion,

            )
        )

        return {

            "access_token":
                access_data[
                    "token"
                ],

            "access_expires_in":
                access_data[
                    "expires_in"
                ],

            "access_expires_at":
                access_data[
                    "expira"
                ].isoformat(),

            "sesion": {

                "id_sesion":
                    str(
                        sesion.id_sesion
                    ),

                "estado":
                    "ACTIVA",

            },

            "mensaje":
                "Token renovado correctamente",

        }