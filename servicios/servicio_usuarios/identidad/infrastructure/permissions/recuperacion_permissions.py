from rest_framework.permissions import (
    BasePermission,
)


class EsJefeOncologia(
    BasePermission
):

    message = (
        "Esta operación está disponible "
        "únicamente para Jefatura de Oncología."
    )

    def has_permission(
        self,
        request,
        view,
    ):

        usuario = getattr(
            request,
            "user",
            None,
        )

        if not usuario:

            return False


        try:

            if (
                not
                usuario
                .estado_usuario
                .es_operativo
            ):

                return False

        except Exception:

            return False


        return (

            usuario
            .asignaciones_roles
            .filter(

                activo=True,

                rol__activo=True,

                rol__codigo=
                    "JEFE_ONCOLOGIA",

            )
            .exists()

        )