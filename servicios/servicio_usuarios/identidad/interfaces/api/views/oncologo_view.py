import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


from identidad.application.use_cases.cambiar_estado_oncologo import (
    CambiarEstadoOncologoUseCase,
)

from identidad.application.use_cases.crear_oncologo import (
    CrearOncologoUseCase,
)

from identidad.application.use_cases.editar_oncologo import (
    EditarOncologoUseCase,
)

from identidad.application.use_cases.listar_oncologos import (
    ListarOncologosUseCase,
)

from identidad.application.use_cases.obtener_oncologo import (
    ObtenerOncologoUseCase,
)


from identidad.infrastructure.auditoria_client import (
    registrar_evento_auditoria,
)


from identidad.infrastructure.permissions.oncologo_permissions import (
    PuedeActivarUsuarios,
    PuedeCrearOncologos,
    PuedeDesactivarUsuarios,
    PuedeEditarOncologos,
    PuedeListarOncologos,
)


from identidad.interfaces.api.serializers.estado_oncologo_serializer import (
    CambiarEstadoOncologoSerializer,
)

from identidad.interfaces.api.serializers.oncologo_serializer import (
    CrearOncologoSerializer,
    EditarOncologoSerializer,
)


# ==========================================================
# CAMPOS QUE PUEDEN APARECER EN EL HISTORIAL
# ==========================================================

CAMPOS_ONCOLOGO_AUDITABLES = [
    "nombres",
    "apellido_paterno",
    "apellido_materno",
    "correo",
    "nombre_usuario",
    "telefono",
    "matricula_profesional",
    "especialidad",
    "subespecialidad",
    "telefono_institucional",
    "estado",
]


# ==========================================================
# CAMPOS SENSIBLES
# ==========================================================
#
# Nunca deben aparecer en Auditoría.
# ==========================================================

CAMPOS_SENSIBLES = {
    "password",
    "password_hash",
    "refresh_token",
    "access_token",
    "codigo",
    "codigo_otp",
}


# ==========================================================
# UTILIDADES DE REQUEST
# ==========================================================

def obtener_ip(
    request
):
    """
    Obtiene la IP original del cliente.
    """

    forwarded_for = (
        request.META.get(
            "HTTP_X_FORWARDED_FOR"
        )
    )

    if forwarded_for:

        return (
            forwarded_for
            .split(",")[0]
            .strip()
        )

    return (
        request.META.get(
            "REMOTE_ADDR"
        )
    )


def obtener_user_agent(
    request
):
    """
    Obtiene el navegador o cliente utilizado.
    """

    return (
        request.META.get(
            "HTTP_USER_AGENT"
        )
    )


# ==========================================================
# UTILIDADES DEL ACTOR
# ==========================================================

def obtener_actor_uuid(
    request
):
    """
    Devuelve el UUID del usuario autenticado.
    """

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
    request
):
    """
    Obtiene el nombre completo del usuario
    que está realizando la operación.
    """

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
    request
):
    """
    Obtiene el rol activo principal del usuario
    que realiza la acción.
    """

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
    errores
):
    """
    Convierte errores del serializer a texto
    para almacenarlos como motivo.
    """

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
# LIMPIAR DATOS SENSIBLES
# ==========================================================

def limpiar_datos_sensibles(
    datos
):
    """
    Devuelve una versión segura del diccionario.

    Password, tokens y códigos nunca salen
    del microservicio de Usuarios.
    """

    if not isinstance(
        datos,
        dict,
    ):
        return {}

    resultado = {}

    for clave, valor in datos.items():

        if (
            clave.lower()
            in CAMPOS_SENSIBLES
        ):
            continue

        resultado[
            clave
        ] = valor

    return resultado


# ==========================================================
# OBTENER SNAPSHOT DE ONCÓLOGO
# ==========================================================

