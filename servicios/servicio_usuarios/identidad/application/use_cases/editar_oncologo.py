from django.db import transaction

from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository,
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)


class EditarOncologoUseCase:
    """
    Actualiza la información administrativa
    y profesional de un oncólogo.
    """

    def __init__(
        self
    ):

        self.usuario_repository = (
            UsuarioRepository()
        )

        self.perfil_repository = (
            PerfilRepository()
        )

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
                "El usuario no existe."
            )

        # ==================================================
        # VALIDAR ROL ONCÓLOGO
        # ==================================================

        es_oncologo = (

            usuario
            .asignaciones_roles

            .filter(

                activo=True,

                rol__codigo="ONCOLOGO",

            )

            .exists()

        )

        if not es_oncologo:

            raise Exception(
                "La cuenta indicada no pertenece a un oncólogo."
            )

        # ==================================================
        # CAMPOS DEL USUARIO
        # ==================================================

        campos_usuario = [

            "nombres",

            "apellido_paterno",

            "apellido_materno",

            "correo",

            "nombre_usuario",

            "telefono",

        ]

        datos_usuario = {}

        for campo in campos_usuario:

            if campo in datos:

                datos_usuario[campo] = (
                    datos[campo]
                )

        if datos_usuario:

            self.usuario_repository.actualizar(

                usuario,

                datos_usuario,

            )

        # ==================================================
        # CAMPOS PROFESIONALES
        # ==================================================

        campos_perfil = [

            "matricula_profesional",

            "especialidad",

            "subespecialidad",

            "telefono_institucional",

        ]

        perfil_datos = {}

        for campo in campos_perfil:

            if campo in datos:

                perfil_datos[campo] = (
                    datos[campo]
                )

        if perfil_datos:

            perfil = (

                self.perfil_repository

                .obtener_por_usuario(
                    usuario
                )

            )

            if perfil:

                self.perfil_repository.actualizar(

                    perfil,

                    perfil_datos,

                )

            else:

                self.perfil_repository.crear(

                    {

                        "usuario":
                            usuario,

                        "cargo":
                            "Oncólogo",

                        **perfil_datos,

                    }

                )

        return usuario