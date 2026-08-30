import hashlib
import secrets
import uuid

from datetime import timedelta

from django.db import transaction
from django.utils import timezone

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
    Genera un token aleatorio para la recuperación.
    """

    return secrets.token_urlsafe(
        48
    )


def hash_token_recuperacion(
    token,
):
    """
    Aunque la columna existente se llama
    token_recuperacion, almacenamos el hash
    y no el token plano.
    """

    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def obtener_estado(
    codigo,
):

    estado = (
        EstadoRecuperacion.objects
        .filter(
            codigo=codigo
        )
        .first()
    )

    if not estado:

        raise Exception(
            f"No existe el estado de recuperación {codigo}."
        )

    return estado


def nombre_completo(
    usuario,
):

    return " ".join(
        parte
        for parte in [
            usuario.nombres,
            usuario.apellido_paterno,
            usuario.apellido_materno,
        ]
        if parte
    )


def actualizar_expiracion_si_corresponde(
    solicitud,
):
    """
    Si una recuperación pendiente o aprobada
    supera su fecha límite, pasa a EXPIRADA.
    """

    if (
        solicitud.estado.codigo
        in (
            "PENDIENTE",
            "APROBADA",
        )
        and
        solicitud.fecha_expiracion
        <=
        timezone.now()
    ):

        solicitud.estado = (
            obtener_estado(
                "EXPIRADA"
            )
        )

        solicitud.save(
            update_fields=[
                "estado",
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

        # Tu modelo real no guarda estos campos.
        del ip_origen
        del user_agent

        correo = (
            correo
            .strip()
            .lower()
        )

        usuario = (
            Usuario.objects
            .select_related(
                "estado_usuario"
            )
            .filter(
                correo__iexact=correo
            )
            .first()
        )

        # Respuesta genérica para no revelar
        # si un correo existe en el sistema.
        if (
            not usuario
            or
            not usuario
            .estado_usuario
            .es_operativo
        ):

            return {
                "mensaje": (
                    "Si el correo pertenece a una cuenta "
                    "registrada, la solicitud será procesada."
                ),
                "creada": False,
            }

        estado_pendiente = (
            obtener_estado(
                "PENDIENTE"
            )
        )

        estado_expirada = (
            obtener_estado(
                "EXPIRADA"
            )
        )

        # ==================================================
        # INVALIDAR RECUPERACIONES ANTERIORES
        # ==================================================

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
                estado=estado_expirada
            )
        )

        # ==================================================
        # CREAR TOKEN
        # ==================================================

        token = (
            generar_token_recuperacion()
        )

        token_hash = (
            hash_token_recuperacion(
                token
            )
        )

        fecha_expiracion = (
            timezone.now()
            +
            timedelta(
                hours=24
            )
        )

        # Tu modelo no tiene default UUID,
        # por eso generamos el ID manualmente.
        solicitud = (
            SolicitudRecuperacion.objects
            .create(
                id_solicitud=
                    uuid.uuid4(),

                usuario=
                    usuario,

                estado=
                    estado_pendiente,

                token_recuperacion=
                    token_hash,

                fecha_expiracion=
                    fecha_expiracion,
            )
        )

        return {
            "mensaje": (
                "Solicitud enviada correctamente. "
                "Debe esperar la aprobación del "
                "Jefe de Oncología."
            ),

            "creada":
                True,

            "id_solicitud":
                str(
                    solicitud.id_solicitud
                ),

            "estado":
                "PENDIENTE",

            "fecha_expiracion":
                solicitud
                .fecha_expiracion
                .isoformat(),

            # Solo para la demostración local.
            # El frontend lo almacena temporalmente.
            "token_recuperacion":
                token,
        }


# ==========================================================
# CONSULTAR ESTADO DE RECUPERACIÓN
# ==========================================================

class ConsultarEstadoRecuperacionUseCase:

    @transaction.atomic
    def ejecutar(
        self,
        token,
    ):

        token_hash = (
            hash_token_recuperacion(
                token
            )
        )

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                token_recuperacion=
                    token_hash
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "El código de recuperación no es válido."
            )

        solicitud = (
            actualizar_expiracion_si_corresponde(
                solicitud
            )
        )

        codigo_estado = (
            solicitud
            .estado
            .codigo
        )

        mensajes = {
            "PENDIENTE": (
                "La solicitud está pendiente de "
                "aprobación por Jefatura de Oncología."
            ),

            "APROBADA": (
                "La solicitud fue aprobada. "
                "Ya puede establecer una nueva contraseña."
            ),

            "RECHAZADA": (
                "La solicitud fue rechazada por "
                "Jefatura de Oncología."
            ),

            "UTILIZADA": (
                "Este código ya fue utilizado para "
                "cambiar la contraseña."
            ),

            "EXPIRADA": (
                "La solicitud de recuperación expiró."
            ),
        }

        return {
            "id_solicitud":
                str(
                    solicitud.id_solicitud
                ),

            "estado":
                codigo_estado,

            "puede_cambiar_password":
                codigo_estado
                ==
                "APROBADA",

            "mensaje":
                mensajes.get(
                    codigo_estado,
                    "Estado de recuperación desconocido.",
                ),

            "fecha_expiracion":
                solicitud
                .fecha_expiracion
                .isoformat(),
        }


# ==========================================================
# LISTAR RECUPERACIONES PARA EL JEFE
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

            consulta = (
                consulta
                .filter(
                    estado__codigo__iexact=
                        estado.strip()
                )
            )

        resultados = []

        for solicitud in consulta:

            solicitud = (
                actualizar_expiracion_si_corresponde(
                    solicitud
                )
            )

            try:

                resolucion = (
                    solicitud.resolucion
                )

            except (
                ResolucionRecuperacion
                .DoesNotExist
            ):

                resolucion = None

            resolucion_data = None

            if resolucion:

                resolucion_data = {
                    "decision": (
                        "APROBADA"
                        if resolucion.aprobado
                        else
                        "RECHAZADA"
                    ),

                    "observacion":
                        resolucion.comentario,

                    "resuelto_por":
                        nombre_completo(
                            resolucion
                            .revisado_por
                        ),

                    "fecha_resolucion":
                        resolucion
                        .fecha_revision
                        .isoformat(),
                }

            resultados.append(
                {
                    "id_solicitud":
                        str(
                            solicitud
                            .id_solicitud
                        ),

                    "usuario": {
                        "id_usuario":
                            str(
                                solicitud
                                .usuario
                                .id_usuario
                            ),

                        "nombre_completo":
                            nombre_completo(
                                solicitud.usuario
                            ),

                        "correo":
                            solicitud
                            .usuario
                            .correo,

                        "nombre_usuario":
                            solicitud
                            .usuario
                            .nombre_usuario,
                    },

                    "estado":
                        solicitud
                        .estado
                        .codigo,

                    "estado_nombre":
                        solicitud
                        .estado
                        .nombre,

                    "fecha_solicitud":
                        solicitud
                        .fecha_solicitud
                        .isoformat(),

                    "fecha_expiracion":
                        solicitud
                        .fecha_expiracion
                        .isoformat(),

                    # Lo espera el frontend,
                    # aunque tu BD no tenga ese campo.
                    "fecha_utilizacion":
                        None,

                    "resolucion":
                        resolucion_data,
                }
            )

        return {
            "total":
                len(
                    resultados
                ),

            "resultados":
                resultados,
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

        decision = (
            decision
            .strip()
            .upper()
        )

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
                id_solicitud=
                    solicitud_id
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "La solicitud de recuperación no existe."
            )

        solicitud = (
            actualizar_expiracion_si_corresponde(
                solicitud
            )
        )

        codigo_estado = (
            solicitud
            .estado
            .codigo
        )

        if (
            codigo_estado
            ==
            "EXPIRADA"
        ):

            raise Exception(
                "La solicitud ya expiró."
            )

        if (
            codigo_estado
            ==
            "UTILIZADA"
        ):

            raise Exception(
                "La solicitud ya fue utilizada."
            )

        if (
            codigo_estado
            !=
            "PENDIENTE"
        ):

            raise Exception(
                "La solicitud ya fue resuelta anteriormente."
            )

        if (
            ResolucionRecuperacion.objects
            .filter(
                solicitud=solicitud
            )
            .exists()
        ):

            raise Exception(
                "La solicitud ya posee una resolución registrada."
            )

        aprobado = (
            decision
            ==
            "APROBADA"
        )

        ResolucionRecuperacion.objects.create(
            id_resolucion=
                uuid.uuid4(),

            solicitud=
                solicitud,

            aprobado=
                aprobado,

            revisado_por=
                jefe,

            comentario=(
                observacion.strip()
                if observacion
                else None
            ),
        )

        solicitud.estado = (
            obtener_estado(
                decision
            )
        )

        solicitud.fecha_resolucion = (
            timezone.now()
        )

        campos_actualizados = [
            "estado",
            "fecha_resolucion",
        ]

        # Después de aprobar,
        # el usuario tiene 30 minutos.
        if aprobado:

            solicitud.fecha_expiracion = (
                timezone.now()
                +
                timedelta(
                    minutes=30
                )
            )

            campos_actualizados.append(
                "fecha_expiracion"
            )

        solicitud.save(
            update_fields=
                campos_actualizados
        )

        return {
            "id_solicitud":
                str(
                    solicitud.id_solicitud
                ),

            "estado":
                decision,

            "mensaje": (
                "Solicitud aprobada correctamente."
                if aprobado
                else
                "Solicitud rechazada correctamente."
            ),
        }


# ==========================================================
# CAMBIAR CONTRASEÑA
# ==========================================================

class CambiarPasswordRecuperacionUseCase:

    def __init__(
        self,
    ):

        self.password_hasher = (
            PasswordHasher()
        )

        self.sesion_repository = (
            SesionRepository()
        )

    @transaction.atomic
    def ejecutar(
        self,
        token,
        nueva_password,
    ):

        token_hash = (
            hash_token_recuperacion(
                token
            )
        )

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                token_recuperacion=
                    token_hash
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "El código de recuperación no es válido."
            )

        solicitud = (
            actualizar_expiracion_si_corresponde(
                solicitud
            )
        )

        codigo_estado = (
            solicitud
            .estado
            .codigo
        )

        if (
            codigo_estado
            ==
            "UTILIZADA"
        ):

            raise Exception(
                "Este código ya fue utilizado."
            )

        if (
            codigo_estado
            ==
            "EXPIRADA"
        ):

            raise Exception(
                "El código de recuperación expiró."
            )

        if (
            codigo_estado
            ==
            "PENDIENTE"
        ):

            raise Exception(
                "La solicitud aún no fue aprobada "
                "por el Jefe de Oncología."
            )

        if (
            codigo_estado
            ==
            "RECHAZADA"
        ):

            raise Exception(
                "La solicitud fue rechazada "
                "por el Jefe de Oncología."
            )

        if (
            codigo_estado
            !=
            "APROBADA"
        ):

            raise Exception(
                "La solicitud no está habilitada "
                "para cambiar la contraseña."
            )

        # Comprobación adicional:
        # debe existir una resolución aprobada.
        try:

            resolucion = (
                solicitud.resolucion
            )

        except (
            ResolucionRecuperacion
            .DoesNotExist
        ):

            resolucion = None

        if (
            not resolucion
            or
            not resolucion.aprobado
        ):

            raise Exception(
                "La recuperación no posee una "
                "aprobación válida de Jefatura."
            )

        credencial = (
            Credencial.objects
            .select_for_update()
            .filter(
                usuario=
                    solicitud.usuario
            )
            .first()
        )

        if not credencial:

            raise Exception(
                "La cuenta no posee una credencial registrada."
            )

        credencial.password_hash = (
            self.password_hasher
            .generar_hash(
                nueva_password
            )
        )

        credencial.debe_cambiar_password = (
            False
        )

        credencial.intentos_fallidos = 0

        credencial.bloqueado_hasta = None

        credencial.fecha_ultimo_cambio = (
            timezone.now()
        )

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

        # Tu tabla no tiene fecha_utilizacion,
        # así que usamos el estado UTILIZADA
        # para impedir un segundo uso.
        solicitud.estado = (
            obtener_estado(
                "UTILIZADA"
            )
        )

        solicitud.save(
            update_fields=[
                "estado",
            ]
        )

        sesiones_revocadas = (
            self.sesion_repository
            .revocar_todas(
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

            "sesiones_revocadas":
                sesiones_revocadas,

            "estado":
                "UTILIZADA",
        }