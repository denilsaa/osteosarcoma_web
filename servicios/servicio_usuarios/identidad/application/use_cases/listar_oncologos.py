from django.db.models import Q

from identidad.models import Usuario


ROLES_ONCOLOGIA = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}


class ListarOncologosUseCase:
    """
    Lista el personal de Oncología.

    Incluye:

    - ONCOLOGO
    - JEFE_ONCOLOGIA

    Permite:

    - búsqueda;
    - filtro por estado;
    - filtro por rol.
    """

    def ejecutar(
        self,
        buscar=None,
        estado=None,
        rol=None,
    ):

        # ==================================================
        # CONSULTA BASE
        # ==================================================

        consulta = (
            Usuario.objects
            .filter(
                asignaciones_roles__activo=True,
                asignaciones_roles__rol__activo=True,
                asignaciones_roles__rol__codigo__in=(
                    ROLES_ONCOLOGIA
                ),
            )
            .select_related(
                "estado_usuario",
                "perfil_profesional",
            )
            .prefetch_related(
                "asignaciones_roles__rol"
            )
            .distinct()
            .order_by(
                "apellido_paterno",
                "nombres",
            )
        )

        # ==================================================
        # BÚSQUEDA
        # ==================================================

        if buscar:

            buscar = (
                buscar
                .strip()
            )

            consulta = (
                consulta
                .filter(

                    Q(
                        nombres__icontains=buscar
                    )

                    |

                    Q(
                        apellido_paterno__icontains=buscar
                    )

                    |

                    Q(
                        apellido_materno__icontains=buscar
                    )

                    |

                    Q(
                        correo__icontains=buscar
                    )

                    |

                    Q(
                        nombre_usuario__icontains=buscar
                    )

                    |

                    Q(
                        ci_numero__icontains=buscar
                    )

                    |

                    Q(
                        perfil_profesional__matricula_profesional__icontains=(
                            buscar
                        )
                    )

                )
            )

        # ==================================================
        # FILTRO ESTADO
        # ==================================================

        if estado:

            consulta = (
                consulta
                .filter(
                    estado_usuario__codigo__iexact=(
                        estado.strip()
                    )
                )
            )

        # ==================================================
        # FILTRO ROL
        # ==================================================

        if rol:

            rol = (
                rol
                .strip()
                .upper()
            )

            if (
                rol
                not in
                ROLES_ONCOLOGIA
            ):

                raise Exception(
                    "El rol utilizado como filtro no es válido."
                )

            consulta = (
                consulta
                .filter(
                    asignaciones_roles__activo=True,
                    asignaciones_roles__rol__codigo=rol,
                )
                .distinct()
            )

        # ==================================================
        # RESULTADOS
        # ==================================================

        oncologos = []

        for usuario in consulta:

            # ==============================================
            # PERFIL
            # ==============================================

            try:

                perfil = (
                    usuario
                    .perfil_profesional
                )

            except Exception:

                perfil = None

            # ==============================================
            # ROLES
            # ==============================================

            roles = [

                asignacion.rol.codigo

                for asignacion
                in usuario.asignaciones_roles.all()

                if (
                    asignacion.activo
                    and
                    asignacion.rol.activo
                    and
                    asignacion.rol.codigo
                    in
                    ROLES_ONCOLOGIA
                )

            ]

            # ==============================================
            # ROL PRINCIPAL
            # ==============================================

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

            # ==============================================
            # OBJETO
            # ==============================================

            oncologos.append(
                {

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
                        usuario.nombre_completo,

                    "ci_numero":
                        usuario.ci_numero,

                    "ci_complemento":
                        usuario.ci_complemento,

                    "ci_expedido":
                        usuario.ci_expedido,

                    "ci_completo":
                        usuario.ci_completo,

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

                    "matricula_profesional":
                        (
                            perfil
                            .matricula_profesional
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

                    "rol":
                        rol_nombre,

                    "rol_codigo":
                        rol_codigo,

                    "roles":
                        roles,

                    "fecha_creacion":
                        usuario.fecha_creacion,

                }
            )

        return {

            "total":
                len(
                    oncologos
                ),

            "resultados":
                oncologos,

        }