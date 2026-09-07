from clinica.application.dto import (
    FieldChangeDTO,
    UpdatePatientDTO,
)
from clinica.domain.exceptions import (
    PatientNotFoundError,
    PatientWithoutChangesError,
)
from clinica.domain.repositories import (
    PatientRepository,
)
from clinica.domain.services import (
    PatientDomainService,
)


class UpdatePatientUseCase:
    def __init__(
        self,
        repository: PatientRepository,
    ):
        self.repository = repository

    @staticmethod
    def _normalize_value(
        value,
    ):
        if value is None:
            return None

        if hasattr(
            value,
            "isoformat",
        ):
            return value.isoformat()

        if isinstance(
            value,
            bool,
        ):
            return (
                "true"
                if value
                else "false"
            )

        return str(value)

    def execute(
        self,
        dto: UpdatePatientDTO,
    ):
        current = (
            self.repository.get_by_id(
                dto.patient_id
            )
        )

        if current is None:
            raise PatientNotFoundError(
                dto.patient_id
            )

        reason = (
            PatientDomainService
            .validate_edit_reason(
                dto.reason
            )
        )

        requested_changes = {}

        if dto.first_names is not None:
            requested_changes[
                "first_names"
            ] = (
                PatientDomainService
                .validate_name(
                    dto.first_names,
                    "Los nombres",
                )
            )

        if (
            dto.paternal_surname
            is not None
        ):
            requested_changes[
                "paternal_surname"
            ] = (
                PatientDomainService
                .validate_name(
                    dto
                    .paternal_surname,
                    "El apellido paterno",
                )
            )

        if (
            dto.maternal_surname
            is not None
        ):
            requested_changes[
                "maternal_surname"
            ] = (
                PatientDomainService
                .normalize_text(
                    dto
                    .maternal_surname
                )
            )

        if dto.birth_date is not None:
            PatientDomainService.validate_birth_date(
                dto.birth_date
            )

            requested_changes[
                "birth_date"
            ] = dto.birth_date

        if dto.sex_id is not None:
            requested_changes[
                "sex_id"
            ] = dto.sex_id

        if dto.active is not None:
            requested_changes[
                "active"
            ] = dto.active

        current_values = {
            "first_names":
                current.first_names,

            "paternal_surname":
                current
                .paternal_surname,

            "maternal_surname":
                current
                .maternal_surname,

            "birth_date":
                current.birth_date,

            "sex_id":
                current.sex_id,

            "active":
                current.active,
        }

        actual_changes = {}

        audit_changes = []

        for field, new_value in (
            requested_changes.items()
        ):
            old_value = (
                current_values[field]
            )

            if old_value == new_value:
                continue

            actual_changes[
                field
            ] = new_value

            audit_changes.append(
                FieldChangeDTO(
                    field=field,

                    old_value=
                        self._normalize_value(
                            old_value
                        ),

                    new_value=
                        self._normalize_value(
                            new_value
                        ),
                )
            )

        if not actual_changes:
            raise PatientWithoutChangesError()

        updated = (
            self.repository.update(
                patient_id=
                    dto.patient_id,

                changes=
                    actual_changes,
            )
        )

        return {
            "patient":
                updated,

            "reason":
                reason,

            "changes":
                audit_changes,
        }