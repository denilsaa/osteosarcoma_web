from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)


ROLES_ONCOLOGIA = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}


class ObtenerOncologoUseCase:
    """
    Consulta el detalle de una cuenta perteneciente
    al personal de Oncología.

    Se consideran válidos:

    - ONCOLOGO
    - JEFE_ONCOLOGIA
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
        # ROLES ACTIVOS
        # ==================================================

        asignaciones = (
            usuario
            .asignaciones_roles
            .filter(
                activo=True,
                rol__activo=True,
            )
            .select_related(
                "rol"
            )
        )

        roles = list(
            asignaciones.values_list(
                "rol__codigo",
                flat=True,
            )
        )

        # ==================================================
        # VALIDAR QUE PERTENEZCA A ONCOLOGÍA
        # ==================================================

        pertenece_oncologia = any(
            rol_codigo
            in
            ROLES_ONCOLOGIA
            for rol_codigo
            in roles
        )

        if not pertenece_oncologia:

            raise Exception(
                "La cuenta indicada no pertenece "
                "al personal de Oncología."
            )

        # ==================================================
        # ROL PRINCIPAL
        # ==================================================
        #
        # Si por datos antiguos un usuario tiene ambos,
        # priorizamos JEFE_ONCOLOGIA.
        # ==================================================

        if (
            "JEFE_ONCOLOGIA"
            in roles
        ):

            rol_codigo = (
                "JEFE_ONCOLOGIA"
            )

            rol_nombre = (
                "Jefe de Oncología"
            )

        else:

            rol_codigo = (
                "ONCOLOGO"
            )

            rol_nombre = (
                "Oncólogo"
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
        # RESPUESTA
        # ==================================================

        return {

            "id_usuario":
                str(
                    usuario.id_usuario
                ),

            # ==============================================
            # DATOS PERSONALES
            # ==============================================

            "nombres":
                usuario.nombres,

            "apellido_paterno":
                usuario.apellido_paterno,

            "apellido_materno":
                usuario.apellido_materno,

            "nombre_completo":
                usuario.nombre_completo,

            "telefono":
                usuario.telefono,

            # ==============================================
            # IDENTIFICACIÓN
            # ==============================================

            "ci_numero":
                usuario.ci_numero,

            "ci_complemento":
                usuario.ci_complemento,

            "ci_expedido":
                usuario.ci_expedido,

            "ci_completo":
                usuario.ci_completo,

            # ==============================================
            # ACCESO
            # ==============================================

            "correo":
                usuario.correo,

            "nombre_usuario":
                usuario.nombre_usuario,

            # ==============================================
            # ESTADO
            # ==============================================

            "estado":
                usuario
                .estado_usuario
                .codigo,

            "estado_nombre":
                usuario
                .estado_usuario
                .nombre,

            # ==============================================
            # ROL PRINCIPAL
            # ==============================================

            "rol_codigo":
                rol_codigo,

            "rol_nombre":
                rol_nombre,

            # ==============================================
            # PERFIL
            # ==============================================

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
                        perfil
                        .especialidad
                        if perfil
                        else None
                    ),

                "subespecialidad":
                    (
                        perfil
                        .subespecialidad
                        if perfil
                        else None
                    ),

                "area_clinica":
                    (
                        perfil
                        .area_clinica
                        if perfil
                        else None
                    ),

                "cargo":
                    (
                        perfil
                        .cargo
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

            # ==============================================
            # ROLES ACTIVOS
            # ==============================================

            "roles":
                roles,

            # ==============================================
            # FECHAS
            # ==============================================

            "fecha_creacion":
                usuario.fecha_creacion,

            "fecha_actualizacion":
                usuario.fecha_actualizacion,

            "ultimo_acceso":
                usuario.ultimo_acceso,

        }