from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from identidad.infrastructure.security.password_hasher import PasswordHasher
from identidad.models import (
    Credencial,
    DesafioSegundoFactor,
    EstadoUsuario,
    PerfilProfesional,
    Permiso,
    Rol,
    RolPermiso,
    Sesion,
    Usuario,
    UsuarioRol,
)


class Command(BaseCommand):
    help = (
        "Crea o actualiza la cuenta del Jefe de Oncología para "
        "denilsonsaavedra2005@gmail.com"
    )

    CORREO = "denilsonsaavedra2005@gmail.com"
    NOMBRE_USUARIO = "denilson.jefe"
    PASSWORD = "Denileren123."

    NOMBRES = "Denilson"
    APELLIDO_PATERNO = "Saavedra"
    APELLIDO_MATERNO = ""
    TELEFONO = "70000001"

    ESPECIALIDAD = "Oncología"
    CARGO = "Jefe de Oncología"
    TELEFONO_INSTITUCIONAL = "22000001"

    PERMISOS_JEFE = [
        {
            "codigo": "ONCOLOGO_CREAR",
            "nombre": "Crear oncólogos",
            "modulo": "IDENTIDAD",
            "descripcion": "Registrar cuentas de oncólogos",
        },
        {
            "codigo": "ONCOLOGO_EDITAR",
            "nombre": "Editar oncólogos",
            "modulo": "IDENTIDAD",
            "descripcion": "Modificar cuentas de oncólogos",
        },
        {
            "codigo": "ONCOLOGO_LISTAR",
            "nombre": "Listar oncólogos",
            "modulo": "IDENTIDAD",
            "descripcion": "Consultar cuentas de oncólogos",
        },
        {
            "codigo": "RECUPERACION_APROBAR",
            "nombre": "Aprobar recuperación",
            "modulo": "SEGURIDAD",
            "descripcion": "Aprobar o rechazar recuperaciones de contraseña",
        },
        {
            "codigo": "USUARIO_ACTIVAR",
            "nombre": "Activar usuario",
            "modulo": "IDENTIDAD",
            "descripcion": "Activar cuentas",
        },
        {
            "codigo": "USUARIO_DESACTIVAR",
            "nombre": "Desactivar usuario",
            "modulo": "IDENTIDAD",
            "descripcion": "Desactivar cuentas",
        },
        {
            "codigo": "PERFIL_EDITAR",
            "nombre": "Editar perfil",
            "modulo": "PERFIL",
            "descripcion": "Editar datos personales autorizados",
        },
    ]

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("")
        self.stdout.write("==============================================")
        self.stdout.write(" CREAR / ACTUALIZAR JEFE DE ONCOLOGÍA")
        self.stdout.write("==============================================")
        self.stdout.write("")

        estado_activo, _ = EstadoUsuario.objects.get_or_create(
            codigo="ACTIVO",
            defaults={
                "nombre": "Activo",
                "descripcion": "Usuario habilitado",
                "es_operativo": True,
            },
        )

        rol_jefe, _ = Rol.objects.get_or_create(
            codigo="JEFE_ONCOLOGIA",
            defaults={
                "nombre": "Jefe de Oncología",
                "descripcion": "Administrador del módulo oncológico",
                "activo": True,
            },
        )

        # --------------------------------------------------
        # EVITAR CONFLICTOS ENTRE CORREO Y NOMBRE DE USUARIO
        # --------------------------------------------------
        usuario_por_correo = (
            Usuario.objects
            .filter(correo__iexact=self.CORREO)
            .first()
        )

        usuario_por_username = (
            Usuario.objects
            .filter(nombre_usuario__iexact=self.NOMBRE_USUARIO)
            .first()
        )

        if (
            usuario_por_correo
            and usuario_por_username
            and usuario_por_correo.id_usuario != usuario_por_username.id_usuario
        ):
            raise RuntimeError(
                "Existe un usuario con el correo indicado y otro usuario "
                "diferente con el nombre de usuario 'denilson.jefe'. "
                "Revise esos registros antes de continuar."
            )

        usuario = usuario_por_correo or usuario_por_username

        creado = False

        if not usuario:
            usuario = Usuario.objects.create(
                estado_usuario=estado_activo,
                nombres=self.NOMBRES,
                apellido_paterno=self.APELLIDO_PATERNO,
                apellido_materno=self.APELLIDO_MATERNO or None,
                correo=self.CORREO,
                nombre_usuario=self.NOMBRE_USUARIO,
                telefono=self.TELEFONO,
            )
            creado = True
        else:
            usuario.estado_usuario = estado_activo
            usuario.nombres = self.NOMBRES
            usuario.apellido_paterno = self.APELLIDO_PATERNO
            usuario.apellido_materno = self.APELLIDO_MATERNO or None
            usuario.correo = self.CORREO
            usuario.nombre_usuario = self.NOMBRE_USUARIO
            usuario.telefono = self.TELEFONO
            usuario.save(
                update_fields=[
                    "estado_usuario",
                    "nombres",
                    "apellido_paterno",
                    "apellido_materno",
                    "correo",
                    "nombre_usuario",
                    "telefono",
                    "fecha_actualizacion",
                ]
            )

        # --------------------------------------------------
        # CONTRASEÑA SEGURA CON EL HASHER REAL DEL PROYECTO
        # --------------------------------------------------
        password_hash = PasswordHasher().generar_hash(
            self.PASSWORD
        )

        credencial, _ = Credencial.objects.get_or_create(
            usuario=usuario,
            defaults={
                "password_hash": password_hash,
                "debe_cambiar_password": False,
                "intentos_fallidos": 0,
                "bloqueado_hasta": None,
            },
        )

        credencial.password_hash = password_hash
        credencial.debe_cambiar_password = False
        credencial.intentos_fallidos = 0
        credencial.bloqueado_hasta = None
        credencial.fecha_ultimo_cambio = timezone.now()
        credencial.save(
            update_fields=[
                "password_hash",
                "debe_cambiar_password",
                "intentos_fallidos",
                "bloqueado_hasta",
                "fecha_ultimo_cambio",
                "fecha_actualizacion",
            ]
        )

        # --------------------------------------------------
        # PERFIL PROFESIONAL
        # --------------------------------------------------
        perfil, _ = PerfilProfesional.objects.get_or_create(
            usuario=usuario,
        )

        if not perfil.matricula_profesional:
            base = "JEF-DEN-001"
            matricula = base
            contador = 1

            while (
                PerfilProfesional.objects
                .exclude(usuario=usuario)
                .filter(matricula_profesional=matricula)
                .exists()
            ):
                contador += 1
                matricula = f"JEF-DEN-{contador:03d}"

            perfil.matricula_profesional = matricula

        perfil.especialidad = self.ESPECIALIDAD
        perfil.subespecialidad = None
        perfil.cargo = self.CARGO
        perfil.telefono_institucional = self.TELEFONO_INSTITUCIONAL
        perfil.save()

        # --------------------------------------------------
        # ROL JEFE
        # --------------------------------------------------
        UsuarioRol.objects.update_or_create(
            usuario=usuario,
            rol=rol_jefe,
            defaults={
                "activo": True,
                "fecha_fin": None,
            },
        )

        # --------------------------------------------------
        # PERMISOS DEL JEFE
        # --------------------------------------------------
        for datos in self.PERMISOS_JEFE:
            permiso, _ = Permiso.objects.get_or_create(
                codigo=datos["codigo"],
                defaults={
                    "nombre": datos["nombre"],
                    "modulo": datos["modulo"],
                    "descripcion": datos["descripcion"],
                    "activo": True,
                },
            )

            if not permiso.activo:
                permiso.activo = True
                permiso.save(update_fields=["activo"])

            RolPermiso.objects.get_or_create(
                rol=rol_jefe,
                permiso=permiso,
            )

        # --------------------------------------------------
        # SEGURIDAD:
        # CERRAR SESIONES / OTP ANTERIORES
        # --------------------------------------------------
        ahora = timezone.now()

        sesiones_revocadas = (
            Sesion.objects
            .filter(
                usuario=usuario,
                revocada=False,
            )
            .update(
                revocada=True,
                fecha_cierre=ahora,
                motivo_revocacion=(
                    "Reinicio administrativo de cuenta de Jefatura"
                ),
            )
        )

        otp_invalidados = (
            DesafioSegundoFactor.objects
            .filter(
                usuario=usuario,
                utilizado=False,
            )
            .update(
                utilizado=True,
                fecha_utilizacion=ahora,
            )
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Cuenta de Jefatura configurada correctamente."
            )
        )
        self.stdout.write("")
        self.stdout.write(
            f"Acción: {'CREADA' if creado else 'ACTUALIZADA'}"
        )
        self.stdout.write(
            f"Correo: {usuario.correo}"
        )
        self.stdout.write(
            f"Usuario: {usuario.nombre_usuario}"
        )
        self.stdout.write(
            f"Rol: {rol_jefe.codigo}"
        )
        self.stdout.write(
            f"Estado: {usuario.estado_usuario.codigo}"
        )
        self.stdout.write(
            f"Matrícula: {perfil.matricula_profesional}"
        )
        self.stdout.write(
            f"Sesiones anteriores revocadas: {sesiones_revocadas}"
        )
        self.stdout.write(
            f"Desafíos 2FA anteriores invalidados: {otp_invalidados}"
        )
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Contraseña temporal configurada: Denileren123."
            )
        )
        self.stdout.write("")
        self.stdout.write(
            "Ya puede iniciar sesión con el correo indicado; "
            "el sistema enviará el código del segundo factor a ese Gmail."
        )
