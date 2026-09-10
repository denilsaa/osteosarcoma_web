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
        serializers.UUIDField()
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