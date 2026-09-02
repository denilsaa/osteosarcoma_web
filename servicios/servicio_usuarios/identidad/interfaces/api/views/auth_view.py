from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from identidad.application.use_cases.cerrar_sesion import (
    CerrarSesionUseCase,
)
from identidad.application.use_cases.login_usuario import (
    LoginUseCase,
)
from identidad.application.use_cases.renovar_sesion import (
    RenovarSesionUseCase,
)
from identidad.application.use_cases.segundo_factor import (
    ReenviarSegundoFactorUseCase,
    VerificarSegundoFactorUseCase,
)

from identidad.infrastructure.auditoria_client import (
    registrar_evento_auditoria,
)
from identidad.infrastructure.security.jwt_manager import (
    JWTManager,
)

from identidad.interfaces.api.serializers.auth_serializer import (
    LoginSerializer,
    LogoutSerializer,
    ReenviarSegundoFactorSerializer,
    RefreshSerializer,
    VerificarSegundoFactorSerializer,
)

from identidad.models import (
    DesafioSegundoFactor,
    Usuario,
)


# ==========================================================
# UTILIDADES DE AUDITORÍA
# ==========================================================

def obtener_ip(request):
    """
    Obtiene la IP del cliente.
    Si existe X-Forwarded-For, utiliza la primera IP.
    """

    forwarded_for = request.META.get(
        "HTTP_X_FORWARDED_FOR"
    )

    if forwarded_for:
        return (
            forwarded_for
            .split(",")[0]
            .strip()
        )

    return request.META.get(
        "REMOTE_ADDR"
    )


def obtener_user_agent(request):
    """
    Obtiene el User-Agent enviado por el cliente.
    """

    return request.META.get(
        "HTTP_USER_AGENT"
    )


def buscar_usuario_por_correo(correo):
    """
    Busca un usuario para poder identificar
    al actor de un intento de autenticación.
    """

    if not correo:
        return None

    try:
        return (
            Usuario.objects
            .select_related(
                "estado_usuario"
            )
            .filter(
                correo__iexact=correo
            )
            .first()
        )

    except Exception:
        return None


def buscar_usuario_desde_refresh(
    refresh_token
):
    """
    Identifica al propietario del refresh token.

    Se utiliza solamente para determinar quién
    realiza el cierre de sesión y enviar esa
    información a Auditoría.

    La validación y revocación real de la sesión
    continúa siendo responsabilidad de
    CerrarSesionUseCase.
    """

    if not refresh_token:
        return None

    try:
        datos = (
            JWTManager()
            .validar_refresh_token(
                refresh_token
            )
        )

        usuario_id = (
            datos.get(
                "usuario_id"
            )
        )

        if not usuario_id:
            return None

        return (
            Usuario.objects
            .select_related(
                "estado_usuario"
            )
            .filter(
                id_usuario=usuario_id
            )
            .first()
        )

    except Exception:
        return None


def obtener_nombre_usuario(usuario):
    """
    Construye el nombre completo del usuario.
    """

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


def obtener_rol_usuario(usuario):
    """
    Obtiene el rol activo del usuario.
    """

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


def resultado_desde_error(error):
    """
    Determina si una operación se registra
    como FALLIDO o DENEGADO.
    """

    mensaje = str(
        error
    ).lower()

    indicadores_denegado = [
        "deshabilitado",
        "bloquead",
        "agotaron",
        "agotados",
        "límite",
        "limite",
        "deneg",
        "sin permiso",
        "no posee permiso",
    ]

    for indicador in indicadores_denegado:
        if indicador in mensaje:
            return "DENEGADO"

    return "FALLIDO"


