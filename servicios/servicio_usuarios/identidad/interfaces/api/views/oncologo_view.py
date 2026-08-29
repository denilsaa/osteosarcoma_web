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


class OncologoListCreateAPIView(
    APIView
):

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

        return super().get_permissions()

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
                status=status.HTTP_200_OK,
            )

        except Exception as error:

            return Response(
                {
                    "error":
                        str(error)
                },
                status=
                    status
                    .HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(
        self,
        request
    ):

        serializer = (
            CrearOncologoSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        try:

            usuario = (
                CrearOncologoUseCase()
                .ejecutar(
                    serializer
                    .validated_data,
                    usuario_creador=
                        request.user,
                )
            )

            return Response(
                {
                    "mensaje":
                        "Oncólogo registrado correctamente.",

                    "id_usuario":
                        str(
                            usuario.id_usuario
                        ),
                },
                status=
                    status.HTTP_201_CREATED,
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


class OncologoDetailAPIView(
    APIView
):

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

        return super().get_permissions()

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
                    status.HTTP_404_NOT_FOUND,
            )

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

        serializer.is_valid(
            raise_exception=True
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

            return Response(
                {
                    "mensaje":
                        "Oncólogo actualizado correctamente.",

                    "id_usuario":
                        str(
                            usuario.id_usuario
                        ),
                },
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


class OncologoEstadoAPIView(
    APIView
):

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

        serializer.is_valid(
            raise_exception=True
        )

        try:

            resultado = (
                CambiarEstadoOncologoUseCase()
                .ejecutar(
                    usuario_id,
                    serializer
                    .validated_data[
                        "estado"
                    ],
                )
            )

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

            return Response(
                {
                    "mensaje":
                        mensaje,

                    **resultado,
                },
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