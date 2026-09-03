import json

from rest_framework import status

from rest_framework.response import (
    Response,
)

from rest_framework.views import (
    APIView,
)


from identidad.application.use_cases.administrar_permisos import (
    ActualizarPermisosOncologoUseCase,
    ObtenerPermisosOncologoUseCase,
)


from identidad.infrastructure.auditoria_client import (
    registrar_evento_auditoria,
)


from identidad.infrastructure.permissions.recuperacion_permissions import (
    EsJefeOncologia,
)


from identidad.interfaces.api.serializers.permiso_serializer import (
    ActualizarPermisosOncologoSerializer,
)


# ==========================================================
# UTILIDADES DEL REQUEST
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
# ACTOR
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
            or asignacion.rol.codigo
        )

    except Exception:

        return None


# ==========================================================
# ERRORES
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
# SNAPSHOT DE PERMISOS
# ==========================================================

def obtener_permisos_asignados():
    """
    Devuelve únicamente los códigos actualmente
    asignados al rol ONCOLOGO.
    """

    resultado = (
        ObtenerPermisosOncologoUseCase()
        .ejecutar()
    )

    permisos = (
        resultado.get(
            "permisos",
            []
        )
    )

    asignados = []

    for permiso in permisos:

        if permiso.get(
            "asignado"
        ):

            asignados.append(
                permiso.get(
                    "codigo"
                )
            )

    return sorted(
        codigo
        for codigo in asignados
        if codigo
    )


# ==========================================================
# CONSTRUIR CAMBIOS
# ==========================================================

def construir_cambios_permisos(
    anteriores,
    nuevos,
):
    """
    Genera un cambio independiente por permiso.

    Ejemplo:

    permiso:PACIENTE_GESTIONAR
    NO_ASIGNADO -> ASIGNADO
    """

    anteriores = set(
        anteriores
        or []
    )

    nuevos = set(
        nuevos
        or []
    )

    todos = sorted(
        anteriores
        |
        nuevos
    )

    cambios = []

    for codigo in todos:

        estaba = (
            codigo
            in anteriores
        )

        esta = (
            codigo
            in nuevos
        )

        if estaba == esta:
            continue

        cambios.append(
            {
                "campo":
                    f"permiso:{codigo}",

                "valor_anterior":
                    (
                        "ASIGNADO"
                        if estaba
                        else "NO_ASIGNADO"
                    ),

                "valor_nuevo":
                    (
                        "ASIGNADO"
                        if esta
                        else "NO_ASIGNADO"
                    ),
            }
        )

    return cambios


# ==========================================================
# REGISTRAR AUDITORÍA
# ==========================================================

def registrar_auditoria_permisos(
    *,
    request,
    accion,
    resultado,
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

        modulo="PERMISOS",

        accion=accion,

        resultado=resultado,

        entidad_tipo="ROL",

        entidad_id="ONCOLOGO",

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
# PERMISOS DENEGADOS
# ==========================================================

class AuditoriaPermisosRolMixin:

    def permission_denied(
        self,
        request,
        message=None,
        code=None,
    ):
        accion = (
            "EDITAR"
            if request.method
            in (
                "PUT",
                "PATCH",
            )
            else "CONSULTAR"
        )

        registrar_auditoria_permisos(

            request=request,

            accion=accion,

            resultado="DENEGADO",

            descripcion=(
                "El usuario intentó administrar "
                "los permisos del rol ONCOLOGO "
                "sin autorización."
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
            },
        )

        return super().permission_denied(
            request,
            message=message,
            code=code,
        )


# ==========================================================
# PERMISOS DEL ROL ONCÓLOGO
# ==========================================================

class PermisosOncologoJefaturaAPIView(
    AuditoriaPermisosRolMixin,
    APIView,
):
    """
    Permite a Jefatura consultar y actualizar
    los permisos administrables del rol ONCOLOGO.
    """

    permission_classes = [
        EsJefeOncologia
    ]

    # ======================================================
    # CONSULTAR
    # ======================================================

    def get(
        self,
        request,
    ):
        try:

            resultado = (
                ObtenerPermisosOncologoUseCase()
                .ejecutar()
            )

            registrar_auditoria_permisos(

                request=request,

                accion="CONSULTAR",

                resultado="EXITOSO",

                descripcion=(
                    "Se consultaron los permisos "
                    "asignados al rol ONCOLOGO."
                ),

                detalle_json={
                    "rol":
                        "ONCOLOGO",

                    "total":
                        resultado.get(
                            "total",
                            0,
                        ),
                },
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            registrar_auditoria_permisos(

                request=request,

                accion="CONSULTAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible consultar "
                    "los permisos del rol ONCOLOGO."
                ),

                motivo=str(
                    error
                ),
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

    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def put(
        self,
        request,
    ):
        serializer = (
            ActualizarPermisosOncologoSerializer(
                data=request.data
            )
        )

        # ==================================================
        # VALIDACIÓN FALLIDA
        # ==================================================

        if not serializer.is_valid():

            registrar_auditoria_permisos(

                request=request,

                accion="EDITAR",

                resultado="FALLIDO",

                descripcion=(
                    "La actualización de permisos "
                    "del rol ONCOLOGO fue rechazada "
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

        # ==================================================
        # ESTADO ANTERIOR
        # ==================================================

        try:

            anteriores = (
                obtener_permisos_asignados()
            )

        except Exception as error:

            registrar_auditoria_permisos(

                request=request,

                accion="EDITAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible obtener "
                    "el estado anterior de permisos."
                ),

                motivo=str(
                    error
                ),
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

        permisos_solicitados = (
            serializer
            .validated_data[
                "permisos"
            ]
        )

        try:

            # ==============================================
            # ACTUALIZACIÓN REAL
            # ==============================================

            resultado = (
                ActualizarPermisosOncologoUseCase()
                .ejecutar(
                    permisos_solicitados
                )
            )

            # ==============================================
            # ESTADO NUEVO
            # ==============================================

            nuevos = (
                obtener_permisos_asignados()
            )

            cambios = (
                construir_cambios_permisos(
                    anteriores,
                    nuevos,
                )
            )

            agregados = sorted(
                set(
                    nuevos
                )
                -
                set(
                    anteriores
                )
            )

            retirados = sorted(
                set(
                    anteriores
                )
                -
                set(
                    nuevos
                )
            )

            # ==============================================
            # AUDITORÍA
            # ==============================================

            registrar_auditoria_permisos(

                request=request,

                accion="EDITAR",

                resultado="EXITOSO",

                descripcion=(
                    "Se actualizaron los permisos "
                    "asignados al rol ONCOLOGO."
                ),

                cambios=cambios,

                detalle_json={

                    "rol":
                        "ONCOLOGO",

                    "permisos_anteriores":
                        anteriores,

                    "permisos_nuevos":
                        nuevos,

                    "permisos_agregados":
                        agregados,

                    "permisos_retirados":
                        retirados,

                    "cantidad_cambios":
                        len(
                            cambios
                        ),
                },
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            registrar_auditoria_permisos(

                request=request,

                accion="EDITAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible actualizar "
                    "los permisos del rol ONCOLOGO."
                ),

                motivo=str(
                    error
                ),

                detalle_json={
                    "permisos_solicitados":
                        permisos_solicitados,
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

    # ======================================================
    # PATCH
    # ======================================================

    def patch(
        self,
        request,
    ):
        return self.put(
            request
        )