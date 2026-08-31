import re

from rest_framework import serializers


class SolicitarRecuperacionSerializer(
    serializers.Serializer
):
    """
    Solicitud inicial.
    Solo recibe el correo que el usuario recuerda.
    El enlace posterior se enviará exclusivamente al correo
    que ya está almacenado en Usuario.correo.
    """

    correo = serializers.EmailField(
        max_length=150
    )

    def validate_correo(
        self,
        valor,
    ):
        return (
            valor
            .strip()
            .lower()
        )


class ResolverRecuperacionSerializer(
    serializers.Serializer
):
    """
    Decisión de Jefatura de Oncología.
    """

    decision = serializers.ChoiceField(
        choices=[
            "APROBADA",
            "RECHAZADA",
        ]
    )

    observacion = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=500,
    )

    def validate_observacion(
        self,
        valor,
    ):
        if not valor:
            return None

        return valor.strip()


class CambiarPasswordRecuperacionSerializer(
    serializers.Serializer
):
    """
    Cambio de contraseña mediante enlace aprobado.
    """

    token = serializers.CharField(
        min_length=20,
        max_length=500,
    )

    nueva_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=64,
        trim_whitespace=False,
    )

    confirmar_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=64,
        trim_whitespace=False,
    )

    def validate_nueva_password(
        self,
        valor,
    ):
        if re.search(
            r"\s",
            valor,
        ):
            raise serializers.ValidationError(
                "La contraseña no puede contener espacios."
            )

        if not re.search(
            r"[A-Z]",
            valor,
        ):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra mayúscula."
            )

        if not re.search(
            r"[a-z]",
            valor,
        ):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra minúscula."
            )

        if not re.search(
            r"[0-9]",
            valor,
        ):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        if not re.search(
            r"[^A-Za-z0-9]",
            valor,
        ):
            raise serializers.ValidationError(
                "La contraseña debe contener al menos un carácter especial."
            )

        comunes = {
            "password",
            "password123",
            "admin123",
            "administrador",
            "qwerty123",
            "12345678",
            "contraseña",
            "contrasena",
        }

        if valor.lower() in comunes:
            raise serializers.ValidationError(
                "La contraseña indicada es demasiado común."
            )

        return valor

    def validate(
        self,
        attrs,
    ):
        if (
            attrs["nueva_password"]
            != attrs["confirmar_password"]
        ):
            raise serializers.ValidationError(
                {
                    "confirmar_password": (
                        "Las contraseñas no coinciden."
                    )
                }
            )

        return attrs
