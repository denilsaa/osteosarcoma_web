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
    Genera un token de recuperación de alta entropía.

    IMPORTANTE:
    El token solamente se genera después de que
    Jefatura aprueba la solicitud.
    """

    return secrets.token_urlsafe(
        48
    )


def hash_token_recuperacion(
    token,
):
    """
    En base de datos se almacena únicamente SHA-256(token).

    El token real solamente existe temporalmente
    para construir el enlace enviado al correo.
    """

    return hashlib.sha256(
        token.encode(
            "utf-8"
        )
    ).hexdigest()


def obtener_estado(
    codigo,
):
    """
    Obtiene un estado de recuperación por código.
    """

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
    """
    Construye el nombre completo de un usuario.
    """

    return " ".join(
        str(parte).strip()

        for parte
        in [
            usuario.nombres,
            usuario.apellido_paterno,
            usuario.apellido_materno,
        ]

        if (
            parte
            and
            str(parte).strip()
        )
    )


def actualizar_expiracion_si_corresponde(
    solicitud,
):
    """
    PENDIENTE:
        vence si Jefatura no responde dentro del
        plazo general.

    APROBADA:
        vence si el usuario no utiliza el enlace
        dentro del plazo configurado.
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

        # --------------------------------------------------
        # INVALIDAR TOKEN
        # --------------------------------------------------

        solicitud.token_recuperacion = (
            None
        )

        solicitud.save(
            update_fields=[
                "estado",
                "token_recuperacion",
            ]
        )

    return solicitud


# ==========================================================
# VALIDAR JEFE DE ONCOLOGÍA
# ==========================================================


def validar_jefe_oncologia(
    usuario,
):
    """
    Verifica que el usuario:

    - exista;
    - tenga cuenta operativa;
    - tenga rol JEFE_ONCOLOGIA activo.
    """

    if not usuario:

        raise Exception(
            "No se pudo identificar al usuario revisor."
        )

    # ------------------------------------------------------
    # ESTADO DEL USUARIO
    # ------------------------------------------------------

    estado_usuario = getattr(
        usuario,
        "estado_usuario",
        None,
    )

    if (
        not estado_usuario
        or
        not estado_usuario.es_operativo
    ):

        raise Exception(
            "La cuenta del revisor no se encuentra activa."
        )

    # ------------------------------------------------------
    # ROL DE JEFATURA
    # ------------------------------------------------------

    es_jefe = (
        usuario
        .asignaciones_roles
        .filter(
            activo=True,
            rol__activo=True,
            rol__codigo="JEFE_ONCOLOGIA",
        )
        .exists()
    )

    if not es_jefe:

        raise Exception(
            "Solo un Jefe de Oncología "
            "puede resolver solicitudes de recuperación."
        )

    return True


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

        # --------------------------------------------------
        # Actualmente IP y user-agent se reciben para
        # auditoría, pero no se almacenan directamente
        # en SolicitudRecuperacion.
        # --------------------------------------------------

        del ip_origen
        del user_agent

        correo = (
            correo
            .strip()
            .lower()
        )

        # ==================================================
        # RESPUESTA GENÉRICA
        # ==================================================
        #
        # No revelar si el correo existe.
        # ==================================================

        respuesta_generica = {
            "mensaje": (
                "Solicitud recibida. Si el correo pertenece "
                "a una cuenta activa, Jefatura de Oncología "
                "podrá revisarla. Si es aprobada, recibirá "
                "un enlace seguro en el correo institucional "
                "registrado."
            )
        }

        # ==================================================
        # BUSCAR USUARIO
        # ==================================================

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

        if (
            not usuario
            or
            not usuario
                .estado_usuario
                .es_operativo
        ):

            return respuesta_generica

        # ==================================================
        # EVITAR SOLICITUDES REPETIDAS MUY RÁPIDAS
        # ==================================================

        limite_repeticion = (
            timezone.now()
            -
            timedelta(
                seconds=60
            )
        )

        solicitud_reciente = (
            SolicitudRecuperacion.objects
            .filter(
                usuario=usuario,
                estado__codigo="PENDIENTE",
                fecha_solicitud__gte=(
                    limite_repeticion
                ),
            )
            .exists()
        )

        if solicitud_reciente:

            return respuesta_generica

        # ==================================================
        # ESTADOS
        # ==================================================

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
                estado=estado_expirada,
                token_recuperacion=None,
            )
        )

        # ==================================================
        # CREAR SOLICITUD
        # ==================================================
        #
        # Mientras esté PENDIENTE:
        # NO existe token utilizable.
        # ==================================================

        SolicitudRecuperacion.objects.create(
            id_solicitud=uuid.uuid4(),
            usuario=usuario,
            estado=estado_pendiente,
            token_recuperacion=None,
            fecha_expiracion=(
                timezone.now()
                +
                timedelta(
                    hours=24
                )
            ),
        )

        return respuesta_generica


