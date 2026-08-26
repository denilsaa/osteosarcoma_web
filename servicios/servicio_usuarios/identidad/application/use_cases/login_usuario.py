from datetime import datetime, timezone


from django.utils import timezone as django_timezone


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
    Caso de uso encargado del inicio de sesión.
    """

    def __init__(self):

        self.usuario_repository = UsuarioRepository()

        self.credencial_repository = CredencialRepository()

        self.sesion_repository = SesionRepository()

        self.password_hasher = PasswordHasher()

        self.jwt_manager = JWTManager()



    def ejecutar(
        self,
        correo,
        password,
        ip_origen=None,
        user_agent=None
    ):


        usuario = (
            self.usuario_repository
            .obtener_por_correo(
                correo
            )
        )


        if not usuario:

            raise Exception(
                "Credenciales inválidas"
            )



        if not usuario.estado_usuario.es_operativo:

            raise Exception(
                "Usuario deshabilitado"
            )



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



        password_correcto = (
            self.password_hasher
            .verificar_password(
                password,
                credencial.password_hash
            )
        )


        if not password_correcto:

            raise Exception(
                "Credenciales inválidas"
            )



        access_token = (
            self.jwt_manager
            .crear_access_token(
                usuario
            )
        )


        refresh_data = (
            self.jwt_manager
            .crear_refresh_token(
                usuario
            )
        )



        refresh_token = refresh_data["token"]

        jti = refresh_data["jti"]

        fecha_expiracion = refresh_data["expira"]



        # Guardamos el hash del refresh token
        refresh_hash = (
            self.password_hasher
            .generar_hash(
                refresh_token
            )
        )



        self.sesion_repository.crear(

            {

                "usuario": usuario,

                "jti_refresh": jti,

                "refresh_token_hash": refresh_hash,

                "ip_origen": ip_origen,

                "user_agent": user_agent,

                "fecha_expiracion": fecha_expiracion,

            }

        )



        return {


            "access_token": access_token,


            "refresh_token": refresh_token,


            "usuario": {


                "id_usuario":
                    str(usuario.id_usuario),


                "nombre_usuario":
                    usuario.nombre_usuario,


                "correo":
                    usuario.correo,


            }

        }