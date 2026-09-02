import hmac
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from identidad.application.services.email_service import (
    EmailService,
)

from identidad.application.services.sesion_autenticada_service import (
    SesionAutenticadaService,
)

from identidad.application.use_cases.login_usuario import (
    enmascarar_correo,
    generar_codigo_otp,
    hash_codigo_otp,
)

from identidad.models import (
    Credencial,
    DesafioSegundoFactor,
)


# ==========================================================
# VERIFICAR SEGUNDO FACTOR
# ==========================================================

class VerificarSegundoFactorUseCase:
    """
    Valida el código OTP.

    IMPORTANTE:

    Los intentos fallidos deben persistir aunque posteriormente
    se lance una excepción hacia la capa API.

    Por ello NO utilizamos @transaction.atomic sobre todo el método.

    La transacción se controla mediante un bloque `with`.
    Primero guardamos el nuevo estado del desafío, permitimos que
    la transacción finalice correctamente y recién después
    lanzamos la excepción correspondiente.
    """

    def ejecutar(
        self,
        desafio_id,
        codigo,
        ip_origen=None,
        user_agent=None,
    ):

        error_mensaje = None

        # ======================================================
        # TRANSACCIÓN
        # ======================================================

        with transaction.atomic():

            desafio = (
                DesafioSegundoFactor.objects
                .select_for_update()
                .select_related(
                    "usuario",
                    "usuario__estado_usuario",
                )
                .filter(
                    id_desafio=desafio_id
                )
                .first()
            )

            # ==================================================
            # DESAFÍO INEXISTENTE
            # ==================================================

            if not desafio:

                error_mensaje = (
                    "La verificación solicitada no existe."
                )

            else:

                ahora = timezone.now()

                # ==============================================
                # YA UTILIZADO
                # ==============================================

                if desafio.utilizado:

                    error_mensaje = (
                        "Este código ya no está disponible."
                    )

                # ==============================================
                # EXPIRADO
                # ==============================================

                elif desafio.fecha_expiracion <= ahora:

                    desafio.utilizado = True
                    desafio.fecha_utilizacion = ahora

                    desafio.save(
                        update_fields=[
                            "utilizado",
                            "fecha_utilizacion",
                        ]
                    )

                    error_mensaje = (
                        "El código de verificación expiró. "
                        "Inicie sesión nuevamente."
                    )

                # ==============================================
                # USUARIO DESHABILITADO
                # ==============================================

                elif (
                    not desafio
                    .usuario
                    .estado_usuario
                    .es_operativo
                ):

                    desafio.utilizado = True
                    desafio.fecha_utilizacion = ahora

                    desafio.save(
                        update_fields=[
                            "utilizado",
                            "fecha_utilizacion",
                        ]
                    )

                    error_mensaje = (
                        "Usuario deshabilitado"
                    )

                else:

                    # ==========================================
                    # CONFIGURACIÓN DE INTENTOS
                    # ==========================================

                    max_intentos = int(
                        getattr(
                            settings,
                            "OTP_MAX_ATTEMPTS",
                            5,
                        )
                    )

                    # ==========================================
                    # YA AGOTÓ INTENTOS
                    # ==========================================

                    if (
                        desafio.intentos_fallidos
                        >= max_intentos
                    ):

                        desafio.utilizado = True

                        if (
                            desafio.fecha_utilizacion
                            is None
                        ):
                            desafio.fecha_utilizacion = (
                                ahora
                            )

                        desafio.save(
                            update_fields=[
                                "utilizado",
                                "fecha_utilizacion",
                            ]
                        )

                        error_mensaje = (
                            "Se agotaron los intentos de "
                            "verificación. Inicie sesión "
                            "nuevamente."
                        )

                    else:

                        # ======================================
                        # CALCULAR HASH DEL OTP
                        # ======================================

                        esperado = hash_codigo_otp(
                            desafio.id_desafio,
                            codigo,
                        )

                        codigo_correcto = (
                            hmac.compare_digest(
                                esperado,
                                desafio.codigo_hash,
                            )
                        )

                        # ======================================
                        # OTP INCORRECTO
                        # ======================================

                        if not codigo_correcto:

                            desafio.intentos_fallidos += 1

                            restantes = max(
                                0,
                                (
                                    max_intentos
                                    - desafio
                                    .intentos_fallidos
                                ),
                            )

                            campos_actualizar = [
                                "intentos_fallidos",
                            ]

                            # ==================================
                            # AGOTÓ EL ÚLTIMO INTENTO
                            # ==================================

                            if restantes == 0:

                                desafio.utilizado = True
                                desafio.fecha_utilizacion = (
                                    ahora
                                )

                                campos_actualizar.extend([
                                    "utilizado",
                                    "fecha_utilizacion",
                                ])

                            desafio.save(
                                update_fields=(
                                    campos_actualizar
                                )
                            )

                            if restantes == 0:

                                error_mensaje = (
                                    "Código incorrecto. "
                                    "Se agotaron los intentos; "
                                    "inicie sesión nuevamente."
                                )

                            else:

                                error_mensaje = (
                                    f"Código incorrecto. "
                                    f"Le quedan "
                                    f"{restantes} intento(s)."
                                )

                        # ======================================
                        # OTP CORRECTO
                        # ======================================

                        else:

                            credencial = (
                                Credencial.objects
                                .select_for_update()
                                .filter(
                                    usuario=(
                                        desafio.usuario
                                    )
                                )
                                .first()
                            )

                            if not credencial:

                                error_mensaje = (
                                    "Credencial no encontrada"
                                )

                            else:

                                desafio.utilizado = True
                                desafio.fecha_utilizacion = (
                                    ahora
                                )

                                desafio.save(
                                    update_fields=[
                                        "utilizado",
                                        "fecha_utilizacion",
                                    ]
                                )

                                # ==============================
                                # CREAR SESIÓN + JWT
                                # ==============================

                                return (
                                    SesionAutenticadaService()
                                    .crear(
                                        usuario=(
                                            desafio.usuario
                                        ),

                                        credencial=(
                                            credencial
                                        ),

                                        ip_origen=(
                                            ip_origen
                                            or desafio.ip_origen
                                        ),

                                        user_agent=(
                                            user_agent
                                            or desafio.user_agent
                                        ),
                                    )
                                )

        # ======================================================
        # ERROR FUERA DE LA TRANSACCIÓN
        # ======================================================
        #
        # A este punto PostgreSQL ya confirmó los cambios.
        # Lanzar la excepción ya NO revierte intentos_fallidos.
        # ======================================================

        if error_mensaje:

            raise Exception(
                error_mensaje
            )

        raise Exception(
            "No fue posible completar la verificación."
        )


