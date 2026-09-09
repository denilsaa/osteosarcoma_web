import uuid

from django.db import models

from .catalog_models import (
    Sexo,
    TipoContacto,
    TipoDocumento,
)


# ==========================================================
# PACIENTE
# ==========================================================


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

    nombres = models.CharField(
        max_length=100,
    )

    apellido_paterno = models.CharField(
        max_length=80,
    )

    apellido_materno = models.CharField(
        max_length=80,
        null=True,
        blank=True,
    )

    fecha_nacimiento = models.DateField()

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    activo = models.BooleanField(
        default=True,
    )

    class Meta:

        db_table = "pacientes"

        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "apellido_paterno",
                    "nombres",
                ],
                name="idx_paciente_nombre",
            ),
        ]

    def __str__(self):

        partes = [
            self.nombres,
            self.apellido_paterno,
            self.apellido_materno,
        ]

        return " ".join(
            parte
            for parte in partes
            if parte
        )


# ==========================================================
# DOCUMENTO DEL PACIENTE
# ==========================================================


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

    numero_documento = models.CharField(
        max_length=50,
    )

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

        app_label = "clinica"

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "tipo_documento",
                    "numero_documento",
                ],
                name="uq_doc_tipo_numero",
            ),
        ]

    def __str__(self):

        return self.numero_documento


# ==========================================================
# CONTACTOS DEL PACIENTE
# ==========================================================


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

    valor = models.CharField(
        max_length=150,
    )

    principal = models.BooleanField(
        default=False,
    )

    class Meta:

        db_table = "contactos_paciente"

        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "paciente",
                    "principal",
                ],
                name="idx_contacto_principal",
            ),
        ]

    def __str__(self):

        return self.valor


# ==========================================================
# CONTACTOS DE EMERGENCIA
# ==========================================================


class ContactoEmergenciaPaciente(models.Model):
    """
    Persona de contacto en caso de emergencia.

    Se almacena separada de ContactoPaciente porque
    representa a un tercero relacionado con el paciente.

    Un paciente puede tener más de un contacto
    de emergencia en el futuro.
    """

    id_contacto_emergencia = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    paciente = models.ForeignKey(
        Paciente,
        on_delete=models.CASCADE,
        related_name="contactos_emergencia",
        db_column="id_paciente",
    )

    nombre_completo = models.CharField(
        max_length=180,
    )

    parentesco = models.CharField(
        max_length=80,
    )

    telefono = models.CharField(
        max_length=25,
    )

    correo = models.EmailField(
        max_length=150,
        null=True,
        blank=True,
    )

    principal = models.BooleanField(
        default=True,
    )

    fecha_registro = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:

        db_table = "contactos_emergencia_paciente"

        app_label = "clinica"

        indexes = [
            models.Index(
                fields=[
                    "paciente",
                    "principal",
                ],
                name="idx_contacto_emergencia",
            ),
        ]

    def __str__(self):

        return (
            f"{self.nombre_completo} "
            f"({self.parentesco})"
        )