def registrar_login_auditoria(
    *,
    usuario,
    resultado,
    request,
    etapa,
    descripcion,
    motivo=None,
):
    """
    Registra eventos relacionados con LOGIN.
    """

    return registrar_evento_auditoria(
        actor_usuario_uuid=(
            str(
                usuario.id_usuario
            )
            if usuario
            else None
        ),

        actor_nombre=(
            obtener_nombre_usuario(
                usuario
            )
        ),

        actor_rol=(
            obtener_rol_usuario(
                usuario
            )
        ),

        servicio="USUARIOS",

        modulo="AUTENTICACION",

        accion="LOGIN",

        resultado=resultado,

        entidad_tipo=(
            "USUARIO"
            if usuario
            else "AUTENTICACION"
        ),

        entidad_id=(
            str(
                usuario.id_usuario
            )
            if usuario
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

        detalle_json={
            "etapa":
                etapa,

            "actor_identificado":
                bool(
                    usuario
                ),
        },
    )


# ==========================================================
# LOGIN - PRIMER FACTOR
# ==========================================================

class LoginView(APIView):
    """
    Primer factor:
    correo + contraseña.

    Este endpoint todavía NO genera la sesión
    definitiva. El usuario debe superar el OTP.
    """

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request
    ):
        serializer = LoginSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        correo = (
            serializer
            .validated_data[
                "correo"
            ]
        )

        usuario = (
            buscar_usuario_por_correo(
                correo
            )
        )

        try:
            resultado = (
                LoginUseCase()
                .ejecutar(
                    correo,

                    serializer
                    .validated_data[
                        "password"
                    ],

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

            # ==================================================
            # IMPORTANTE
            # ==================================================
            #
            # Aquí NO registramos LOGIN EXITOSO.
            #
            # El acceso solo se considera exitoso después
            # de validar correctamente el segundo factor.
            # ==================================================

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            registrar_login_auditoria(
                usuario=usuario,

                resultado=(
                    resultado_desde_error(
                        error
                    )
                ),

                request=request,

                etapa="PRIMER_FACTOR",

                descripcion=(
                    "Intento de inicio de sesión "
                    "rechazado durante la validación "
                    "de correo y contraseña."
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
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# SEGUNDO FACTOR
# ==========================================================

class VerificarSegundoFactorView(
    APIView
):
    """
    Valida el código OTP.

    Solo si el código es correcto se registra
    LOGIN + EXITOSO.
    """

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request
    ):
        serializer = (
            VerificarSegundoFactorSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        desafio_id = (
            serializer
            .validated_data[
                "desafio_id"
            ]
        )

        desafio = (
            DesafioSegundoFactor.objects
            .select_related(
                "usuario",
                "usuario__estado_usuario",
            )
            .filter(
                id_desafio=desafio_id
            )
            .first()
        )

        usuario = (
            desafio.usuario
            if desafio
            else None
        )

        try:
            resultado = (
                VerificarSegundoFactorUseCase()
                .ejecutar(
                    desafio_id=(
                        desafio_id
                    ),

                    codigo=(
                        serializer
                        .validated_data[
                            "codigo"
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

            # ==================================================
            # LOGIN REALMENTE COMPLETADO
            # ==================================================

            registrar_login_auditoria(
                usuario=usuario,

                resultado="EXITOSO",

                request=request,

                etapa="SEGUNDO_FACTOR",

                descripcion=(
                    "Inicio de sesión completado "
                    "correctamente después de validar "
                    "el segundo factor."
                ),
            )

            return Response(
                resultado,
                status=(
                    status.HTTP_200_OK
                ),
            )

        except Exception as error:

            registrar_login_auditoria(
                usuario=usuario,

                resultado=(
                    resultado_desde_error(
                        error
                    )
                ),

                request=request,

                etapa="SEGUNDO_FACTOR",

                descripcion=(
                    "El inicio de sesión no pudo "
                    "completarse durante la validación "
                    "del segundo factor."
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
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# REENVIAR SEGUNDO FACTOR
# ==========================================================

class ReenviarSegundoFactorView(
    APIView
):
    """
    Reenvía un nuevo código OTP.
    """

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request
    ):
        serializer = (
            ReenviarSegundoFactorSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            resultado = (
                ReenviarSegundoFactorUseCase()
                .ejecutar(
                    desafio_id=(
                        serializer
                        .validated_data[
                            "desafio_id"
                        ]
                    )
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
                    .HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# LOGOUT
# ==========================================================

class LogoutView(APIView):
    """
    Cierra la sesión del usuario y registra
    automáticamente el resultado en Auditoría.
    """

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request
    ):
        serializer = LogoutSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        refresh_token = (
            serializer
            .validated_data[
                "refresh_token"
            ]
        )

        # ==================================================
        # IDENTIFICAR ACTOR ANTES DE REVOCAR LA SESIÓN
        # ==================================================

        usuario = (
            buscar_usuario_desde_refresh(
                refresh_token
            )
        )

        try:
            # ==============================================
            # CERRAR SESIÓN REAL
            # ==============================================

            resultado = (
                CerrarSesionUseCase()
                .ejecutar(
                    refresh_token
                )
            )

            # ==============================================
            # OBTENER SESIÓN DEVUELTA
            # ==============================================

            sesion = (
                resultado.get(
                    "sesion"
                )
                if isinstance(
                    resultado,
                    dict
                )
                else None
            )

            id_sesion = None

            if isinstance(
                sesion,
                dict
            ):
                id_sesion = (
                    sesion.get(
                        "id_sesion"
                    )
                )

            # ==============================================
            # AUDITORÍA - LOGOUT EXITOSO
            # ==============================================

            registrar_evento_auditoria(
                actor_usuario_uuid=(
                    str(
                        usuario.id_usuario
                    )
                    if usuario
                    else None
                ),

                actor_nombre=(
                    obtener_nombre_usuario(
                        usuario
                    )
                ),

                actor_rol=(
                    obtener_rol_usuario(
                        usuario
                    )
                ),

                servicio="USUARIOS",

                modulo="AUTENTICACION",

                accion="LOGOUT",

                resultado="EXITOSO",

                entidad_tipo=(
                    "SESION"
                    if id_sesion
                    else "USUARIO"
                ),

                entidad_id=(
                    str(
                        id_sesion
                    )
                    if id_sesion
                    else (
                        str(
                            usuario.id_usuario
                        )
                        if usuario
                        else None
                    )
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

                descripcion=(
                    "La sesión del usuario fue "
                    "cerrada correctamente."
                ),

                detalle_json={
                    "tipo_cierre":
                        "MANUAL",

                    "actor_identificado":
                        bool(
                            usuario
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

            # ==============================================
            # AUDITORÍA - LOGOUT FALLIDO / DENEGADO
            # ==============================================

            registrar_evento_auditoria(
                actor_usuario_uuid=(
                    str(
                        usuario.id_usuario
                    )
                    if usuario
                    else None
                ),

                actor_nombre=(
                    obtener_nombre_usuario(
                        usuario
                    )
                ),

                actor_rol=(
                    obtener_rol_usuario(
                        usuario
                    )
                ),

                servicio="USUARIOS",

                modulo="AUTENTICACION",

                accion="LOGOUT",

                resultado=(
                    resultado_desde_error(
                        error
                    )
                ),

                entidad_tipo="USUARIO",

                entidad_id=(
                    str(
                        usuario.id_usuario
                    )
                    if usuario
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

                descripcion=(
                    "No fue posible cerrar "
                    "la sesión solicitada."
                ),

                motivo=str(
                    error
                ),

                detalle_json={
                    "tipo_cierre":
                        "MANUAL",

                    "actor_identificado":
                        bool(
                            usuario
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
                    status
                    .HTTP_400_BAD_REQUEST
                ),
            )


# ==========================================================
# REFRESH
# ==========================================================

class RefreshView(APIView):
    """
    Renueva el access token utilizando
    un refresh token válido.
    """

    permission_classes = [
        AllowAny
    ]

    def post(
        self,
        request
    ):
        serializer = RefreshSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:
            resultado = (
                RenovarSesionUseCase()
                .ejecutar(
                    serializer
                    .validated_data[
                        "refresh_token"
                    ]
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
                    .HTTP_400_BAD_REQUEST
                ),
            )