import json

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


# ==========================================================
# CASOS DE USO
# ==========================================================

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


# ==========================================================
# AUDITORÍA
# ==========================================================

from identidad.infrastructure.auditoria_client import (
    registrar_evento_auditoria,
)


# ==========================================================
# PERMISOS
# ==========================================================

from identidad.infrastructure.permissions.oncologo_permissions import (
    PuedeActivarUsuarios,
    PuedeCrearOncologos,
    PuedeDesactivarUsuarios,
    PuedeEditarOncologos,
    PuedeListarOncologos,
)


# ==========================================================
# SERIALIZERS
# ==========================================================

from identidad.interfaces.api.serializers.estado_oncologo_serializer import (
    CambiarEstadoOncologoSerializer,
)

from identidad.interfaces.api.serializers.oncologo_serializer import (
    CrearOncologoSerializer,
    EditarOncologoSerializer,
)


# ==========================================================
# CAMPOS AUDITABLES
# ==========================================================

CAMPOS_ONCOLOGO_AUDITABLES = [

    # ------------------------------------------------------
    # DATOS PERSONALES
    # ------------------------------------------------------

    "nombres",
    "apellido_paterno",
    "apellido_materno",
    "telefono",

    # ------------------------------------------------------
    # IDENTIFICACIÓN
    # ------------------------------------------------------

    "ci_numero",
    "ci_complemento",
    "ci_expedido",

    # ------------------------------------------------------
    # ACCESO
    # ------------------------------------------------------

    "correo",
    "nombre_usuario",

    # ------------------------------------------------------
    # PROFESIONAL
    # ------------------------------------------------------

    "matricula_profesional",
    "especialidad",
    "subespecialidad",
    "area_clinica",
    "telefono_institucional",

    # ------------------------------------------------------
    # ROL / ESTADO
    # ------------------------------------------------------

    "rol_codigo",
    "estado",
]


# ==========================================================
# CAMPOS SENSIBLES
# ==========================================================
#
# Estos valores nunca deben llegar al servicio Auditoría.
# ==========================================================

CAMPOS_SENSIBLES = {
    "password",
    "password_temporal",
    "password_hash",
    "refresh_token",
    "access_token",
    "codigo",
    "codigo_otp",
    "otp",
    "token",
}


# ==========================================================
# OBTENER IP
# ==========================================================


def obtener_ip(
    request,
):
    """
    Obtiene la IP original del cliente.

    Si existe proxy inverso, primero intenta utilizar
    X-Forwarded-For.
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


# ==========================================================
# USER AGENT
# ==========================================================


def obtener_user_agent(
    request,
):
    """
    Obtiene navegador o cliente utilizado.
    """

    return (
        request.META.get(
            "HTTP_USER_AGENT"
        )
    )


# ==========================================================
# ACTOR UUID
# ==========================================================


def obtener_actor_uuid(
    request,
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


# ==========================================================
# NOMBRE DEL ACTOR
# ==========================================================


def obtener_nombre_actor(
    request,
):
    """
    Devuelve el nombre completo del usuario
    que ejecuta la operación.
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

        for parte
        in partes

        if (
            parte
            and
            str(parte).strip()
        )

    ).strip()

    if nombre:

        return nombre

    return getattr(
        usuario,
        "nombre_usuario",
        None,
    )


# ==========================================================
# ROL PRINCIPAL DEL ACTOR
# ==========================================================


