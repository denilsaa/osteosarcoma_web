import re
from datetime import date

from ..exceptions import (
    EditReasonRequiredError,
    InvalidPatientDataError,
)


class PatientDomainService:
    """
    Reglas puras del dominio Paciente.

    No depende de Django,
    base de datos, HTTP ni RabbitMQ.
    """

    @staticmethod
    def normalize_text(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = " ".join(
            value.strip().split()
        )

        return value or None

    @staticmethod
    def normalize_document(
        value: str,
    ) -> str:
        value = value.strip().upper()

        value = re.sub(
            r"\s+",
            "",
            value,
        )

        if not value:
            raise InvalidPatientDataError(
                "El número de documento "
                "es obligatorio."
            )

        return value

    @staticmethod
    def normalize_contact(
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value or None

    @staticmethod
    def validate_name(
        value: str,
        field_name: str,
    ) -> str:
        normalized = (
            PatientDomainService
            .normalize_text(
                value
            )
        )

        if (
            not normalized
            or len(normalized) < 2
        ):
            raise InvalidPatientDataError(
                f"{field_name} no es válido."
            )

        return normalized

    @staticmethod
    def validate_birth_date(
        birth_date: date,
    ) -> None:
        if birth_date > date.today():
            raise InvalidPatientDataError(
                "La fecha de nacimiento "
                "no puede ser futura."
            )

    @staticmethod
    def validate_edit_reason(
        reason: str | None,
    ) -> str:
        reason = (
            PatientDomainService
            .normalize_text(
                reason
            )
        )

        if (
            not reason
            or len(reason) < 5
        ):
            raise EditReasonRequiredError()

        return reason