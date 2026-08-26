from identidad.models import (
    Rol,
    UsuarioRol,
)


class RolRepository:
    """
    Maneja roles y asignaciones.
    """

    def obtener_por_codigo(
        self,
        codigo
    ):

        return (
            Rol.objects
            .filter(
                codigo=codigo
            )
            .first()
        )


    def asignar_rol(
        self,
        usuario,
        rol,
        asignado_por=None
    ):

        return UsuarioRol.objects.create(

            usuario=usuario,

            rol=rol,

            asignado_por=asignado_por,

        )


    def obtener_usuarios_por_rol(
        self,
        codigo_rol
    ):

        return (
            UsuarioRol.objects
            .filter(
                rol__codigo=codigo_rol,
                activo=True
            )
            .select_related(
                "usuario",
                "rol"
            )
        )