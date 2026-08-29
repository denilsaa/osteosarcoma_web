from django.db import transaction

from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository,
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)

from identidad.models import EstadoUsuario


class CambiarEstadoOncologoUseCase:

    def __init__(self):

        self.usuario_repository = (
            UsuarioRepository()
        )

        self.sesion_repository = (
            SesionRepository()
        )

    @transaction.atomic
    def ejecutar(
        self,
        usuario_id,
        nuevo_estado,
    ):

        nuevo_estado = (
            str(nuevo_estado)
            .strip()
            .upper()
        )

        if nuevo_estado not in (
            "ACTIVO",
            "INACTIVO",
        ):

            raise Exception(
                "El estado solicitado no es válido."
            )

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

        estado = (
            EstadoUsuario.objects
            .filter(
                codigo=nuevo_estado
            )
            .first()
        )

        if not estado:

            raise Exception(
                f"No existe el estado {nuevo_estado}."
            )

        if (
            usuario
            .estado_usuario
            .codigo
            ==
            nuevo_estado
        ):

            return {
                "id_usuario":
                    str(
                        usuario.id_usuario
                    ),

                "estado":
                    usuario
                    .estado_usuario
                    .codigo,

                "estado_nombre":
                    usuario
                    .estado_usuario
                    .nombre,

                "sesiones_revocadas":
                    0,
            }

        usuario.estado_usuario = estado

        usuario.save(
            update_fields=[
                "estado_usuario",
                "fecha_actualizacion",
            ]
        )

        sesiones_revocadas = 0

        if nuevo_estado == "INACTIVO":

            sesiones = (
                self.sesion_repository
                .sesiones_activas(
                    usuario
                )
            )

            for sesion in sesiones:

                self.sesion_repository.revocar(
                    sesion,
                    "Cuenta desactivada por Jefatura de Oncología",
                )

                sesiones_revocadas += 1

        return {

            "id_usuario":
                str(
                    usuario.id_usuario
                ),

            "estado":
                usuario
                .estado_usuario
                .codigo,

            "estado_nombre":
                usuario
                .estado_usuario
                .nombre,

            "sesiones_revocadas":
                sesiones_revocadas,

        }