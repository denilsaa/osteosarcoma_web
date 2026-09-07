from functools import (
    lru_cache,
)

from clinica.application.services import (
    AuditService,
)
from clinica.application.use_cases import (
    CreatePatientUseCase,
    FindPatientDuplicatesUseCase,
    GetPatientCatalogsUseCase,
    GetPatientUseCase,
    ListPatientCasesUseCase,
    ListPatientsUseCase,
    UpdatePatientUseCase,
)
from clinica.infrastructure.messaging import (
    RabbitMQAuditEventPublisher,
)
from clinica.infrastructure.persistence.repositories import (
    DjangoCatalogRepository,
    DjangoClinicalCaseRepository,
    DjangoPatientRepository,
)


class ApplicationContainer:
    """
    Composition Root del microservicio Clínico.
    """

    def __init__(
        self,
    ):

        # ======================================================
        # REPOSITORIES
        # ======================================================

        self.patient_repository = (
            DjangoPatientRepository()
        )


        self.catalog_repository = (
            DjangoCatalogRepository()
        )


        self.clinical_case_repository = (
            DjangoClinicalCaseRepository()
        )


        # ======================================================
        # MESSAGING ADAPTERS
        # ======================================================

        self.audit_event_publisher = (
            RabbitMQAuditEventPublisher()
        )


        # ======================================================
        # APPLICATION SERVICES
        # ======================================================

        self.audit_service = (
            AuditService(
                self.audit_event_publisher
            )
        )


        # ======================================================
        # USE CASES - PACIENTES
        # ======================================================

        self.create_patient = (
            CreatePatientUseCase(
                self.patient_repository
            )
        )


        self.get_patient = (
            GetPatientUseCase(
                self.patient_repository
            )
        )


        self.list_patients = (
            ListPatientsUseCase(
                self.patient_repository
            )
        )


        self.find_patient_duplicates = (
            FindPatientDuplicatesUseCase(
                self.patient_repository
            )
        )


        self.update_patient = (
            UpdatePatientUseCase(
                self.patient_repository
            )
        )


        self.get_patient_catalogs = (
            GetPatientCatalogsUseCase(
                self.catalog_repository
            )
        )


        # ======================================================
        # USE CASES - CASOS CLÍNICOS
        # ======================================================

        self.list_patient_cases = (
            ListPatientCasesUseCase(
                patient_repository=
                    self.patient_repository,

                case_repository=
                    self.clinical_case_repository,
            )
        )


@lru_cache(
    maxsize=1
)
def get_container(
) -> ApplicationContainer:

    return ApplicationContainer()