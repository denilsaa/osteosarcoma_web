from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository,
)


class ObtenerMiPerfilUseCase:
    """
    Consulta el perfil del usuario
    autenticado.

    No recibe ID desde el frontend.
    """

    def __init__(
        self,
    ):

        self.perfil_repository = (
            PerfilRepository()
        )


    def ejecutar(
        self,
        usuario,
    ):

        if not usuario:

            raise Exception(
                "No existe un usuario autenticado."
            )


        perfil = (
            self.perfil_repository
            .obtener_por_usuario(
                usuario
            )
        )


        # ==================================================
        # ROLES
        # ==================================================

        roles = list(

            usuario
            .asignaciones_roles

            .filter(
                activo=True,
                rol__activo=True,
            )

            .values_list(
                "rol__codigo",
                flat=True,
            )

            .distinct()

        )


        # ==================================================
        # RESPUESTA
        # ==================================================

        return {

            "id_usuario":
                str(
                    usuario.id_usuario
                ),

            "nombres":
                usuario.nombres,

            "apellido_paterno":
                usuario.apellido_paterno,

            "apellido_materno":
                usuario.apellido_materno,

            "nombre_completo":
                self._nombre_completo(
                    usuario
                ),

            "correo":
                usuario.correo,

            "nombre_usuario":
                usuario.nombre_usuario,

            "telefono":
                usuario.telefono,

            "estado":
                usuario
                .estado_usuario
                .codigo,

            "estado_nombre":
                usuario
                .estado_usuario
                .nombre,

            "roles":
                roles,

            "perfil_profesional": {

                "matricula_profesional":
                    (
                        perfil
                        .matricula_profesional

                        if perfil
                        else None
                    ),

                "especialidad":
                    (
                        perfil.especialidad

                        if perfil
                        else None
                    ),

                "subespecialidad":
                    (
                        perfil.subespecialidad

                        if perfil
                        else None
                    ),

                "cargo":
                    (
                        perfil.cargo

                        if perfil
                        else None
                    ),

                "telefono_institucional":
                    (
                        perfil
                        .telefono_institucional

                        if perfil
                        else None
                    ),
            },

            "fecha_creacion":
                (
                    usuario
                    .fecha_creacion
                    .isoformat()
                ),

            "ultimo_acceso":
                (
                    usuario
                    .ultimo_acceso
                    .isoformat()

                    if usuario.ultimo_acceso
                    else None
                ),

        }


    @staticmethod
    def _nombre_completo(
        usuario,
    ):

        return " ".join(

            parte

            for parte in [

                usuario.nombres,

                usuario.apellido_paterno,

                usuario.apellido_materno,

            ]

            if parte

        )