from rest_framework.permissions import BasePermission



class IsAuthenticatedUser(BasePermission):
    """
    Permite acceso únicamente a usuarios autenticados.
    """

    def has_permission(
        self,
        request,
        view
    ):

        return bool(
            request.user
            and request.user.is_authenticated
        )





class HasRole(BasePermission):
    """
    Permiso genérico basado en roles
    del sistema de identidad.
    """


    required_role = None



    def has_permission(
        self,
        request,
        view
    ):


        usuario = request.user


        if not usuario or not usuario.is_authenticated:

            return False



        if not self.required_role:

            return False



        return usuario.asignaciones_roles.filter(

            rol__codigo=self.required_role,

            activo=True

        ).exists()





class IsJefeOncologia(HasRole):
    """
    Permite únicamente Jefe de Oncología.
    """

    required_role = "JEFE_ONCOLOGIA"





class IsOncologo(HasRole):
    """
    Permite únicamente médicos oncólogos.
    """

    required_role = "ONCOLOGO"