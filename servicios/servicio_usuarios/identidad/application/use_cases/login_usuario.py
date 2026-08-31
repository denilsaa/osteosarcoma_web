import hashlib
import hmac
import secrets
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from identidad.application.services.email_service import EmailService
from identidad.infrastructure.repositories.credencial_repository import (
    CredencialRepository,
)
from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)
from identidad.infrastructure.security.password_hasher import PasswordHasher
from identidad.models import DesafioSegundoFactor


def generar_codigo_otp():
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_codigo_otp(desafio_id, codigo):
    mensaje = f"{desafio_id}:{codigo}".encode("utf-8")
    secreto = settings.SECRET_KEY.encode("utf-8")
    return hmac.new(secreto, mensaje, hashlib.sha256).hexdigest()


def enmascarar_correo(correo):
    local, dominio = correo.split("@", 1)
    if len(local) <= 2:
        local_mascara = local[:1] + "•"
    else:
        local_mascara = local[0] + ("•" * min(len(local) - 1, 8))
    return f"{local_mascara}@{dominio}"


class LoginUseCase:
    """
    Primer factor de autenticación.

    Valida correo + contraseña, pero NO emite JWT.
    Si son correctos, crea un desafío OTP y lo envía al correo
    institucional registrado del usuario.
    """

    def __init__(self):
        self.usuario_repository = UsuarioRepository()
        self.credencial_repository = CredencialRepository()
        self.password_hasher = PasswordHasher()

    @transaction.atomic
    def ejecutar(
        self,
        correo,
        password,
        ip_origen=None,
        user_agent=None,
    ):
        usuario = self.usuario_repository.obtener_por_correo(correo)

        if not usuario:
            raise Exception("Credenciales inválidas")

        if not usuario.estado_usuario.es_operativo:
            raise Exception("Usuario deshabilitado")

        credencial = self.credencial_repository.obtener_por_usuario(usuario)
        if not credencial:
            raise Exception("Credencial no encontrada")

        ahora = timezone.now()

        if credencial.bloqueado_hasta and credencial.bloqueado_hasta > ahora:
            raise Exception("La cuenta se encuentra temporalmente bloqueada")

        password_correcto = self.password_hasher.verificar_password(
            password,
            credencial.password_hash,
        )

        if not password_correcto:
            max_intentos_password = int(
                getattr(settings, "LOGIN_MAX_FAILED_ATTEMPTS", 5)
            )
            minutos_bloqueo = int(
                getattr(settings, "LOGIN_LOCK_MINUTES", 15)
            )

            credencial.intentos_fallidos += 1

            if credencial.intentos_fallidos >= max_intentos_password:
                credencial.bloqueado_hasta = ahora + timedelta(
                    minutes=minutos_bloqueo
                )

            credencial.save(
                update_fields=[
                    "intentos_fallidos",
                    "bloqueado_hasta",
                    "fecha_actualizacion",
                ]
            )

            raise Exception("Credenciales inválidas")

        # Elimina desafíos anteriores no utilizados para que solo exista
        # un código activo por usuario.
        DesafioSegundoFactor.objects.filter(
            usuario=usuario,
            utilizado=False,
        ).delete()

        minutos_vigencia = int(
            getattr(settings, "OTP_CODE_MINUTES", 5)
        )

        codigo = generar_codigo_otp()

        desafio = DesafioSegundoFactor.objects.create(
            usuario=usuario,
            codigo_hash="PENDIENTE",
            fecha_expiracion=ahora + timedelta(minutes=minutos_vigencia),
            fecha_ultimo_envio=ahora,
            ip_origen=ip_origen,
            user_agent=user_agent,
        )

        desafio.codigo_hash = hash_codigo_otp(
            desafio.id_desafio,
            codigo,
        )
        desafio.save(update_fields=["codigo_hash"])

        try:
            EmailService().enviar_codigo_doble_factor(
                usuario=usuario,
                codigo=codigo,
                minutos_vigencia=minutos_vigencia,
            )
        except Exception as error:
            raise Exception(
                "No fue posible enviar el código de verificación al correo institucional."
            ) from error

        return {
            "requiere_segundo_factor": True,
            "desafio_id": str(desafio.id_desafio),
            "correo_enmascarado": enmascarar_correo(usuario.correo),
            "expira_en_segundos": minutos_vigencia * 60,
            "reenvio_disponible_en": int(
                getattr(settings, "OTP_RESEND_SECONDS", 60)
            ),
            "mensaje": (
                "Credenciales correctas. Ingrese el código enviado "
                "a su correo institucional para completar el acceso."
            ),
        }
