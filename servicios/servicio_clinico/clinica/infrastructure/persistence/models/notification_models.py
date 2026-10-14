"""Avisos clínicos internos, sin datos personales del paciente."""
import uuid
from django.db import models
from .case_models import CasoClinico, HistorialGestionCaso


class NotificacionClinica(models.Model):
    id_notificacion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    destinatario_uuid = models.UUIDField()
    caso = models.ForeignKey(CasoClinico, on_delete=models.CASCADE,
                             db_column="id_caso", related_name="notificaciones")
    evento_gestion = models.OneToOneField(
        HistorialGestionCaso, on_delete=models.CASCADE,
        db_column="id_gestion", related_name="notificacion", null=True, blank=True
    )
    evento_ia_uuid = models.UUIDField(unique=True, null=True, blank=True)
    tipo = models.CharField(max_length=24)
    titulo = models.CharField(max_length=100)
    mensaje = models.CharField(max_length=255)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "notificaciones_clinicas"
        app_label = "clinica"
        indexes = [
            models.Index(fields=["destinatario_uuid", "fecha_creacion"], name="idx_notif_dest_fecha"),
            models.Index(fields=["destinatario_uuid", "fecha_lectura"], name="idx_notif_dest_lect"),
        ]
