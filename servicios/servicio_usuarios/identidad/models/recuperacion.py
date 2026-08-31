from django.db import models

from .usuario import Usuario



class EstadoRecuperacion(models.Model):

    id_estado_recuperacion = models.SmallAutoField(
        primary_key=True
    )


    codigo = models.CharField(
        max_length=30,
        unique=True
    )


    nombre = models.CharField(
        max_length=80
    )


    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )


    class Meta:

        db_table = "estados_recuperacion"


    def __str__(self):

        return self.nombre





class SolicitudRecuperacion(models.Model):

    id_solicitud = models.UUIDField(
        primary_key=True,
        editable=False
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="solicitudes_recuperacion",
        db_column="id_usuario"
    )


    estado = models.ForeignKey(
        EstadoRecuperacion,
        on_delete=models.PROTECT,
        related_name="solicitudes",
        db_column="id_estado_recuperacion"
    )


    token_recuperacion = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
    )


    fecha_solicitud = models.DateTimeField(
        auto_now_add=True
    )


    fecha_expiracion = models.DateTimeField()


    fecha_resolucion = models.DateTimeField(
        null=True,
        blank=True
    )


    class Meta:

        db_table = "solicitudes_recuperacion"



    def __str__(self):

        return f"Solicitud {self.id_solicitud}"





class ResolucionRecuperacion(models.Model):

    id_resolucion = models.UUIDField(
        primary_key=True,
        editable=False
    )


    solicitud = models.OneToOneField(
        SolicitudRecuperacion,
        on_delete=models.CASCADE,
        related_name="resolucion",
        db_column="id_solicitud"
    )


    aprobado = models.BooleanField(
        default=False
    )


    revisado_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="recuperaciones_revisadas",
        db_column="id_usuario_revisor"
    )


    comentario = models.TextField(
        null=True,
        blank=True
    )


    fecha_revision = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        db_table = "resoluciones_recuperacion"



    def __str__(self):

        return f"Resolución {self.id_resolucion}"