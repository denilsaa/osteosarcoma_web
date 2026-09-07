from __future__ import annotations

from abc import ABC, abstractmethod


class CatalogRepository(ABC):
    """
    Puerto de lectura para catálogos del dominio clínico.
    """

    @abstractmethod
    def get_patient_catalogs(
        self,
    ) -> dict:
        raise NotImplementedError