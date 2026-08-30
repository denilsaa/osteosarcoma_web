from rest_framework import serializers


class ActualizarPermisosOncologoSerializer(
    serializers.Serializer
):

    permisos = serializers.ListField(

        child=
            serializers.CharField(
                max_length=80
            ),

        required=True,

        allow_empty=True,

    )


    def validate_permisos(
        self,
        valor,
    ):

        normalizados = []


        for codigo in valor:

            codigo_normalizado = (
                codigo
                .strip()
                .upper()
            )


            if (
                codigo_normalizado
                and
                codigo_normalizado
                not in
                normalizados
            ):

                normalizados.append(
                    codigo_normalizado
                )


        return normalizados