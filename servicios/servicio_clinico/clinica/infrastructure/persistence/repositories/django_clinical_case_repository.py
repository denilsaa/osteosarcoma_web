import uuid

from datetime import date

from uuid import UUID

from django.db import (
    transaction,
)

from django.db.models import (
    Q,
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
    ClinicalCaseRepository,
)

from clinica.infrastructure.persistence.models import (
    CasoClinico,
    EstadoCaso,
    HistorialEstadoCaso,
    PrioridadCaso,
)


class DjangoClinicalCaseRepository(
    ClinicalCaseRepository,
):

    # ======================================================
    # CONVERTIR ORM -> ENTIDAD
    # ======================================================

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


        patient_name = " ".join(
            part.strip()
            for part in [
                model
                .paciente
                .nombres,

                model
                .paciente
                .apellido_paterno,

                model
                .paciente
                .apellido_materno,
            ]
            if part
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

            patient_name=
                patient_name,
        )


    # ======================================================
    # QUERYSET BASE
    # ======================================================

    @staticmethod
    def _base_queryset():

        return (
            CasoClinico
            .objects
            .select_related(
                "paciente",
                "estado_caso",
                "prioridad",
            )
        )


    # ======================================================
    # CREAR
    # ======================================================

    @transaction.atomic
    def create(
        self,
        *,
        patient_id: UUID,
        priority_id: int,
        responsible_oncologist_uuid: UUID,
        consultation_reason: str,
        general_observation: str | None,
    ) -> ClinicalCase:

        estado = (
            EstadoCaso
            .objects
            .get(
                codigo=
                    "REGISTRADO",
            )
        )


        prioridad = (
            PrioridadCaso
            .objects
            .get(
                id_prioridad=
                    priority_id,
            )
        )


        case_uuid = (
            uuid.uuid4()
        )


        codigo = (
            f"CAS-"
            f"{timezone.now().year}-"
            f"{case_uuid.hex[:8].upper()}"
        )


        model = (
            CasoClinico
            .objects
            .create(
                id_caso=
                    case_uuid,

                paciente_id=
                    patient_id,

                estado_caso=
                    estado,

                prioridad=
                    prioridad,

                codigo_caso=
                    codigo,

                oncologo_responsable_uuid=
                    responsible_oncologist_uuid,

                motivo_consulta=
                    consultation_reason,

                observacion_general=
                    general_observation,
            )
        )


        model = (
            self
            ._base_queryset()
            .get(
                id_caso=
                    model.id_caso,
            )
        )


        return self._to_entity(
            model,
        )


    # ======================================================
    # OBTENER
    # ======================================================

    def get_by_id(
        self,
        case_id: UUID,
    ) -> ClinicalCase | None:

        model = (
            self
            ._base_queryset()
            .filter(
                id_caso=
                    case_id,
            )
            .first()
        )


        if model is None:

            return None


        return self._to_entity(
            model,
        )


    # ======================================================
    # CASOS POR PACIENTE
    # ======================================================

    def list_by_patient(
        self,
        patient_id: UUID,
    ) -> list[
        ClinicalCase
    ]:

        queryset = (
            self
            ._base_queryset()
            .filter(
                paciente_id=
                    patient_id,
            )
            .order_by(
                "-fecha_apertura",
            )
        )


        return [
            self._to_entity(
                model,
            )
            for model
            in queryset
        ]


    # ======================================================
    # LISTADO GENERAL
    # ======================================================

    def list_cases(
        self,
        *,
        search: str | None,
        status_code: str | None,
        priority_code: str | None,
        patient_id: UUID | None,
        responsible_oncologist_uuid: UUID | None,
        opening_date: date | None,
        page: int,
        page_size: int,
    ) -> tuple[
        list[ClinicalCase],
        int,
    ]:

        queryset = (
            self
            ._base_queryset()
            .all()
        )


        if search:

            value = (
                search.strip()
            )


            queryset = (
                queryset
                .filter(
                    Q(
                        codigo_caso__icontains=
                            value,
                    )
                    |
                    Q(
                        paciente__nombres__icontains=
                            value,
                    )
                    |
                    Q(
                        paciente__apellido_paterno__icontains=
                            value,
                    )
                    |
                    Q(
                        paciente__apellido_materno__icontains=
                            value,
                    )
                )
            )


        if status_code:

            queryset = (
                queryset
                .filter(
                    estado_caso__codigo=
                        status_code,
                )
            )


        if priority_code:

            queryset = (
                queryset
                .filter(
                    prioridad__codigo=
                        priority_code,
                )
            )


        if patient_id:

            queryset = (
                queryset
                .filter(
                    paciente_id=
                        patient_id,
                )
            )


        if responsible_oncologist_uuid:

            queryset = (
                queryset
                .filter(
                    oncologo_responsable_uuid=
                        responsible_oncologist_uuid,
                )
            )


        if opening_date:

            queryset = (
                queryset
                .filter(
                    fecha_apertura__date=
                        opening_date,
                )
            )


        queryset = (
            queryset
            .order_by(
                "-fecha_apertura",
            )
        )


        total = (
            queryset.count()
        )


        start = (
            (
                page - 1
            )
            *
            page_size
        )


        end = (
            start
            +
            page_size
        )


        models = (
            queryset[
                start:end
            ]
        )


        return (
            [
                self._to_entity(
                    model,
                )
                for model
                in models
            ],
            total,
        )


    # ======================================================
    # HISTORIAL INICIAL
    # ======================================================

    @transaction.atomic
    def create_initial_history(
        self,
        *,
        case_id: UUID,
        user_uuid: UUID,
        observation: str | None = None,
    ) -> None:

        case = (
            CasoClinico
            .objects
            .select_related(
                "estado_caso",
            )
            .get(
                id_caso=
                    case_id,
            )
        )


        HistorialEstadoCaso.objects.create(
            caso=
                case,

            estado_anterior=
                None,

            estado_nuevo=
                case.estado_caso,

            usuario_uuid=
                user_uuid,

            observacion=
                (
                    observation
                    or
                    "Registro inicial del caso clínico."
                ),
        )


    # ======================================================
    # CATÁLOGOS
    # ======================================================

    def list_catalogs(
        self,
    ) -> dict:

        estados = [
            {
                "id":
                    item.id_estado_caso,

                "code":
                    item.codigo,

                "name":
                    item.nombre,
            }
            for item
            in EstadoCaso
            .objects
            .all()
            .order_by(
                "id_estado_caso",
            )
        ]


        prioridades = [
            {
                "id":
                    item.id_prioridad,

                "code":
                    item.codigo,

                "name":
                    item.nombre,

                "level":
                    item.nivel,
            }
            for item
            in PrioridadCaso
            .objects
            .all()
            .order_by(
                "nivel",
            )
        ]


        return {
            "statuses":
                estados,

            "priorities":
                prioridades,
        }