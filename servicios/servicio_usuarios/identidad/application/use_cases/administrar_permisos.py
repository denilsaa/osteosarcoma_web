from django.db import transaction

from identidad.models import (
    Permiso,
    Rol,
    RolPermiso,
)


PERMISOS_ONCOLOGO_ADMINISTRABLES = [

    "PACIENTE_GESTIONAR",

    "CASO_CLINICO_GESTIONAR",

    "RADIOGRAFIA_GESTIONAR",

    "ANALISIS_IA_USAR",

    "INFORME_CONSULTAR",

    "PERFIL_EDITAR",

]


class ObtenerPermisosOncologoUseCase:

    def ejecutar(
        self,
    ):

        rol = (
            Rol.objects
            .filter(
                codigo=
                    "ONCOLOGO",

                activo=
                    True,
            )
            .first()
        )


        if not rol:

            raise Exception(
                "No existe el rol ONCOLOGO."
            )


        permisos = (

            Permiso.objects

            .filter(

                codigo__in=
                    PERMISOS_ONCOLOGO_ADMINISTRABLES,

                activo=True,

            )

            .order_by(
                "modulo",
                "nombre",
            )

        )


        permisos_asignados = set(

            RolPermiso.objects

            .filter(
                rol=rol,
            )

            .values_list(
                "permiso__codigo",
                flat=True,
            )

        )


        resultados = []


        for permiso in permisos:

            resultados.append(
                {
                    "id_permiso":
                        permiso.id_permiso,

                    "codigo":
                        permiso.codigo,

                    "nombre":
                        permiso.nombre,

                    "descripcion":
                        permiso.descripcion,

                    "modulo":
                        permiso.modulo,

                    "asignado":
                        (
                            permiso.codigo
                            in
                            permisos_asignados
                        ),
                }
            )


        return {
            "rol": {
                "codigo":
                    rol.codigo,

                "nombre":
                    rol.nombre,

                "descripcion":
                    rol.descripcion,
            },

            "total":
                len(
                    resultados
                ),

            "permisos":
                resultados,
        }


class ActualizarPermisosOncologoUseCase:

    @transaction.atomic
    def ejecutar(
        self,
        codigos_permisos,
    ):

        codigos_solicitados = set(
            codigos_permisos
        )


        codigos_permitidos = set(
            PERMISOS_ONCOLOGO_ADMINISTRABLES
        )


        codigos_invalidos = (

            codigos_solicitados

            -

            codigos_permitidos

        )


        if codigos_invalidos:

            raise Exception(
                (
                    "Existen permisos que no pueden "
                    "ser administrados desde esta pantalla: "
                    +
                    ", ".join(
                        sorted(
                            codigos_invalidos
                        )
                    )
                )
            )


        rol = (
            Rol.objects
            .select_for_update()
            .filter(
                codigo=
                    "ONCOLOGO",

                activo=
                    True,
            )
            .first()
        )


        if not rol:

            raise Exception(
                "No existe el rol ONCOLOGO."
            )


        permisos_existentes = {

            permiso.codigo:
                permiso

            for permiso in (

                Permiso.objects

                .filter(

                    codigo__in=
                        PERMISOS_ONCOLOGO_ADMINISTRABLES,

                    activo=True,

                )

            )

        }


        faltantes = (

            codigos_solicitados

            -

            set(
                permisos_existentes.keys()
            )

        )


        if faltantes:

            raise Exception(
                (
                    "No existen los siguientes permisos: "
                    +
                    ", ".join(
                        sorted(
                            faltantes
                        )
                    )
                )
            )


        # ==================================================
        # QUITAR PERMISOS DESMARCADOS
        # ==================================================

        (
            RolPermiso.objects

            .filter(

                rol=
                    rol,

                permiso__codigo__in=
                    PERMISOS_ONCOLOGO_ADMINISTRABLES,

            )

            .exclude(

                permiso__codigo__in=
                    codigos_solicitados

            )

            .delete()
        )


        # ==================================================
        # AGREGAR LOS SELECCIONADOS
        # ==================================================

        for codigo in (
            codigos_solicitados
        ):

            permiso = (
                permisos_existentes[
                    codigo
                ]
            )


            RolPermiso.objects.get_or_create(

                rol=
                    rol,

                permiso=
                    permiso,

            )


        resultado = (

            ObtenerPermisosOncologoUseCase()

            .ejecutar()

        )


        return {
            "mensaje":
                (
                    "Permisos del rol Oncólogo "
                    "actualizados correctamente."
                ),

            **resultado,
        }