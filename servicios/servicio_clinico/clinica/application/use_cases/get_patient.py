from uuid import UUID

from clinica.domain.exceptions import (
    PatientNotFoundError,
)
from clinica.domain.repositories import (
    PatientRepository,
)


class GetPatientUseCase:
    def __init__(
        self,
        repository: PatientRepository,
    ):
        self.repository = repository

    def execute(
        self,
        patient_id: UUID,
    ):
        patient = (
            self.repository.get_by_id(
                patient_id
            )
        )

        if patient is None:
            raise PatientNotFoundError(
                patient_id
            )

        return patient