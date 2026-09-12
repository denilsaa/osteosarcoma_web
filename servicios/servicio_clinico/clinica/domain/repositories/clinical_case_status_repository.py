from abc import (
    ABC,
    abstractmethod,
)

from uuid import (
    UUID,
)

from clinica.domain.entities import (
    ClinicalCase,
)


class ClinicalCaseStatusRepository(
    ABC,
):

    @abstractmethod
    def list_status_history(
        self,
        case_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError


    @abstractmethod
    def advance_status(
        self,
        *,
        case_id: UUID,
        user_uuid: UUID,
        observation: str | None = None,
    ) -> ClinicalCase:
        raise NotImplementedError