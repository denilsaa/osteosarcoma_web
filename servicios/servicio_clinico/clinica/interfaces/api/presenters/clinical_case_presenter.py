from __future__ import annotations

from clinica.domain.entities import (
    ClinicalCase,
)


class ClinicalCasePresenter:

    # ======================================================
    # DETALLE
    # ======================================================

    @staticmethod
    def detail(
        case: ClinicalCase,
    ) -> dict:

        return {

            "id_case":
                str(
                    case.id_case
                ),

            "patient_id":
                str(
                    case.patient_id
                ),

            "patient_name":
                case.patient_name,

            "code":
                case.code,

            "status": {

                "id":
                    case.status.id,

                "code":
                    case.status.code,

                "name":
                    case.status.name,

            },

            "priority": {

                "id":
                    case.priority.id,

                "code":
                    case.priority.code,

                "name":
                    case.priority.name,

                "level":
                    case.priority.level,

            },

            "responsible_oncologist_uuid":
                (
                    str(
                        case
                        .responsible_oncologist_uuid
                    )
                    if case
                    .responsible_oncologist_uuid
                    else None
                ),

            "opening_date":
                case
                .opening_date
                .isoformat(),

            "closing_date":
                (
                    case
                    .closing_date
                    .isoformat()
                    if case
                    .closing_date
                    else None
                ),

            "consultation_reason":
                case
                .consultation_reason,

            "general_observation":
                case
                .general_observation,

        }


    # ======================================================
    # LISTADO POR PACIENTE
    # ======================================================

    @classmethod
    def list(
        cls,
        cases: list[ClinicalCase],
    ) -> dict:

        return {

            "data": [

                cls.detail(
                    case
                )

                for case
                in cases

            ],

            "total":
                len(
                    cases
                ),

        }


    # ======================================================
    # LISTADO GENERAL PAGINADO
    # ======================================================

    @classmethod
    def paginated(
        cls,
        *,
        cases: list[ClinicalCase],
        pagination: dict,
    ) -> dict:

        return {

            "data": [

                cls.detail(
                    case
                )

                for case
                in cases

            ],

            "pagination":
                pagination,

        }