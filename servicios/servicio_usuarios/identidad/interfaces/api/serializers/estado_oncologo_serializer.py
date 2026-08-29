from rest_framework import serializers


class CambiarEstadoOncologoSerializer(
    serializers.Serializer
):

    estado = serializers.ChoiceField(
        choices=[
            "ACTIVO",
            "INACTIVO",
        ]
    )