"""Asignaciones de pacientes a profesionales, con historial conservado."""
import uuid
from django.db import models
from django.db.models import Q
from django.utils import timezone
from .patient_models import Paciente


class AsignacionPaciente(models.Model):
    id_asignacion = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        Paciente, on_delete=models.PROTECT, related_name="asignaciones_clinicas",
        db_column="id_paciente",
    )
    oncologo_uuid = models.UUIDField()
    asignado_por_uuid = models.UUIDField()
    motivo = models.CharField(max_length=500)
    fecha_asignacion = models.DateTimeField(default=timezone.now)
    activa = models.BooleanField(default=True)
    fecha_revocacion = models.DateTimeField(null=True, blank=True)
    revocado_por_uuid = models.UUIDField(null=True, blank=True)
    motivo_revocacion = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        db_table = "asignaciones_pacientes"
        app_label = "clinica"
        constraints = [
            models.UniqueConstraint(
                fields=["paciente", "oncologo_uuid"],
                condition=Q(activa=True),
                name="uq_paciente_onco_activo",
            ),
        ]
        indexes = [
            models.Index(fields=["oncologo_uuid", "activa"], name="idx_asig_onco_activa"),
            models.Index(fields=["paciente", "activa"], name="idx_asig_paciente_act"),
        ]
