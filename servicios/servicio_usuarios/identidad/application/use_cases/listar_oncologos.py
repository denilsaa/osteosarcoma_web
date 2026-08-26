from identidad.infrastructure.repositories.rol_repository import (
    RolRepository
)


class ListarOncologosUseCase:
    """
    Caso de uso encargado de listar
    oncólogos registrados.
    """

    def __init__(self):

        self.rol_repository = RolRepository()


    def ejecutar(self):

        usuarios_roles = (
            self.rol_repository
            .obtener_usuarios_por_rol(
                "ONCOLOGO"
            )
        )


        oncologos = []


        for usuario_rol in usuarios_roles:

            usuario = usuario_rol.usuario


            try:

                perfil = usuario.perfil_profesional

            except Exception:

                perfil = None


            oncologos.append(

                {
                    "id_usuario": str(
                        usuario.id_usuario
                    ),

                    "nombres":
                        usuario.nombres,

                    "apellido_paterno":
                        usuario.apellido_paterno,

                    "apellido_materno":
                        usuario.apellido_materno,

                    "correo":
                        usuario.correo,

                    "nombre_usuario":
                        usuario.nombre_usuario,

                    "telefono":
                        usuario.telefono,

                    "estado":
                        usuario.estado_usuario.nombre,

                    "especialidad":
                        (
                            perfil.especialidad
                            if perfil
                            else None
                        ),

                    "matricula_profesional":
                        (
                            perfil.matricula_profesional
                            if perfil
                            else None
                        ),

                    "rol":
                        usuario_rol.rol.nombre
                }

            )


        return oncologos