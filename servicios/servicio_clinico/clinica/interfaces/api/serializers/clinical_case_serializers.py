from rest_framework import (
    serializers,
)


class CreateClinicalCaseSerializer(
    serializers.Serializer,
):

    priority_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    responsible_oncologist_uuid = (
        serializers.UUIDField(
            required=False,
            allow_null=True,
        )
    )

    consultation_reason = (
        serializers.CharField(
            min_length=5,
            max_length=2000,
            trim_whitespace=True,
        )
    )

    general_observation = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=4000,
            trim_whitespace=True,
        )
    )


# ==========================================================
# ESTADO DEL CASO
# ==========================================================

class AdvanceClinicalCaseStatusSerializer(
    serializers.Serializer,
):

    observation = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=2000,
            trim_whitespace=True,
        )
    )


# ==========================================================
# ANTECEDENTES
# ==========================================================

class CreateClinicalAntecedentSerializer(
    serializers.Serializer,
):

    antecedent_type_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    description = (
        serializers.CharField(
            min_length=3,
            max_length=4000,
            trim_whitespace=True,
        )
    )


# ==========================================================
# SINTOMAS
# ==========================================================

class CreateClinicalSymptomSerializer(
    serializers.Serializer,
):

    symptom_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    intensity_id = (
        serializers.IntegerField(
            min_value=1,
            required=False,
            allow_null=True,
        )
    )

    start_date = (
        serializers.DateField(
            required=False,
            allow_null=True,
        )
    )

    observation = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=4000,
            trim_whitespace=True,
        )
    )


# ==========================================================
# SIGNOS
# ==========================================================

class CreateClinicalSignSerializer(
    serializers.Serializer,
):

    sign_id = (
        serializers.IntegerField(
            min_value=1,
        )
    )

    finding_description = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=4000,
            trim_whitespace=True,
        )
    )


# ==========================================================
# OBSERVACIONES
# ==========================================================

class CreateClinicalObservationSerializer(
    serializers.Serializer,
):

    content = (
        serializers.CharField(
            min_length=3,
            max_length=4000,
            trim_whitespace=True,
        )
    )