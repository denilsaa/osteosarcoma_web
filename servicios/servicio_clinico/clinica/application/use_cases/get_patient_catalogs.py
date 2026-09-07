from clinica.domain.repositories import (
    CatalogRepository,
)


class GetPatientCatalogsUseCase:
    def __init__(
        self,
        repository: CatalogRepository,
    ):
        self.repository = repository

    def execute(
        self,
    ) -> dict:
        return (
            self.repository
            .get_patient_catalogs()
        )