import uuid

from django.db import models
from django.db.models import Q


# ==========================================================
# DATASETS
# ==========================================================

class Dataset(models.Model):
    id_dataset = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    nombre = models.CharField(
        max_length=150,
        unique=True,
    )

    descripcion = models.TextField(
        null=True,
        blank=True,
    )

    origen = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "datasets"

    def __str__(self):
        return self.nombre


class EstadoVersionDataset(models.Model):
    id_estado_version = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_version_dataset"

    def __str__(self):
        return self.nombre


class VersionDataset(models.Model):
    id_version_dataset = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="versiones",
        db_column="id_dataset",
    )

    estado_version = models.ForeignKey(
        EstadoVersionDataset,
        on_delete=models.PROTECT,
        related_name="versiones",
        db_column="id_estado_version",
    )

    numero_version = models.PositiveIntegerField()

    cantidad_imagenes = models.PositiveIntegerField(default=0)

    hash_manifiesto = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "versiones_dataset"

        constraints = [
            models.UniqueConstraint(
                fields=["dataset", "numero_version"],
                name="uq_dataset_version",
            ),
        ]

        indexes = [
            models.Index(
                fields=["dataset", "estado_version"],
                name="idx_dataset_estado",
            ),
        ]

    def __str__(self):
        return f"{self.dataset.nombre} v{self.numero_version}"


class ClaseDataset(models.Model):
    id_clase = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=50,
        unique=True,
    )

    nombre = models.CharField(max_length=100)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "clases_dataset"

    def __str__(self):
        return self.nombre


class ParticionDataset(models.Model):
    id_particion = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=60)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "particiones_dataset"

    def __str__(self):
        return self.nombre


class ImagenDataset(models.Model):
    id_imagen_dataset = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    version_dataset = models.ForeignKey(
        VersionDataset,
        on_delete=models.CASCADE,
        related_name="imagenes",
        db_column="id_version_dataset",
    )

    clase = models.ForeignKey(
        ClaseDataset,
        on_delete=models.PROTECT,
        related_name="imagenes",
        db_column="id_clase",
    )

    particion = models.ForeignKey(
        ParticionDataset,
        on_delete=models.PROTECT,
        related_name="imagenes",
        db_column="id_particion",
    )

    referencia_imagen = models.CharField(max_length=500)

    hash_imagen = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    paciente_anonimo_hash = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "imagenes_dataset"

        constraints = [
            models.UniqueConstraint(
                fields=["version_dataset", "referencia_imagen"],
                name="uq_version_imagen",
            ),
        ]

        indexes = [
            models.Index(
                fields=["version_dataset", "particion"],
                name="idx_img_version_part",
            ),
            models.Index(
                fields=["clase", "particion"],
                name="idx_img_clase_part",
            ),
        ]

    def __str__(self):
        return self.referencia_imagen


# ==========================================================
# PREPROCESAMIENTO
# ==========================================================

class ConfiguracionPreprocesamiento(models.Model):
    id_config_preproc = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    nombre = models.CharField(max_length=120)

    ancho_objetivo = models.PositiveIntegerField()

    alto_objetivo = models.PositiveIntegerField()

    normalizacion = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )

    aumento_datos = models.BooleanField(default=False)

    configuracion_aumento = models.JSONField(
        null=True,
        blank=True,
    )

    descripcion = models.TextField(
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "config_preprocesamiento"

        constraints = [
            models.CheckConstraint(
                condition=Q(ancho_objetivo__gt=0),
                name="ck_preproc_ancho",
            ),
            models.CheckConstraint(
                condition=Q(alto_objetivo__gt=0),
                name="ck_preproc_alto",
            ),
        ]

    def __str__(self):
        return self.nombre


# ==========================================================
# ENTRENAMIENTO
# ==========================================================

class EstadoExperimento(models.Model):
    id_estado_experimento = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_experimento"

    def __str__(self):
        return self.nombre


class Experimento(models.Model):
    id_experimento = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    version_dataset = models.ForeignKey(
        VersionDataset,
        on_delete=models.PROTECT,
        related_name="experimentos",
        db_column="id_version_dataset",
    )

    config_preprocesamiento = models.ForeignKey(
        ConfiguracionPreprocesamiento,
        on_delete=models.PROTECT,
        related_name="experimentos",
        db_column="id_config_preproc",
    )

    estado_experimento = models.ForeignKey(
        EstadoExperimento,
        on_delete=models.PROTECT,
        related_name="experimentos",
        db_column="id_estado_experimento",
    )

    nombre = models.CharField(max_length=150)

    descripcion = models.TextField(
        null=True,
        blank=True,
    )

    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
    )

    creado_por_uuid = models.UUIDField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "experimentos"

        indexes = [
            models.Index(
                fields=["version_dataset", "estado_experimento"],
                name="idx_exp_dataset_estado",
            ),
        ]

    def __str__(self):
        return self.nombre


