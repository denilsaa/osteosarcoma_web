from uuid import (
    UUID,
)

from clinica.application.dto import (
    CreateClinicalAntecedentDTO,
    CreateClinicalObservationDTO,
    CreateClinicalSignDTO,
    CreateClinicalSymptomDTO,
)

from clinica.domain.repositories import (
    ClinicalCaseRepository,
)


class ClinicalCaseInformationUseCase:

    def __init__(
        self,
        case_repository:
            ClinicalCaseRepository,
    ):

        self.case_repository = (
            case_repository
        )


    # ======================================================
    # ANTECEDENTES
    # ======================================================

    def list_antecedents(
        self,
        case_id: UUID,
    ) -> list[dict]:

        return (
            self.case_repository
            .list_antecedents(
                case_id,
            )
        )


    def create_antecedent(
        self,
        dto:
            CreateClinicalAntecedentDTO,
        *,
        actor_uuid:
            UUID,
    ) -> dict:

        description = (
            dto.description.strip()
        )

        if len(description) < 3:
            raise ValueError(
                "La descripción del antecedente "
                "debe contener al menos 3 caracteres."
            )

        return (
            self.case_repository
            .create_antecedent(
                case_id=
                    dto.case_id,

                antecedent_type_id=
                    dto.antecedent_type_id,

                description=
                    description,

                author_uuid=
                    actor_uuid,
            )
        )


    # ======================================================
    # SINTOMAS
    # ======================================================

    def list_symptoms(
        self,
        case_id: UUID,
    ) -> list[dict]:

        return (
            self.case_repository
            .list_symptoms(
                case_id,
            )
        )


    def create_symptom(
        self,
        dto:
            CreateClinicalSymptomDTO,
        *,
        actor_uuid:
            UUID,
    ) -> dict:

        return (
            self.case_repository
            .create_symptom(
                case_id=
                    dto.case_id,

                symptom_id=
                    dto.symptom_id,

                intensity_id=
                    dto.intensity_id,

                start_date=
                    dto.start_date,

                observation=
                    dto.observation,

                author_uuid=
                    actor_uuid,
            )
        )


    # ======================================================
    # SIGNOS
    # ======================================================

    def list_signs(
        self,
        case_id: UUID,
    ) -> list[dict]:

        return (
            self.case_repository
            .list_signs(
                case_id,
            )
        )


    def create_sign(
        self,
        dto:
            CreateClinicalSignDTO,
        *,
        actor_uuid:
            UUID,
    ) -> dict:

        return (
            self.case_repository
            .create_sign(
                case_id=
                    dto.case_id,

                sign_id=
                    dto.sign_id,

                finding_description=
                    dto.finding_description,

                author_uuid=
                    actor_uuid,
            )
        )


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    def list_observations(
        self,
        case_id: UUID,
    ) -> list[dict]:

        return (
            self.case_repository
            .list_observations(
                case_id,
            )
        )


    def create_observation(
        self,
        dto:
            CreateClinicalObservationDTO,
        *,
        actor_uuid:
            UUID,
    ) -> dict:

        content = (
            dto.content.strip()
        )

        if len(content) < 3:
            raise ValueError(
                "La observación debe contener "
                "al menos 3 caracteres."
            )

        return (
            self.case_repository
            .create_observation(
                case_id=
                    dto.case_id,

                content=
                    content,

                author_uuid=
                    actor_uuid,
            )
        )