def obtener_rol_actor(
    request,
):
    """
    Obtiene el rol principal activo.

    Si por datos antiguos el usuario tiene simultáneamente
    JEFE_ONCOLOGIA y ONCOLOGO, se prioriza JEFE_ONCOLOGIA.
    """

    usuario = getattr(
        request,
        "user",
        None,
    )

    if not usuario:

        return None

    try:

        asignaciones = (
            usuario
            .asignaciones_roles
            .select_related(
                "rol"
            )
            .filter(
                activo=True,
                rol__activo=True,
            )
        )

        # --------------------------------------------------
        # PRIORIZAR JEFATURA
        # --------------------------------------------------

        jefe = (
            asignaciones
            .filter(
                rol__codigo="JEFE_ONCOLOGIA"
            )
            .first()
        )

        if jefe:

            return (
                jefe.rol.nombre
                or
                jefe.rol.codigo
            )

        # --------------------------------------------------
        # OTRO ROL ACTIVO
        # --------------------------------------------------

        asignacion = (
            asignaciones
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
    """
    Convierte errores DRF en texto seguro
    para registrarlos como motivo de auditoría.
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
    datos,
):
    """
    Genera una copia segura de un diccionario.

    Contraseñas, tokens y códigos nunca abandonan
    el microservicio de Usuarios.
    """

    if not isinstance(
        datos,
        dict,
    ):

        return {}

    resultado = {}

    for clave, valor in datos.items():

        clave_normalizada = (
            str(
                clave
            )
            .strip()
            .lower()
        )

        if (
            clave_normalizada
            in
            CAMPOS_SENSIBLES
        ):

            continue

        resultado[
            clave
        ] = valor

    return resultado


# ==========================================================
# SNAPSHOT DEL PERSONAL DE ONCOLOGÍA
# ==========================================================


def obtener_snapshot_oncologo(
    usuario_id,
):
    """
    Obtiene una fotografía funcional del usuario.

    Se utiliza para calcular:

    valor anterior
        ->
    valor nuevo
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

        # --------------------------------------------------
        # IDENTIFICADOR
        # --------------------------------------------------

        "id_usuario":
            datos.get(
                "id_usuario"
            ),

        # --------------------------------------------------
        # PERSONALES
        # --------------------------------------------------

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

        "telefono":
            datos.get(
                "telefono"
            ),

        # --------------------------------------------------
        # IDENTIFICACIÓN
        # --------------------------------------------------

        "ci_numero":
            datos.get(
                "ci_numero"
            ),

        "ci_complemento":
            datos.get(
                "ci_complemento"
            ),

        "ci_expedido":
            datos.get(
                "ci_expedido"
            ),

        # --------------------------------------------------
        # ACCESO
        # --------------------------------------------------

        "correo":
            datos.get(
                "correo"
            ),

        "nombre_usuario":
            datos.get(
                "nombre_usuario"
            ),

        # --------------------------------------------------
        # PROFESIONAL
        # --------------------------------------------------

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

        "area_clinica":
            perfil.get(
                "area_clinica"
            ),

        "telefono_institucional":
            perfil.get(
                "telefono_institucional"
            ),

        # --------------------------------------------------
        # ROL
        # --------------------------------------------------

        "rol_codigo":
            datos.get(
                "rol_codigo"
            ),

        # --------------------------------------------------
        # ESTADO
        # --------------------------------------------------

        "estado":
            datos.get(
                "estado"
            ),
    }


# ==========================================================
# CONSTRUIR CAMBIOS
# ==========================================================


