from rest_framework import serializers



class CrearOncologoSerializer(serializers.Serializer):

    nombres = serializers.CharField(
        max_length=100
    )


    apellido_paterno = serializers.CharField(
        max_length=80
    )


    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True
    )


    correo = serializers.EmailField()


    nombre_usuario = serializers.CharField(
        max_length=80
    )


    telefono = serializers.CharField(
        required=False,
        allow_blank=True
    )


    password = serializers.CharField(
        write_only=True,
        min_length=8
    )


    matricula_profesional = serializers.CharField(
        required=False,
        allow_blank=True
    )


    especialidad = serializers.CharField(
        required=False,
        allow_blank=True
    )


    subespecialidad = serializers.CharField(
        required=False,
        allow_blank=True
    )



class EditarOncologoSerializer(serializers.Serializer):

    nombres = serializers.CharField(
        required=False
    )


    apellido_paterno = serializers.CharField(
        required=False
    )


    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True
    )


    correo = serializers.EmailField(
        required=False
    )


    telefono = serializers.CharField(
        required=False
    )


    matricula_profesional = serializers.CharField(
        required=False
    )


    especialidad = serializers.CharField(
        required=False
    )


    subespecialidad = serializers.CharField(
        required=False
    )