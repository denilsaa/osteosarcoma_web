from django.db import models


class Sexo(models.Model):
    id_sexo = models.SmallAutoField(
        primary_key=True
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
    )

    nombre = models.CharField(
        max_length=50
    )

    class Meta:
        db_table = "sexos"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class TipoDocumento(models.Model):
    id_tipo_documento = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(
        max_length=80
    )

    class Meta:
        db_table = "tipos_documento"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class TipoContacto(models.Model):
    id_tipo_contacto = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(
        max_length=60
    )

    class Meta:
        db_table = "tipos_contacto"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class EstadoCaso(models.Model):
    id_estado_caso = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(
        max_length=80
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "estados_caso"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class PrioridadCaso(models.Model):
    id_prioridad = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
    )

    nombre = models.CharField(
        max_length=50
    )

    nivel = models.PositiveSmallIntegerField(
        unique=True
    )

    class Meta:
        db_table = "prioridades_caso"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class TipoAntecedente(models.Model):
    id_tipo_antecedente = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=40,
        unique=True,
    )

    nombre = models.CharField(
        max_length=80
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "tipos_antecedente"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class CatalogoSintoma(models.Model):
    id_sintoma = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=50,
        unique=True,
    )

    nombre = models.CharField(
        max_length=100
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalogo_sintomas"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class NivelIntensidad(models.Model):
    id_nivel_intensidad = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=20,
        unique=True,
    )

    nombre = models.CharField(
        max_length=50
    )

    nivel = models.PositiveSmallIntegerField(
        unique=True
    )

    class Meta:
        db_table = "niveles_intensidad"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class CatalogoSigno(models.Model):
    id_signo = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=50,
        unique=True,
    )

    nombre = models.CharField(
        max_length=100
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "catalogo_signos"
        app_label = "clinica"

    def __str__(self):
        return self.nombre


class CriterioValoracion(models.Model):
    id_criterio = (
        models.SmallAutoField(
            primary_key=True
        )
    )

    codigo = models.CharField(
        max_length=30,
        unique=True,
    )

    nombre = models.CharField(
        max_length=80
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "criterios_valoracion"
        app_label = "clinica"

    def __str__(self):
        return self.nombre