import json

from rest_framework import status

from rest_framework.permissions import (
    AllowAny,
)

from rest_framework.response import Response

from rest_framework.views import APIView


from identidad.application.use_cases.recuperacion_password import (
    CambiarPasswordRecuperacionUseCase,
    ConsultarEstadoRecuperacionUseCase,
    ListarRecuperacionesUseCase,
    ResolverRecuperacionUseCase,
    SolicitarRecuperacionUseCase,
)


from identidad.infrastructure.auditoria_client import (
    registrar_evento_auditoria,
)


from identidad.infrastructure.permissions.recuperacion_permissions import (
    EsJefeOncologia,
)


from identidad.interfaces.api.serializers.recuperacion_serializer import (
    CambiarPasswordRecuperacionSerializer,
    ResolverRecuperacionSerializer,
    SolicitarRecuperacionSerializer,
)


from identidad.models import (
    SolicitudRecuperacion,
)


# ==========================================================
# UTILIDADES GENERALES
# ==========================================================

def obtener_ip(
    request,
):
    forwarded = (
        request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )
    )

    if forwarded:

        return (
            forwarded
            .split(",")[0]
            .strip()
        )

    return request.META.get(
        "REMOTE_ADDR"
    )


def obtener_user_agent(
    request,
):
    return (
        request
        .headers
        .get(
            "User-Agent"
        )
    )


# ==========================================================
# ACTOR DE AUDITORÍA
# ==========================================================

def obtener_actor_uuid(
    request,
):
    usuario = getattr(
        request,
        "user",
        None,
    )

    if not usuario:
        return None

    usuario_id = getattr(
        usuario,
        "id_usuario",
        None,
    )

    if not usuario_id:
        return None

    return str(
        usuario_id
    )


def obtener_nombre_actor(
    request,
):
    usuario = getattr(
        request,
        "user",
        None,
    )

    if not usuario:
        return None

    partes = [
        getattr(
            usuario,
            "nombres",
            None,
        ),

        getattr(
            usuario,
            "apellido_paterno",
            None,
        ),

        getattr(
            usuario,
            "apellido_materno",
            None,
        ),
    ]

    nombre = " ".join(
        str(parte).strip()
        for parte in partes
        if parte
        and str(parte).strip()
    ).strip()

    if nombre:
        return nombre

    return getattr(
        usuario,
        "nombre_usuario",
        None,
    )


def obtener_rol_actor(
    request,
):
    usuario = getattr(
        request,
        "user",
        None,
    )

    if not usuario:
        return None

    try:

        asignacion = (
            usuario
            .asignaciones_roles
            .select_related(
                "rol"
            )
            .filter(
                activo=True,
                rol__activo=True,
            )
            .order_by(
                "-fecha_asignacion"
            )
            .first()
        )

        if not asignacion:
            return None

        return (
            asignacion.rol.nombre
            or
            asignacion.rol.codigo
        )

    except Exception:

        return None


# ==========================================================
# SERIALIZAR ERRORES
# ==========================================================

def serializar_errores(
    errores,
):
    try:

        return json.dumps(
            errores,
            ensure_ascii=False,
            default=str,
        )

    except Exception:

        return str(
            errores
        )


# ==========================================================
# ACCIÓN SEGÚN DECISIÓN
# ==========================================================

def obtener_accion_resolucion(
    decision,
):
    decision = (
        str(
            decision
            or ""
        )
        .strip()
        .upper()
    )

    if decision == "APROBADA":
        return "APROBAR"

    if decision == "RECHAZADA":
        return "RECHAZAR"

    return "EDITAR"


# ==========================================================
# SNAPSHOT DE RECUPERACIÓN
# ==========================================================

