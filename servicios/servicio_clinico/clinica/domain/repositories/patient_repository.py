from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from typing import Optional
from uuid import UUID

from ..entities.patient import Patient


class PatientRepository(ABC):
    """
    Puerto de persistencia del agregado Paciente.

    La capa de aplicación depende de esta abstracción
    y nunca directamente del ORM de Django.

    Las implementaciones concretas pertenecen a
    Infrastructure.
    """

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
        contact_type_id: int | None,
        contact_value: str | None,
    ) -> Patient:
        """
        Registra un paciente junto con su documento
        y contacto principal.
        """
        raise NotImplementedError

    @abstractmethod
    def get_by_id(
        self,
        patient_id: UUID,
    ) -> Optional[Patient]:
        """
        Obtiene un paciente mediante su UUID.
        """
        raise NotImplementedError

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
    ) -> tuple[list[Patient], int]:
        """
        Obtiene pacientes aplicando filtros
        y paginación.

        Retorna:
            tuple:
                - pacientes de la página actual
                - cantidad total de coincidencias
        """
        raise NotImplementedError

    @abstractmethod
    def find_exact_document(
        self,
        *,
        document_type_id: int,
        document_number: str,
    ) -> Optional[Patient]:
        """
        Busca una coincidencia exacta por
        tipo y número de documento.
        """
        raise NotImplementedError

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
        """
        Busca posibles pacientes duplicados.

        Puede utilizar coincidencia exacta de documento
        o coincidencia de identidad mediante nombres
        y fecha de nacimiento.
        """
        raise NotImplementedError

    @abstractmethod
    def update(
        self,
        *,
        patient_id: UUID,
        changes: dict,
    ) -> Patient:
        """
        Actualiza únicamente los campos recibidos
        y retorna la representación actualizada
        del paciente.
        """
        raise NotImplementedError