import re

from rest_framework import serializers


class SolicitarRecuperacionSerializer(
    serializers.Serializer
):
    """
    Valida la solicitud inicial de
    recuperación de contraseña.
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
    Valida la decisión del Jefe de Oncología.
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
    Valida el cambio de contraseña
    posterior a la aprobación.
    """

    token = serializers.CharField(
        min_length=20,
        max_length=500,
    )

    nueva_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
    )

    confirmar_password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
    )

    def validate_nueva_password(
        self,
        valor,
    ):

        if not re.search(
            r"[A-Za-z]",
            valor,
        ):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos una letra."
            )

        if not re.search(
            r"[0-9]",
            valor,
        ):

            raise serializers.ValidationError(
                "La contraseña debe contener al menos un número."
            )

        return valor

    def validate(
        self,
        attrs,
    ):

        if (
            attrs["nueva_password"]
            !=
            attrs["confirmar_password"]
        ):

            raise serializers.ValidationError(
                {
                    "confirmar_password":
                        "Las contraseñas no coinciden."
                }
            )

        return attrs