def obtener_snapshot_recuperacion(
    solicitud_id,
):
    """
    Obtiene información segura de una solicitud.

    IMPORTANTE:
    NO retorna token_recuperacion.
    """

    if not solicitud_id:
        return None

    try:

        solicitud = (
            SolicitudRecuperacion.objects
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
            return None

        usuario = (
            solicitud.usuario
        )

        nombre_usuario = " ".join(
            parte
            for parte in [
                usuario.nombres,
                usuario.apellido_paterno,
                usuario.apellido_materno,
            ]
            if parte
        )

        fecha_resolucion = getattr(
            solicitud,
            "fecha_resolucion",
            None,
        )

        return {

            "id_solicitud":
                str(
                    solicitud.id_solicitud
                ),

            "estado":
                solicitud
                .estado
                .codigo,

            "usuario_id":
                str(
                    usuario.id_usuario
                ),

            "usuario_nombre":
                nombre_usuario,

            "usuario_correo":
                usuario.correo,

            "fecha_solicitud":
                (
                    solicitud
                    .fecha_solicitud
                    .isoformat()
                    if solicitud.fecha_solicitud
                    else None
                ),

            "fecha_resolucion":
                (
                    fecha_resolucion.isoformat()
                    if fecha_resolucion
                    else None
                ),
        }

    except Exception:

        return None


# ==========================================================
# CAMBIOS DE RECUPERACIÓN
# ==========================================================

def construir_cambios_recuperacion(
    anterior,
    nuevo,
):
    """
    Registra solamente información administrativa.

    Nunca incluye:
    - token
    - password
    - hash
    """

    anterior = (
        anterior
        or {}
    )

    nuevo = (
        nuevo
        or {}
    )

    cambios = []

    # ======================================================
    # ESTADO
    # ======================================================

    if (
        anterior.get(
            "estado"
        )
        !=
        nuevo.get(
            "estado"
        )
    ):

        cambios.append(
            {
                "campo":
                    "estado",

                "valor_anterior":
                    anterior.get(
                        "estado"
                    ),

                "valor_nuevo":
                    nuevo.get(
                        "estado"
                    ),
            }
        )

    # ======================================================
    # FECHA DE RESOLUCIÓN
    # ======================================================

    if (
        anterior.get(
            "fecha_resolucion"
        )
        !=
        nuevo.get(
            "fecha_resolucion"
        )
    ):

        cambios.append(
            {
                "campo":
                    "fecha_resolucion",

                "valor_anterior":
                    anterior.get(
                        "fecha_resolucion"
                    ),

                "valor_nuevo":
                    nuevo.get(
                        "fecha_resolucion"
                    ),
            }
        )

    return cambios


# ==========================================================
# REGISTRAR AUDITORÍA DE RECUPERACIÓN
# ==========================================================

def registrar_auditoria_recuperacion(
    *,
    request,
    accion,
    resultado,
    solicitud_id=None,
    descripcion=None,
    motivo=None,
    cambios=None,
    detalle_json=None,
):
    detalle = (
        detalle_json.copy()
        if isinstance(
            detalle_json,
            dict,
        )
        else {}
    )

    detalle[
        "actor_identificado"
    ] = bool(
        obtener_actor_uuid(
            request
        )
    )

    return registrar_evento_auditoria(

        actor_usuario_uuid=(
            obtener_actor_uuid(
                request
            )
        ),

        actor_nombre=(
            obtener_nombre_actor(
                request
            )
        ),

        actor_rol=(
            obtener_rol_actor(
                request
            )
        ),

        servicio="USUARIOS",

        modulo="RECUPERACIONES",

        accion=accion,

        resultado=resultado,

        entidad_tipo="RECUPERACION",

        entidad_id=(
            str(
                solicitud_id
            )
            if solicitud_id
            else None
        ),

        direccion_ip=(
            obtener_ip(
                request
            )
        ),

        user_agent=(
            obtener_user_agent(
                request
            )
        ),

        descripcion=descripcion,

        motivo=motivo,

        detalle_json=detalle,

        cambios=(
            cambios
            or []
        ),
    )


# ==========================================================
# MIXIN - PERMISOS DENEGADOS
# ==========================================================

class AuditoriaPermisosRecuperacionMixin:
    """
    Registra intentos de acceso a funciones
    de Jefatura sin autorización.
    """

    def permission_denied(
        self,
        request,
        message=None,
        code=None,
    ):
        solicitud_id = None

        try:

            solicitud_id = (
                self.kwargs.get(
                    "solicitud_id"
                )
            )

        except Exception:

            solicitud_id = None

        decision = (
            request
            .data
            .get(
                "decision"
            )
            if hasattr(
                request,
                "data",
            )
            else None
        )

        accion = (
            obtener_accion_resolucion(
                decision
            )
            if solicitud_id
            else "CONSULTAR"
        )

        registrar_auditoria_recuperacion(

            request=request,

            accion=accion,

            resultado="DENEGADO",

            solicitud_id=solicitud_id,

            descripcion=(
                "El usuario intentó acceder "
                "a una función de recuperación "
                "reservada para Jefatura."
            ),

            motivo=(
                str(
                    message
                )
                if message
                else
                "El usuario no posee el permiso requerido."
            ),

            detalle_json={
                "permiso_denegado":
                    True,

                "metodo_http":
                    request.method,

                "decision_solicitada":
                    (
                        str(
                            decision
                        )
                        .strip()
                        .upper()
                        if decision
                        else None
                    ),
            },
        )

        return super().permission_denied(
            request,
            message=message,
            code=code,
        )


# ==========================================================
# SOLICITAR RECUPERACIÓN
# ==========================================================

class SolicitarRecuperacionAPIView(
    APIView
):

    authentication_classes = []

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request,
    ):
        serializer = (
            SolicitarRecuperacionSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            resultado = (
                SolicitarRecuperacionUseCase()
                .ejecutar(

                    correo=(
                        serializer
                        .validated_data[
                            "correo"
                        ]
                    ),

                    ip_origen=(
                        obtener_ip(
                            request
                        )
                    ),

                    user_agent=(
                        obtener_user_agent(
                            request
                        )
                    ),
                )
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            return Response(
                {
                    "error":
                        str(
                            error
                        )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# CONSULTAR ESTADO
# ==========================================================

class EstadoRecuperacionAPIView(
    APIView
):

    authentication_classes = []

    permission_classes = [
        AllowAny
    ]

    def get(
        self,
        request,
    ):
        token = (
            request
            .query_params
            .get(
                "token"
            )
        )

        if not token:

            return Response(
                {
                    "error":
                        (
                            "Debe proporcionar el "
                            "código de recuperación."
                        )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        try:

            resultado = (
                ConsultarEstadoRecuperacionUseCase()
                .ejecutar(
                    token
                )
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            return Response(
                {
                    "error":
                        str(
                            error
                        )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# CAMBIAR CONTRASEÑA
# ==========================================================

class CambiarPasswordRecuperacionAPIView(
    APIView
):

    authentication_classes = []

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request,
    ):
        serializer = (
            CambiarPasswordRecuperacionSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            resultado = (
                CambiarPasswordRecuperacionUseCase()
                .ejecutar(

                    token=(
                        serializer
                        .validated_data[
                            "token"
                        ]
                    ),

                    nueva_password=(
                        serializer
                        .validated_data[
                            "nueva_password"
                        ]
                    ),
                )
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            return Response(
                {
                    "error":
                        str(
                            error
                        )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# JEFATURA - LISTADO
# ==========================================================

class RecuperacionesJefaturaAPIView(
    AuditoriaPermisosRecuperacionMixin,
    APIView,
):

    permission_classes = [
        EsJefeOncologia
    ]

    def get(
        self,
        request,
    ):
        estado = (
            request
            .query_params
            .get(
                "estado"
            )
        )

        resultado = (
            ListarRecuperacionesUseCase()
            .ejecutar(
                estado=estado
            )
        )

        return Response(
            resultado,
            status=(
                status.HTTP_200_OK
            ),
        )


# ==========================================================
# JEFATURA - RESOLVER
# ==========================================================

class ResolverRecuperacionAPIView(
    AuditoriaPermisosRecuperacionMixin,
    APIView,
):

    permission_classes = [
        EsJefeOncologia
    ]

    def post(
        self,
        request,
        solicitud_id,
    ):
        serializer = (
            ResolverRecuperacionSerializer(
                data=request.data
            )
        )

        # ==================================================
        # VALIDACIÓN DEL PAYLOAD
        # ==================================================

        if not serializer.is_valid():

            decision_raw = (
                request
                .data
                .get(
                    "decision"
                )
            )

            accion = (
                obtener_accion_resolucion(
                    decision_raw
                )
            )

            registrar_auditoria_recuperacion(

                request=request,

                accion=accion,

                resultado="FALLIDO",

                solicitud_id=solicitud_id,

                descripcion=(
                    "La resolución de la solicitud "
                    "de recuperación fue rechazada "
                    "durante la validación."
                ),

                motivo=(
                    serializar_errores(
                        serializer.errors
                    )
                ),

                detalle_json={
                    "etapa":
                        "VALIDACION",
                },
            )

            return Response(
                serializer.errors,
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )

        decision = (
            serializer
            .validated_data[
                "decision"
            ]
            .strip()
            .upper()
        )

        observacion = (
            serializer
            .validated_data
            .get(
                "observacion"
            )
        )

        accion = (
            obtener_accion_resolucion(
                decision
            )
        )

        # ==================================================
        # SNAPSHOT ANTERIOR
        # ==================================================

        anterior = (
            obtener_snapshot_recuperacion(
                solicitud_id
            )
        )

        try:

            resultado = (
                ResolverRecuperacionUseCase()
                .ejecutar(

                    solicitud_id=(
                        solicitud_id
                    ),

                    jefe=(
                        request.user
                    ),

                    decision=decision,

                    observacion=observacion,
                )
            )

            # ==============================================
            # SNAPSHOT NUEVO
            # ==============================================

            nuevo = (
                obtener_snapshot_recuperacion(
                    solicitud_id
                )
            )

            cambios = (
                construir_cambios_recuperacion(
                    anterior,
                    nuevo,
                )
            )

            # ==============================================
            # DETALLE SEGURO
            # ==============================================

            detalle = {

                "decision":
                    decision,

                "correo_enviado":
                    resultado.get(
                        "correo_enviado",
                        False,
                    ),

                "usuario_afectado_id":
                    (
                        nuevo.get(
                            "usuario_id"
                        )
                        if nuevo
                        else (
                            anterior.get(
                                "usuario_id"
                            )
                            if anterior
                            else None
                        )
                    ),

                "usuario_afectado":
                    (
                        nuevo.get(
                            "usuario_nombre"
                        )
                        if nuevo
                        else (
                            anterior.get(
                                "usuario_nombre"
                            )
                            if anterior
                            else None
                        )
                    ),

                "usuario_correo":
                    (
                        nuevo.get(
                            "usuario_correo"
                        )
                        if nuevo
                        else (
                            anterior.get(
                                "usuario_correo"
                            )
                            if anterior
                            else None
                        )
                    ),

                "estado_anterior":
                    (
                        anterior.get(
                            "estado"
                        )
                        if anterior
                        else None
                    ),

                "estado_nuevo":
                    (
                        nuevo.get(
                            "estado"
                        )
                        if nuevo
                        else resultado.get(
                            "estado"
                        )
                    ),

                "cantidad_cambios":
                    len(
                        cambios
                    ),
            }

            registrar_auditoria_recuperacion(

                request=request,

                accion=accion,

                resultado="EXITOSO",

                solicitud_id=solicitud_id,

                descripcion=(
                    (
                        "La solicitud de recuperación "
                        "fue aprobada por Jefatura."
                    )
                    if decision
                    == "APROBADA"
                    else
                    (
                        "La solicitud de recuperación "
                        "fue rechazada por Jefatura."
                    )
                ),

                motivo=(
                    observacion
                    if observacion
                    else None
                ),

                cambios=cambios,

                detalle_json=detalle,
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            registrar_auditoria_recuperacion(

                request=request,

                accion=accion,

                resultado="FALLIDO",

                solicitud_id=solicitud_id,

                descripcion=(
                    "No fue posible resolver "
                    "la solicitud de recuperación."
                ),

                motivo=str(
                    error
                ),

                detalle_json={

                    "decision_solicitada":
                        decision,

                    "estado_actual":
                        (
                            anterior.get(
                                "estado"
                            )
                            if anterior
                            else None
                        ),

                    "usuario_afectado":
                        (
                            anterior.get(
                                "usuario_nombre"
                            )
                            if anterior
                            else None
                        ),
                },
            )

            return Response(
                {
                    "error":
                        str(
                            error
                        )
                },
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )