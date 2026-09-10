import re

from rest_framework import (
    serializers,
)


# ==========================================================
# CONSTANTES
# ==========================================================


EXPEDIDOS_BOLIVIA = {
    "LP": "La Paz",
    "CB": "Cochabamba",
    "SC": "Santa Cruz",
    "OR": "Oruro",
    "PT": "Potosí",
    "CH": "Chuquisaca",
    "TJ": "Tarija",
    "BE": "Beni",
    "PD": "Pando",
}


PARENTESCOS = (
    "MADRE",
    "PADRE",
    "HERMANO",
    "HERMANA",
    "HIJO",
    "HIJA",
    "ESPOSO",
    "ESPOSA",
    "TUTOR",
    "TUTORA",
    "ABUELO",
    "ABUELA",
    "TIO",
    "TIA",
    "PRIMO",
    "PRIMA",
    "OTRO",
)


PATRON_CELULAR = re.compile(
    r"^[67]\d{7}$"
)


PATRON_TELEFONO = re.compile(
    r"^\d{7,8}$"
)


# ==========================================================
# UTILIDADES
# ==========================================================


def normalizar_opcional(
    valor,
):

    if valor in (
        None,
        "",
    ):

        return None


    valor = str(
        valor
    ).strip()


    return (
        valor
        if valor
        else None
    )


# ==========================================================
# CONTACTO DEL PACIENTE
# ==========================================================


