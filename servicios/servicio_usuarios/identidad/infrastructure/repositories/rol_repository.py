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