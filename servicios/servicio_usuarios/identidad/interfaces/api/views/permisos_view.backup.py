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


from identidad.infrastructure.permissions.recuperacion_permissions import (
    EsJefeOncologia,
)


from identidad.interfaces.api.serializers.permiso_serializer import (
    ActualizarPermisosOncologoSerializer,
)


class PermisosOncologoJefaturaAPIView(
    APIView
):
    """
    Permite al Jefe de Oncología consultar y
    actualizar los permisos asignados al rol
    ONCOLOGO.

    GET:
        Consulta los permisos administrables.

    PUT / PATCH:
        Actualiza los permisos seleccionados.
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


        serializer.is_valid(
            raise_exception=True
        )


        try:

            resultado = (
                ActualizarPermisosOncologoUseCase()
                .ejecutar(
                    serializer
                    .validated_data[
                        "permisos"
                    ]
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
    # PATCH
    # ======================================================

    def patch(
        self,
        request,
    ):

        return self.put(
            request
        )