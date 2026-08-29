from django.core.management.base import BaseCommand
from django.db import transaction

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher,
)

from identidad.models import (
    Credencial,
    EstadoUsuario,
    PerfilProfesional,
    Permiso,
    Rol,
    RolPermiso,
    Usuario,
    UsuarioRol,
)


class Command(BaseCommand):

    help = "Crea o actualiza una cuenta de demostración para Jefatura de Oncología"

    @transaction.atomic
    def handle(self, *args, **kwargs):

        correo = "jefe.oncologia@hospital.com"
        nombre_usuario = "jefe.oncologia"
        password = "JefeTemporal123!"

        estado = EstadoUsuario.objects.filter(
            codigo="ACTIVO"
        ).first()

        if not estado:
            self.stdout.write(
                self.style.ERROR(
                    "No existe el estado ACTIVO."
                )
            )
            return

        rol = Rol.objects.filter(
            codigo="JEFE_ONCOLOGIA"
        ).first()

        if not rol:
            self.stdout.write(
                self.style.ERROR(
                    "No existe el rol JEFE_ONCOLOGIA."
                )
            )
            return

        usuario, creado = Usuario.objects.get_or_create(

            correo=correo,

            defaults={
                "estado_usuario": estado,
                "nombres": "Javier",
                "apellido_paterno": "Mendoza",
                "apellido_materno": "Flores",
                "nombre_usuario": nombre_usuario,
                "telefono": "70000001",
            },

        )

        usuario.estado_usuario = estado
        usuario.nombres = "Javier"
        usuario.apellido_paterno = "Mendoza"
        usuario.apellido_materno = "Flores"
        usuario.nombre_usuario = nombre_usuario
        usuario.telefono = "70000001"

        usuario.save()

        password_hash = PasswordHasher().generar_hash(
            password
        )

        credencial, _ = Credencial.objects.get_or_create(
            usuario=usuario,
            defaults={
                "password_hash": password_hash,
                "debe_cambiar_password": False,
            },
        )

        credencial.password_hash = password_hash
        credencial.debe_cambiar_password = False
        credencial.intentos_fallidos = 0
        credencial.bloqueado_hasta = None
        credencial.save()

        PerfilProfesional.objects.get_or_create(
            usuario=usuario,
            defaults={
                "matricula_profesional": "JEF-ONC-001",
                "especialidad": "Oncología",
                "cargo": "Jefe de Oncología",
                "telefono_institucional": "22000001",
            },
        )

        UsuarioRol.objects.update_or_create(

            usuario=usuario,
            rol=rol,

            defaults={
                "activo": True,
                "fecha_fin": None,
            },

        )

        permisos_jefe = [
            "ONCOLOGO_CREAR",
            "ONCOLOGO_EDITAR",
            "ONCOLOGO_LISTAR",
            "RECUPERACION_APROBAR",
            "USUARIO_ACTIVAR",
            "USUARIO_DESACTIVAR",
            "PERFIL_EDITAR",
        ]

        for codigo in permisos_jefe:

            permiso = Permiso.objects.filter(
                codigo=codigo
            ).first()

            if permiso:

                RolPermiso.objects.get_or_create(
                    rol=rol,
                    permiso=permiso,
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Cuenta Jefe de Oncología lista."
            )
        )

        self.stdout.write(
            f"Correo: {correo}"
        )

        self.stdout.write(
            f"Usuario: {nombre_usuario}"
        )

        self.stdout.write(
            f"Contraseña: {password}"
        )