from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


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


    def get(self, request):

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
                status=500
            )



    def post(self, request):

        serializer = CrearOncologoSerializer(
            data=request.data
        )


        if not serializer.is_valid():

            return Response(

                serializer.errors,

                status=status.HTTP_400_BAD_REQUEST

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
                    str(usuario.id_usuario)

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
                resultado
            )


        except Exception as error:


            return Response(

                {
                    "error": str(error)
                },

                status=404

            )



    def put(
        self,
        request,
        usuario_id
    ):


        serializer = EditarOncologoSerializer(
            data=request.data
        )


        if not serializer.is_valid():

            return Response(

                serializer.errors,

                status=400

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
                }

            )


        except Exception as error:


            return Response(

                {
                    "error":str(error)
                },

                status=400

            )