from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny


from identidad.application.use_cases.login_usuario import (
    LoginUseCase
)


from identidad.application.use_cases.cerrar_sesion import (
    CerrarSesionUseCase
)


from identidad.application.use_cases.renovar_sesion import (
    RenovarSesionUseCase
)



from identidad.interfaces.api.serializers.auth_serializer import (
    LoginSerializer,
    RefreshSerializer,
    LogoutSerializer
)





class LoginView(APIView):

    """
    Endpoint público para iniciar sesión.
    Genera access token y refresh token.
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


        try:


            resultado = LoginUseCase().ejecutar(

                serializer.validated_data[
                    "correo"
                ],


                serializer.validated_data[
                    "password"
                ],


                ip_origen=request.META.get(
                    "REMOTE_ADDR"
                ),


                user_agent=request.META.get(
                    "HTTP_USER_AGENT"
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

                status=status.HTTP_400_BAD_REQUEST

            )








class LogoutView(APIView):

    """
    Endpoint público para cerrar sesión.
    Revoca el refresh token almacenado.
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



        try:


            resultado = (
                CerrarSesionUseCase()
                .ejecutar(

                    serializer.validated_data[
                        "refresh_token"
                    ]

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

                status=status.HTTP_400_BAD_REQUEST

            )









class RefreshView(APIView):

    """
    Endpoint público para renovar
    un access token utilizando
    refresh token válido.
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

                    serializer.validated_data[
                        "refresh_token"
                    ]

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

                status=status.HTTP_400_BAD_REQUEST

            )