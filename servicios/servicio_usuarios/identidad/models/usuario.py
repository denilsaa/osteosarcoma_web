import uuid

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


# ==========================================================
# ESTADOS DE USUARIO
# ==========================================================


class EstadoUsuario(models.Model):

    id_estado_usuario = models.SmallAutoField(
        primary_key=True
    )

    codigo = models.CharField(
        max_length=30,
        unique=True
    )

    nombre = models.CharField(
        max_length=60
    )

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    es_operativo = models.BooleanField(
        default=True
    )

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "estados_usuario"

        ordering = [
            "id_estado_usuario"
        ]

    def __str__(self):

        return self.nombre


# ==========================================================
# USUARIO
# ==========================================================


class Usuario(models.Model):

    # ======================================================
    # DEPARTAMENTOS DE EXPEDICIÓN DEL CI
    # ======================================================

    EXPEDIDO_LA_PAZ = "LP"
    EXPEDIDO_COCHABAMBA = "CB"
    EXPEDIDO_SANTA_CRUZ = "SC"
    EXPEDIDO_ORURO = "OR"
    EXPEDIDO_POTOSI = "PT"
    EXPEDIDO_CHUQUISACA = "CH"
    EXPEDIDO_TARIJA = "TJ"
    EXPEDIDO_BENI = "BE"
    EXPEDIDO_PANDO = "PD"

    EXPEDIDO_CHOICES = [

        (
            EXPEDIDO_LA_PAZ,
            "La Paz"
        ),

        (
            EXPEDIDO_COCHABAMBA,
            "Cochabamba"
        ),

        (
            EXPEDIDO_SANTA_CRUZ,
            "Santa Cruz"
        ),

        (
            EXPEDIDO_ORURO,
            "Oruro"
        ),

        (
            EXPEDIDO_POTOSI,
            "Potosí"
        ),

        (
            EXPEDIDO_CHUQUISACA,
            "Chuquisaca"
        ),

        (
            EXPEDIDO_TARIJA,
            "Tarija"
        ),

        (
            EXPEDIDO_BENI,
            "Beni"
        ),

        (
            EXPEDIDO_PANDO,
            "Pando"
        ),

    ]

    # ======================================================
    # IDENTIFICADOR
    # ======================================================

    id_usuario = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # ======================================================
    # ESTADO
    # ======================================================

    estado_usuario = models.ForeignKey(
        EstadoUsuario,
        on_delete=models.PROTECT,
        related_name="usuarios",
        db_column="id_estado_usuario",
    )

    # ======================================================
    # DATOS PERSONALES
    # ======================================================

    nombres = models.CharField(
        max_length=100
    )

    apellido_paterno = models.CharField(
        max_length=80
    )

    apellido_materno = models.CharField(
        max_length=80,
        null=True,
        blank=True,
    )

    telefono = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )

    # ======================================================
    # DOCUMENTO DE IDENTIDAD
    # ======================================================
    #
    # Se dejan como nullable temporalmente para no romper
    # usuarios antiguos que ya existen en la base de datos.
    #
    # En el nuevo registro de oncólogos serán obligatorios
    # desde serializer y backend.
    # ======================================================

    ci_numero = models.CharField(
        max_length=20,
        null=True,
        blank=True,
    )

    ci_complemento = models.CharField(
        max_length=10,
        null=True,
        blank=True,
    )

    ci_expedido = models.CharField(
        max_length=2,
        choices=EXPEDIDO_CHOICES,
        null=True,
        blank=True,
    )

    # ======================================================
    # ACCESO
    # ======================================================

    correo = models.CharField(
        max_length=150
    )

    nombre_usuario = models.CharField(
        max_length=80
    )

    # ======================================================
    # FECHAS
    # ======================================================

    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )

    fecha_actualizacion = models.DateTimeField(
        auto_now=True
    )

    ultimo_acceso = models.DateTimeField(
        null=True,
        blank=True
    )

    # ======================================================
    # CONFIGURACIÓN DE TABLA
    # ======================================================

    class Meta:

        db_table = "usuarios"

        constraints = [

            # ==================================================
            # CORREO ÚNICO SIN DIFERENCIAR MAYÚSCULAS
            # ==================================================

            models.UniqueConstraint(
                Lower("correo"),
                name="uq_usuarios_correo_lower",
            ),

            # ==================================================
            # NOMBRE DE USUARIO ÚNICO
            # ==================================================

            models.UniqueConstraint(
                Lower("nombre_usuario"),
                name="uq_usuarios_nombre_usuario_lower",
            ),

            # ==================================================
            # CI + COMPLEMENTO ÚNICO
            # ==================================================
            #
            # IMPORTANTE:
            #
            # nulls_distinct=False hace que PostgreSQL considere
            # NULL como un valor comparable dentro de la
            # restricción única.
            #
            # Por ejemplo:
            #
            # 8459217 + NULL
            # no podrá repetirse.
            #
            # Pero:
            #
            # 8459217 + 1A
            # 8459217 + 2B
            #
            # sí son combinaciones diferentes.
            # ==================================================

            models.UniqueConstraint(
                fields=[
                    "ci_numero",
                    "ci_complemento",
                ],
                condition=Q(
                    ci_numero__isnull=False,
                ),
                nulls_distinct=False,
                name="uq_usuarios_ci_complemento",
            ),

            # ==================================================
            # CORREO NO VACÍO
            # ==================================================

            models.CheckConstraint(
                condition=~Q(
                    correo=""
                ),
                name="ck_usuarios_correo_no_vacio",
            ),

            # ==================================================
            # NOMBRE DE USUARIO NO VACÍO
            # ==================================================

            models.CheckConstraint(
                condition=~Q(
                    nombre_usuario=""
                ),
                name="ck_usuarios_nombre_usuario_no_vacio",
            ),

        ]

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return self.nombre_usuario

    # ======================================================
    # NOMBRE COMPLETO
    # ======================================================

    @property
    def nombre_completo(self):

        partes = [

            self.nombres,

            self.apellido_paterno,

            self.apellido_materno,

        ]

        return " ".join(
            str(parte).strip()
            for parte in partes
            if parte
            and str(parte).strip()
        )

    # ======================================================
    # CI COMPLETO
    # ======================================================

    @property
    def ci_completo(self):

        if not self.ci_numero:

            return None

        documento = str(
            self.ci_numero
        ).strip()

        if self.ci_complemento:

            documento = (
                f"{documento}-"
                f"{str(self.ci_complemento).strip()}"
            )

        if self.ci_expedido:

            documento = (
                f"{documento} "
                f"{self.ci_expedido}"
            )

        return documento

    # ======================================================
    # COMPATIBILIDAD DJANGO REST FRAMEWORK
    # ======================================================

    @property
    def is_authenticated(self):

        """
        DRF necesita esta propiedad
        para IsAuthenticated.

        El proyecto utiliza un modelo Usuario propio
        junto con autenticación JWT.
        """

        return True

    @property
    def is_anonymous(self):

        return False


