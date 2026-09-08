from django.db import transaction
from django.utils import timezone

from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository,
)

from identidad.infrastructure.repositories.rol_repository import (
    RolRepository,
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)

from identidad.models import UsuarioRol


ROLES_ONCOLOGIA = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}

ESPECIALIDAD_ONCOLOGIA = (
    "Oncología"
)

AREA_CLINICA_OSTEOSARCOMA = (
    "Tumores óseos / Osteosarcoma"
)


class EditarOncologoUseCase:
    """
    Actualiza una cuenta del personal de Oncología.

    Permite trabajar con:

    - ONCOLOGO
    - JEFE_ONCOLOGIA

    También permite cambiar entre ambos roles.
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

        self.rol_repository = (
            RolRepository()
        )

    # ======================================================
    # EJECUTAR
    # ======================================================

    @transaction.atomic
    def ejecutar(
        self,
        usuario_id,
        datos,
        usuario_editor=None,
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
        # VALIDAR QUE SEA PERSONAL DE ONCOLOGÍA
        # ==================================================

        pertenece_oncologia = (
            usuario
            .asignaciones_roles
            .filter(
                activo=True,
                rol__codigo__in=(
                    ROLES_ONCOLOGIA
                ),
            )
            .exists()
        )

        if not pertenece_oncologia:

            raise Exception(
                "La cuenta indicada no pertenece "
                "al personal de Oncología."
            )

        # ==================================================
        # CAMPOS DEL USUARIO
        # ==================================================

        campos_usuario = [

            "nombres",

            "apellido_paterno",

            "apellido_materno",

            "correo",

            "telefono",

            "ci_numero",

            "ci_complemento",

            "ci_expedido",

        ]

        datos_usuario = {}

        for campo in campos_usuario:

            if campo in datos:

                datos_usuario[
                    campo
                ] = (
                    datos[
                        campo
                    ]
                )

        if datos_usuario:

            self.usuario_repository.actualizar(
                usuario,
                datos_usuario,
            )

        # ==================================================
        # PERFIL PROFESIONAL
        # ==================================================

        campos_perfil = [

            "matricula_profesional",

            "subespecialidad",

            "telefono_institucional",

        ]

        datos_perfil = {}

        for campo in campos_perfil:

            if campo in datos:

                datos_perfil[
                    campo
                ] = (
                    datos[
                        campo
                    ]
                )

        # --------------------------------------------------
        # VALORES CONTROLADOS
        # --------------------------------------------------

        datos_perfil[
            "especialidad"
        ] = (
            ESPECIALIDAD_ONCOLOGIA
        )

        datos_perfil[
            "area_clinica"
        ] = (
            AREA_CLINICA_OSTEOSARCOMA
        )

        # ==================================================
        # ROL
        # ==================================================

        nuevo_rol_codigo = (
            datos.get(
                "rol_codigo"
            )
        )

        if nuevo_rol_codigo:

            nuevo_rol_codigo = (
                str(
                    nuevo_rol_codigo
                )
                .strip()
                .upper()
            )

            if (
                nuevo_rol_codigo
                not in
                ROLES_ONCOLOGIA
            ):

                raise Exception(
                    "El rol seleccionado no es válido."
                )

            if (
                nuevo_rol_codigo
                ==
                "JEFE_ONCOLOGIA"
            ):

                datos_perfil[
                    "cargo"
                ] = (
                    "Jefe de Oncología"
                )

            else:

                datos_perfil[
                    "cargo"
                ] = (
                    "Oncólogo"
                )

        # ==================================================
        # PERFIL EXISTENTE
        # ==================================================

        perfil = (
            self.perfil_repository
            .obtener_por_usuario(
                usuario
            )
        )

        if perfil:

            self.perfil_repository.actualizar(
                perfil,
                datos_perfil,
            )

        else:

            if (
                "cargo"
                not in
                datos_perfil
            ):

                datos_perfil[
                    "cargo"
                ] = (
                    "Oncólogo"
                )

            self.perfil_repository.crear(
                {
                    "usuario":
                        usuario,

                    **datos_perfil,
                }
            )

        # ==================================================
        # CAMBIAR ROL SI FUE SOLICITADO
        # ==================================================

        if nuevo_rol_codigo:

            self._actualizar_rol(
                usuario=usuario,
                nuevo_rol_codigo=(
                    nuevo_rol_codigo
                ),
                usuario_editor=(
                    usuario_editor
                ),
            )

        return usuario

    # ======================================================
    # ACTUALIZAR ROL
    # ======================================================

    def _actualizar_rol(
        self,
        *,
        usuario,
        nuevo_rol_codigo,
        usuario_editor=None,
    ):

        nuevo_rol = (
            self.rol_repository
            .obtener_por_codigo(
                nuevo_rol_codigo
            )
        )

        if not nuevo_rol:

            raise Exception(
                "El rol seleccionado no existe."
            )

        if not nuevo_rol.activo:

            raise Exception(
                "El rol seleccionado está inactivo."
            )

        # ==================================================
        # DESACTIVAR OTROS ROLES DE ONCOLOGÍA
        # ==================================================

        asignaciones = (
            UsuarioRol.objects
            .filter(
                usuario=usuario,
                rol__codigo__in=(
                    ROLES_ONCOLOGIA
                ),
            )
            .select_related(
                "rol"
            )
        )

        for asignacion in asignaciones:

            if (
                asignacion.rol.codigo
                ==
                nuevo_rol_codigo
            ):

                asignacion.activo = True

                asignacion.fecha_fin = None

                asignacion.save(
                    update_fields=[
                        "activo",
                        "fecha_fin",
                    ]
                )

            else:

                asignacion.activo = False

                asignacion.fecha_fin = (
                    timezone.now()
                )

                asignacion.save(
                    update_fields=[
                        "activo",
                        "fecha_fin",
                    ]
                )

        # ==================================================
        # SI NUNCA TUVO ESE ROL, CREAR ASIGNACIÓN
        # ==================================================

        existe_asignacion = (
            UsuarioRol.objects
            .filter(
                usuario=usuario,
                rol=nuevo_rol,
            )
            .exists()
        )

        if not existe_asignacion:

            self.rol_repository.asignar_rol(
                usuario,
                nuevo_rol,
                usuario_editor,
            )