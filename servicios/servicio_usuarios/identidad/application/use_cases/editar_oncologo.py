from django.db import transaction


from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository
)

from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository
)



class EditarOncologoUseCase:
    """
    Caso de uso para actualizar
    datos de un oncólogo.
    """

    def __init__(self):

        self.usuario_repository = UsuarioRepository()

        self.perfil_repository = PerfilRepository()



    @transaction.atomic
    def ejecutar(
        self,
        usuario_id,
        datos
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


        campos_usuario = [

            "nombres",

            "apellido_paterno",

            "apellido_materno",

            "telefono",

            "correo",

        ]


        for campo in campos_usuario:

            if campo in datos:

                setattr(
                    usuario,
                    campo,
                    datos[campo]
                )



        usuario.save()



        perfil_datos = {}


        campos_perfil = [

            "matricula_profesional",

            "especialidad",

            "subespecialidad",

            "cargo",

            "telefono_institucional",

        ]


        for campo in campos_perfil:

            if campo in datos:

                perfil_datos[campo] = datos[campo]



        if perfil_datos:

            perfil = usuario.perfil_profesional


            self.perfil_repository.actualizar(

                perfil,

                perfil_datos

            )



        return usuario