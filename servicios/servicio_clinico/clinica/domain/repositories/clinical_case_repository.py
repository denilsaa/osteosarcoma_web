from abc import (
    ABC,
    abstractmethod,
)

from datetime import date

from uuid import UUID

from clinica.domain.entities import (
    ClinicalCase,
)


class ClinicalCaseRepository(
    ABC,
):

    @abstractmethod
    def create(
        self,
        *,
        patient_id: UUID,
        priority_id: int,
        responsible_oncologist_uuid: UUID,
        consultation_reason: str,
        general_observation: str | None,
    ) -> ClinicalCase:
        raise NotImplementedError


    @abstractmethod
    def get_by_id(
        self,
        case_id: UUID,
    ) -> ClinicalCase | None:
        raise NotImplementedError


    @abstractmethod
    def list_by_patient(
        self,
        patient_id: UUID,
    ) -> list[
        ClinicalCase
    ]:
        raise NotImplementedError


    @abstractmethod
    def list_cases(
        self,
        *,
        search: str | None,
        status_code: str | None,
        priority_code: str | None,
        patient_id: UUID | None,
        responsible_oncologist_uuid: UUID | None,
        opening_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[
        list[ClinicalCase],
        int,
    ]:
        raise NotImplementedError


    @abstractmethod
    def create_initial_history(
        self,
        *,
        case_id: UUID,
        user_uuid: UUID,
        observation: str | None = None,
    ) -> None:
        raise NotImplementedError


    @abstractmethod
    def list_catalogs(
        self,
    ) -> dict:
        raise NotImplementedError