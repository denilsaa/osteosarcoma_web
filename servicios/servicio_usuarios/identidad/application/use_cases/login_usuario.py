from django.utils import timezone


from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)

from identidad.infrastructure.repositories.credencial_repository import (
    CredencialRepository
)

from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher
)

from identidad.infrastructure.security.jwt_manager import (
    JWTManager
)


class LoginUseCase:
    """
    Caso de uso encargado del inicio de sesiÃ³n.

    Flujo:
    1. Validar usuario.
    2. Validar credencial.
    3. Crear refresh.
    4. Registrar sesiÃ³n.
    5. Crear access ligado a la sesiÃ³n.
    """

    def __init__(self):

        self.usuario_repository = (
            UsuarioRepository()
        )

        self.credencial_repository = (
            CredencialRepository()
        )

        self.sesion_repository = (
            SesionRepository()
        )

        self.password_hasher = (
            PasswordHasher()
        )

        self.jwt_manager = (
            JWTManager()
        )

    def ejecutar(
        self,
        correo,
        password,
        ip_origen=None,
        user_agent=None
    ):

        # ==================================================
        # USUARIO
        # ==================================================

        usuario = (
            self.usuario_repository
            .obtener_por_correo(
                correo
            )
        )

        if not usuario:

            raise Exception(
                "Credenciales invÃ¡lidas"
            )

        # ==================================================
        # ESTADO
        # ==================================================

        if (
            not
            usuario.estado_usuario.es_operativo
        ):

            raise Exception(
                "Usuario deshabilitado"
            )

        # ==================================================
        # CREDENCIAL
        # ==================================================

        credencial = (
            self.credencial_repository
            .obtener_por_usuario(
                usuario
            )
        )

        if not credencial:

            raise Exception(
                "Credencial no encontrada"
            )

        # ==================================================
        # BLOQUEO TEMPORAL
        # ==================================================

        if (
            credencial.bloqueado_hasta
            and
            credencial.bloqueado_hasta
            >
            timezone.now()
        ):

            raise Exception(
                "La cuenta se encuentra temporalmente bloqueada"
            )

        # ==================================================
        # PASSWORD
        # ==================================================

        password_correcto = (
            self.password_hasher
            .verificar_password(

                password,

                credencial.password_hash,

            )
        )

        if not password_correcto:

            raise Exception(
                "Credenciales invÃ¡lidas"
            )

        # ==================================================
        # REFRESH TOKEN
        # ==================================================

        refresh_data = (
            self.jwt_manager
            .crear_refresh_token(
                usuario
            )
        )

        refresh_token = (
            refresh_data[
                "token"
            ]
        )

        jti = (
            refresh_data[
                "jti"
            ]
        )

        fecha_expiracion = (
            refresh_data[
                "expira"
            ]
        )

        # ==================================================
        # HASH DEL REFRESH
        # ==================================================

        refresh_hash = (
            self.password_hasher
            .generar_hash(
                refresh_token
            )
        )

        # ==================================================
        # CREAR SESIÃ“N
        # ==================================================

        sesion = (
            self.sesion_repository
            .crear(
                {

                    "usuario":
                        usuario,

                    "jti_refresh":
                        jti,

                    "refresh_token_hash":
                        refresh_hash,

                    "ip_origen":
                        ip_origen,

                    "user_agent":
                        user_agent,

                    "fecha_expiracion":
                        fecha_expiracion,

                }
            )
        )

        # ==================================================
        # ACCESS TOKEN VINCULADO A LA SESIÃ“N
        # ==================================================

        access_data = (
            self.jwt_manager
            .crear_access_token(

                usuario,

                sesion.id_sesion,

            )
        )

        # ==================================================
        # ÃšLTIMO ACCESO
        # ==================================================

        usuario.ultimo_acceso = (
            timezone.now()
        )

        usuario.save(
            update_fields=[
                "ultimo_acceso"
            ]
        )

        # ==================================================
        # ROLES
        # ==================================================

        asignaciones = (
            usuario
            .asignaciones_roles
            .filter(

                activo=True,

                rol__activo=True,

            )
        )

        roles = list(

            asignaciones
            .values_list(

                "rol__codigo",

                flat=True,

            )
            .distinct()

        )

        # ==================================================
        # PERMISOS
        # ==================================================

        permisos = list(

            asignaciones
            .filter(

                rol__permisos_asignados__permiso__activo=True

            )
            .values_list(

                "rol__permisos_asignados__"
                "permiso__codigo",

                flat=True,

            )
            .distinct()

        )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {

            "access_token":
                access_data[
                    "token"
                ],

            "refresh_token":
                refresh_token,

            "access_expires_in":
                access_data[
                    "expires_in"
                ],

            "access_expires_at":
                access_data[
                    "expira"
                ].isoformat(),

            "refresh_expires_in":
                refresh_data[
                    "expires_in"
                ],

            "refresh_expires_at":
                refresh_data[
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

            "usuario": {

                "id_usuario":
                    str(
                        usuario.id_usuario
                    ),

                "nombre_usuario":
                    usuario.nombre_usuario,

                "correo":
                    usuario.correo,

                "nombres":
                    usuario.nombres,

                "apellido_paterno":
                    usuario.apellido_paterno,

                "apellido_materno":
                    usuario.apellido_materno,

                "telefono":
                    usuario.telefono,

                "estado":
                    usuario.estado_usuario.codigo,

                "debe_cambiar_password":
                    credencial.debe_cambiar_password,

                "roles":
                    roles,

                "permisos":
                    permisos,

            },

        }