def obtener_snapshot_oncologo(
    usuario_id
):
    """
    Obtiene una fotografía del oncólogo para
    comparar valor anterior y valor nuevo.
    """

    if not usuario_id:
        return None

    try:

        datos = (
            ObtenerOncologoUseCase()
            .ejecutar(
                usuario_id
            )
        )

    except Exception:

        return None


    perfil = (
        datos.get(
            "perfil"
        )
        or {}
    )


    return {

        "id_usuario":
            datos.get(
                "id_usuario"
            ),

        "nombres":
            datos.get(
                "nombres"
            ),

        "apellido_paterno":
            datos.get(
                "apellido_paterno"
            ),

        "apellido_materno":
            datos.get(
                "apellido_materno"
            ),

        "correo":
            datos.get(
                "correo"
            ),

        "nombre_usuario":
            datos.get(
                "nombre_usuario"
            ),

        "telefono":
            datos.get(
                "telefono"
            ),

        "matricula_profesional":
            perfil.get(
                "matricula_profesional"
            ),

        "especialidad":
            perfil.get(
                "especialidad"
            ),

        "subespecialidad":
            perfil.get(
                "subespecialidad"
            ),

        "telefono_institucional":
            perfil.get(
                "telefono_institucional"
            ),

        "estado":
            datos.get(
                "estado"
            ),
    }


# ==========================================================
# CONSTRUIR CAMBIOS ANTERIOR -> NUEVO
# ==========================================================

def construir_cambios(
    anterior,
    nuevo,
    campos=None,
):
    """
    Devuelve únicamente los campos cuyo valor
    realmente cambió.
    """

    anterior = (
        anterior
        or {}
    )

    nuevo = (
        nuevo
        or {}
    )


    if campos is None:

        campos = (
            CAMPOS_ONCOLOGO_AUDITABLES
        )


    resultado = []


    for campo in campos:

        if (
            campo
            in CAMPOS_SENSIBLES
        ):
            continue


        valor_anterior = (
            anterior.get(
                campo
            )
        )

        valor_nuevo = (
            nuevo.get(
                campo
            )
        )


        if (
            valor_anterior
            ==
            valor_nuevo
        ):
            continue


        resultado.append(
            {
                "campo":
                    campo,

                "valor_anterior":
                    valor_anterior,

                "valor_nuevo":
                    valor_nuevo,
            }
        )


    return resultado


# ==========================================================
# CAMBIOS DURANTE CREACIÓN
# ==========================================================

def construir_cambios_creacion(
    snapshot
):
    """
    Para una creación, el valor anterior es NULL
    y el valor nuevo corresponde a los datos creados.
    """

    if not snapshot:
        return []


    cambios = []


    for campo in (
        CAMPOS_ONCOLOGO_AUDITABLES
    ):

        if (
            campo
            in CAMPOS_SENSIBLES
        ):
            continue


        valor = (
            snapshot.get(
                campo
            )
        )


        if valor is None:
            continue


        cambios.append(
            {
                "campo":
                    campo,

                "valor_anterior":
                    None,

                "valor_nuevo":
                    valor,
            }
        )


    return cambios


# ==========================================================
# REGISTRAR AUDITORÍA ONCÓLOGOS
# ==========================================================

