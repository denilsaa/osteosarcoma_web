from django.db import (
    IntegrityError,
)

from django.db.models import (
    ProtectedError,
)

from rest_framework import (
    status,
)

from rest_framework.response import (
    Response,
)

from clinica.domain.exceptions import (
    DuplicatePatientError,
    EditReasonRequiredError,
    InvalidPatientDataError,
    PatientNotFoundError,
    PatientWithoutChangesError,
)

from clinica.infrastructure.security import (
    ClinicalAuthenticationError,
    ClinicalAuthorizationError,
)


def domain_error_response(
    exception: Exception,
) -> Response:

    # ======================================================
    # AUTENTICACIÓN
    # ======================================================

    if isinstance(
        exception,
        ClinicalAuthenticationError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "AUTHENTICATION_REQUIRED",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_401_UNAUTHORIZED,
        )

    # ======================================================
    # AUTORIZACIÓN
    # ======================================================

    if isinstance(
        exception,
        ClinicalAuthorizationError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "ACCESS_DENIED",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_403_FORBIDDEN,
        )

    # ======================================================
    # PACIENTE NO ENCONTRADO
    # ======================================================

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

    # ======================================================
    # PACIENTE DUPLICADO
    # ======================================================

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

    # ======================================================
    # MOTIVO DE EDICIÓN
    # ======================================================

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

    # ======================================================
    # SIN CAMBIOS
    # ======================================================

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

    # ======================================================
    # DATOS INVÁLIDOS
    # ======================================================

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

    # ======================================================
    # VALUE ERROR
    # ======================================================

    if isinstance(
        exception,
        ValueError,
    ):
        return Response(
            {
                "error": {
                    "code":
                        "INVALID_REQUEST",

                    "message":
                        str(exception),
                }
            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )

    # ======================================================
    # CONFLICTO DE BASE DE DATOS
    # ======================================================

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

    # ======================================================
    # RECURSO PROTEGIDO
    # ======================================================

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

    # ======================================================
    # ERROR NO CONTROLADO
    # ======================================================

    raise exception