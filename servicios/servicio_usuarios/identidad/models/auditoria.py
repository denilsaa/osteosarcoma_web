from django.db import models

from .usuario import Usuario



class TipoEventoAcceso(models.Model):

    id_tipo_evento = models.SmallAutoField(
        primary_key=True
    )


    codigo = models.CharField(
        max_length=50,
        unique=True
    )


    nombre = models.CharField(
        max_length=100
    )


    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    class Meta:

        db_table = "tipos_evento_acceso"


    def __str__(self):

        return self.nombre





class EventoAcceso(models.Model):

    id_evento = models.UUIDField(
        primary_key=True,
        editable=False
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name="eventos_acceso",
        db_column="id_usuario",
        null=True,
        blank=True
    )


    tipo_evento = models.ForeignKey(
        TipoEventoAcceso,
        on_delete=models.PROTECT,
        related_name="eventos",
        db_column="id_tipo_evento"
    )


    fecha_evento = models.DateTimeField(
        auto_now_add=True
    )


    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True
    )


    user_agent = models.TextField(
        null=True,
        blank=True
    )


    detalle = models.JSONField(
        null=True,
        blank=True
    )


    class Meta:

        db_table = "eventos_acceso"



    def __str__(self):

        return f"{self.tipo_evento} - {self.fecha_evento}"