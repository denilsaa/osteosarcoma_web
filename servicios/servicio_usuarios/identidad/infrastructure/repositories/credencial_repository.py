from identidad.models import Credencial



class CredencialRepository:
    """
    Maneja persistencia
    de credenciales.
    """

    def obtener_por_usuario(
        self,
        usuario
    ):

        return (
            Credencial.objects
            .filter(
                usuario=usuario
            )
            .first()
        )


    def crear(
        self,
        datos
    ):

        return Credencial.objects.create(
            **datos
        )


    def actualizar_password(
        self,
        credencial,
        password_hash
    ):

        credencial.password_hash = password_hash

        credencial.debe_cambiar_password = False

        credencial.save()

        return credencial