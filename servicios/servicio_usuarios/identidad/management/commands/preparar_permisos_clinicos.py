from django.core.management.base import BaseCommand
from django.db import transaction

from identidad.models import (
    Permiso,
    Rol,
    RolPermiso,
)


class Command(BaseCommand):

    help = (
        "Prepara los permisos clínicos administrables "
        "para el rol ONCOLOGO."
    )

    @transaction.atomic
    def handle(
        self,
        *args,
        **options,
    ):

        permisos_clinicos = [

            {
                "codigo":
                    "PACIENTE_GESTIONAR",

                "nombre":
                    "Gestionar pacientes",

                "descripcion":
                    (
                        "Permite consultar y trabajar "
                        "con pacientes."
                    ),

                "modulo":
                    "PACIENTES",
            },

            {
                "codigo":
                    "CASO_CLINICO_GESTIONAR",

                "nombre":
                    "Gestionar casos clínicos",

                "descripcion":
                    (
                        "Permite consultar y trabajar "
                        "con casos clínicos."
                    ),

                "modulo":
                    "CASOS",
            },

            {
                "codigo":
                    "RADIOGRAFIA_GESTIONAR",

                "nombre":
                    "Gestionar radiografías",

                "descripcion":
                    (
                        "Permite consultar y cargar "
                        "radiografías."
                    ),

                "modulo":
                    "RADIOGRAFIAS",
            },

            {
                "codigo":
                    "ANALISIS_IA_USAR",

                "nombre":
                    "Utilizar análisis IA",

                "descripcion":
                    (
                        "Permite utilizar las herramientas "
                        "de análisis mediante IA."
                    ),

                "modulo":
                    "IA",
            },

            {
                "codigo":
                    "INFORME_CONSULTAR",

                "nombre":
                    "Consultar informes",

                "descripcion":
                    (
                        "Permite acceder al módulo "
                        "de informes."
                    ),

                "modulo":
                    "INFORMES",
            },

            {
                "codigo":
                    "PERFIL_EDITAR",

                "nombre":
                    "Editar perfil",

                "descripcion":
                    (
                        "Permite actualizar los datos "
                        "personales autorizados."
                    ),

                "modulo":
                    "PERFIL",
            },

        ]


        permisos_creados = {}


        for datos in permisos_clinicos:

            permiso, _ = (
                Permiso.objects.update_or_create(

                    codigo=
                        datos["codigo"],

                    defaults={
                        "nombre":
                            datos["nombre"],

                        "descripcion":
                            datos["descripcion"],

                        "modulo":
                            datos["modulo"],

                        "activo":
                            True,
                    },

                )
            )

            permisos_creados[
                permiso.codigo
            ] = permiso


        rol_oncologo = (
            Rol.objects
            .filter(
                codigo="ONCOLOGO"
            )
            .first()
        )


        rol_jefe = (
            Rol.objects
            .filter(
                codigo="JEFE_ONCOLOGIA"
            )
            .first()
        )


        if not rol_oncologo:

            self.stdout.write(
                self.style.ERROR(
                    "No existe el rol ONCOLOGO."
                )
            )

            return


        if not rol_jefe:

            self.stdout.write(
                self.style.ERROR(
                    "No existe el rol JEFE_ONCOLOGIA."
                )
            )

            return


        # ==================================================
        # POR DEFECTO:
        # ONCÓLOGO TIENE TODOS LOS PERMISOS CLÍNICOS
        # ==================================================

        for permiso in (
            permisos_creados.values()
        ):

            RolPermiso.objects.get_or_create(

                rol=
                    rol_oncologo,

                permiso=
                    permiso,

            )


        # ==================================================
        # EL JEFE TAMBIÉN CONSERVA LOS PERMISOS CLÍNICOS
        # ==================================================

        for permiso in (
            permisos_creados.values()
        ):

            RolPermiso.objects.get_or_create(

                rol=
                    rol_jefe,

                permiso=
                    permiso,

            )


        # ==================================================
        # PERMISOS ADMINISTRATIVOS DEL JEFE
        # ==================================================

        permisos_jefe = [

            "ONCOLOGO_CREAR",

            "ONCOLOGO_EDITAR",

            "ONCOLOGO_LISTAR",

            "RECUPERACION_APROBAR",

            "USUARIO_ACTIVAR",

            "USUARIO_DESACTIVAR",

        ]


        for codigo in permisos_jefe:

            permiso = (
                Permiso.objects
                .filter(
                    codigo=codigo
                )
                .first()
            )


            if permiso:

                RolPermiso.objects.get_or_create(

                    rol=
                        rol_jefe,

                    permiso=
                        permiso,

                )


        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Permisos clínicos preparados "
                    "correctamente."
                )
            )
        )