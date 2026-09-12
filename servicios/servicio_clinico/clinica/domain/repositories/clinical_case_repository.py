from abc import (
    ABC,
    abstractmethod,
)

from datetime import (
    date,
)

from uuid import (
    UUID,
)

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


    # ======================================================
    # ANTECEDENTES
    # ======================================================

    @abstractmethod
    def list_antecedents(
        self,
        case_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError


    @abstractmethod
    def create_antecedent(
        self,
        *,
        case_id: UUID,
        antecedent_type_id: int,
        description: str,
        author_uuid: UUID,
    ) -> dict:
        raise NotImplementedError


    # ======================================================
    # SINTOMAS
    # ======================================================

    @abstractmethod
    def list_symptoms(
        self,
        case_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError


    @abstractmethod
    def create_symptom(
        self,
        *,
        case_id: UUID,
        symptom_id: int,
        intensity_id: int | None,
        start_date: date | None,
        observation: str | None,
        author_uuid: UUID,
    ) -> dict:
        raise NotImplementedError


    # ======================================================
    # SIGNOS
    # ======================================================

    @abstractmethod
    def list_signs(
        self,
        case_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError


    @abstractmethod
    def create_sign(
        self,
        *,
        case_id: UUID,
        sign_id: int,
        finding_description: str | None,
        author_uuid: UUID,
    ) -> dict:
        raise NotImplementedError


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    @abstractmethod
    def list_observations(
        self,
        case_id: UUID,
    ) -> list[dict]:
        raise NotImplementedError


    @abstractmethod
    def create_observation(
        self,
        *,
        case_id: UUID,
        content: str,
        author_uuid: UUID,
    ) -> dict:
        raise NotImplementedError