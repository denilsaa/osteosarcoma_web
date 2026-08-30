import re

from rest_framework import serializers


class ActualizarMiPerfilSerializer(
    serializers.Serializer
):
    """
    Únicamente permite modificar
    datos personales autorizados.

    Campos institucionales como:
    - correo
    - nombre_usuario
    - rol
    - matrícula
    - especialidad

    NO pueden modificarse desde Mi perfil.
    """

    nombres = serializers.CharField(
        required=False,
        max_length=100,
    )

    apellido_paterno = serializers.CharField(
        required=False,
        max_length=80,
    )

    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=25,
    )


    # ======================================================
    # BLOQUEAR CAMPOS NO AUTORIZADOS
    # ======================================================

    def to_internal_value(
        self,
        data,
    ):

        campos_permitidos = {
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "telefono",
        }


        campos_recibidos = set(
            data.keys()
        )


        campos_no_permitidos = (
            campos_recibidos
            -
            campos_permitidos
        )


        if campos_no_permitidos:

            raise serializers.ValidationError(
                {
                    "campos_no_autorizados": (
                        "No tiene autorización para modificar: "
                        +
                        ", ".join(
                            sorted(
                                campos_no_permitidos
                            )
                        )
                    )
                }
            )


        return super().to_internal_value(
            data
        )


    # ======================================================
    # NOMBRES
    # ======================================================

    def validate_nombres(
        self,
        valor,
    ):

        valor = valor.strip()


        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese un nombre válido."
            )


        return valor


    # ======================================================
    # APELLIDO PATERNO
    # ======================================================

    def validate_apellido_paterno(
        self,
        valor,
    ):

        valor = valor.strip()


        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese un apellido paterno válido."
            )


        return valor


    # ======================================================
    # APELLIDO MATERNO
    # ======================================================

    def validate_apellido_materno(
        self,
        valor,
    ):

        if valor in (
            None,
            "",
        ):

            return None


        return valor.strip()


    # ======================================================
    # TELÉFONO
    # ======================================================

    def validate_telefono(
        self,
        valor,
    ):

        if valor in (
            None,
            "",
        ):

            return None


        valor = valor.strip()


        patron = (
            r"^[0-9+\-\s()]{7,25}$"
        )


        if not re.fullmatch(
            patron,
            valor,
        ):

            raise serializers.ValidationError(
                "Ingrese un número de teléfono válido."
            )


        return valor