import hashlib
import secrets
import uuid

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from identidad.application.services.email_service import (
    EmailService,
)

from identidad.infrastructure.repositories.sesion_repository import (
    SesionRepository,
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher,
)

from identidad.models import (
    Credencial,
    EstadoRecuperacion,
    ResolucionRecuperacion,
    SolicitudRecuperacion,
    Usuario,
)


# ==========================================================
# UTILIDADES
# ==========================================================


def generar_token_recuperacion():
    """
    Token de recuperación de alta entropía.

    IMPORTANTE:
    Se genera únicamente cuando Jefatura APRUEBA la solicitud.
    """

    return secrets.token_urlsafe(48)


def hash_token_recuperacion(token):
    """
    En base de datos se almacena solamente SHA-256(token).
    El token en texto plano existe únicamente para construir
    el enlace enviado al correo del usuario.
    """

    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def obtener_estado(codigo):
    estado = (
        EstadoRecuperacion.objects
        .filter(codigo=codigo)
        .first()
    )

    if not estado:
        raise Exception(
            f"No existe el estado de recuperación {codigo}."
        )

    return estado


def nombre_completo(usuario):
    return " ".join(
        parte
        for parte in [
            usuario.nombres,
            usuario.apellido_paterno,
            usuario.apellido_materno,
        ]
        if parte
    )


def actualizar_expiracion_si_corresponde(solicitud):
    """
    PENDIENTE:
      vence si Jefatura no responde dentro del plazo general.

    APROBADA:
      vence si el usuario no utiliza el enlace dentro del
      plazo corto configurado para el enlace.
    """

    if (
        solicitud.estado.codigo
        in (
            "PENDIENTE",
            "APROBADA",
        )
        and
        solicitud.fecha_expiracion <= timezone.now()
    ):
        solicitud.estado = obtener_estado(
            "EXPIRADA"
        )

        # Al expirar destruimos la capacidad de recuperación.
        solicitud.token_recuperacion = None

        solicitud.save(
            update_fields=[
                "estado",
                "token_recuperacion",
            ]
        )

    return solicitud


# ==========================================================
# SOLICITAR RECUPERACIÓN
# ==========================================================


class SolicitarRecuperacionUseCase:

    @transaction.atomic
    def ejecutar(
        self,
        correo,
        ip_origen=None,
        user_agent=None,
    ):
        # El modelo actual no guarda IP ni user-agent en la
        # solicitud. Se reciben para poder incorporarlos luego
        # en auditoría sin cambiar la firma del caso de uso.
        del ip_origen
        del user_agent

        correo = correo.strip().lower()

        respuesta_generica = {
            "mensaje": (
                "Solicitud recibida. Si el correo pertenece a una "
                "cuenta activa, Jefatura de Oncología podrá revisarla. "
                "Si es aprobada, recibirá un enlace seguro en el correo "
                "institucional registrado."
            )
        }

        usuario = (
            Usuario.objects
            .select_related("estado_usuario")
            .filter(correo__iexact=correo)
            .first()
        )

        # No revelar si el correo existe o si la cuenta está activa.
        if (
            not usuario
            or
            not usuario.estado_usuario.es_operativo
        ):
            return respuesta_generica

        # Evita spam accidental por doble clic / reintentos rápidos.
        limite_repeticion = (
            timezone.now()
            - timedelta(seconds=60)
        )

        solicitud_reciente = (
            SolicitudRecuperacion.objects
            .filter(
                usuario=usuario,
                estado__codigo="PENDIENTE",
                fecha_solicitud__gte=limite_repeticion,
            )
            .exists()
        )

        if solicitud_reciente:
            return respuesta_generica

        estado_pendiente = obtener_estado(
            "PENDIENTE"
        )

        estado_expirada = obtener_estado(
            "EXPIRADA"
        )

        # Cualquier recuperación anterior pendiente o aprobada
        # queda invalidada al iniciar una nueva.
        (
            SolicitudRecuperacion.objects
            .filter(
                usuario=usuario,
                estado__codigo__in=[
                    "PENDIENTE",
                    "APROBADA",
                ],
            )
            .update(
                estado=estado_expirada,
                token_recuperacion=None,
            )
        )

        # Mientras está PENDIENTE NO existe token utilizable.
        SolicitudRecuperacion.objects.create(
            id_solicitud=uuid.uuid4(),
            usuario=usuario,
            estado=estado_pendiente,
            token_recuperacion=None,
            fecha_expiracion=(
                timezone.now()
                + timedelta(hours=24)
            ),
        )

        return respuesta_generica


# ==========================================================
# VALIDAR / CONSULTAR TOKEN DEL ENLACE
# ==========================================================


