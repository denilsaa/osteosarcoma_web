from django.db import transaction


from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)

from identidad.infrastructure.repositories.credencial_repository import (
    CredencialRepository
)

from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository
)

from identidad.infrastructure.repositories.rol_repository import (
    RolRepository
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher
)



class CrearOncologoUseCase:
    """
    Caso de uso para registrar
    una cuenta de oncólogo.
    """


    def __init__(self):

        self.usuario_repository = UsuarioRepository()

        self.credencial_repository = CredencialRepository()

        self.perfil_repository = PerfilRepository()

        self.rol_repository = RolRepository()

        self.password_hasher = PasswordHasher()



    @transaction.atomic
    def ejecutar(
        self,
        datos,
        usuario_creador=None
    ):

        correo = datos["correo"]

        usuario_existente = (
            self.usuario_repository
            .obtener_por_correo(
                correo
            )
        )


        if usuario_existente:

            raise Exception(
                "El correo ya está registrado"
            )



        estado_activo = (
            self.obtener_estado_activo()
        )



        usuario = (
            self.usuario_repository
            .crear(
                {

                    "estado_usuario": estado_activo,

                    "nombres": datos["nombres"],

                    "apellido_paterno": datos["apellido_paterno"],

                    "apellido_materno": datos.get(
                        "apellido_materno"
                    ),

                    "correo": correo,

                    "nombre_usuario": datos["nombre_usuario"],

                    "telefono": datos.get(
                        "telefono"
                    ),

                }
            )
        )



        password_hash = (
            self.password_hasher
            .generar_hash(
                datos["password"]
            )
        )



        self.credencial_repository.crear(

            {

                "usuario": usuario,

                "password_hash": password_hash,

                "debe_cambiar_password": True,

            }

        )



        self.perfil_repository.crear(

            {

                "usuario": usuario,

                "matricula_profesional":
                    datos.get(
                        "matricula_profesional"
                    ),

                "especialidad":
                    datos.get(
                        "especialidad"
                    ),

                "subespecialidad":
                    datos.get(
                        "subespecialidad"
                    ),

                "cargo":
                    "Oncólogo",

                "telefono_institucional":
                    datos.get(
                        "telefono_institucional"
                    ),

            }

        )



        rol_oncologo = (
            self.rol_repository
            .obtener_por_codigo(
                "ONCOLOGO"
            )
        )


        if not rol_oncologo:

            raise Exception(
                "No existe el rol ONCOLOGO"
            )



        self.rol_repository.asignar_rol(

            usuario,

            rol_oncologo,

            usuario_creador

        )



        return usuario



    def obtener_estado_activo(self):

        from identidad.models import EstadoUsuario


        return (
            EstadoUsuario.objects
            .filter(
                codigo="ACTIVO"
            )
            .first()
        )