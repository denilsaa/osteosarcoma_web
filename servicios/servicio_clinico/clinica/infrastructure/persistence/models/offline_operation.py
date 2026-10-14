"""Clave de idempotencia para altas diferidas. Nunca guarda PHI en este registro."""
import uuid
from django.db import models
from .patient_models import Paciente


class AltaPacienteOffline(models.Model):
    operacion_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_uuid = models.UUIDField()
    payload_sha256 = models.CharField(max_length=64)
    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, db_column="id_paciente")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "altas_pacientes_offline"
        app_label = "clinica"
