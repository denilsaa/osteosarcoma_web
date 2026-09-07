import uuid

from django.db import models

from .catalog_models import (
    CatalogoSigno,
    CatalogoSintoma,
    CriterioValoracion,
    EstadoCaso,
    NivelIntensidad,
    PrioridadCaso,
    TipoAntecedente,
)
from .patient_models import Paciente


class CasoClinico(models.Model):
    id_caso = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.PROTECT,
        related_name="casos_clinicos",
        db_column="id_paciente",
    )

    estado_caso = models.ForeignKey(
        EstadoCaso,
        on_delete=models.PROTECT,
        related_name="casos",
        db_column="id_estado_caso",
    )

    prioridad = models.ForeignKey(
        PrioridadCaso,
        on_delete=models.PROTECT,
        related_name="casos",
        db_column="id_prioridad",
    )

    codigo_caso = models.CharField(
        max_length=50,
        unique=True,
    )

    oncologo_responsable_uuid = (
        models.UUIDField(
            null=True,
            blank=True,
        )
    )

    fecha_apertura = models.DateTimeField(
        auto_now_add=True
    )

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
    )

    motivo_consulta = models.TextField()

    observacion_general = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "casos_clinicos"
        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "paciente",
                    "fecha_apertura",
                ],
                name="idx_caso_paciente_fecha",
            ),

            models.Index(
                fields=[
                    "estado_caso",
                    "prioridad",
                ],
                name="idx_caso_estado_prior",
            ),

            models.Index(
                fields=[
                    "oncologo_responsable_uuid",
                ],
                name="idx_caso_oncologo",
            ),
        ]

    def __str__(self):
        return self.codigo_caso


class HistorialEstadoCaso(models.Model):
    id_historial = models.BigAutoField(
        primary_key=True
    )

    caso = models.ForeignKey(
        CasoClinico,
        on_delete=models.CASCADE,
        related_name="historial_estados",
        db_column="id_caso",
    )

    estado_anterior = models.ForeignKey(
        EstadoCaso,
        on_delete=models.PROTECT,
        related_name=
            "historial_como_anterior",
        db_column=
            "id_estado_anterior",
        null=True,
        blank=True,
    )

    estado_nuevo = models.ForeignKey(
        EstadoCaso,
        on_delete=models.PROTECT,
        related_name=
            "historial_como_nuevo",
        db_column=
            "id_estado_nuevo",
    )

    usuario_uuid = models.UUIDField()

    fecha_cambio = models.DateTimeField(
        auto_now_add=True
    )

    observacion = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "historial_estado_caso"
        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "caso",
                    "fecha_cambio",
                ],
                name="idx_hist_caso_fecha",
            ),
        ]

    def __str__(self):
        return (
            f"{self.caso.codigo_caso} - "
            f"{self.estado_nuevo.codigo}"
        )


class AntecedenteClinico(models.Model):
    id_antecedente = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="antecedentes",
        db_column="id_paciente",
    )

    tipo_antecedente = models.ForeignKey(
        TipoAntecedente,
        on_delete=models.PROTECT,
        related_name="antecedentes",
        db_column="id_tipo_antecedente",
    )

    descripcion = models.TextField()

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    vigente = models.BooleanField(
        default=True
    )

    class Meta:
        db_table = "antecedentes_clinicos"
        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "paciente",
                    "tipo_antecedente",
                ],
                name="idx_ant_paciente_tipo",
            ),
        ]

    def __str__(self):
        return str(
            self.id_antecedente
        )


class CasoSintoma(models.Model):
    id_caso_sintoma = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    caso = models.ForeignKey(
        CasoClinico,
        on_delete=models.CASCADE,
        related_name="sintomas",
        db_column="id_caso",
    )

    sintoma = models.ForeignKey(
        CatalogoSintoma,
        on_delete=models.PROTECT,
        related_name="casos",
        db_column="id_sintoma",
    )

    intensidad = models.ForeignKey(
        NivelIntensidad,
        on_delete=models.PROTECT,
        related_name="sintomas_caso",
        db_column="id_nivel_intensidad",
        null=True,
        blank=True,
    )

    fecha_inicio = models.DateField(
        null=True,
        blank=True,
    )

    observacion = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "caso_sintoma"
        app_label = "clinica"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "caso",
                    "sintoma",
                ],
                name="uq_caso_sintoma",
            ),
        ]

    def __str__(self):
        return (
            f"{self.caso.codigo_caso} - "
            f"{self.sintoma.nombre}"
        )


class CasoSigno(models.Model):
    id_caso_signo = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    caso = models.ForeignKey(
        CasoClinico,
        on_delete=models.CASCADE,
        related_name="signos",
        db_column="id_caso",
    )

    signo = models.ForeignKey(
        CatalogoSigno,
        on_delete=models.PROTECT,
        related_name="casos",
        db_column="id_signo",
    )

    descripcion_hallazgo = (
        models.TextField(
            null=True,
            blank=True,
        )
    )

    fecha_observacion = (
        models.DateTimeField(
            auto_now_add=True
        )
    )

    observado_por_uuid = (
        models.UUIDField()
    )

    class Meta:
        db_table = "caso_signo"
        app_label = "clinica"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "caso",
                    "signo",
                ],
                name="uq_caso_signo",
            ),
        ]

    def __str__(self):
        return (
            f"{self.caso.codigo_caso} - "
            f"{self.signo.nombre}"
        )


class ValoracionEspecialista(
    models.Model
):
    id_valoracion = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    caso = models.ForeignKey(
        CasoClinico,
        on_delete=models.CASCADE,
        related_name="valoraciones",
        db_column="id_caso",
    )

    criterio = models.ForeignKey(
        CriterioValoracion,
        on_delete=models.PROTECT,
        related_name="valoraciones",
        db_column="id_criterio",
    )

    oncologo_uuid = models.UUIDField()

    resultado_ia_uuid = models.UUIDField(
        null=True,
        blank=True,
    )

    observacion = models.TextField(
        null=True,
        blank=True,
    )

    fecha_valoracion = (
        models.DateTimeField(
            auto_now_add=True
        )
    )

    class Meta:
        db_table = (
            "valoraciones_especialista"
        )
        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "caso",
                    "fecha_valoracion",
                ],
                name="idx_val_caso_fecha",
            ),
        ]

    def __str__(self):
        return str(
            self.id_valoracion
        )