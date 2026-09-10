from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)

from datetime import date
from typing import Optional
from uuid import UUID

from ..entities.patient import (
    Patient,
)


class PatientRepository(
    ABC
):
    """
    Puerto de persistencia del agregado Paciente.
    """

    # ======================================================
    # CREAR
    # ======================================================

    @abstractmethod
    def create(
        self,
        *,
        first_names: str,
        paternal_surname: str,
        maternal_surname: str | None,
        birth_date: date,
        sex_id: int,
        document_type_id: int,
        document_number: str,
        complement: str | None,
        issued_in: str | None,
        contacts: list[dict],
        emergency_contacts: list[dict],
    ) -> Patient:

        raise NotImplementedError


    # ======================================================
    # OBTENER
    # ======================================================

    @abstractmethod
    def get_by_id(
        self,
        patient_id: UUID,
    ) -> Optional[Patient]:

        raise NotImplementedError


    # ======================================================
    # LISTAR
    # ======================================================

    @abstractmethod
    def list_patients(
        self,
        *,
        search: str | None,
        sex_code: str | None,
        active: bool | None,
        document_type_code: str | None,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Patient],
        int,
    ]:

        raise NotImplementedError


    # ======================================================
    # DOCUMENTO EXACTO
    # ======================================================

    @abstractmethod
    def find_exact_document(
        self,
        *,
        document_type_id: int,
        document_number: str,
    ) -> Optional[Patient]:

        raise NotImplementedError


    # ======================================================
    # POSIBLES DUPLICADOS
    # ======================================================

    @abstractmethod
    def find_possible_duplicates(
        self,
        *,
        document_type_id: int | None,
        document_number: str | None,
        first_names: str | None,
        paternal_surname: str | None,
        maternal_surname: str | None,
        birth_date: date | None,
        limit: int = 10,
    ) -> list[Patient]:

        raise NotImplementedError


    # ======================================================
    # ACTUALIZAR
    # ======================================================

    @abstractmethod
    def update(
        self,
        *,
        patient_id: UUID,
        changes: dict,
    ) -> Patient:

        raise NotImplementedError