from identidad.infrastructure.permissions.database_permissions import (
    HasPermissionCode
)



class PuedeListarOncologos(
    HasPermissionCode
):

    permission_code = "ONCOLOGO_LISTAR"



class PuedeCrearOncologos(
    HasPermissionCode
):

    permission_code = "ONCOLOGO_CREAR"



class PuedeEditarOncologos(
    HasPermissionCode
):

    permission_code = "ONCOLOGO_EDITAR"