# ==========================================================
# REENVIAR SEGUNDO FACTOR
# ==========================================================

class ReenviarSegundoFactorUseCase:
    """
    Genera un nuevo OTP para el mismo desafío respetando
    cooldown y límite de reenvíos.
    """

    @transaction.atomic
    def ejecutar(
        self,
        desafio_id,
    ):

        desafio = (
            DesafioSegundoFactor.objects
            .select_for_update()
            .select_related(
                "usuario",
                "usuario__estado_usuario",
            )
            .filter(
                id_desafio=desafio_id
            )
            .first()
        )

        # ======================================================
        # VALIDACIONES
        # ======================================================

        if not desafio:

            raise Exception(
                "La verificación solicitada no existe."
            )

        if desafio.utilizado:

            raise Exception(
                "Esta verificación ya no está disponible."
            )

        if (
            not desafio
            .usuario
            .estado_usuario
            .es_operativo
        ):

            raise Exception(
                "Usuario deshabilitado"
            )

        ahora = timezone.now()

        cooldown = int(
            getattr(
                settings,
                "OTP_RESEND_SECONDS",
                60,
            )
        )

        max_reenvios = int(
            getattr(
                settings,
                "OTP_MAX_RESENDS",
                3,
            )
        )

        # ======================================================
        # LÍMITE DE REENVÍOS
        # ======================================================

        if desafio.reenvios >= max_reenvios:

            raise Exception(
                "Se alcanzó el límite de reenvíos. "
                "Inicie sesión nuevamente."
            )

        # ======================================================
        # COOLDOWN
        # ======================================================

        segundos_transcurridos = int(
            (
                ahora
                - desafio.fecha_ultimo_envio
            )
            .total_seconds()
        )

        if segundos_transcurridos < cooldown:

            faltan = (
                cooldown
                - segundos_transcurridos
            )

            raise Exception(
                f"Espere {faltan} segundo(s) "
                "antes de solicitar otro código."
            )

        # ======================================================
        # NUEVO OTP
        # ======================================================

        minutos_vigencia = int(
            getattr(
                settings,
                "OTP_CODE_MINUTES",
                5,
            )
        )

        codigo = generar_codigo_otp()

        desafio.codigo_hash = hash_codigo_otp(
            desafio.id_desafio,
            codigo,
        )

        desafio.fecha_expiracion = (
            ahora
            + timedelta(
                minutes=minutos_vigencia
            )
        )

        desafio.fecha_ultimo_envio = ahora

        desafio.intentos_fallidos = 0

        desafio.reenvios += 1

        desafio.save(
            update_fields=[
                "codigo_hash",
                "fecha_expiracion",
                "fecha_ultimo_envio",
                "intentos_fallidos",
                "reenvios",
            ]
        )

        # ======================================================
        # ENVÍO DE CORREO
        # ======================================================

        try:

            EmailService().enviar_codigo_doble_factor(
                usuario=(
                    desafio.usuario
                ),

                codigo=(
                    codigo
                ),

                minutos_vigencia=(
                    minutos_vigencia
                ),
            )

        except Exception as error:

            raise Exception(
                "No fue posible reenviar el código "
                "al correo institucional."
            ) from error

        # ======================================================
        # RESPUESTA
        # ======================================================

        return {

            "desafio_id":
                str(
                    desafio.id_desafio
                ),

            "correo_enmascarado":
                enmascarar_correo(
                    desafio.usuario.correo
                ),

            "expira_en_segundos":
                minutos_vigencia * 60,

            "reenvio_disponible_en":
                cooldown,

            "reenvios_restantes":
                (
                    max_reenvios
                    - desafio.reenvios
                ),

            "mensaje":
                "Se envió un nuevo código "
                "de verificación.",
        }