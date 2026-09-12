from uuid import (
    UUID,
)

from django.db import (
    transaction,
)

from django.utils import (
    timezone,
)

from clinica.domain.entities import (
    ClinicalCase,
    ClinicalCasePriority,
    ClinicalCaseStatus,
)

from clinica.domain.repositories import (
    ClinicalCaseStatusRepository,
)

from clinica.infrastructure.persistence.models import (
    CasoClinico,
    EstadoCaso,
    HistorialEstadoCaso,
)


STATUS_FLOW = (
    "REGISTRADO",
    "PENDIENTE",
    "EN_ANALISIS",
    "REVISADO",
    "CERRADO",
)


class DjangoClinicalCaseStatusRepository(
    ClinicalCaseStatusRepository,
):

    # ======================================================
    # CONVERTIR ORM -> ENTIDAD
    # ======================================================

    @staticmethod
    def _to_entity(
        model: CasoClinico,
    ) -> ClinicalCase:

        status = ClinicalCaseStatus(
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

        priority = ClinicalCasePriority(
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

        patient_name = " ".join(
            part.strip()
            for part in [
                model.paciente.nombres,
                model.paciente.apellido_paterno,
                model.paciente.apellido_materno,
            ]
            if part
        )

        return ClinicalCase(
            id_case=
                model.id_caso,

            patient_id=
                model.paciente_id,

            code=
                model.codigo_caso,

            status=
                status,

            priority=
                priority,

            responsible_oncologist_uuid=
                model
                .oncologo_responsable_uuid,

            opening_date=
                model.fecha_apertura,

            closing_date=
                model.fecha_cierre,

            consultation_reason=
                model.motivo_consulta,

            general_observation=
                model.observacion_general,

            patient_name=
                patient_name,
        )


    # ======================================================
    # HISTORIAL DE ESTADOS
    # ======================================================

    def list_status_history(
        self,
        case_id: UUID,
    ) -> list[dict]:

        exists = (
            CasoClinico
            .objects
            .filter(
                id_caso=
                    case_id,
            )
            .exists()
        )

        if not exists:

            raise ValueError(
                "El caso clínico no existe."
            )


        queryset = (
            HistorialEstadoCaso
            .objects
            .select_related(
                "estado_anterior",
                "estado_nuevo",
            )
            .filter(
                caso_id=
                    case_id,
            )
            .order_by(
                "fecha_cambio",
                "id_historial",
            )
        )


        return [
            {
                "id_history":
                    item.id_historial,

                "previous_status":
                    (
                        {
                            "id":
                                item
                                .estado_anterior
                                .id_estado_caso,

                            "code":
                                item
                                .estado_anterior
                                .codigo,

                            "name":
                                item
                                .estado_anterior
                                .nombre,
                        }
                        if
                        item.estado_anterior
                        else None
                    ),

                "new_status": {
                    "id":
                        item
                        .estado_nuevo
                        .id_estado_caso,

                    "code":
                        item
                        .estado_nuevo
                        .codigo,

                    "name":
                        item
                        .estado_nuevo
                        .nombre,
                },

                "user_uuid":
                    str(
                        item.usuario_uuid
                    ),

                "changed_at":
                    item
                    .fecha_cambio
                    .isoformat(),

                "observation":
                    item.observacion,
            }
            for item in queryset
        ]


    # ======================================================
    # AVANZAR ESTADO
    # ======================================================

    @transaction.atomic
    def advance_status(
        self,
        *,
        case_id: UUID,
        user_uuid: UUID,
        observation: str | None = None,
    ) -> ClinicalCase:

        case = (
            CasoClinico
            .objects
            .select_for_update()
            .select_related(
                "paciente",
                "estado_caso",
                "prioridad",
            )
            .filter(
                id_caso=
                    case_id,
            )
            .first()
        )


        if case is None:

            raise ValueError(
                "El caso clínico no existe."
            )


        current_code = (
            case
            .estado_caso
            .codigo
        )


        try:

            current_index = (
                STATUS_FLOW
                .index(
                    current_code
                )
            )

        except ValueError as error:

            raise ValueError(
                "El estado actual del caso "
                "no pertenece al flujo clínico válido."
            ) from error


        if (
            current_code
            ==
            "CERRADO"
        ):

            raise ValueError(
                "El caso clínico ya se encuentra cerrado."
            )


        next_code = (
            STATUS_FLOW[
                current_index
                +
                1
            ]
        )


        next_status = (
            EstadoCaso
            .objects
            .filter(
                codigo=
                    next_code,
            )
            .first()
        )


        if next_status is None:

            raise ValueError(
                (
                    "No se encontró el estado siguiente "
                    f"'{next_code}' en el catálogo."
                )
            )


        previous_status = (
            case.estado_caso
        )


        case.estado_caso = (
            next_status
        )


        update_fields = [
            "estado_caso",
        ]


        if (
            next_code
            ==
            "CERRADO"
        ):

            case.fecha_cierre = (
                timezone.now()
            )

            update_fields.append(
                "fecha_cierre"
            )


        case.save(
            update_fields=
                update_fields
        )


        HistorialEstadoCaso.objects.create(
            caso=
                case,

            estado_anterior=
                previous_status,

            estado_nuevo=
                next_status,

            usuario_uuid=
                user_uuid,

            observacion=
                (
                    observation
                    or
                    (
                        f"Avance de estado de "
                        f"{previous_status.nombre} "
                        f"a {next_status.nombre}."
                    )
                ),
        )


        refreshed = (
            CasoClinico
            .objects
            .select_related(
                "paciente",
                "estado_caso",
                "prioridad",
            )
            .get(
                id_caso=
                    case_id,
            )
        )


        return (
            self._to_entity(
                refreshed
            )
        )