# ==========================================================
# PERFIL PROFESIONAL
# ==========================================================


class PerfilProfesional(models.Model):

    # ======================================================
    # IDENTIFICADOR
    # ======================================================

    id_perfil_profesional = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    # ======================================================
    # USUARIO
    # ======================================================

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_profesional",
        db_column="id_usuario",
    )

    # ======================================================
    # MATRÍCULA PROFESIONAL
    # ======================================================

    matricula_profesional = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )

    # ======================================================
    # ESPECIALIDAD
    # ======================================================

    especialidad = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )

    # ======================================================
    # SUBESPECIALIDAD
    # ======================================================

    subespecialidad = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )

    # ======================================================
    # ÁREA CLÍNICA
    # ======================================================
    #
    # Ejemplo:
    #
    # Tumores óseos / Osteosarcoma
    #
    # Osteosarcoma no será tratado como subespecialidad,
    # sino como área clínica de enfoque.
    # ======================================================

    area_clinica = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )

    # ======================================================
    # CARGO
    # ======================================================
    #
    # El rol real del usuario se controla desde UsuarioRol.
    #
    # Este campo queda únicamente como descripción
    # profesional/institucional.
    # ======================================================

    cargo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )

    # ======================================================
    # TELÉFONO INSTITUCIONAL
    # ======================================================

    telefono_institucional = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )

    # ======================================================
    # FECHA
    # ======================================================

    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:

        db_table = "perfiles_profesionales"

    # ======================================================
    # REPRESENTACIÓN
    # ======================================================

    def __str__(self):

        return f"Perfil de {self.usuario}"