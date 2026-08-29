import re

from rest_framework import serializers

from identidad.models import (
    PerfilProfesional,
    Usuario,
)


def validar_telefono(valor):

    if valor in (
        None,
        "",
    ):

        return valor

    valor = valor.strip()

    patron = r"^[0-9+\-\s()]{7,25}$"

    if not re.fullmatch(
        patron,
        valor,
    ):

        raise serializers.ValidationError(
            "Ingrese un número de teléfono válido."
        )

    return valor


class CrearOncologoSerializer(
    serializers.Serializer
):

    nombres = serializers.CharField(
        max_length=100
    )

    apellido_paterno = serializers.CharField(
        max_length=80
    )

    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    correo = serializers.EmailField(
        max_length=150
    )

    nombre_usuario = serializers.CharField(
        max_length=80
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=25,
    )

    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=128,
        trim_whitespace=False,
    )

    matricula_profesional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=50,
    )

    especialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )

    subespecialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )

    telefono_institucional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=25,
    )

    # ======================================================
    # VALIDACIONES DE CAMPOS
    # ======================================================

    def validate_nombres(
        self,
        valor
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )

        return valor

    def validate_apellido_paterno(
        self,
        valor
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )

        return valor

    def validate_correo(
        self,
        valor
    ):

        valor = (
            valor
            .strip()
            .lower()
        )

        if (
            Usuario.objects
            .filter(
                correo__iexact=valor
            )
            .exists()
        ):

            raise serializers.ValidationError(
                "Este correo ya se encuentra registrado."
            )

        return valor

    def validate_nombre_usuario(
        self,
        valor
    ):

        valor = valor.strip()

        if " " in valor:

            raise serializers.ValidationError(
                "El nombre de usuario no puede contener espacios."
            )

        if (
            Usuario.objects
            .filter(
                nombre_usuario__iexact=valor
            )
            .exists()
        ):

            raise serializers.ValidationError(
                "Este nombre de usuario ya se encuentra registrado."
            )

        return valor

    def validate_telefono(
        self,
        valor
    ):

        return validar_telefono(
            valor
        )

    def validate_telefono_institucional(
        self,
        valor
    ):

        return validar_telefono(
            valor
        )

    def validate_matricula_profesional(
        self,
        valor
    ):

        if not valor:

            return None

        valor = valor.strip()

        if (
            PerfilProfesional.objects
            .filter(
                matricula_profesional__iexact=valor
            )
            .exists()
        ):

            raise serializers.ValidationError(
                "Esta matrícula profesional ya se encuentra registrada."
            )

        return valor

    # ======================================================
    # NORMALIZACIÓN
    # ======================================================

    def validate(
        self,
        attrs
    ):

        campos_opcionales = [

            "apellido_materno",

            "telefono",

            "matricula_profesional",

            "especialidad",

            "subespecialidad",

            "telefono_institucional",

        ]

        for campo in campos_opcionales:

            if (
                campo in attrs
                and
                attrs[campo] == ""
            ):

                attrs[campo] = None

        return attrs


class EditarOncologoSerializer(
    serializers.Serializer
):

    nombres = serializers.CharField(
        required=False,
        max_length=100
    )

    apellido_paterno = serializers.CharField(
        required=False,
        max_length=80
    )

    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    correo = serializers.EmailField(
        required=False,
        max_length=150
    )

    nombre_usuario = serializers.CharField(
        required=False,
        max_length=80
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=25,
    )

    matricula_profesional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=50,
    )

    especialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )

    subespecialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )

    telefono_institucional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=25,
    )

    # ======================================================
    # UTILIDADES
    # ======================================================

    def obtener_usuario_id(
        self
    ):

        return self.context.get(
            "usuario_id"
        )

    # ======================================================
    # VALIDACIONES
    # ======================================================

    def validate_nombres(
        self,
        valor
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )

        return valor

    def validate_apellido_paterno(
        self,
        valor
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )

        return valor

    def validate_correo(
        self,
        valor
    ):

        valor = (
            valor
            .strip()
            .lower()
        )

        usuario_id = (
            self.obtener_usuario_id()
        )

        consulta = (
            Usuario.objects
            .filter(
                correo__iexact=valor
            )
        )

        if usuario_id:

            consulta = consulta.exclude(
                id_usuario=usuario_id
            )

        if consulta.exists():

            raise serializers.ValidationError(
                "Este correo ya pertenece a otra cuenta."
            )

        return valor

    def validate_nombre_usuario(
        self,
        valor
    ):

        valor = valor.strip()

        if " " in valor:

            raise serializers.ValidationError(
                "El nombre de usuario no puede contener espacios."
            )

        usuario_id = (
            self.obtener_usuario_id()
        )

        consulta = (
            Usuario.objects
            .filter(
                nombre_usuario__iexact=valor
            )
        )

        if usuario_id:

            consulta = consulta.exclude(
                id_usuario=usuario_id
            )

        if consulta.exists():

            raise serializers.ValidationError(
                "Este nombre de usuario pertenece a otra cuenta."
            )

        return valor

    def validate_telefono(
        self,
        valor
    ):

        return validar_telefono(
            valor
        )

    def validate_telefono_institucional(
        self,
        valor
    ):

        return validar_telefono(
            valor
        )

    def validate_matricula_profesional(
        self,
        valor
    ):

        if not valor:

            return None

        valor = valor.strip()

        usuario_id = (
            self.obtener_usuario_id()
        )

        consulta = (
            PerfilProfesional.objects
            .filter(
                matricula_profesional__iexact=valor
            )
        )

        if usuario_id:

            consulta = consulta.exclude(
                usuario_id=usuario_id
            )

        if consulta.exists():

            raise serializers.ValidationError(
                "Esta matrícula profesional pertenece a otro oncólogo."
            )

        return valor

    def validate(
        self,
        attrs
    ):

        if not attrs:

            raise serializers.ValidationError(
                "No se enviaron datos para actualizar."
            )

        campos_opcionales = [

            "apellido_materno",

            "telefono",

            "matricula_profesional",

            "especialidad",

            "subespecialidad",

            "telefono_institucional",

        ]

        for campo in campos_opcionales:

            if (
                campo in attrs
                and
                attrs[campo] == ""
            ):

                attrs[campo] = None

        return attrs