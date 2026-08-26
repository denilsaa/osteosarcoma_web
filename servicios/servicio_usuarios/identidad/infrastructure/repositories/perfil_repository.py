from identidad.models import PerfilProfesional


class PerfilRepository:
    """
    Maneja perfiles profesionales.
    """


    def crear(
        self,
        datos
    ):

        return PerfilProfesional.objects.create(
            **datos
        )


    def obtener_por_usuario(
        self,
        usuario
    ):

        return (
            PerfilProfesional.objects
            .filter(
                usuario=usuario
            )
            .first()
        )


    def actualizar(
        self,
        perfil,
        datos
    ):

        for campo, valor in datos.items():

            setattr(
                perfil,
                campo,
                valor
            )


        perfil.save()

        return perfil