class ArquitecturaModelo(models.Model):
    id_arquitectura = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=50,
        unique=True,
    )

    nombre = models.CharField(max_length=100)

    descripcion = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "arquitecturas_modelo"

    def __str__(self):
        return self.nombre


class Optimizador(models.Model):
    id_optimizador = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "optimizadores"

    def __str__(self):
        return self.nombre


class ConfiguracionEntrenamiento(models.Model):
    id_config_entrenamiento = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    experimento = models.OneToOneField(
        Experimento,
        on_delete=models.CASCADE,
        related_name="configuracion_entrenamiento",
        db_column="id_experimento",
    )

    arquitectura = models.ForeignKey(
        ArquitecturaModelo,
        on_delete=models.PROTECT,
        related_name="configuraciones",
        db_column="id_arquitectura",
    )

    optimizador = models.ForeignKey(
        Optimizador,
        on_delete=models.PROTECT,
        related_name="configuraciones",
        db_column="id_optimizador",
    )

    learning_rate = models.DecimalField(
        max_digits=12,
        decimal_places=10,
    )

    batch_size = models.PositiveIntegerField()

    epochs = models.PositiveIntegerField()

    fine_tuning = models.BooleanField(default=False)

    capas_descongeladas = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    seed = models.IntegerField(
        null=True,
        blank=True,
    )

    parametros_adicionales = models.JSONField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "config_entrenamiento"

        constraints = [
            models.CheckConstraint(
                condition=Q(learning_rate__gt=0),
                name="ck_train_lr",
            ),
            models.CheckConstraint(
                condition=Q(batch_size__gt=0),
                name="ck_train_batch",
            ),
            models.CheckConstraint(
                condition=Q(epochs__gt=0),
                name="ck_train_epochs",
            ),
        ]

    def __str__(self):
        return str(self.id_config_entrenamiento)


# ==========================================================
# MÉTRICAS
# ==========================================================

class TipoMetrica(models.Model):
    id_tipo_metrica = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=40,
        unique=True,
    )

    nombre = models.CharField(max_length=100)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "tipos_metrica"

    def __str__(self):
        return self.nombre


class MetricaExperimento(models.Model):
    id_metrica_experimento = models.BigAutoField(primary_key=True)

    experimento = models.ForeignKey(
        Experimento,
        on_delete=models.CASCADE,
        related_name="metricas",
        db_column="id_experimento",
    )

    tipo_metrica = models.ForeignKey(
        TipoMetrica,
        on_delete=models.PROTECT,
        related_name="metricas",
        db_column="id_tipo_metrica",
    )

    particion = models.ForeignKey(
        ParticionDataset,
        on_delete=models.PROTECT,
        related_name="metricas",
        db_column="id_particion",
    )

    valor = models.DecimalField(
        max_digits=12,
        decimal_places=8,
    )

    epoch = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "metricas_experimento"

        indexes = [
            models.Index(
                fields=["experimento", "tipo_metrica"],
                name="idx_metrica_exp_tipo",
            ),
        ]

    def __str__(self):
        return f"{self.tipo_metrica.codigo}: {self.valor}"


# ==========================================================
# MODELOS ENTRENADOS
# ==========================================================

