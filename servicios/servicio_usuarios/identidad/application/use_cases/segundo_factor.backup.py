import hmac
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from identidad.application.services.email_service import EmailService
from identidad.application.services.sesion_autenticada_service import (
    SesionAutenticadaService,
)
from identidad.application.use_cases.login_usuario import (
    enmascarar_correo,
    generar_codigo_otp,
    hash_codigo_otp,
)
from identidad.models import Credencial, DesafioSegundoFactor


class VerificarSegundoFactorUseCase:
    """Valida el OTP y recién entonces crea la sesión y los JWT."""

    @transaction.atomic
    def ejecutar(
        self,
        desafio_id,
        codigo,
        ip_origen=None,
        user_agent=None,
    ):
        desafio = (
            DesafioSegundoFactor.objects
            .select_for_update()
            .select_related("usuario", "usuario__estado_usuario")
            .filter(id_desafio=desafio_id)
            .first()
        )

        if not desafio:
            raise Exception("La verificación solicitada no existe.")

        if desafio.utilizado:
            raise Exception("Este código ya no está disponible.")

        ahora = timezone.now()

        if desafio.fecha_expiracion <= ahora:
            desafio.utilizado = True
            desafio.fecha_utilizacion = ahora
            desafio.save(
                update_fields=["utilizado", "fecha_utilizacion"]
            )
            raise Exception("El código de verificación expiró. Inicie sesión nuevamente.")

        if not desafio.usuario.estado_usuario.es_operativo:
            desafio.utilizado = True
            desafio.fecha_utilizacion = ahora
            desafio.save(
                update_fields=["utilizado", "fecha_utilizacion"]
            )
            raise Exception("Usuario deshabilitado")

        max_intentos = int(
            getattr(settings, "OTP_MAX_ATTEMPTS", 5)
        )

        if desafio.intentos_fallidos >= max_intentos:
            desafio.utilizado = True
            desafio.fecha_utilizacion = ahora
            desafio.save(
                update_fields=["utilizado", "fecha_utilizacion"]
            )
            raise Exception("Se agotaron los intentos de verificación. Inicie sesión nuevamente.")

        esperado = hash_codigo_otp(
            desafio.id_desafio,
            codigo,
        )

        if not hmac.compare_digest(esperado, desafio.codigo_hash):
            desafio.intentos_fallidos += 1

            if desafio.intentos_fallidos >= max_intentos:
                desafio.utilizado = True
                desafio.fecha_utilizacion = ahora

            desafio.save(
                update_fields=[
                    "intentos_fallidos",
                    "utilizado",
                    "fecha_utilizacion",
                ]
            )

            restantes = max(0, max_intentos - desafio.intentos_fallidos)

            if restantes == 0:
                raise Exception(
                    "Código incorrecto. Se agotaron los intentos; inicie sesión nuevamente."
                )

            raise Exception(
                f"Código incorrecto. Le quedan {restantes} intento(s)."
            )

        credencial = (
            Credencial.objects
            .select_for_update()
            .filter(usuario=desafio.usuario)
            .first()
        )

        if not credencial:
            raise Exception("Credencial no encontrada")

        desafio.utilizado = True
        desafio.fecha_utilizacion = ahora
        desafio.save(
            update_fields=["utilizado", "fecha_utilizacion"]
        )

        return SesionAutenticadaService().crear(
            usuario=desafio.usuario,
            credencial=credencial,
            ip_origen=ip_origen or desafio.ip_origen,
            user_agent=user_agent or desafio.user_agent,
        )


class ReenviarSegundoFactorUseCase:
    """Genera un nuevo OTP para el mismo desafío respetando cooldown y límite."""

    @transaction.atomic
    def ejecutar(self, desafio_id):
        desafio = (
            DesafioSegundoFactor.objects
            .select_for_update()
            .select_related("usuario", "usuario__estado_usuario")
            .filter(id_desafio=desafio_id)
            .first()
        )

        if not desafio:
            raise Exception("La verificación solicitada no existe.")

        if desafio.utilizado:
            raise Exception("Esta verificación ya no está disponible.")

        if not desafio.usuario.estado_usuario.es_operativo:
            raise Exception("Usuario deshabilitado")

        ahora = timezone.now()
        cooldown = int(
            getattr(settings, "OTP_RESEND_SECONDS", 60)
        )
        max_reenvios = int(
            getattr(settings, "OTP_MAX_RESENDS", 3)
        )

        if desafio.reenvios >= max_reenvios:
            raise Exception(
                "Se alcanzó el límite de reenvíos. Inicie sesión nuevamente."
            )

        segundos_transcurridos = int(
            (ahora - desafio.fecha_ultimo_envio).total_seconds()
        )

        if segundos_transcurridos < cooldown:
            faltan = cooldown - segundos_transcurridos
            raise Exception(
                f"Espere {faltan} segundo(s) antes de solicitar otro código."
            )

        minutos_vigencia = int(
            getattr(settings, "OTP_CODE_MINUTES", 5)
        )
        codigo = generar_codigo_otp()

        desafio.codigo_hash = hash_codigo_otp(
            desafio.id_desafio,
            codigo,
        )
        desafio.fecha_expiracion = ahora + timedelta(
            minutes=minutos_vigencia
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

        try:
            EmailService().enviar_codigo_doble_factor(
                usuario=desafio.usuario,
                codigo=codigo,
                minutos_vigencia=minutos_vigencia,
            )
        except Exception as error:
            raise Exception(
                "No fue posible reenviar el código al correo institucional."
            ) from error

        return {
            "desafio_id": str(desafio.id_desafio),
            "correo_enmascarado": enmascarar_correo(desafio.usuario.correo),
            "expira_en_segundos": minutos_vigencia * 60,
            "reenvio_disponible_en": cooldown,
            "reenvios_restantes": max_reenvios - desafio.reenvios,
            "mensaje": "Se envió un nuevo código de verificación.",
        }