class ConsultarEstadoRecuperacionUseCase:

    @transaction.atomic
    def ejecutar(
        self,
        token,
    ):
        token_hash = hash_token_recuperacion(
            token
        )

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                token_recuperacion=token_hash
            )
            .first()
        )

        if not solicitud:
            raise Exception(
                "El enlace de recuperación no es válido o ya no está disponible."
            )

        solicitud = actualizar_expiracion_si_corresponde(
            solicitud
        )

        codigo_estado = solicitud.estado.codigo

        mensajes = {
            "APROBADA": (
                "El enlace es válido. Puede establecer una nueva contraseña."
            ),
            "RECHAZADA": (
                "La solicitud fue rechazada por Jefatura de Oncología."
            ),
            "UTILIZADA": (
                "Este enlace ya fue utilizado."
            ),
            "EXPIRADA": (
                "El enlace de recuperación expiró. Solicite uno nuevo."
            ),
            "PENDIENTE": (
                "La solicitud todavía no está autorizada."
            ),
        }

        return {
            "id_solicitud": str(
                solicitud.id_solicitud
            ),
            "estado": codigo_estado,
            "puede_cambiar_password": (
                codigo_estado == "APROBADA"
            ),
            "mensaje": mensajes.get(
                codigo_estado,
                "Estado de recuperación desconocido.",
            ),
            "fecha_expiracion": (
                solicitud.fecha_expiracion.isoformat()
            ),
        }


# ==========================================================
# LISTAR RECUPERACIONES PARA JEFATURA
# ==========================================================


class ListarRecuperacionesUseCase:

    def ejecutar(
        self,
        estado=None,
    ):
        consulta = (
            SolicitudRecuperacion.objects
            .select_related(
                "usuario",
                "estado",
            )
            .order_by(
                "-fecha_solicitud"
            )
        )

        if estado:
            consulta = consulta.filter(
                estado__codigo__iexact=estado.strip()
            )

        resultados = []

        for solicitud in consulta:
            solicitud = actualizar_expiracion_si_corresponde(
                solicitud
            )

            try:
                resolucion = solicitud.resolucion
            except ResolucionRecuperacion.DoesNotExist:
                resolucion = None

            resolucion_data = None

            if resolucion:
                resolucion_data = {
                    "decision": (
                        "APROBADA"
                        if resolucion.aprobado
                        else "RECHAZADA"
                    ),
                    "observacion": resolucion.comentario,
                    "resuelto_por": nombre_completo(
                        resolucion.revisado_por
                    ),
                    "fecha_resolucion": (
                        resolucion.fecha_revision.isoformat()
                    ),
                }

            resultados.append(
                {
                    "id_solicitud": str(
                        solicitud.id_solicitud
                    ),
                    "usuario": {
                        "id_usuario": str(
                            solicitud.usuario.id_usuario
                        ),
                        "nombre_completo": nombre_completo(
                            solicitud.usuario
                        ),
                        "correo": solicitud.usuario.correo,
                        "nombre_usuario": (
                            solicitud.usuario.nombre_usuario
                        ),
                    },
                    "estado": solicitud.estado.codigo,
                    "estado_nombre": solicitud.estado.nombre,
                    "fecha_solicitud": (
                        solicitud.fecha_solicitud.isoformat()
                    ),
                    "fecha_expiracion": (
                        solicitud.fecha_expiracion.isoformat()
                    ),
                    "fecha_utilizacion": None,
                    "resolucion": resolucion_data,
                }
            )

        return {
            "total": len(resultados),
            "resultados": resultados,
        }


# ==========================================================
# APROBAR / RECHAZAR
# ==========================================================


