import uuid

from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


class EstadoUsuario(models.Model):
    id_estado_usuario = models.SmallAutoField(primary_key=True)
    codigo = models.CharField(max_length=30, unique=True)
    nombre = models.CharField(max_length=60)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    es_operativo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "estados_usuario"
        ordering = ["id_estado_usuario"]

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

    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=80)
    apellido_materno = models.CharField(
        max_length=80,
        null=True,
        blank=True,
    )

    correo = models.CharField(max_length=150)
    nombre_usuario = models.CharField(max_length=80)

    telefono = models.CharField(
        max_length=25,
        null=True,
        blank=True,
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    ultimo_acceso = models.DateTimeField(
        null=True,
        blank=True,
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
        indexes = [
            models.Index(
                fields=["estado_usuario"],
                name="idx_usuario_estado",
            ),
        ]

    def __str__(self):
        return self.nombre_usuario


class Credencial(models.Model):
    id_credencial = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="credencial",
        db_column="id_usuario",
    )

    password_hash = models.CharField(max_length=255)

    debe_cambiar_password = models.BooleanField(default=False)

    intentos_fallidos = models.PositiveSmallIntegerField(default=0)

    bloqueado_hasta = models.DateTimeField(
        null=True,
        blank=True,
    )

    fecha_ultimo_cambio = models.DateTimeField(auto_now_add=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "credenciales"

    def __str__(self):
        return f"Credencial {self.usuario.nombre_usuario}"


class Rol(models.Model):
    id_rol = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=40,
        unique=True,
    )

    nombre = models.CharField(max_length=80)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    activo = models.BooleanField(default=True)

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "roles"
        ordering = ["id_rol"]

    def __str__(self):
        return self.nombre


class Permiso(models.Model):
    id_permiso = models.SmallAutoField(primary_key=True)

    codigo = models.CharField(
        max_length=80,
        unique=True,
    )

    nombre = models.CharField(max_length=120)

    descripcion = models.CharField(
        max_length=255,
        null=True,
        blank=True,
    )

    modulo = models.CharField(max_length=60)

    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "permisos"
        ordering = ["modulo", "codigo"]

    def __str__(self):
        return self.codigo


class UsuarioRol(models.Model):
    id_usuario_rol = models.BigAutoField(primary_key=True)

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

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    fecha_fin = models.DateTimeField(
        null=True,
        blank=True,
    )

    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "usuario_rol"
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "rol"],
                name="uq_usuario_rol",
            )
        ]
        indexes = [
            models.Index(
                fields=["usuario", "activo"],
                name="idx_usuario_rol_activo",
            ),
        ]

    def __str__(self):
        return f"{self.usuario} - {self.rol}"


class RolPermiso(models.Model):
    id_rol_permiso = models.BigAutoField(primary_key=True)

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

    fecha_asignacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "rol_permiso"
        constraints = [
            models.UniqueConstraint(
                fields=["rol", "permiso"],
                name="uq_rol_permiso",
            )
        ]

    def __str__(self):
        return f"{self.rol} - {self.permiso}"


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

    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "perfiles_profesionales"

    def __str__(self):
        return f"Perfil de {self.usuario}"


class Sesion(models.Model):
    id_sesion = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="sesiones",
        db_column="id_usuario",
    )

    jti_refresh = models.UUIDField(unique=True)

    refresh_token_hash = models.CharField(max_length=255)

    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    fecha_inicio = models.DateTimeField(auto_now_add=True)

    fecha_expiracion = models.DateTimeField()

    fecha_cierre = models.DateTimeField(
        null=True,
        blank=True,
    )

    revocada = models.BooleanField(default=False)

    motivo_revocacion = models.CharField(
        max_length=120,
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "sesiones"
        indexes = [
            models.Index(
                fields=["usuario"],
                name="idx_sesion_usuario",
            ),
            models.Index(
                fields=["revocada", "fecha_expiracion"],
                name="idx_sesion_estado",
            ),
        ]

    def __str__(self):
        return str(self.id_sesion)


class EstadoRecuperacion(models.Model):
    id_estado_recuperacion = models.SmallAutoField(primary_key=True)

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
        db_table = "estados_recuperacion"
        ordering = ["id_estado_recuperacion"]

    def __str__(self):
        return self.nombre


class SolicitudRecuperacion(models.Model):
    id_solicitud = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="solicitudes_recuperacion",
        db_column="id_usuario",
    )

    estado_recuperacion = models.ForeignKey(
        EstadoRecuperacion,
        on_delete=models.PROTECT,
        related_name="solicitudes",
        db_column="id_estado_recuperacion",
    )

    token_hash = models.CharField(
        max_length=255,
        unique=True,
    )

    fecha_solicitud = models.DateTimeField(auto_now_add=True)

    fecha_expiracion = models.DateTimeField()

    fecha_utilizacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    ip_solicitud = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    class Meta:
        db_table = "solicitudes_recuperacion"
        indexes = [
            models.Index(
                fields=["usuario", "estado_recuperacion"],
                name="idx_recup_usr_estado",
            ),
        ]

    def __str__(self):
        return str(self.id_solicitud)


class ResolucionRecuperacion(models.Model):
    id_resolucion = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    solicitud = models.OneToOneField(
        SolicitudRecuperacion,
        on_delete=models.CASCADE,
        related_name="resolucion",
        db_column="id_solicitud",
    )

    resuelto_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="recuperaciones_resueltas",
        db_column="resuelto_por",
    )

    decision = models.CharField(max_length=15)

    observacion = models.TextField(
        null=True,
        blank=True,
    )

    fecha_resolucion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "resoluciones_recuperacion"
        constraints = [
            models.CheckConstraint(
                condition=Q(decision__in=["APROBADA", "RECHAZADA"]),
                name="ck_resolucion_decision",
            ),
        ]

    def __str__(self):
        return self.decision


class TipoEventoAcceso(models.Model):
    id_tipo_evento = models.SmallAutoField(primary_key=True)

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
        db_table = "tipos_evento_acceso"
        ordering = ["id_tipo_evento"]

    def __str__(self):
        return self.codigo


class EventoAcceso(models.Model):
    id_evento = models.BigAutoField(primary_key=True)

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        related_name="eventos_acceso",
        db_column="id_usuario",
        null=True,
        blank=True,
    )

    tipo_evento = models.ForeignKey(
        TipoEventoAcceso,
        on_delete=models.PROTECT,
        related_name="eventos",
        db_column="id_tipo_evento",
    )

    sesion = models.ForeignKey(
        Sesion,
        on_delete=models.SET_NULL,
        related_name="eventos",
        db_column="id_sesion",
        null=True,
        blank=True,
    )

    exitoso = models.BooleanField()

    ip_origen = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.TextField(
        null=True,
        blank=True,
    )

    detalle = models.JSONField(
        null=True,
        blank=True,
    )

    fecha_evento = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "eventos_acceso"
        indexes = [
            models.Index(
                fields=["usuario", "fecha_evento"],
                name="idx_evento_usuario_fecha",
            ),
            models.Index(
                fields=["tipo_evento", "fecha_evento"],
                name="idx_evento_tipo_fecha",
            ),
        ]

    def __str__(self):
        return f"{self.tipo_evento.codigo} - {self.fecha_evento}"