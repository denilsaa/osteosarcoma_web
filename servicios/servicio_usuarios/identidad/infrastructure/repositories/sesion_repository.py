from identidad.models import Sesion



class SesionRepository:
    """
    Maneja sesiones activas
    y revocaciones.
    """

    def crear(
        self,
        datos
    ):

        return Sesion.objects.create(
            **datos
        )


    def obtener_por_jti(
        self,
        jti
    ):

        return (
            Sesion.objects
            .filter(
                jti_refresh=jti
            )
            .first()
        )


    def revocar(
        self,
        sesion,
        motivo=None
    ):

        sesion.revocada = True

        sesion.motivo_revocacion = motivo

        sesion.save()

        return sesion


    def sesiones_activas(
        self,
        usuario
    ):

        return (
            Sesion.objects
            .filter(
                usuario=usuario,
                revocada=False
            )
        )