import re

from rest_framework import serializers


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


PATRON_CELULAR = re.compile(
    r"^[67]\d{7}$"
)


PATRON_TELEFONO_FIJO = re.compile(
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

    if not valor:
        return None

    return valor


def validar_celular(
    valor,
):
    valor = normalizar_opcional(
        valor
    )

    if valor is None:
        return None

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El celular solo puede contener números."
        )

    if not PATRON_CELULAR.fullmatch(
        valor
    ):
        raise serializers.ValidationError(
            "El celular debe tener 8 dígitos y comenzar con 6 o 7."
        )

    return valor


def validar_telefono_fijo(
    valor,
):
    valor = normalizar_opcional(
        valor
    )

    if valor is None:
        return None

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El teléfono fijo solo puede contener números."
        )

    if not PATRON_TELEFONO_FIJO.fullmatch(
        valor
    ):
        raise serializers.ValidationError(
            "El teléfono fijo debe tener entre 7 y 8 dígitos."
        )

    return valor


# ==========================================================
# CREAR PACIENTE
# ==========================================================


class CreatePatientRequestSerializer(
    serializers.Serializer
):
    # ======================================================
    # DATOS PERSONALES
    # ======================================================

    first_names = serializers.CharField(
        max_length=100,
    )

    paternal_surname = serializers.CharField(
        max_length=80,
    )

    maternal_surname = serializers.CharField(
        max_length=80,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    birth_date = serializers.DateField()

    sex_id = serializers.IntegerField(
        min_value=1,
    )

    # ======================================================
    # DOCUMENTO
    # ======================================================

    document_type_id = serializers.IntegerField(
        min_value=1,
    )

    document_number = serializers.CharField(
        max_length=50,
    )

    complement = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    issued_in = serializers.ChoiceField(
        choices=[
            (
                codigo,
                nombre,
            )
            for codigo, nombre
            in EXPEDIDOS_BOLIVIA.items()
        ],
        required=True,
    )

    # ======================================================
    # CONTACTOS DEL PACIENTE
    # ======================================================

    mobile_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    landline_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=150,
    )

    # ======================================================
    # CONTACTO DE EMERGENCIA
    # ======================================================

    emergency_contact_name = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=180,
    )

    emergency_relationship = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    emergency_phone = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    emergency_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=150,
    )

    # ======================================================
    # VALIDACIONES DATOS PERSONALES
    # ======================================================

    def validate_first_names(
        self,
        valor,
    ):
        valor = valor.strip()

        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese los nombres del paciente."
            )

        return valor

    def validate_paternal_surname(
        self,
        valor,
    ):
        valor = valor.strip()

        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese el apellido paterno del paciente."
            )

        return valor

    def validate_maternal_surname(
        self,
        valor,
    ):
        return normalizar_opcional(
            valor
        )

    # ======================================================
    # DOCUMENTO
    # ======================================================

    def validate_document_number(
        self,
        valor,
    ):
        valor = valor.strip()

        if len(valor) < 4:
            raise serializers.ValidationError(
                "El número de documento es demasiado corto."
            )

        return valor

    def validate_complement(
        self,
        valor,
    ):
        valor = normalizar_opcional(
            valor
        )

        if valor is None:
            return None

        return (
            valor
            .upper()
            .replace(
                " ",
                "",
            )
        )

    def validate_issued_in(
        self,
        valor,
    ):
        valor = valor.strip().upper()

        if valor not in EXPEDIDOS_BOLIVIA:
            raise serializers.ValidationError(
                "El departamento de expedición no es válido."
            )

        return valor

    # ======================================================
    # CONTACTOS PROPIOS
    # ======================================================

    def validate_mobile_phone(
        self,
        valor,
    ):
        return validar_celular(
            valor
        )

    def validate_landline_phone(
        self,
        valor,
    ):
        return validar_telefono_fijo(
            valor
        )

    def validate_email(
        self,
        valor,
    ):
        valor = normalizar_opcional(
            valor
        )

        if valor is None:
            return None

        return valor.lower()

    # ======================================================
    # CONTACTO DE EMERGENCIA
    # ======================================================

    def validate_emergency_contact_name(
        self,
        valor,
    ):
        return normalizar_opcional(
            valor
        )

    def validate_emergency_relationship(
        self,
        valor,
    ):
        return normalizar_opcional(
            valor
        )

    def validate_emergency_phone(
        self,
        valor,
    ):
        return validar_celular(
            valor
        )

    def validate_emergency_email(
        self,
        valor,
    ):
        valor = normalizar_opcional(
            valor
        )

        if valor is None:
            return None

        return valor.lower()

    # ======================================================
    # VALIDACIÓN GENERAL
    # ======================================================

    def validate(
        self,
        attrs,
    ):
        emergency_fields = [
            attrs.get(
                "emergency_contact_name"
            ),
            attrs.get(
                "emergency_relationship"
            ),
            attrs.get(
                "emergency_phone"
            ),
            attrs.get(
                "emergency_email"
            ),
        ]

        tiene_datos_emergencia = any(
            valor not in (
                None,
                "",
            )
            for valor
            in emergency_fields
        )

        # --------------------------------------------------
        # SI SE INICIA CONTACTO DE EMERGENCIA,
        # EXIGIR LOS CAMPOS PRINCIPALES
        # --------------------------------------------------

        if tiene_datos_emergencia:
            if not attrs.get(
                "emergency_contact_name"
            ):
                raise serializers.ValidationError(
                    {
                        "emergency_contact_name":
                            (
                                "Ingrese el nombre del "
                                "contacto de emergencia."
                            )
                    }
                )

            if not attrs.get(
                "emergency_relationship"
            ):
                raise serializers.ValidationError(
                    {
                        "emergency_relationship":
                            (
                                "Ingrese el parentesco "
                                "del contacto de emergencia."
                            )
                    }
                )

            if not attrs.get(
                "emergency_phone"
            ):
                raise serializers.ValidationError(
                    {
                        "emergency_phone":
                            (
                                "Ingrese el teléfono del "
                                "contacto de emergencia."
                            )
                    }
                )

        return attrs


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