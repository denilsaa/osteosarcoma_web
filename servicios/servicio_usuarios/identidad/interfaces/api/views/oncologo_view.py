from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


from identidad.infrastructure.permissions.role_permissions import (
    IsJefeOncologia
)


from identidad.application.use_cases.crear_oncologo import (
    CrearOncologoUseCase
)


from identidad.application.use_cases.listar_oncologos import (
    ListarOncologosUseCase
)


from identidad.application.use_cases.obtener_oncologo import (
    ObtenerOncologoUseCase
)


from identidad.application.use_cases.editar_oncologo import (
    EditarOncologoUseCase
)



from identidad.interfaces.api.serializers.oncologo_serializer import (
    CrearOncologoSerializer,
    EditarOncologoSerializer
)





class OncologoListCreateAPIView(APIView):

    """
    Gestión de oncólogos.
    Solo permitido para Jefe de Oncología.
    """


    permission_classes = [
        IsJefeOncologia
    ]



    def get(
        self,
        request
    ):


        try:

            resultado = (
                ListarOncologosUseCase()
                .ejecutar()
            )


            return Response(

                resultado,

                status=status.HTTP_200_OK

            )



        except Exception as error:


            return Response(

                {
                    "error": str(error)
                },

                status=status.HTTP_500_INTERNAL_SERVER_ERROR

            )







    def post(
        self,
        request
    ):


        serializer = CrearOncologoSerializer(
            data=request.data
        )



        serializer.is_valid(
            raise_exception=True
        )



        try:


            usuario = (
                CrearOncologoUseCase()
                .ejecutar(

                    serializer.validated_data

                )
            )



            return Response(

                {

                    "mensaje":
                    "Oncólogo creado correctamente",


                    "id_usuario":
                    str(
                        usuario.id_usuario
                    )

                },


                status=status.HTTP_201_CREATED

            )



        except Exception as error:


            return Response(

                {
                    "error": str(error)
                },

                status=status.HTTP_400_BAD_REQUEST

            )









class OncologoDetailAPIView(APIView):

    """
    Consulta y edición de un oncólogo.
    Solo permitido para Jefe de Oncología.
    """



    permission_classes = [
        IsJefeOncologia
    ]




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

                status=status.HTTP_200_OK

            )



        except Exception as error:


            return Response(

                {
                    "error": str(error)
                },

                status=status.HTTP_404_NOT_FOUND

            )







    def put(
        self,
        request,
        usuario_id
    ):


        serializer = EditarOncologoSerializer(
            data=request.data
        )



        serializer.is_valid(
            raise_exception=True
        )



        try:


            EditarOncologoUseCase().ejecutar(

                usuario_id,

                serializer.validated_data

            )



            return Response(

                {
                    "mensaje":
                    "Oncólogo actualizado correctamente"
                },

                status=status.HTTP_200_OK

            )



        except Exception as error:


            return Response(

                {
                    "error": str(error)
                },

                status=status.HTTP_400_BAD_REQUEST

            )