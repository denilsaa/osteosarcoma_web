from identidad.infrastructure.permissions.database_permissions import (
    HasPermissionCode,
)


class PuedeEditarPerfil(
    HasPermissionCode
):

    permission_code = (
        "PERFIL_EDITAR"
    )