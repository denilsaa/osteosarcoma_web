from rest_framework import status

from rest_framework.permissions import (
    IsAuthenticated,
)

from rest_framework.response import (
    Response,
)

from rest_framework.views import (
    APIView,
)


from identidad.application.use_cases.actualizar_perfil import (
    ActualizarMiPerfilUseCase,
)

from identidad.application.use_cases.obtener_perfil import (
    ObtenerMiPerfilUseCase,
)


from identidad.infrastructure.permissions.perfil_permissions import (
    PuedeEditarPerfil,
)


from identidad.interfaces.api.serializers.perfil_serializer import (
    ActualizarMiPerfilSerializer,
)


class MiPerfilAPIView(
    APIView
):

    # ======================================================
    # PERMISOS SEGÚN OPERACIÓN
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
                IsAuthenticated()
            ]


        if (
            self.request.method
            in (
                "PUT",
                "PATCH",
            )
        ):

            return [
                PuedeEditarPerfil()
            ]


        return [
            IsAuthenticated()
        ]


    # ======================================================
    # CONSULTAR MI PERFIL
    # ======================================================

    def get(
        self,
        request,
    ):

        try:

            resultado = (

                ObtenerMiPerfilUseCase()

                .ejecutar(
                    request.user
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


    # ======================================================
    # PUT
    # ======================================================

    def put(
        self,
        request,
    ):

        return self._actualizar(
            request
        )


    # ======================================================
    # PATCH
    # ======================================================

    def patch(
        self,
        request,
    ):

        return self._actualizar(
            request
        )


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    def _actualizar(
        self,
        request,
    ):

        serializer = (

            ActualizarMiPerfilSerializer(

                data=request.data,

                partial=True,

            )

        )


        serializer.is_valid(
            raise_exception=True
        )


        try:

            resultado = (

                ActualizarMiPerfilUseCase()

                .ejecutar(

                    usuario=
                        request.user,

                    datos=
                        serializer
                        .validated_data,

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