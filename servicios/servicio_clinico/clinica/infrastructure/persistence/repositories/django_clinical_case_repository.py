from uuid import UUID

from clinica.domain.entities import (
    ClinicalCase,
    ClinicalCasePriority,
    ClinicalCaseStatus,
)
from clinica.domain.repositories import (
    ClinicalCaseRepository,
)
from clinica.infrastructure.persistence.models import (
    CasoClinico,
)


class DjangoClinicalCaseRepository(
    ClinicalCaseRepository,
):

    @staticmethod
    def _to_entity(
        model: CasoClinico,
    ) -> ClinicalCase:

        status = (
            ClinicalCaseStatus(
                id=
                    model
                    .estado_caso
                    .id_estado_caso,

                code=
                    model
                    .estado_caso
                    .codigo,

                name=
                    model
                    .estado_caso
                    .nombre,
            )
        )


        priority = (
            ClinicalCasePriority(
                id=
                    model
                    .prioridad
                    .id_prioridad,

                code=
                    model
                    .prioridad
                    .codigo,

                name=
                    model
                    .prioridad
                    .nombre,

                level=
                    model
                    .prioridad
                    .nivel,
            )
        )


        return ClinicalCase(
            id_case=
                model
                .id_caso,

            patient_id=
                model
                .paciente_id,

            code=
                model
                .codigo_caso,

            status=
                status,

            priority=
                priority,

            responsible_oncologist_uuid=
                model
                .oncologo_responsable_uuid,

            opening_date=
                model
                .fecha_apertura,

            closing_date=
                model
                .fecha_cierre,

            consultation_reason=
                model
                .motivo_consulta,

            general_observation=
                model
                .observacion_general,
        )


    def list_by_patient(
        self,
        patient_id: UUID,
    ) -> list[
        ClinicalCase
    ]:

        queryset = (
            CasoClinico
            .objects
            .filter(
                paciente_id=
                    patient_id,
            )
            .select_related(
                "estado_caso",
                "prioridad",
            )
            .order_by(
                "-fecha_apertura",
            )
        )


        return [
            self._to_entity(
                model
            )
            for model
            in queryset
        ]