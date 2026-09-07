from uuid import UUID

from clinica.domain.exceptions import (
    PatientNotFoundError,
)
from clinica.domain.repositories import (
    ClinicalCaseRepository,
    PatientRepository,
)


class ListPatientCasesUseCase:

    def __init__(
        self,
        patient_repository:
            PatientRepository,

        case_repository:
            ClinicalCaseRepository,
    ):

        self.patient_repository = (
            patient_repository
        )

        self.case_repository = (
            case_repository
        )


    def execute(
        self,
        patient_id: UUID,
    ):

        patient = (
            self.patient_repository
            .get_by_id(
                patient_id
            )
        )


        if patient is None:

            raise PatientNotFoundError(
                patient_id
            )


        return (
            self.case_repository
            .list_by_patient(
                patient_id
            )
        )