from django.utils import timezone

from identidad.models import Sesion



class SesionRepository:
    """
    Maneja creación,
    validación y revocación
    de sesiones.
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



    def obtener_sesion_valida(
        self,
        jti
    ):

        sesion = (
            self.obtener_por_jti(
                jti
            )
        )


        if not sesion:

            return None



        if sesion.revocada:

            return None



        if sesion.fecha_expiracion < timezone.now():

            return None



        return sesion




    def revocar(
        self,
        sesion,
        motivo=None
    ):

        sesion.revocada = True

        sesion.motivo_revocacion = motivo

        sesion.fecha_cierre = timezone.now()

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
                revocada=False,
                fecha_expiracion__gt=timezone.now()
            )
        )