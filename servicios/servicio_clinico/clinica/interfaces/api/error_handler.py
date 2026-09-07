from django.db import IntegrityError
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response

from clinica.domain.exceptions import (
    DuplicatePatientError,
    EditReasonRequiredError,
    InvalidPatientDataError,
    PatientNotFoundError,
    PatientWithoutChangesError,
)


def domain_error_response(
    exception: Exception,
) -> Response:

    if isinstance(
        exception,
        PatientNotFoundError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "PATIENT_NOT_FOUND",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_404_NOT_FOUND,
        )

    if isinstance(
        exception,
        DuplicatePatientError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "PATIENT_DUPLICATE",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_409_CONFLICT,
        )

    if isinstance(
        exception,
        EditReasonRequiredError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "EDIT_REASON_REQUIRED",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(
        exception,
        PatientWithoutChangesError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "PATIENT_WITHOUT_CHANGES",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(
        exception,
        InvalidPatientDataError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "INVALID_PATIENT_DATA",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(
        exception,
        IntegrityError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "DATABASE_CONFLICT",

                    "message":
                        (
                            "La información entra "
                            "en conflicto con un "
                            "registro existente."
                        ),
                }
            },
            status=
                status.HTTP_409_CONFLICT,
        )

    if isinstance(
        exception,
        ProtectedError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "PROTECTED_RESOURCE",

                    "message":
                        (
                            "La operación no puede "
                            "realizarse porque el "
                            "registro está siendo "
                            "utilizado."
                        ),
                }
            },
            status=
                status.HTTP_409_CONFLICT,
        )

    raise exception