class ResolverRecuperacionUseCase:

    @transaction.atomic
    def ejecutar(
        self,
        solicitud_id,
        jefe,
        decision,
        observacion=None,
    ):
        decision = decision.strip().upper()

        if decision not in (
            "APROBADA",
            "RECHAZADA",
        ):
            raise Exception(
                "La decisión indicada no es válida."
            )

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                id_solicitud=solicitud_id
            )
            .first()
        )

        if not solicitud:
            raise Exception(
                "La solicitud de recuperación no existe."
            )

        solicitud = actualizar_expiracion_si_corresponde(
            solicitud
        )

        codigo_estado = solicitud.estado.codigo

        if codigo_estado == "EXPIRADA":
            raise Exception(
                "La solicitud ya expiró."
            )

        if codigo_estado == "UTILIZADA":
            raise Exception(
                "La solicitud ya fue utilizada."
            )

        if codigo_estado != "PENDIENTE":
            raise Exception(
                "La solicitud ya fue resuelta anteriormente."
            )

        if (
            ResolucionRecuperacion.objects
            .filter(solicitud=solicitud)
            .exists()
        ):
            raise Exception(
                "La solicitud ya posee una resolución registrada."
            )

        aprobado = decision == "APROBADA"

        ResolucionRecuperacion.objects.create(
            id_resolucion=uuid.uuid4(),
            solicitud=solicitud,
            aprobado=aprobado,
            revisado_por=jefe,
            comentario=(
                observacion.strip()
                if observacion
                else None
            ),
        )

        solicitud.estado = obtener_estado(
            decision
        )

        solicitud.fecha_resolucion = timezone.now()

        campos_actualizados = [
            "estado",
            "fecha_resolucion",
        ]

        if aprobado:
            # El token real se crea AQUÍ, después de la aprobación.
            token = generar_token_recuperacion()

            solicitud.token_recuperacion = (
                hash_token_recuperacion(token)
            )

            minutos_vigencia = int(
                getattr(
                    settings,
                    "RECOVERY_LINK_MINUTES",
                    15,
                )
            )

            solicitud.fecha_expiracion = (
                timezone.now()
                + timedelta(
                    minutes=minutos_vigencia
                )
            )

            campos_actualizados.extend(
                [
                    "token_recuperacion",
                    "fecha_expiracion",
                ]
            )

            solicitud.save(
                update_fields=campos_actualizados
            )

            # El envío forma parte de la operación de aprobación.
            # Si SMTP falla, se lanza excepción y la transacción
            # se revierte: la solicitud seguirá PENDIENTE y el Jefe
            # podrá reintentar después de corregir la configuración.
            try:
                EmailService().enviar_enlace_recuperacion(
                    usuario=solicitud.usuario,
                    token=token,
                    minutos_vigencia=minutos_vigencia,
                    observacion=observacion,
                )
            except Exception as error:
                raise Exception(
                    "No se pudo enviar el enlace al correo institucional. "
                    "La aprobación no fue aplicada. Revise la configuración SMTP."
                ) from error

            return {
                "id_solicitud": str(
                    solicitud.id_solicitud
                ),
                "estado": decision,
                "correo_enviado": True,
                "mensaje": (
                    "Recuperación aprobada correctamente. "
                    "Se envió un enlace seguro al correo institucional "
                    "registrado del oncólogo."
                ),
            }

        # RECHAZADA: no existe enlace ni token de cambio.
        solicitud.token_recuperacion = None
        solicitud.fecha_expiracion = timezone.now()

        campos_actualizados.extend(
            [
                "token_recuperacion",
                "fecha_expiracion",
            ]
        )

        solicitud.save(
            update_fields=campos_actualizados
        )

        try:
            EmailService().enviar_notificacion_rechazo(
                usuario=solicitud.usuario,
                observacion=observacion,
            )
        except Exception as error:
            raise Exception(
                "No se pudo enviar el correo de rechazo al correo institucional. "
                "La resolución no fue aplicada. Revise la configuración SMTP."
            ) from error

        return {
            "id_solicitud": str(
                solicitud.id_solicitud
            ),
            "estado": decision,
            "correo_enviado": True,
            "mensaje": (
                "Solicitud rechazada correctamente. "
                "Se notificó la decisión al correo institucional "
                "registrado del oncólogo."
            ),
        }


# ==========================================================
# CAMBIAR CONTRASEÑA DESDE EL ENLACE
# ==========================================================


class CambiarPasswordRecuperacionUseCase:

    def __init__(self):
        self.password_hasher = PasswordHasher()
        self.sesion_repository = SesionRepository()

    @transaction.atomic
    def ejecutar(
        self,
        token,
        nueva_password,
    ):
        token_hash = hash_token_recuperacion(
            token
        )

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                token_recuperacion=token_hash
            )
            .first()
        )

        if not solicitud:
            raise Exception(
                "El enlace de recuperación no es válido o ya no está disponible."
            )

        solicitud = actualizar_expiracion_si_corresponde(
            solicitud
        )

        codigo_estado = solicitud.estado.codigo

        if codigo_estado == "EXPIRADA":
            raise Exception(
                "El enlace de recuperación expiró. Solicite uno nuevo."
            )

        if codigo_estado == "UTILIZADA":
            raise Exception(
                "Este enlace ya fue utilizado."
            )

        if codigo_estado != "APROBADA":
            raise Exception(
                "La solicitud no está habilitada para cambiar la contraseña."
            )

        try:
            resolucion = solicitud.resolucion
        except ResolucionRecuperacion.DoesNotExist:
            resolucion = None

        if (
            not resolucion
            or
            not resolucion.aprobado
        ):
            raise Exception(
                "La recuperación no posee una aprobación válida de Jefatura."
            )

        credencial = (
            Credencial.objects
            .select_for_update()
            .filter(
                usuario=solicitud.usuario
            )
            .first()
        )

        if not credencial:
            raise Exception(
                "La cuenta no posee una credencial registrada."
            )

        credencial.password_hash = (
            self.password_hasher.generar_hash(
                nueva_password
            )
        )

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

        solicitud.estado = obtener_estado(
            "UTILIZADA"
        )

        # Destruimos el hash del enlace después del uso.
        solicitud.token_recuperacion = None

        solicitud.save(
            update_fields=[
                "estado",
                "token_recuperacion",
            ]
        )

        sesiones_revocadas = (
            self.sesion_repository.revocar_todas(
                solicitud.usuario,
                (
                    "Cambio de contraseña mediante "
                    "recuperación aprobada"
                ),
            )
        )

        return {
            "mensaje": (
                "Contraseña actualizada correctamente. "
                "Ya puede iniciar sesión con su nueva contraseña."
            ),
            "sesiones_revocadas": sesiones_revocadas,
            "estado": "UTILIZADA",
        }
