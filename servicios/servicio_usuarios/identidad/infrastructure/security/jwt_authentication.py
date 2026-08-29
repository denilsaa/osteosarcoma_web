from rest_framework.authentication import (
    BaseAuthentication
)

from rest_framework.exceptions import (
    AuthenticationFailed
)


from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)

from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)


class JWTAuthentication(BaseAuthentication):
    """
    Autenticación JWT personalizada.

    Un access token solamente es aceptado cuando:

    1. Su firma JWT es correcta.
    2. No está vencido.
    3. Es de tipo access.
    4. El usuario existe.
    5. El usuario está activo.
    6. La sesión existe.
    7. La sesión no fue revocada.
    8. La sesión no está expirada.
    """

    def __init__(self):

        self.jwt_manager = (
            JWTManager()
        )

        self.usuario_repository = (
            UsuarioRepository()
        )

        self.sesion_repository = (
            SesionRepository()
        )

    def authenticate(
        self,
        request
    ):

        # ==================================================
        # HEADER
        # ==================================================

        auth_header = (
            request.headers.get(
                "Authorization"
            )
        )

        if not auth_header:

            return None

        # ==================================================
        # BEARER
        # ==================================================

        try:

            esquema, token = (
                auth_header.split(
                    " ",
                    1
                )
            )

        except ValueError:

            raise AuthenticationFailed(
                "Formato de autorización inválido"
            )

        if (
            esquema.lower()
            !=
            "bearer"
        ):

            raise AuthenticationFailed(
                "Debe utilizar Bearer Token"
            )

        if not token.strip():

            raise AuthenticationFailed(
                "Token no proporcionado"
            )

        # ==================================================
        # VALIDAR ACCESS JWT
        # ==================================================

        try:

            payload = (
                self.jwt_manager
                .validar_access_token(
                    token
                )
            )

        except Exception as error:

            raise AuthenticationFailed(
                str(error)
            )

        # ==================================================
        # DATOS
        # ==================================================

        usuario_id = (
            payload.get(
                "usuario_id"
            )
        )

        sesion_id = (
            payload.get(
                "sid"
            )
        )

        # ==================================================
        # USUARIO
        # ==================================================

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

        # ==================================================
        # ESTADO DE CUENTA
        # ==================================================

        if (
            not
            usuario.estado_usuario.es_operativo
        ):

            raise AuthenticationFailed(
                "La cuenta se encuentra deshabilitada"
            )

        # ==================================================
        # SESIÓN
        # ==================================================

        sesion = (
            self.sesion_repository
            .obtener_sesion_access_valida(

                sesion_id,

                usuario_id,

            )
        )

        if not sesion:

            raise AuthenticationFailed(
                "Sesión cerrada, expirada o inválida"
            )

        # ==================================================
        # AUTENTICACIÓN CORRECTA
        # ==================================================

        return (
            usuario,
            token
        )