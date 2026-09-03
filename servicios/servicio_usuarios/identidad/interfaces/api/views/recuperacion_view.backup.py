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


from identidad.infrastructure.permissions.recuperacion_permissions import (
    EsJefeOncologia,
)


from identidad.interfaces.api.serializers.recuperacion_serializer import (
    CambiarPasswordRecuperacionSerializer,
    ResolverRecuperacionSerializer,
    SolicitarRecuperacionSerializer,
)


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

                    correo=
                        serializer
                        .validated_data[
                            "correo"
                        ],

                    ip_origen=
                        obtener_ip(
                            request
                        ),

                    user_agent=
                        request
                        .headers
                        .get(
                            "User-Agent"
                        ),

                )

            )


            return Response(

                resultado,

                status=
                    status.HTTP_200_OK,

            )

        except Exception as error:

            return Response(

                {
                    "error":
                        str(error)
                },

                status=
                    status.HTTP_400_BAD_REQUEST,

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
                        "Debe proporcionar el código de recuperación."
                },

                status=
                    status.HTTP_400_BAD_REQUEST,

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

                status=
                    status.HTTP_200_OK,

            )

        except Exception as error:

            return Response(

                {
                    "error":
                        str(error)
                },

                status=
                    status.HTTP_400_BAD_REQUEST,

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

                    token=
                        serializer
                        .validated_data[
                            "token"
                        ],

                    nueva_password=
                        serializer
                        .validated_data[
                            "nueva_password"
                        ],

                )

            )


            return Response(

                resultado,

                status=
                    status.HTTP_200_OK,

            )

        except Exception as error:

            return Response(

                {
                    "error":
                        str(error)
                },

                status=
                    status.HTTP_400_BAD_REQUEST,

            )


# ==========================================================
# JEFATURA - LISTADO
# ==========================================================

class RecuperacionesJefaturaAPIView(
    APIView
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

            status=
                status.HTTP_200_OK,

        )


# ==========================================================
# JEFATURA - RESOLVER
# ==========================================================

class ResolverRecuperacionAPIView(
    APIView
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


        serializer.is_valid(
            raise_exception=True
        )


        try:

            resultado = (

                ResolverRecuperacionUseCase()

                .ejecutar(

                    solicitud_id=
                        solicitud_id,

                    jefe=
                        request.user,

                    decision=
                        serializer
                        .validated_data[
                            "decision"
                        ],

                    observacion=
                        serializer
                        .validated_data
                        .get(
                            "observacion"
                        ),

                )

            )


            return Response(

                resultado,

                status=
                    status.HTTP_200_OK,

            )

        except Exception as error:

            return Response(

                {
                    "error":
                        str(error)
                },

                status=
                    status.HTTP_400_BAD_REQUEST,

            )