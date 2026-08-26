from identidad.models import Usuario


class UsuarioRepository:
    """
    Repositorio encargado del acceso
    a datos de usuarios.
    """

    def obtener_por_id(self, usuario_id):

        return (
            Usuario.objects
            .filter(id_usuario=usuario_id)
            .first()
        )


    def obtener_por_correo(self, correo):

        return (
            Usuario.objects
            .filter(
                correo__iexact=correo
            )
            .first()
        )


    def obtener_por_nombre_usuario(
        self,
        nombre_usuario
    ):

        return (
            Usuario.objects
            .filter(
                nombre_usuario__iexact=nombre_usuario
            )
            .first()
        )


    def listar(self):

        return Usuario.objects.all()


    def crear(self, datos):

        usuario = Usuario.objects.create(
            **datos
        )

        return usuario


    def actualizar(
        self,
        usuario,
        datos
    ):

        for campo, valor in datos.items():

            setattr(
                usuario,
                campo,
                valor
            )


        usuario.save()

        return usuario