class EstadoModelo(models.Model):
    id_estado_modelo = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_modelo"

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    id_modelo = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    experimento = models.ForeignKey(
        Experimento,
        on_delete=models.PROTECT,
        related_name="modelos",
        db_column="id_experimento",
    )

    estado_modelo = models.ForeignKey(
        EstadoModelo,
        on_delete=models.PROTECT,
        related_name="modelos",
        db_column="id_estado_modelo",
    )

    nombre = models.CharField(max_length=150)

    version = models.PositiveIntegerField()

    ruta_modelo = models.CharField(max_length=500)

    hash_modelo = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "modelos"

        constraints = [
            models.UniqueConstraint(
                fields=["nombre", "version"],
                name="uq_modelo_version",
            ),
        ]

        indexes = [
            models.Index(
                fields=["estado_modelo"],
                name="idx_modelo_estado",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} v{self.version}"


class UmbralModelo(models.Model):
    id_umbral = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.CASCADE,
        related_name="umbrales",
        db_column="id_modelo",
    )

    clase = models.ForeignKey(
        ClaseDataset,
        on_delete=models.PROTECT,
        related_name="umbrales",
        db_column="id_clase",
    )

    valor_umbral = models.DecimalField(
        max_digits=6,
        decimal_places=5,
    )

    fecha_configuracion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "umbrales_modelo"

        constraints = [
            models.UniqueConstraint(
                fields=["modelo", "clase"],
                name="uq_umbral_modelo_clase",
            ),
            models.CheckConstraint(
                condition=Q(valor_umbral__gte=0)
                & Q(valor_umbral__lte=1),
                name="ck_umbral_rango",
            ),
        ]

    def __str__(self):
        return str(self.valor_umbral)


# ==========================================================
# INFERENCIA
# ==========================================================

class EstadoInferencia(models.Model):
    id_estado_inferencia = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_inferencia"

    def __str__(self):
        return self.nombre


class SolicitudInferencia(models.Model):
    id_solicitud_inferencia = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    modelo = models.ForeignKey(
        Modelo,
        on_delete=models.PROTECT,
        related_name="solicitudes_inferencia",
        db_column="id_modelo",
    )

    estado_inferencia = models.ForeignKey(
        EstadoInferencia,
        on_delete=models.PROTECT,
        related_name="solicitudes",
        db_column="id_estado_inferencia",
    )

    radiografia_uuid = models.UUIDField()

    caso_uuid = models.UUIDField()

    solicitado_por_uuid = models.UUIDField(
        null=True,
        blank=True,
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    fecha_inicio = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
    )

    numero_intentos = models.PositiveSmallIntegerField(default=0)

    mensaje_error = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "solicitudes_inferencia"

        indexes = [
            models.Index(
                fields=["estado_inferencia", "fecha_solicitud"],
                name="idx_inf_estado_fecha",
            ),
            models.Index(
                fields=["radiografia_uuid"],
                name="idx_inf_radiografia",
            ),
            models.Index(
                fields=["caso_uuid"],
                name="idx_inf_caso",
            ),
        ]

    def __str__(self):
        return str(self.id_solicitud_inferencia)


class ResultadoInferencia(models.Model):
    id_resultado_inferencia = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    solicitud = models.OneToOneField(
        SolicitudInferencia,
        on_delete=models.CASCADE,
        related_name="resultado",
        db_column="id_solicitud_inferencia",
    )

    clase_predicha = models.ForeignKey(
        ClaseDataset,
        on_delete=models.PROTECT,
        related_name="resultados",
        db_column="id_clase_predicha",
    )

    probabilidad = models.DecimalField(
        max_digits=8,
        decimal_places=7,
    )

    tiempo_procesamiento_ms = models.PositiveIntegerField(
        null=True,
        blank=True,
    )

    fecha_resultado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resultados_inferencia"

        constraints = [
            models.CheckConstraint(
                condition=Q(probabilidad__gte=0)
                & Q(probabilidad__lte=1),
                name="ck_resultado_prob",
            ),
        ]

    def __str__(self):
        return str(self.id_resultado_inferencia)


# ==========================================================
# EXPLICABILIDAD / GRAD-CAM
# ==========================================================

class TipoArtefacto(models.Model):
    id_tipo_artefacto = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "tipos_artefacto"

    def __str__(self):
        return self.nombre


class ArtefactoExplicabilidad(models.Model):
    id_artefacto = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    resultado = models.ForeignKey(
        ResultadoInferencia,
        on_delete=models.CASCADE,
        related_name="artefactos",
        db_column="id_resultado_inferencia",
    )

    tipo_artefacto = models.ForeignKey(
        TipoArtefacto,
        on_delete=models.PROTECT,
        related_name="artefactos",
        db_column="id_tipo_artefacto",
    )

    ruta_archivo = models.CharField(max_length=500)

    hash_archivo = models.CharField(
        max_length=64,
        null=True,
        blank=True,
    )

    fecha_generacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "artefactos_explicabilidad"

        constraints = [
            models.UniqueConstraint(
                fields=["resultado", "tipo_artefacto"],
                name="uq_resultado_artefacto",
            ),
        ]

    def __str__(self):
        return str(self.id_artefacto)