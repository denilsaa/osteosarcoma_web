from django.db import models

from .usuario import Usuario



class Rol(models.Model):

    id_rol = models.SmallAutoField(
        primary_key=True
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


    activo = models.BooleanField(
        default=True
    )


    fecha_creacion = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        db_table = "roles"

        ordering = [
            "id_rol"
        ]


    def __str__(self):

        return self.nombre





class Permiso(models.Model):

    id_permiso = models.SmallAutoField(
        primary_key=True
    )


    codigo = models.CharField(
        max_length=80,
        unique=True,
    )


    nombre = models.CharField(
        max_length=120
    )


    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )


    modulo = models.CharField(
        max_length=60
    )


    activo = models.BooleanField(
        default=True
    )


    class Meta:

        db_table = "permisos"

        ordering = [
            "modulo",
            "codigo"
        ]


    def __str__(self):

        return self.codigo





class UsuarioRol(models.Model):

    id_usuario_rol = models.BigAutoField(
        primary_key=True
    )


    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="asignaciones_roles",
        db_column="id_usuario",
    )


    rol = models.ForeignKey(
        Rol,
        on_delete=models.PROTECT,
        related_name="asignaciones_usuarios",
        db_column="id_rol",
    )


    asignado_por = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name="roles_asignados_por_mi",
        db_column="asignado_por",
        null=True,
        blank=True,
    )


    fecha_asignacion = models.DateTimeField(
        auto_now_add=True
    )


    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
    )


    activo = models.BooleanField(
        default=True
    )


    class Meta:

        db_table = "usuario_rol"


        constraints = [

            models.UniqueConstraint(
                fields=[
                    "usuario",
                    "rol"
                ],
                name="uq_usuario_rol",
            )

        ]


    def __str__(self):

        return f"{self.usuario} - {self.rol}"





class RolPermiso(models.Model):

    id_rol_permiso = models.BigAutoField(
        primary_key=True
    )


    rol = models.ForeignKey(
        Rol,
        on_delete=models.CASCADE,
        related_name="permisos_asignados",
        db_column="id_rol",
    )


    permiso = models.ForeignKey(
        Permiso,
        on_delete=models.CASCADE,
        related_name="roles_asignados",
        db_column="id_permiso",
    )


    fecha_asignacion = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:

        db_table = "rol_permiso"


        constraints = [

            models.UniqueConstraint(
                fields=[
                    "rol",
                    "permiso"
                ],
                name="uq_rol_permiso",
            )

        ]


    def __str__(self):

        return f"{self.rol} - {self.permiso}"