from rest_framework import serializers


class CreatePatientRequestSerializer(
    serializers.Serializer
):
    first_names = serializers.CharField(
        max_length=100,
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

    birth_date = serializers.DateField()

    sex_id = serializers.IntegerField(
        min_value=1,
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

    complement = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    issued_in = serializers.CharField(
        max_length=40,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    contact_type_id = (
        serializers.IntegerField(
            min_value=1,
            required=False,
            allow_null=True,
        )
    )

    contact_value = (
        serializers.CharField(
            max_length=150,
            required=False,
            allow_blank=True,
            allow_null=True,
        )
    )


class UpdatePatientRequestSerializer(
    serializers.Serializer
):
    first_names = serializers.CharField(
        max_length=100,
        required=False,
    )

    paternal_surname = (
        serializers.CharField(
            max_length=80,
            required=False,
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

    document_type_code = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=30,
        )
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


class PossibleDuplicateQuerySerializer(
    serializers.Serializer
):
    document_type_id = (
        serializers.IntegerField(
            required=False,
            allow_null=True,
            min_value=1,
        )
    )

    document_number = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=50,
        )
    )

    first_names = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
    )

    paternal_surname = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=80,
        )
    )

    maternal_surname = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            max_length=80,
        )
    )

    birth_date = serializers.DateField(
        required=False,
        allow_null=True,
    )