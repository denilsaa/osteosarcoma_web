from django.utils import timezone

from identidad.models import Sesion


class SesionRepository:
    """
    Repositorio encargado del manejo
    de las sesiones de usuario.
    """

    # ======================================================
    # CREAR
    # ======================================================

    def crear(
        self,
        datos
    ):

        return Sesion.objects.create(
            **datos
        )

    # ======================================================
    # BUSCAR POR ID DE SESIÓN
    # ======================================================

    def obtener_por_id(
        self,
        sesion_id
    ):

        return (
            Sesion.objects
            .select_related(
                "usuario",
                "usuario__estado_usuario",
            )
            .filter(
                id_sesion=sesion_id
            )
            .first()
        )

    # ======================================================
    # BUSCAR POR JTI DEL REFRESH
    # ======================================================

    def obtener_por_jti(
        self,
        jti
    ):

        return (
            Sesion.objects
            .select_related(
                "usuario",
                "usuario__estado_usuario",
            )
            .filter(
                jti_refresh=jti
            )
            .first()
        )

    # ======================================================
    # VALIDAR SESIÓN USANDO REFRESH
    # ======================================================

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

        if (
            sesion.fecha_expiracion
            <=
            timezone.now()
        ):

            return None

        if (
            not
            sesion.usuario.estado_usuario.es_operativo
        ):

            return None

        return sesion

    # ======================================================
    # VALIDAR SESIÓN USANDO ACCESS TOKEN
    # ======================================================

    def obtener_sesion_access_valida(
        self,
        sesion_id,
        usuario_id=None
    ):

        sesion = (
            self.obtener_por_id(
                sesion_id
            )
        )

        if not sesion:

            return None

        if usuario_id is not None:

            if (
                str(
                    sesion.usuario_id
                )
                !=
                str(
                    usuario_id
                )
            ):

                return None

        if sesion.revocada:

            return None

        if (
            sesion.fecha_expiracion
            <=
            timezone.now()
        ):

            return None

        if (
            not
            sesion.usuario.estado_usuario.es_operativo
        ):

            return None

        return sesion

    # ======================================================
    # REVOCAR UNA SESIÓN
    # ======================================================

    def revocar(
        self,
        sesion,
        motivo=None
    ):

        if sesion.revocada:

            return sesion

        sesion.revocada = True

        sesion.motivo_revocacion = (
            motivo
        )

        sesion.fecha_cierre = (
            timezone.now()
        )

        sesion.save(

            update_fields=[

                "revocada",

                "motivo_revocacion",

                "fecha_cierre",

            ]

        )

        return sesion

    # ======================================================
    # SESIONES ACTIVAS
    # ======================================================

    def sesiones_activas(
        self,
        usuario
    ):

        return (
            Sesion.objects
            .filter(

                usuario=usuario,

                revocada=False,

                fecha_expiracion__gt=
                    timezone.now(),

            )
        )

    # ======================================================
    # REVOCAR TODAS LAS SESIONES DE UN USUARIO
    # ======================================================

    def revocar_todas(
        self,
        usuario,
        motivo=None
    ):

        sesiones = (
            self.sesiones_activas(
                usuario
            )
        )

        cantidad = 0

        for sesion in sesiones:

            self.revocar(

                sesion,

                motivo or
                "Sesiones revocadas",

            )

            cantidad += 1

        return cantidad