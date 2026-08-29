from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)


class ObtenerOncologoUseCase:
    """
    Consulta el detalle de una cuenta
    perteneciente realmente al rol ONCOLOGO.
    """

    def __init__(
        self
    ):

        self.usuario_repository = (
            UsuarioRepository()
        )

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
                "El usuario no existe."
            )

        # ==================================================
        # COMPROBAR QUE ES ONCÓLOGO
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
        # PERFIL PROFESIONAL
        # ==================================================

        try:

            perfil = (
                usuario
                .perfil_profesional
            )

        except Exception:

            perfil = None

        # ==================================================
        # ROLES
        # ==================================================

        roles = list(

            usuario
            .asignaciones_roles

            .filter(
                activo=True
            )

            .values_list(
                "rol__codigo",
                flat=True,
            )

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
                " ".join(

                    parte

                    for parte in [

                        usuario.nombres,

                        usuario.apellido_paterno,

                        usuario.apellido_materno,

                    ]

                    if parte

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

            "perfil": {

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

            "roles":
                roles,

            "fecha_creacion":
                usuario.fecha_creacion,

            "fecha_actualizacion":
                usuario.fecha_actualizacion,

            "ultimo_acceso":
                usuario.ultimo_acceso,

        }