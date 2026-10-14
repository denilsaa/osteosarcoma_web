"""Recibo idempotente de creación de caso en contingencia (sin PHI duplicada)."""
import uuid
from django.db import models
from .case_models import CasoClinico

class AltaCasoOffline(models.Model):
    operacion_uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor_uuid = models.UUIDField()
    payload_sha256 = models.CharField(max_length=64)
    caso = models.ForeignKey(CasoClinico, on_delete=models.PROTECT, db_column="id_caso")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "altas_casos_offline"
        app_label = "clinica"
