from django.db import transaction

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)

from identidad.application.use_cases.obtener_perfil import (
    ObtenerMiPerfilUseCase,
)


class ActualizarMiPerfilUseCase:
    """
    Actualiza exclusivamente los datos personales
    autorizados del usuario autenticado.

    IMPORTANTE:
    No recibe id_usuario.
    Siempre trabaja con request.user.
    """

    CAMPOS_AUTORIZADOS = {

        "nombres",

        "apellido_paterno",

        "apellido_materno",

        "telefono",

    }


    def __init__(
        self,
    ):

        self.usuario_repository = (
            UsuarioRepository()
        )


    @transaction.atomic
    def ejecutar(
        self,
        usuario,
        datos,
    ):

        if not usuario:

            raise Exception(
                "No existe un usuario autenticado."
            )


        # ==================================================
        # DOBLE PROTECCIÓN
        # ==================================================
        # El serializer ya bloquea campos no autorizados,
        # pero el caso de uso vuelve a aplicar la regla.
        # ==================================================

        campos_no_autorizados = (

            set(
                datos.keys()
            )

            -

            self.CAMPOS_AUTORIZADOS

        )


        if campos_no_autorizados:

            raise Exception(
                (
                    "Intento de modificar campos "
                    "no autorizados: "
                    +
                    ", ".join(
                        sorted(
                            campos_no_autorizados
                        )
                    )
                )
            )


        # ==================================================
        # NORMALIZAR CAMPOS
        # ==================================================

        datos_actualizacion = {}


        for campo in self.CAMPOS_AUTORIZADOS:

            if campo not in datos:
                continue


            valor = datos[campo]


            if campo in (
                "apellido_materno",
                "telefono",
            ):

                if valor in (
                    "",
                    None,
                ):

                    valor = None


            datos_actualizacion[
                campo
            ] = valor


        if not datos_actualizacion:

            raise Exception(
                "No se enviaron datos para actualizar."
            )


        # ==================================================
        # ACTUALIZAR ÚNICAMENTE AL USUARIO AUTENTICADO
        # ==================================================

        self.usuario_repository.actualizar(

            usuario,

            datos_actualizacion,

        )


        # ==================================================
        # DEVOLVER EL PERFIL ACTUALIZADO
        # ==================================================

        perfil_actualizado = (

            ObtenerMiPerfilUseCase()

            .ejecutar(
                usuario
            )

        )


        return {

            "mensaje":
                "Perfil actualizado correctamente.",

            "perfil":
                perfil_actualizado,

        }