def construir_cambios(
    anterior,
    nuevo,
    campos=None,
):
    """
    Devuelve únicamente los campos cuyo valor
    cambió realmente.
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
            in
            CAMPOS_SENSIBLES
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
# CAMBIOS DE CREACIÓN
# ==========================================================


def construir_cambios_creacion(
    snapshot,
):
    """
    Para una creación:

    anterior = NULL
    nuevo    = valor creado
    """

    if not snapshot:

        return []

    cambios = []

    for campo in (
        CAMPOS_ONCOLOGO_AUDITABLES
    ):

        if (
            campo
            in
            CAMPOS_SENSIBLES
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
# AUDITORÍA DE ONCÓLOGOS
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
    Registra eventos globales de Gestión de Oncólogos.

    IMPORTANTE:

    Este evento se envía al servicio global de Auditoría.

    El historial funcional propio del usuario permanece
    dentro del servicio Usuarios.
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
# MIXIN DE AUDITORÍA DE PERMISOS
# ==========================================================


class AuditoriaPermisosOncologoMixin:
    """
    Registra intentos rechazados por permisos.

    Resultados posibles:

    EXITOSO
    FALLIDO
    DENEGADO
    """

    def obtener_accion_denegada(
        self,
        request,
    ):

        metodo = (
            request.method
            .strip()
            .upper()
        )

        if metodo == "POST":

            return "CREAR"

        if metodo == "PUT":

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

    # ======================================================
    # PERMISO DENEGADO
    # ======================================================

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
                str(
                    message
                )
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
# LISTAR / CREAR PERSONAL DE ONCOLOGÍA
# ==========================================================


class OncologoListCreateAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self,
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
        request,
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

            rol = (
                request
                .query_params
                .get(
                    "rol"
                )
            )

            resultado = (
                ListarOncologosUseCase()
                .ejecutar(
                    buscar=buscar,
                    estado=estado,
                    rol=rol,
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

    # ======================================================
    # CREAR
    # ======================================================

    def post(
        self,
        request,
    ):

        serializer = (
            CrearOncologoSerializer(
                data=request.data
            )
        )

        # ==================================================
        # ERROR DE VALIDACIÓN
        # ==================================================

        if not serializer.is_valid():

            registrar_auditoria_oncologo(

                request=request,

                accion="CREAR",

                resultado="FALLIDO",

                descripcion=(
                    "No fue posible registrar "
                    "la cuenta del profesional "
                    "de Oncología."
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
            # CREAR CUENTA
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
            # SNAPSHOT
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
            # ROL CREADO
            # ==============================================

            rol_codigo = (
                getattr(
                    usuario,
                    "rol_codigo_creado",
                    None,
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
                    "cuenta del personal de Oncología."
                ),

                cambios=cambios,

                detalle_json={

                    "usuario_generado":
                        usuario.nombre_usuario,

                    "rol_asignado":
                        rol_codigo,

                    "correo_credenciales_enviado":
                        bool(
                            getattr(
                                usuario,
                                "correo_credenciales_enviado",
                                False,
                            )
                        ),

                    "cantidad_cambios":
                        len(
                            cambios
                        ),
                },
            )

            # ==============================================
            # RESPUESTA
            # ==============================================
            #
            # IMPORTANTE:
            # La contraseña temporal NO se devuelve.
            # ==============================================

            return Response(
                {

                    "mensaje": (
                        "Profesional de Oncología "
                        "registrado correctamente."
                    ),

                    "oncologo": {

                        "id_usuario":
                            usuario_id,

                        "nombre_usuario":
                            usuario.nombre_usuario,

                        "correo":
                            usuario.correo,

                        "rol_codigo":
                            rol_codigo,

                        "nombre_completo":
                            usuario.nombre_completo,

                    },

                    "correo_credenciales_enviado":
                        bool(
                            getattr(
                                usuario,
                                "correo_credenciales_enviado",
                                False,
                            )
                        ),
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
                    "la cuenta del profesional "
                    "de Oncología."
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
# DETALLE / EDICIÓN
# ==========================================================


class OncologoDetailAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self,
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
    # CONSULTAR
    # ======================================================

    def get(
        self,
        request,
        usuario_id,
    ):

        try:

            resultado = (
                ObtenerOncologoUseCase()
                .ejecutar(
                    usuario_id
                )
            )

            registrar_auditoria_oncologo(

                request=request,

                accion="CONSULTAR",

                resultado="EXITOSO",

                usuario_id=usuario_id,

                descripcion=(
                    "Se consultó la ficha "
                    "de un profesional de Oncología."
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
                    "la ficha del profesional "
                    "de Oncología."
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
        usuario_id,
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
                    "La modificación del profesional "
                    "de Oncología fue rechazada "
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

                    usuario_editor=(
                        request.user
                    ),
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

            # ==============================================
            # CAMPOS ENVIADOS
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
                    "del profesional de Oncología."
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

            # ==============================================
            # RESPUESTA
            # ==============================================

            return Response(
                {

                    "mensaje": (
                        "Profesional de Oncología "
                        "actualizado correctamente."
                    ),

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
                    "los datos del profesional "
                    "de Oncología."
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
# ACTIVAR / DESACTIVAR
# ==========================================================


class OncologoEstadoAPIView(
    AuditoriaPermisosOncologoMixin,
    APIView,
):

    # ======================================================
    # PERMISOS
    # ======================================================

    def get_permissions(
        self,
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
        usuario_id,
    ):

        serializer = (
            CambiarEstadoOncologoSerializer(
                data=request.data
            )
        )

        # ==================================================
        # ERROR DE VALIDACIÓN
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

                if (
                    estado_solicitado
                    ==
                    "ACTIVO"
                )

                else (
                    "DESACTIVAR"

                    if (
                        estado_solicitado
                        ==
                        "INACTIVO"
                    )

                    else
                    "EDITAR"
                )
            )

            registrar_auditoria_oncologo(

                request=request,

                accion=accion,

                resultado="FALLIDO",

                usuario_id=usuario_id,

                descripcion=(
                    "El cambio de estado "
                    "del profesional de Oncología "
                    "fue rechazado."
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

            if (
                nuevo_estado
                ==
                "ACTIVO"
            )

            else
            "DESACTIVAR"
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

            resultado = (
                CambiarEstadoOncologoUseCase()
                .ejecutar(

                    usuario_id,

                    nuevo_estado,
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
                    "El historial del usuario se conserva."
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
                    "del profesional de Oncología."

                    if (
                        nuevo_estado
                        ==
                        "ACTIVO"
                    )

                    else

                    "Se desactivó la cuenta "
                    "del profesional de Oncología."

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
                    "el estado del profesional "
                    "de Oncología."
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