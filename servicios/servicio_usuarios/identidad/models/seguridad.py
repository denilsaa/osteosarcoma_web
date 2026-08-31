import uuid

from django.db import models

from .usuario import Usuario


class Credencial(models.Model):

    id_credencial = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )


    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="credencial",
        db_column="id_usuario",
    )


    password_hash = models.CharField(
        max_length=255
    )


    debe_cambiar_password = models.BooleanField(
        default=False
    )


    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0
    )


    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
    )


    fecha_ultimo_cambio = models.DateTimeField(
        auto_now_add=True
    )


    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )


    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )


    class Meta:

        db_table = "credenciales"


    def __str__(self):

        return f"Credencial {self.usuario.nombre_usuario}"





class Sesion(models.Model):

    id_sesion = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="sesiones",
        db_column="id_usuario",
    )


    jti_refresh = models.UUIDField(
        unique=True
    )


    refresh_token_hash = models.CharField(
        max_length=255
    )


    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
    )


    user_agent = models.TextField(
        null=True,
        blank=True,
    )


    fecha_inicio = models.DateTimeField(
        auto_now_add=True
    )


    fecha_expiracion = models.DateTimeField()


    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
    )


    revocada = models.BooleanField(
        default=False
    )


    motivo_revocacion = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )


    class Meta:

        db_table = "sesiones"


        indexes = [

            models.Index(
                fields=[
                    "usuario"
                ],
                name="idx_sesion_usuario",
            ),


            models.Index(
                fields=[
                    "revocada",
                    "fecha_expiracion"
                ],
                name="idx_sesion_estado",
            ),

        ]


    def __str__(self):

        return str(self.id_sesion)

class DesafioSegundoFactor(models.Model):
    """Desafío temporal de verificación por correo antes de emitir JWT."""

    id_desafio = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="desafios_segundo_factor",
        db_column="id_usuario",
    )

    codigo_hash = models.CharField(
        max_length=64,
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
    )

    fecha_expiracion = models.DateTimeField()

    fecha_ultimo_envio = models.DateTimeField()

    intentos_fallidos = models.PositiveSmallIntegerField(
        default=0,
    )

    reenvios = models.PositiveSmallIntegerField(
        default=0,
    )

    utilizado = models.BooleanField(
        default=False,
    )

    fecha_utilizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "desafios_segundo_factor"
        indexes = [
            models.Index(
                fields=["usuario", "utilizado"],
                name="idx_2fa_usuario",
            ),
            models.Index(
                fields=["utilizado", "fecha_expiracion"],
                name="idx_2fa_estado",
            ),
        ]

    def __str__(self):
        return str(self.id_desafio)
