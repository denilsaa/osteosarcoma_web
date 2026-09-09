from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository,
)


# ==========================================================
# ROLES DE ONCOLOGÍA
# ==========================================================

ROLES_ONCOLOGIA = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}


class ObtenerMiPerfilUseCase:
    """
    Consulta el perfil completo del usuario autenticado.

    IMPORTANTE:

    - No recibe id_usuario desde frontend.
    - Siempre utiliza request.user.
    - No permite consultar perfiles ajenos.
    - Devuelve información personal e institucional.
    """

    # ======================================================
    # INICIALIZACIÓN
    # ======================================================

    def __init__(
        self,
    ):

        self.perfil_repository = (
            PerfilRepository()
        )

    # ======================================================
    # EJECUTAR
    # ======================================================

    def ejecutar(
        self,
        usuario,
    ):

        if not usuario:

            raise Exception(
                "No existe un usuario autenticado."
            )

        # ==================================================
        # PERFIL PROFESIONAL
        # ==================================================

        perfil = (
            self.perfil_repository
            .obtener_por_usuario(
                usuario
            )
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
            asignaciones
            .values_list(
                "rol__codigo",
                flat=True,
            )
            .distinct()
        )

        # ==================================================
        # ROL PRINCIPAL
        # ==================================================
        #
        # Algunos usuarios antiguos pueden tener
        # simultáneamente:
        #
        # ONCOLOGO
        # JEFE_ONCOLOGIA
        #
        # En ese escenario se prioriza Jefatura.
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

        elif (
            "ONCOLOGO"
            in roles
        ):

            rol_codigo = (
                "ONCOLOGO"
            )

            rol_nombre = (
                "Oncólogo"
            )

        elif roles:

            rol_codigo = (
                roles[0]
            )

            rol_nombre = (
                roles[0]
            )

        else:

            rol_codigo = (
                None
            )

            rol_nombre = (
                None
            )

        # ==================================================
        # CI COMPLETO
        # ==================================================

        ci_completo = (
            self._ci_completo(
                usuario
            )
        )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {

            # ==============================================
            # IDENTIFICADOR
            # ==============================================

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
                self._nombre_completo(
                    usuario
                ),

            "telefono":
                usuario.telefono,

            # ==============================================
            # DOCUMENTO DE IDENTIDAD
            # ==============================================

            "ci_numero":
                usuario.ci_numero,

            "ci_complemento":
                usuario.ci_complemento,

            "ci_expedido":
                usuario.ci_expedido,

            "ci_completo":
                ci_completo,

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

            "roles":
                roles,

            # ==============================================
            # PERFIL PROFESIONAL
            # ==============================================

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
            # FECHAS
            # ==============================================

            "fecha_creacion":
                (
                    usuario
                    .fecha_creacion
                    .isoformat()
                ),

            "fecha_actualizacion":
                (
                    usuario
                    .fecha_actualizacion
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

    # ======================================================
    # NOMBRE COMPLETO
    # ======================================================

    @staticmethod
    def _nombre_completo(
        usuario,
    ):

        return " ".join(

            str(
                parte
            ).strip()

            for parte
            in [

                usuario.nombres,

                usuario.apellido_paterno,

                usuario.apellido_materno,

            ]

            if (
                parte
                and
                str(
                    parte
                ).strip()
            )

        )

    # ======================================================
    # CI COMPLETO
    # ======================================================

    @staticmethod
    def _ci_completo(
        usuario,
    ):

        if not usuario.ci_numero:

            return None

        documento = (
            str(
                usuario.ci_numero
            )
            .strip()
        )

        if usuario.ci_complemento:

            documento = (
                f"{documento}-"
                f"{str(usuario.ci_complemento).strip()}"
            )

        if usuario.ci_expedido:

            documento = (
                f"{documento} "
                f"{usuario.ci_expedido}"
            )

        return documento