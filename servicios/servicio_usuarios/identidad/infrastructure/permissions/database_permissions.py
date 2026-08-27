from rest_framework.permissions import BasePermission



class HasPermissionCode(BasePermission):
    """
    Permiso dinámico basado en permisos
    almacenados en base de datos.
    """

    permission_code = None


    def has_permission(
        self,
        request,
        view
    ):

        usuario = request.user


        if not usuario:
            return False


        if not hasattr(
            usuario,
            "asignaciones_roles"
        ):
            return False


        if not self.permission_code:
            return False



        return usuario.asignaciones_roles.filter(

            activo=True,

            rol__permisos_asignados__permiso__codigo=
                self.permission_code,

            rol__permisos_asignados__permiso__activo=True

        ).exists()