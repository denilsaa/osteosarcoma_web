from django.utils import timezone

from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository,
)
from identidad.infrastructure.security.jwt_manager import (
    JWTManager,
)
from identidad.infrastructure.security.password_hasher import (
    PasswordHasher,
)


class SesionAutenticadaService:
    """Crea la sesión y los JWT únicamente después de validar el segundo factor."""

    def __init__(self):
        self.sesion_repository = SesionRepository()
        self.jwt_manager = JWTManager()
        self.password_hasher = PasswordHasher()

    def crear(self, usuario, credencial, ip_origen=None, user_agent=None):
        refresh_data = self.jwt_manager.crear_refresh_token(usuario)
        refresh_token = refresh_data["token"]

        sesion = self.sesion_repository.crear(
            {
                "usuario": usuario,
                "jti_refresh": refresh_data["jti"],
                "refresh_token_hash": self.password_hasher.generar_hash(
                    refresh_token
                ),
                "ip_origen": ip_origen,
                "user_agent": user_agent,
                "fecha_expiracion": refresh_data["expira"],
            }
        )

        access_data = self.jwt_manager.crear_access_token(
            usuario,
            sesion.id_sesion,
        )

        usuario.ultimo_acceso = timezone.now()
        usuario.save(update_fields=["ultimo_acceso"])

        credencial.intentos_fallidos = 0
        credencial.bloqueado_hasta = None
        credencial.save(
            update_fields=[
                "intentos_fallidos",
                "bloqueado_hasta",
                "fecha_actualizacion",
            ]
        )

        asignaciones = usuario.asignaciones_roles.filter(
            activo=True,
            rol__activo=True,
        )

        roles = list(
            asignaciones.values_list(
                "rol__codigo",
                flat=True,
            ).distinct()
        )

        permisos = list(
            asignaciones.filter(
                rol__permisos_asignados__permiso__activo=True
            )
            .values_list(
                "rol__permisos_asignados__permiso__codigo",
                flat=True,
            )
            .distinct()
        )

        return {
            "access_token": access_data["token"],
            "refresh_token": refresh_token,
            "access_expires_in": access_data["expires_in"],
            "access_expires_at": access_data["expira"].isoformat(),
            "refresh_expires_in": refresh_data["expires_in"],
            "refresh_expires_at": refresh_data["expira"].isoformat(),
            "sesion": {
                "id_sesion": str(sesion.id_sesion),
                "estado": "ACTIVA",
            },
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_usuario": usuario.nombre_usuario,
                "correo": usuario.correo,
                "nombres": usuario.nombres,
                "apellido_paterno": usuario.apellido_paterno,
                "apellido_materno": usuario.apellido_materno,
                "telefono": usuario.telefono,
                "estado": usuario.estado_usuario.codigo,
                "debe_cambiar_password": credencial.debe_cambiar_password,
                "roles": roles,
                "permisos": permisos,
            },
        }
