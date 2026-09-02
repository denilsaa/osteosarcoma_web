from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from identidad.application.use_cases.cerrar_sesion import CerrarSesionUseCase
from identidad.application.use_cases.login_usuario import LoginUseCase
from identidad.application.use_cases.renovar_sesion import RenovarSesionUseCase
from identidad.application.use_cases.segundo_factor import (
    ReenviarSegundoFactorUseCase,
    VerificarSegundoFactorUseCase,
)
from identidad.interfaces.api.serializers.auth_serializer import (
    LoginSerializer,
    LogoutSerializer,
    ReenviarSegundoFactorSerializer,
    RefreshSerializer,
    VerificarSegundoFactorSerializer,
)


class LoginView(APIView):
    """
    Primer factor: correo + contraseña.

    IMPORTANTE: este endpoint ya NO entrega JWT.
    Devuelve un desafio_id y envía un código OTP al correo institucional.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = LoginUseCase().ejecutar(
                serializer.validated_data["correo"],
                serializer.validated_data["password"],
                ip_origen=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class VerificarSegundoFactorView(APIView):
    """Segundo factor: valida OTP y recién entonces entrega access + refresh JWT."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerificarSegundoFactorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = VerificarSegundoFactorUseCase().ejecutar(
                desafio_id=serializer.validated_data["desafio_id"],
                codigo=serializer.validated_data["codigo"],
                ip_origen=request.META.get("REMOTE_ADDR"),
                user_agent=request.META.get("HTTP_USER_AGENT"),
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ReenviarSegundoFactorView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ReenviarSegundoFactorSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = ReenviarSegundoFactorUseCase().ejecutar(
                desafio_id=serializer.validated_data["desafio_id"],
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = CerrarSesionUseCase().ejecutar(
                serializer.validated_data["refresh_token"]
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )


class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            resultado = RenovarSesionUseCase().ejecutar(
                serializer.validated_data["refresh_token"]
            )
            return Response(resultado, status=status.HTTP_200_OK)
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )
