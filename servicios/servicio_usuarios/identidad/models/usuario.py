import uuid

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower



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








class Usuario(models.Model):


    id_usuario = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )



    estado_usuario = models.ForeignKey(
        EstadoUsuario,
        on_delete=models.PROTECT,
        related_name="usuarios",
        db_column="id_estado_usuario",
    )



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



    correo = models.CharField(
        max_length=150
    )



    nombre_usuario = models.CharField(
        max_length=80
    )



    telefono = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )



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





    class Meta:

        db_table = "usuarios"



        constraints = [


            models.UniqueConstraint(
                Lower("correo"),
                name="uq_usuarios_correo_lower",
            ),



            models.UniqueConstraint(
                Lower("nombre_usuario"),
                name="uq_usuarios_nombre_usuario_lower",
            ),



            models.CheckConstraint(
                condition=~Q(correo=""),
                name="ck_usuarios_correo_no_vacio",
            ),



            models.CheckConstraint(
                condition=~Q(nombre_usuario=""),
                name="ck_usuarios_nombre_usuario_no_vacio",
            ),

        ]





    def __str__(self):

        return self.nombre_usuario




    # ======================================================
    # COMPATIBILIDAD DJANGO REST FRAMEWORK
    # ======================================================

    @property
    def is_authenticated(self):

        """
        DRF necesita esta propiedad
        para IsAuthenticated.
        Nuestro sistema usa Usuario propio,
        no Django User.
        """

        return True



    @property
    def is_anonymous(self):

        return False







class PerfilProfesional(models.Model):


    id_perfil_profesional = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )



    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="perfil_profesional",
        db_column="id_usuario",
    )



    matricula_profesional = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )



    especialidad = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )



    subespecialidad = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )



    cargo = models.CharField(
        max_length=100,
        null=True,
        blank=True,
    )



    telefono_institucional = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )



    fecha_registro = models.DateTimeField(
        auto_now_add=True
    )





    class Meta:

        db_table = "perfiles_profesionales"





    def __str__(self):

        return f"Perfil de {self.usuario}"