def registrar_auditoria_oncologo(
    *,
    request,
    accion,
    resultado,
    usuario_id=None,
    descripcion=None,
    motivo=None,
    cambios=None,
    detalle_json=None,
):
    """
    Función central de Auditoría para Gestión
    de Oncólogos.
    """

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

        modulo="ONCOLOGOS",

        accion=accion,

        resultado=resultado,

        entidad_tipo="ONCOLOGO",

        entidad_id=(
            str(
                usuario_id
            )
            if usuario_id
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
# MIXIN - AUDITAR PERMISOS DENEGADOS
# ==========================================================

class AuditoriaPermisosOncologoMixin:
    """
    Registra también los intentos rechazados
    por falta de permisos.

    Esto permite diferenciar:

    EXITOSO
    FALLIDO
    DENEGADO
    """

    def obtener_accion_denegada(
        self,
        request
    ):

        metodo = (
            request.method
            .strip()
            .upper()
        )


        if metodo == "POST":
            return "CREAR"


        if metodo in (
            "PUT",
        ):
            return "EDITAR"


        if metodo == "PATCH":

            estado = (
                str(
                    request.data.get(
                        "estado",
                        ""
                    )
                )
                .strip()
                .upper()
            )

            if estado == "ACTIVO":
                return "ACTIVAR"

            if estado == "INACTIVO":
                return "DESACTIVAR"

            return "EDITAR"


        return "CONSULTAR"


    def permission_denied(
        self,
        request,
        message=None,
        code=None,
    ):

        usuario_id = None


        try:

            usuario_id = (
                self.kwargs.get(
                    "usuario_id"
                )
            )

        except Exception:

            usuario_id = None


        registrar_auditoria_oncologo(

            request=request,

            accion=(
                self
                .obtener_accion_denegada(
                    request
                )
            ),

            resultado="DENEGADO",

            usuario_id=usuario_id,

            descripcion=(
                "El usuario intentó realizar "
                "una acción sobre Gestión de "
                "Oncólogos sin autorización."
            ),

            motivo=(
                str(message)
                if message
                else
                "El usuario no posee el permiso requerido."
            ),

            detalle_json={
                "metodo_http":
                    request.method,

                "permiso_denegado":
                    True,
            },
        )


        return super().permission_denied(
            request,
            message=message,
            code=code,
        )


# ==========================================================
# LISTAR / CREAR ONCÓLOGOS
# ==========================================================

class OncologoListCreateAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self
    ):

        if (
            self.request.method
            ==
            "GET"
        ):

            return [
                PuedeListarOncologos()
            ]


        if (
            self.request.method
            ==
            "POST"
        ):

            return [
                PuedeCrearOncologos()
            ]


        return (
            super()
            .get_permissions()
        )


    # ======================================================
    # LISTAR
    # ======================================================

    def get(
        self,
        request
    ):

        try:

            buscar = (
                request
                .query_params
                .get(
                    "buscar"
                )
            )


            estado = (
                request
                .query_params
                .get(
                    "estado"
                )
            )


            resultado = (
                ListarOncologosUseCase()
                .ejecutar(
                    buscar=buscar,
                    estado=estado,
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
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR
                ),
            )


    # ======================================================
    # CREAR
    # ======================================================

    def post(
        self,
        request
    ):

        serializer = (
            CrearOncologoSerializer(
                data=request.data
            )
        )


        # ==================================================
        # VALIDACIÓN FALLIDA
        # ==================================================

        if not serializer.is_valid():

            registrar_auditoria_oncologo(

                request=request,

                accion="CREAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible registrar "
                    "la cuenta del oncólogo."
                ),

                motivo=(
                    serializar_errores(
                        serializer.errors
                    )
                ),

                detalle_json={
                    "etapa":
                        "VALIDACION",

                    "datos_recibidos":
                        limpiar_datos_sensibles(
                            dict(
                                request.data
                            )
                        ),
                },
            )


            return Response(
                serializer.errors,
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )


        try:

            # ==============================================
            # CREACIÓN REAL
            # ==============================================

            usuario = (
                CrearOncologoUseCase()
                .ejecutar(

                    serializer
                    .validated_data,

                    usuario_creador=(
                        request.user
                    ),
                )
            )


            usuario_id = str(
                usuario.id_usuario
            )


            # ==============================================
            # SNAPSHOT DESPUÉS DE CREAR
            # ==============================================

            nuevo = (
                obtener_snapshot_oncologo(
                    usuario_id
                )
            )


            cambios = (
                construir_cambios_creacion(
                    nuevo
                )
            )


            # ==============================================
            # AUDITORÍA
            # ==============================================

            registrar_auditoria_oncologo(

                request=request,

                accion="CREAR",

                resultado="EXITOSO",

                usuario_id=usuario_id,

                descripcion=(
                    "Se registró una nueva "
                    "cuenta de oncólogo."
                ),

                cambios=cambios,

                detalle_json={
                    "oncologo_creado":
                        (
                            nuevo.get(
                                "nombre_usuario"
                            )
                            if nuevo
                            else None
                        ),

                    "cantidad_cambios":
                        len(
                            cambios
                        ),
                },
            )


            return Response(
                {
                    "mensaje":
                        "Oncólogo registrado correctamente.",

                    "id_usuario":
                        usuario_id,
                },
                status=(
                    status.HTTP_201_CREATED
                ),
            )


        except Exception as error:

            registrar_auditoria_oncologo(

                request=request,

                accion="CREAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible registrar "
                    "la cuenta del oncólogo."
                ),

                motivo=str(
                    error
                ),

                detalle_json={
                    "etapa":
                        "CREACION",
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


# ==========================================================
# DETALLE / EDICIÓN ONCÓLOGO
# ==========================================================

class OncologoDetailAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self
    ):

        if (
            self.request.method
            ==
            "GET"
        ):

            return [
                PuedeListarOncologos()
            ]


        if (
            self.request.method
            ==
            "PUT"
        ):

            return [
                PuedeEditarOncologos()
            ]


        return (
            super()
            .get_permissions()
        )


    # ======================================================
    # CONSULTAR DETALLE
    # ======================================================

    def get(
        self,
        request,
        usuario_id
    ):

        try:

            resultado = (
                ObtenerOncologoUseCase()
                .ejecutar(
                    usuario_id
                )
            )


            # ==============================================
            # AUDITORÍA DE CONSULTA
            # ==============================================

            registrar_auditoria_oncologo(

                request=request,

                accion="CONSULTAR",

                resultado="EXITOSO",

                usuario_id=usuario_id,

                descripcion=(
                    "Se consultó la ficha "
                    "de un oncólogo."
                ),
            )


            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )


        except Exception as error:

            registrar_auditoria_oncologo(

                request=request,

                accion="CONSULTAR",

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "No fue posible consultar "
                    "la ficha del oncólogo."
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
                    status.HTTP_404_NOT_FOUND
                ),
            )


    # ======================================================
    # EDITAR
    # ======================================================

    def put(
        self,
        request,
        usuario_id
    ):

        serializer = (
            EditarOncologoSerializer(

                data=request.data,

                context={
                    "usuario_id":
                        usuario_id,
                },
            )
        )


        # ==================================================
        # VALIDACIÓN
        # ==================================================

        if not serializer.is_valid():

            registrar_auditoria_oncologo(

                request=request,

                accion="EDITAR",

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "La modificación del oncólogo "
                    "fue rechazada durante "
                    "la validación."
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
        # SNAPSHOT ANTERIOR
        # ==================================================

        anterior = (
            obtener_snapshot_oncologo(
                usuario_id
            )
        )


        try:

            usuario = (
                EditarOncologoUseCase()
                .ejecutar(

                    usuario_id,

                    serializer
                    .validated_data,
                )
            )


            # ==============================================
            # SNAPSHOT NUEVO
            # ==============================================

            nuevo = (
                obtener_snapshot_oncologo(
                    usuario_id
                )
            )


            # ==============================================
            # SOLO COMPARAR CAMPOS ENVIADOS
            # ==============================================

            campos_enviados = [

                campo

                for campo
                in serializer
                .validated_data
                .keys()

                if (
                    campo
                    not in
                    CAMPOS_SENSIBLES
                )
            ]


            cambios = (
                construir_cambios(

                    anterior,

                    nuevo,

                    campos=(
                        campos_enviados
                    ),
                )
            )


            # ==============================================
            # AUDITORÍA
            # ==============================================

            registrar_auditoria_oncologo(

                request=request,

                accion="EDITAR",

                resultado="EXITOSO",

                usuario_id=usuario_id,

                descripcion=(
                    "Se actualizaron los datos "
                    "del oncólogo."
                ),

                cambios=cambios,

                detalle_json={
                    "campos_enviados":
                        campos_enviados,

                    "cantidad_cambios":
                        len(
                            cambios
                        ),
                },
            )


            return Response(
                {
                    "mensaje":
                        "Oncólogo actualizado correctamente.",

                    "id_usuario":
                        str(
                            usuario.id_usuario
                        ),
                },
                status=(
                    status.HTTP_200_OK
                ),
            )


        except Exception as error:

            registrar_auditoria_oncologo(

                request=request,

                accion="EDITAR",

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "No fue posible actualizar "
                    "los datos del oncólogo."
                ),

                motivo=str(
                    error
                ),

                detalle_json={
                    "etapa":
                        "ACTUALIZACION",
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


# ==========================================================
# ACTIVAR / DESACTIVAR ONCÓLOGO
# ==========================================================

class OncologoEstadoAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self
    ):

        estado = (
            str(
                self.request
                .data
                .get(
                    "estado",
                    ""
                )
            )
            .strip()
            .upper()
        )


        if estado == "ACTIVO":

            return [
                PuedeActivarUsuarios()
            ]


        return [
            PuedeDesactivarUsuarios()
        ]


    # ======================================================
    # CAMBIAR ESTADO
    # ======================================================

    def patch(
        self,
        request,
        usuario_id
    ):

        serializer = (
            CambiarEstadoOncologoSerializer(
                data=request.data
            )
        )


        # ==================================================
        # VALIDACIÓN FALLIDA
        # ==================================================

        if not serializer.is_valid():

            estado_solicitado = (
                str(
                    request.data.get(
                        "estado",
                        ""
                    )
                )
                .strip()
                .upper()
            )


            accion = (
                "ACTIVAR"
                if estado_solicitado
                == "ACTIVO"

                else "DESACTIVAR"
                if estado_solicitado
                == "INACTIVO"

                else "EDITAR"
            )


            registrar_auditoria_oncologo(

                request=request,

                accion=accion,

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "El cambio de estado "
                    "del oncólogo fue rechazado."
                ),

                motivo=(
                    serializar_errores(
                        serializer.errors
                    )
                ),

                detalle_json={
                    "estado_solicitado":
                        estado_solicitado,
                },
            )


            return Response(
                serializer.errors,
                status=(
                    status.HTTP_400_BAD_REQUEST
                ),
            )


        nuevo_estado = (
            serializer
            .validated_data[
                "estado"
            ]
        )


        accion = (
            "ACTIVAR"
            if nuevo_estado
            == "ACTIVO"
            else
            "DESACTIVAR"
        )


        # ==================================================
        # ESTADO ANTERIOR
        # ==================================================

        anterior = (
            obtener_snapshot_oncologo(
                usuario_id
            )
        )


        try:

            resultado = (
                CambiarEstadoOncologoUseCase()
                .ejecutar(

                    usuario_id,

                    nuevo_estado,
                )
            )


            # ==============================================
            # ESTADO NUEVO
            # ==============================================

            nuevo = (
                obtener_snapshot_oncologo(
                    usuario_id
                )
            )


            cambios = (
                construir_cambios(

                    anterior,

                    nuevo,

                    campos=[
                        "estado"
                    ],
                )
            )


            # ==============================================
            # MENSAJE
            # ==============================================

            if (
                resultado[
                    "estado"
                ]
                ==
                "ACTIVO"
            ):

                mensaje = (
                    "Cuenta activada correctamente."
                )

            else:

                mensaje = (
                    "Cuenta desactivada correctamente. "
                    "El historial del oncólogo se conserva."
                )


            # ==============================================
            # AUDITORÍA
            # ==============================================

            registrar_auditoria_oncologo(

                request=request,

                accion=accion,

                resultado="EXITOSO",

                usuario_id=usuario_id,

                descripcion=(
                    "Se activó la cuenta "
                    "del oncólogo."
                    if nuevo_estado
                    == "ACTIVO"
                    else
                    "Se desactivó la cuenta "
                    "del oncólogo."
                ),

                cambios=cambios,

                detalle_json={

                    "estado_anterior":
                        (
                            anterior.get(
                                "estado"
                            )
                            if anterior
                            else None
                        ),

                    "estado_nuevo":
                        resultado.get(
                            "estado"
                        ),

                    "sesiones_revocadas":
                        resultado.get(
                            "sesiones_revocadas",
                            0,
                        ),
                },
            )


            return Response(
                {
                    "mensaje":
                        mensaje,

                    **resultado,
                },
                status=(
                    status.HTTP_200_OK
                ),
            )


        except Exception as error:

            registrar_auditoria_oncologo(

                request=request,

                accion=accion,

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "No fue posible cambiar "
                    "el estado del oncólogo."
                ),

                motivo=str(
                    error
                ),

                detalle_json={
                    "estado_solicitado":
                        nuevo_estado,
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