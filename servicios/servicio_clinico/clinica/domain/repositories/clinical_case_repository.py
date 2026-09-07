from abc import (
    ABC,
    abstractmethod,
)
from uuid import UUID

from clinica.domain.entities import (
    ClinicalCase,
)


class ClinicalCaseRepository(
    ABC,
):

    @abstractmethod
    def list_by_patient(
        self,
        patient_id: UUID,
    ) -> list[
        ClinicalCase
    ]:
        raise NotImplementedError