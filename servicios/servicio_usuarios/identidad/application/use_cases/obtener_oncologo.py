from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)


class ObtenerOncologoUseCase:
    """
    Caso de uso para consultar
    el detalle de un oncólogo.
    """


    def __init__(self):

        self.usuario_repository = UsuarioRepository()



    def ejecutar(
        self,
        usuario_id
    ):

        usuario = (
            self.usuario_repository
            .obtener_por_id(
                usuario_id
            )
        )


        if not usuario:

            raise Exception(
                "El usuario no existe"
            )


        try:

            perfil = usuario.perfil_profesional

        except Exception:

            perfil = None



        roles = [

            rol.rol.nombre

            for rol in usuario.asignaciones_roles.all()

            if rol.activo

        ]



        return {

            "id_usuario":
                str(usuario.id_usuario),


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


            "perfil": {

                "matricula_profesional":
                    perfil.matricula_profesional
                    if perfil
                    else None,


                "especialidad":
                    perfil.especialidad
                    if perfil
                    else None,


                "subespecialidad":
                    perfil.subespecialidad
                    if perfil
                    else None,


                "cargo":
                    perfil.cargo
                    if perfil
                    else None,

            },


            "roles": roles,


            "fecha_creacion":
                usuario.fecha_creacion,

        }