# ==========================================================
# CONSULTAR ESTADO DEL ENLACE
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
                token_recuperacion=(
                    token_hash
                )
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "El enlace de recuperación "
                "no es válido o ya no está disponible."
            )

        # ==================================================
        # EXPIRACIÓN
        # ==================================================

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

        # ==================================================
        # MENSAJES
        # ==================================================

        mensajes = {

            "APROBADA":
                (
                    "El enlace es válido. "
                    "Puede establecer una nueva contraseña."
                ),

            "RECHAZADA":
                (
                    "La solicitud fue rechazada "
                    "por Jefatura de Oncología."
                ),

            "UTILIZADA":
                (
                    "Este enlace ya fue utilizado."
                ),

            "EXPIRADA":
                (
                    "El enlace de recuperación expiró. "
                    "Solicite uno nuevo."
                ),

            "PENDIENTE":
                (
                    "La solicitud todavía "
                    "no está autorizada."
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
                (
                    codigo_estado
                    ==
                    "APROBADA"
                ),

            "mensaje":
                mensajes.get(
                    codigo_estado,
                    "Estado de recuperación desconocido.",
                ),

            "fecha_expiracion":
                (
                    solicitud
                    .fecha_expiracion
                    .isoformat()
                ),
        }


# ==========================================================
# LISTAR RECUPERACIONES PARA JEFATURA
# ==========================================================


class ListarRecuperacionesUseCase:

    def ejecutar(
        self,
        estado=None,
        usuario_revisor=None,
    ):
        """
        Lista solicitudes de recuperación.

        Si usuario_revisor es enviado, agrega información
        que permitirá a frontend saber si la solicitud
        pertenece al propio Jefe que está visualizando
        la bandeja.
        """

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

        # ==================================================
        # FILTRO POR ESTADO
        # ==================================================

        if estado:

            consulta = (
                consulta
                .filter(
                    estado__codigo__iexact=(
                        estado.strip()
                    )
                )
            )

        resultados = []

        # ==================================================
        # RECORRER SOLICITUDES
        # ==================================================

        for solicitud in consulta:

            solicitud = (
                actualizar_expiracion_si_corresponde(
                    solicitud
                )
            )

            # ==============================================
            # RESOLUCIÓN
            # ==============================================

            try:

                resolucion = (
                    solicitud
                    .resolucion
                )

            except ResolucionRecuperacion.DoesNotExist:

                resolucion = (
                    None
                )

            resolucion_data = (
                None
            )

            if resolucion:

                resolucion_data = {

                    "decision":
                        (
                            "APROBADA"
                            if resolucion.aprobado
                            else "RECHAZADA"
                        ),

                    "observacion":
                        resolucion.comentario,

                    "resuelto_por":
                        nombre_completo(
                            resolucion
                            .revisado_por
                        ),

                    "fecha_resolucion":
                        (
                            resolucion
                            .fecha_revision
                            .isoformat()
                        ),

                }

            # ==============================================
            # DETERMINAR SI ES SOLICITUD PROPIA
            # ==============================================

            es_solicitud_propia = (
                False
            )

            if usuario_revisor:

                es_solicitud_propia = (
                    str(
                        solicitud
                        .usuario
                        .id_usuario
                    )
                    ==
                    str(
                        usuario_revisor
                        .id_usuario
                    )
                )

            # ==============================================
            # OBJETO DE RESPUESTA
            # ==============================================

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
                        (
                            solicitud
                            .fecha_solicitud
                            .isoformat()
                        ),

                    "fecha_expiracion":
                        (
                            solicitud
                            .fecha_expiracion
                            .isoformat()
                        ),

                    "fecha_utilizacion":
                        None,

                    "resolucion":
                        resolucion_data,

                    # ======================================
                    # INFORMACIÓN PARA LA UI
                    # ======================================

                    "es_solicitud_propia":
                        es_solicitud_propia,

                    "puede_resolver":
                        (
                            solicitud
                            .estado
                            .codigo
                            ==
                            "PENDIENTE"
                            and
                            not es_solicitud_propia
                        ),

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
# RESOLVER RECUPERACIÓN
# ==========================================================


class ResolverRecuperacionUseCase:
    """
    Aprueba o rechaza una solicitud.

    REGLAS:

    1. Solo JEFE_ONCOLOGIA activo puede resolver.

    2. Un Jefe jamás puede aprobar o rechazar
       su propia solicitud.

    3. La solicitud debe estar PENDIENTE.

    4. Una solicitud solo puede resolverse una vez.

    5. El token solamente se genera al aprobar.

    6. Si falla SMTP, la transacción completa
       se revierte.
    """

    # ======================================================
    # EJECUTAR
    # ======================================================

    @transaction.atomic
    def ejecutar(
        self,
        solicitud_id,
        jefe,
        decision,
        observacion=None,
    ):

        # ==================================================
        # VALIDAR JEFE
        # ==================================================

        validar_jefe_oncologia(
            jefe
        )

        # ==================================================
        # NORMALIZAR DECISIÓN
        # ==================================================

        decision = (
            str(
                decision
            )
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

        # ==================================================
        # OBTENER SOLICITUD CON BLOQUEO
        # ==================================================

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "usuario__estado_usuario",
                "estado",
            )
            .filter(
                id_solicitud=(
                    solicitud_id
                )
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "La solicitud de recuperación no existe."
            )

        # ==================================================
        # PROHIBIR AUTORESOLUCIÓN
        # ==================================================
        #
        # Esta validación está en backend.
        #
        # Aunque alguien intente llamar directamente
        # al endpoint, no puede saltarse la regla.
        # ==================================================

        if (
            str(
                solicitud
                .usuario
                .id_usuario
            )
            ==
            str(
                jefe
                .id_usuario
            )
        ):

            raise Exception(
                "No puede aprobar ni rechazar "
                "su propia solicitud de recuperación. "
                "La solicitud debe ser revisada "
                "por otro Jefe de Oncología."
            )

        # ==================================================
        # VALIDAR USUARIO AFECTADO
        # ==================================================

        if (
            not solicitud
            .usuario
            .estado_usuario
            .es_operativo
        ):

            raise Exception(
                "La cuenta que solicita la recuperación "
                "no se encuentra activa."
            )

        # ==================================================
        # ACTUALIZAR EXPIRACIÓN
        # ==================================================

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

        # ==================================================
        # VALIDAR ESTADO DE SOLICITUD
        # ==================================================

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

        # ==================================================
        # EVITAR DOBLE RESOLUCIÓN
        # ==================================================

        resolucion_existente = (
            ResolucionRecuperacion.objects
            .filter(
                solicitud=solicitud
            )
            .exists()
        )

        if resolucion_existente:

            raise Exception(
                "La solicitud ya posee "
                "una resolución registrada."
            )

        # ==================================================
        # NORMALIZAR OBSERVACIÓN
        # ==================================================

        observacion_normalizada = (
            str(
                observacion
            )
            .strip()
            if observacion
            else None
        )

        # ==================================================
        # DECISIÓN
        # ==================================================

        aprobado = (
            decision
            ==
            "APROBADA"
        )

        # ==================================================
        # CREAR RESOLUCIÓN
        # ==================================================

        ResolucionRecuperacion.objects.create(
            id_resolucion=(
                uuid.uuid4()
            ),
            solicitud=solicitud,
            aprobado=aprobado,
            revisado_por=jefe,
            comentario=(
                observacion_normalizada
            ),
        )

        # ==================================================
        # ACTUALIZAR SOLICITUD
        # ==================================================

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

        # ==================================================
        # APROBAR
        # ==================================================

        if aprobado:

            # ==============================================
            # GENERAR TOKEN
            # ==============================================

            token = (
                generar_token_recuperacion()
            )

            solicitud.token_recuperacion = (
                hash_token_recuperacion(
                    token
                )
            )

            # ==============================================
            # VIGENCIA
            # ==============================================

            minutos_vigencia = int(
                getattr(
                    settings,
                    "RECOVERY_LINK_MINUTES",
                    15,
                )
            )

            solicitud.fecha_expiracion = (
                timezone.now()
                +
                timedelta(
                    minutes=(
                        minutos_vigencia
                    )
                )
            )

            campos_actualizados.extend(
                [
                    "token_recuperacion",
                    "fecha_expiracion",
                ]
            )

            solicitud.save(
                update_fields=(
                    campos_actualizados
                )
            )

            # ==============================================
            # CORREO
            # ==============================================

            try:

                EmailService().enviar_enlace_recuperacion(

                    usuario=(
                        solicitud.usuario
                    ),

                    token=token,

                    minutos_vigencia=(
                        minutos_vigencia
                    ),

                    observacion=(
                        observacion_normalizada
                    ),
                )

            except Exception as error:

                raise Exception(
                    "No se pudo enviar el enlace "
                    "al correo institucional. "
                    "La aprobación no fue aplicada. "
                    "Revise la configuración SMTP."
                ) from error

            # ==============================================
            # RESPUESTA
            # ==============================================

            return {

                "id_solicitud":
                    str(
                        solicitud
                        .id_solicitud
                    ),

                "estado":
                    "APROBADA",

                "correo_enviado":
                    True,

                "revisado_por":
                    nombre_completo(
                        jefe
                    ),

                "mensaje": (
                    "Recuperación aprobada correctamente. "
                    "Se envió un enlace seguro al correo "
                    "institucional registrado."
                ),

            }

        # ==================================================
        # RECHAZAR
        # ==================================================

        solicitud.token_recuperacion = (
            None
        )

        solicitud.fecha_expiracion = (
            timezone.now()
        )

        campos_actualizados.extend(
            [
                "token_recuperacion",
                "fecha_expiracion",
            ]
        )

        solicitud.save(
            update_fields=(
                campos_actualizados
            )
        )

        # ==================================================
        # CORREO DE RECHAZO
        # ==================================================

        try:

            EmailService().enviar_notificacion_rechazo(

                usuario=(
                    solicitud.usuario
                ),

                observacion=(
                    observacion_normalizada
                ),
            )

        except Exception as error:

            raise Exception(
                "No se pudo enviar el correo "
                "de rechazo al correo institucional. "
                "La resolución no fue aplicada. "
                "Revise la configuración SMTP."
            ) from error

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {

            "id_solicitud":
                str(
                    solicitud
                    .id_solicitud
                ),

            "estado":
                "RECHAZADA",

            "correo_enviado":
                True,

            "revisado_por":
                nombre_completo(
                    jefe
                ),

            "mensaje": (
                "Solicitud rechazada correctamente. "
                "Se notificó la decisión al correo "
                "institucional registrado."
            ),

        }


# ==========================================================
# CAMBIAR CONTRASEÑA DESDE EL ENLACE
# ==========================================================


class CambiarPasswordRecuperacionUseCase:

    def __init__(
        self
    ):

        self.password_hasher = (
            PasswordHasher()
        )

        self.sesion_repository = (
            SesionRepository()
        )

    # ======================================================
    # EJECUTAR
    # ======================================================

    @transaction.atomic
    def ejecutar(
        self,
        token,
        nueva_password,
    ):

        # ==================================================
        # HASH DEL TOKEN
        # ==================================================

        token_hash = (
            hash_token_recuperacion(
                token
            )
        )

        # ==================================================
        # OBTENER SOLICITUD
        # ==================================================

        solicitud = (
            SolicitudRecuperacion.objects
            .select_for_update()
            .select_related(
                "usuario",
                "estado",
            )
            .filter(
                token_recuperacion=(
                    token_hash
                )
            )
            .first()
        )

        if not solicitud:

            raise Exception(
                "El enlace de recuperación "
                "no es válido o ya no está disponible."
            )

        # ==================================================
        # EXPIRACIÓN
        # ==================================================

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

        # ==================================================
        # VALIDACIONES
        # ==================================================

        if (
            codigo_estado
            ==
            "EXPIRADA"
        ):

            raise Exception(
                "El enlace de recuperación expiró. "
                "Solicite uno nuevo."
            )

        if (
            codigo_estado
            ==
            "UTILIZADA"
        ):

            raise Exception(
                "Este enlace ya fue utilizado."
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

        # ==================================================
        # VALIDAR RESOLUCIÓN
        # ==================================================

        try:

            resolucion = (
                solicitud
                .resolucion
            )

        except ResolucionRecuperacion.DoesNotExist:

            resolucion = (
                None
            )

        if (
            not resolucion
            or
            not resolucion.aprobado
        ):

            raise Exception(
                "La recuperación no posee una "
                "aprobación válida de Jefatura."
            )

        # ==================================================
        # CREDENCIAL
        # ==================================================

        credencial = (
            Credencial.objects
            .select_for_update()
            .filter(
                usuario=(
                    solicitud.usuario
                )
            )
            .first()
        )

        if not credencial:

            raise Exception(
                "La cuenta no posee "
                "una credencial registrada."
            )

        # ==================================================
        # NUEVO HASH
        # ==================================================

        credencial.password_hash = (
            self
            .password_hasher
            .generar_hash(
                nueva_password
            )
        )

        # ==================================================
        # RESTABLECER SEGURIDAD
        # ==================================================

        credencial.debe_cambiar_password = (
            False
        )

        credencial.intentos_fallidos = (
            0
        )

        credencial.bloqueado_hasta = (
            None
        )

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

        # ==================================================
        # MARCAR COMO UTILIZADA
        # ==================================================

        solicitud.estado = (
            obtener_estado(
                "UTILIZADA"
            )
        )

        # ==================================================
        # DESTRUIR TOKEN
        # ==================================================

        solicitud.token_recuperacion = (
            None
        )

        solicitud.save(
            update_fields=[
                "estado",
                "token_recuperacion",
            ]
        )

        # ==================================================
        # REVOCAR TODAS LAS SESIONES
        # ==================================================

        sesiones_revocadas = (
            self
            .sesion_repository
            .revocar_todas(

                solicitud.usuario,

                (
                    "Cambio de contraseña mediante "
                    "recuperación aprobada"
                ),
            )
        )

        # ==================================================
        # RESPUESTA
        # ==================================================

        return {

            "mensaje": (
                "Contraseña actualizada correctamente. "
                "Ya puede iniciar sesión "
                "con su nueva contraseña."
            ),

            "sesiones_revocadas":
                sesiones_revocadas,

            "estado":
                "UTILIZADA",

        }