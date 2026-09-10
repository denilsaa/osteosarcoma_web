from uuid import UUID

from clinica.application.dto import (
    CreateClinicalCaseDTO,
)

from clinica.domain.repositories import (
    ClinicalCaseRepository,
    PatientRepository,
)


class CreateClinicalCaseUseCase:

    def __init__(
        self,
        *,
        patient_repository:
            PatientRepository,

        case_repository:
            ClinicalCaseRepository,
    ):

        self.patient_repository = (
            patient_repository
        )

        self.case_repository = (
            case_repository
        )


    def execute(
        self,
        dto:
            CreateClinicalCaseDTO,

        actor_uuid:
            UUID,
    ):

        patient = (
            self
            .patient_repository
            .get_by_id(
                dto.patient_id,
            )
        )


        if patient is None:

            raise ValueError(
                "El paciente no existe."
            )


        if not patient.active:

            raise ValueError(
                "No puede registrar un caso clínico "
                "para un paciente inactivo."
            )


        reason = (
            dto
            .consultation_reason
            .strip()
        )


        if len(reason) < 5:

            raise ValueError(
                "El motivo de consulta debe contener "
                "al menos 5 caracteres."
            )


        observation = (
            dto
            .general_observation
            .strip()
            if dto.general_observation
            else None
        )


        case = (
            self
            .case_repository
            .create(
                patient_id=
                    dto.patient_id,

                priority_id=
                    dto.priority_id,

                responsible_oncologist_uuid=
                    dto.responsible_oncologist_uuid,

                consultation_reason=
                    reason,

                general_observation=
                    observation,
            )
        )


        self.case_repository.create_initial_history(
            case_id=
                case.id_case,

            user_uuid=
                actor_uuid,

            observation=
                "Caso clínico registrado.",
        )


        return case