class PatientContactInputSerializer(
    serializers.Serializer
):

    contact_type_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )


    value = (
        serializers.CharField(
            max_length=150,
        )
    )


    primary = (
        serializers.BooleanField(
            required=False,
            default=False,
        )
    )


    def validate_value(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if not value:

            raise serializers.ValidationError(
                "Ingrese el valor del contacto."
            )


        return value


# ==========================================================
# CONTACTO DE EMERGENCIA
# ==========================================================


class EmergencyContactInputSerializer(
    serializers.Serializer
):

    full_name = (
        serializers.CharField(
            max_length=180,
        )
    )


    relationship = (
        serializers.ChoiceField(
            choices=[
                (
                    value,
                    value,
                )
                for value
                in PARENTESCOS
            ],
        )
    )


    phone = (
        serializers.CharField(
            max_length=8,
        )
    )


    email = (
        serializers.EmailField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=150,
        )
    )


    primary = (
        serializers.BooleanField(
            required=False,
            default=False,
        )
    )


    def validate_full_name(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if len(value) < 3:

            raise serializers.ValidationError(
                "Ingrese el nombre completo."
            )


        return value


    def validate_phone(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if not PATRON_CELULAR.fullmatch(
            value
        ):

            raise serializers.ValidationError(
                "El teléfono debe tener 8 dígitos "
                "y comenzar con 6 o 7."
            )


        return value


    def validate_email(
        self,
        value,
    ):

        value = (
            normalizar_opcional(
                value
            )
        )


        if value is None:

            return None


        return value.lower()


# ==========================================================
# CREAR PACIENTE
# ==========================================================


class CreatePatientRequestSerializer(
    serializers.Serializer
):

    first_names = (
        serializers.CharField(
            max_length=100,
        )
    )


    paternal_surname = (
        serializers.CharField(
            max_length=80,
        )
    )


    maternal_surname = (
        serializers.CharField(
            max_length=80,
            required=False,
            allow_blank=True,
            allow_null=True,
        )
    )


    birth_date = (
        serializers.DateField()
    )


    sex_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )


    document_type_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )


    document_number = (
        serializers.CharField(
            max_length=50,
        )
    )


    complement = (
        serializers.CharField(
            max_length=20,
            required=False,
            allow_blank=True,
            allow_null=True,
        )
    )


    issued_in = (
        serializers.ChoiceField(
            choices=[
                (
                    code,
                    name,
                )
                for code, name
                in EXPEDIDOS_BOLIVIA.items()
            ],
        )
    )


    contacts = (
        PatientContactInputSerializer(
            many=True,
            required=False,
            default=list,
        )
    )


    emergency_contacts = (
        EmergencyContactInputSerializer(
            many=True,
            required=False,
            default=list,
        )
    )


    # ======================================================
    # NOMBRES
    # ======================================================

    def validate_first_names(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if len(value) < 2:

            raise serializers.ValidationError(
                "Ingrese los nombres del paciente."
            )


        return value


    def validate_paternal_surname(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if len(value) < 2:

            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )


        return value


    def validate_maternal_surname(
        self,
        value,
    ):

        return (
            normalizar_opcional(
                value
            )
        )


    # ======================================================
    # SEXO
    # ======================================================

    def validate_sex_id(
        self,
        value,
    ):

        if value not in (
            1,
            2,
        ):

            raise serializers.ValidationError(
                "Solo se permite Masculino o Femenino."
            )


        return value


    # ======================================================
    # DOCUMENTO
    # ======================================================

    def validate_document_number(
        self,
        value,
    ):

        value = (
            value.strip()
        )


        if len(value) < 4:

            raise serializers.ValidationError(
                "El número de documento es demasiado corto."
            )


        return value


    def validate_complement(
        self,
        value,
    ):

        value = (
            normalizar_opcional(
                value
            )
        )


        if value is None:

            return None


        return (
            value
            .upper()
            .replace(
                " ",
                "",
            )
        )


    # ======================================================
    # CONTACTOS
    # ======================================================

    def validate_contacts(
        self,
        contacts,
    ):

        if len(contacts) > 10:

            raise serializers.ValidationError(
                "Puede registrar como máximo "
                "10 medios de contacto."
            )


        principals = sum(
            1
            for contact
            in contacts
            if contact.get(
                "primary"
            )
        )


        if principals > 1:

            raise serializers.ValidationError(
                "Solo un medio de contacto "
                "puede ser principal."
            )


        return contacts


    # ======================================================
    # EMERGENCIAS
    # ======================================================

    def validate_emergency_contacts(
        self,
        contacts,
    ):

        if len(contacts) > 10:

            raise serializers.ValidationError(
                "Puede registrar como máximo "
                "10 contactos de emergencia."
            )


        principals = sum(
            1
            for contact
            in contacts
            if contact.get(
                "primary"
            )
        )


        if principals > 1:

            raise serializers.ValidationError(
                "Solo un contacto de emergencia "
                "puede ser principal."
            )


        return contacts


# ==========================================================
# ACTUALIZAR PACIENTE
# ==========================================================


class UpdatePatientRequestSerializer(
    serializers.Serializer
):

    first_names = serializers.CharField(
        max_length=100,
        required=False,
    )

    paternal_surname = serializers.CharField(
        max_length=80,
        required=False,
    )

    maternal_surname = serializers.CharField(
        max_length=80,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    birth_date = serializers.DateField(
        required=False,
    )

    sex_id = serializers.IntegerField(
        min_value=1,
        required=False,
    )

    active = serializers.BooleanField(
        required=False,
    )

    reason = serializers.CharField(
        min_length=5,
        max_length=500,
    )


    def validate_sex_id(
        self,
        value,
    ):

        if value not in (
            1,
            2,
        ):

            raise serializers.ValidationError(
                "Solo se permite Masculino o Femenino."
            )


        return value


# ==========================================================
# LISTADO
# ==========================================================


class PatientListQuerySerializer(
    serializers.Serializer
):

    search = serializers.CharField(
        required=False,
        allow_blank=True,
    )

    sex_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=20,
    )

    active = serializers.BooleanField(
        required=False,
    )

    document_type_code = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=30,
    )

    page = serializers.IntegerField(
        required=False,
        default=1,
        min_value=1,
    )

    page_size = serializers.IntegerField(
        required=False,
        default=10,
        min_value=1,
        max_value=100,
    )


# ==========================================================
# POSIBLES DUPLICADOS
# ==========================================================


class PossibleDuplicateQuerySerializer(
    serializers.Serializer
):

    document_type_id = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
    )

    document_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50,
    )

    first_names = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    paternal_surname = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=80,
    )

    maternal_surname = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=80,
    )

    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
    )