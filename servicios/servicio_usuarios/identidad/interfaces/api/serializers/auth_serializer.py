import re

from rest_framework import serializers


class LoginSerializer(serializers.Serializer):
    correo = serializers.EmailField(max_length=150)
    password = serializers.CharField(
        write_only=True,
        trim_whitespace=False,
        max_length=128,
    )

    def validate_correo(self, value):
        return value.strip().lower()


class VerificarSegundoFactorSerializer(serializers.Serializer):
    desafio_id = serializers.UUIDField()
    codigo = serializers.CharField(
        min_length=6,
        max_length=6,
        trim_whitespace=True,
    )

    def validate_codigo(self, value):
        value = value.strip()
        if not re.fullmatch(r"\d{6}", value):
            raise serializers.ValidationError(
                "El código debe contener exactamente 6 dígitos."
            )
        return value


class ReenviarSegundoFactorSerializer(serializers.Serializer):
    desafio_id = serializers.UUIDField()


class RefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()
