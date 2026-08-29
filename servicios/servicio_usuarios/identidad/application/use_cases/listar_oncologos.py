from django.db.models import Q

from identidad.models import UsuarioRol


class ListarOncologosUseCase:
    """
    Lista las cuentas que tienen asignado
    el rol ONCOLOGO.

    Permite:
    - listar todos los oncólogos;
    - buscar por datos personales/profesionales;
    - filtrar por estado.
    """

    def ejecutar(
        self,
        buscar=None,
        estado=None,
    ):

        # ==================================================
        # CONSULTA BASE
        # ==================================================

        consulta = (
            UsuarioRol.objects
            .filter(
                rol__codigo="ONCOLOGO",
                activo=True,
            )
            .select_related(
                "usuario",
                "usuario__estado_usuario",
                "usuario__perfil_profesional",
                "rol",
            )
            .order_by(
                "usuario__apellido_paterno",
                "usuario__nombres",
            )
        )

        # ==================================================
        # BÚSQUEDA
        # ==================================================

        if buscar:

            buscar = buscar.strip()

            consulta = consulta.filter(
                Q(
                    usuario__nombres__icontains=buscar
                )
                |
                Q(
                    usuario__apellido_paterno__icontains=buscar
                )
                |
                Q(
                    usuario__apellido_materno__icontains=buscar
                )
                |
                Q(
                    usuario__correo__icontains=buscar
                )
                |
                Q(
                    usuario__nombre_usuario__icontains=buscar
                )
                |
                Q(
                    usuario__perfil_profesional__matricula_profesional__icontains=buscar
                )
            )

        # ==================================================
        # FILTRO POR ESTADO
        # ==================================================

        if estado:

            estado = estado.strip()

            consulta = consulta.filter(
                usuario__estado_usuario__codigo__iexact=estado
            )

        # ==================================================
        # SERIALIZACIÓN
        # ==================================================

        oncologos = []

        for usuario_rol in consulta:

            usuario = usuario_rol.usuario

            try:
                perfil = usuario.perfil_profesional
            except Exception:
                perfil = None

            nombre_completo = " ".join(
                parte
                for parte in [
                    usuario.nombres,
                    usuario.apellido_paterno,
                    usuario.apellido_materno,
                ]
                if parte
            )

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

                    "nombre_completo":
                        nombre_completo,

                    "correo":
                        usuario.correo,

                    "nombre_usuario":
                        usuario.nombre_usuario,

                    "telefono":
                        usuario.telefono,

                    "estado":
                        usuario.estado_usuario.codigo,

                    "estado_nombre":
                        usuario.estado_usuario.nombre,

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

                    "matricula_profesional":
                        (
                            perfil.matricula_profesional
                            if perfil
                            else None
                        ),

                    "telefono_institucional":
                        (
                            perfil.telefono_institucional
                            if perfil
                            else None
                        ),

                    "rol":
                        usuario_rol.rol.nombre,

                    "fecha_creacion":
                        usuario.fecha_creacion,
                }
            )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {
            "total":
                len(oncologos),

            "resultados":
                oncologos,
        }