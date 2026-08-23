import uuid

from django.db import models
from django.db.models import Q


class Sexo(models.Model):
    id_sexo = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)

    class Meta:
        db_table = "sexos"

    def __str__(self):
        return self.nombre


class TipoDocumento(models.Model):
    id_tipo_documento = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)

    class Meta:
        db_table = "tipos_documento"

    def __str__(self):
        return self.nombre


class Paciente(models.Model):
    id_paciente = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    sexo = models.ForeignKey(
        Sexo,
        on_delete=models.PROTECT,
        related_name="pacientes",
        db_column="id_sexo",
    )

    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=80)
    apellido_materno = models.CharField(
        max_length=80,
        null=True,
        blank=True,
    )
    fecha_nacimiento = models.DateField()
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "pacientes"
        indexes = [
            models.Index(
                fields=["apellido_paterno", "nombres"],
                name="idx_paciente_nombre",
            ),
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno}"


class DocumentoPaciente(models.Model):
    id_documento = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="documentos",
        db_column="id_paciente",
    )

    tipo_documento = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name="documentos",
        db_column="id_tipo_documento",
    )

    numero_documento = models.CharField(max_length=50)
    complemento = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )
    expedido_en = models.CharField(
        max_length=40,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "documentos_paciente"
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="uq_doc_tipo_numero",
            ),
        ]

    def __str__(self):
        return self.numero_documento


class TipoContacto(models.Model):
    id_tipo_contacto = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=60)

    class Meta:
        db_table = "tipos_contacto"

    def __str__(self):
        return self.nombre


class ContactoPaciente(models.Model):
    id_contacto = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="contactos",
        db_column="id_paciente",
    )

    tipo_contacto = models.ForeignKey(
        TipoContacto,
        on_delete=models.PROTECT,
        related_name="contactos",
        db_column="id_tipo_contacto",
    )

    valor = models.CharField(max_length=150)
    principal = models.BooleanField(default=False)

    class Meta:
        db_table = "contactos_paciente"
        indexes = [
            models.Index(
                fields=["paciente", "principal"],
                name="idx_contacto_principal",
            ),
        ]

    def __str__(self):
        return self.valor


class EstadoCaso(models.Model):
    id_estado_caso = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_caso"

    def __str__(self):
        return self.nombre


class PrioridadCaso(models.Model):
    id_prioridad = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)
    nivel = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        db_table = "prioridades_caso"

    def __str__(self):
        return self.nombre


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

    oncologo_responsable_uuid = models.UUIDField(
        null=True,
        blank=True,
    )

    fecha_apertura = models.DateTimeField(auto_now_add=True)
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
        indexes = [
            models.Index(
                fields=["paciente", "fecha_apertura"],
                name="idx_caso_paciente_fecha",
            ),
            models.Index(
                fields=["estado_caso", "prioridad"],
                name="idx_caso_estado_prior",
            ),
            models.Index(
                fields=["oncologo_responsable_uuid"],
                name="idx_caso_oncologo",
            ),
        ]

    def __str__(self):
        return self.codigo_caso


class HistorialEstadoCaso(models.Model):
    id_historial = models.BigAutoField(primary_key=True)

    caso = models.ForeignKey(
        CasoClinico,
        on_delete=models.CASCADE,
        related_name="historial_estados",
        db_column="id_caso",
    )

    estado_anterior = models.ForeignKey(
        EstadoCaso,
        on_delete=models.PROTECT,
        related_name="historial_como_anterior",
        db_column="id_estado_anterior",
        null=True,
        blank=True,
    )

    estado_nuevo = models.ForeignKey(
        EstadoCaso,
        on_delete=models.PROTECT,
        related_name="historial_como_nuevo",
        db_column="id_estado_nuevo",
    )

    usuario_uuid = models.UUIDField()

    fecha_cambio = models.DateTimeField(auto_now_add=True)

    observacion = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "historial_estado_caso"
        indexes = [
            models.Index(
                fields=["caso", "fecha_cambio"],
                name="idx_hist_caso_fecha",
            ),
        ]

    def __str__(self):
        return f"{self.caso.codigo_caso} - {self.estado_nuevo.codigo}"


class TipoAntecedente(models.Model):
    id_tipo_antecedente = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "tipos_antecedente"

    def __str__(self):
        return self.nombre


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
    fecha_registro = models.DateTimeField(auto_now_add=True)
    vigente = models.BooleanField(default=True)

    class Meta:
        db_table = "antecedentes_clinicos"
        indexes = [
            models.Index(
                fields=["paciente", "tipo_antecedente"],
                name="idx_ant_paciente_tipo",
            ),
        ]

    def __str__(self):
        return str(self.id_antecedente)


class CatalogoSintoma(models.Model):
    id_sintoma = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalogo_sintomas"

    def __str__(self):
        return self.nombre


class NivelIntensidad(models.Model):
    id_nivel_intensidad = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=50)
    nivel = models.PositiveSmallIntegerField(unique=True)

    class Meta:
        db_table = "niveles_intensidad"

    def __str__(self):
        return self.nombre


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
        constraints = [
            models.UniqueConstraint(
                fields=["caso", "sintoma"],
                name="uq_caso_sintoma",
            ),
        ]

    def __str__(self):
        return f"{self.caso.codigo_caso} - {self.sintoma.nombre}"


class CatalogoSigno(models.Model):
    id_signo = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalogo_signos"

    def __str__(self):
        return self.nombre


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

    descripcion_hallazgo = models.TextField(
        null=True,
        blank=True,
    )

    fecha_observacion = models.DateTimeField(auto_now_add=True)

    observado_por_uuid = models.UUIDField()

    class Meta:
        db_table = "caso_signo"
        constraints = [
            models.UniqueConstraint(
                fields=["caso", "signo"],
                name="uq_caso_signo",
            ),
        ]

    def __str__(self):
        return f"{self.caso.codigo_caso} - {self.signo.nombre}"


class CriterioValoracion(models.Model):
    id_criterio = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=80)
    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "criterios_valoracion"

    def __str__(self):
        return self.nombre


class ValoracionEspecialista(models.Model):
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

    fecha_valoracion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "valoraciones_especialista"
        indexes = [
            models.Index(
                fields=["caso", "fecha_valoracion"],
                name="idx_val_caso_fecha",
            ),
        ]

    def __str__(self):
        return str(self.id_valoracion)