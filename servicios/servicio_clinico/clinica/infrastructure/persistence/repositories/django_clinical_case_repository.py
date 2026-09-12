import uuid

from datetime import (
    date,
)

from uuid import (
    UUID,
)

from django.db import (
    IntegrityError,
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
    AntecedenteClinico,
    CasoClinico,
    CasoObservacion,
    CasoSigno,
    CasoSintoma,
    CatalogoSigno,
    CatalogoSintoma,
    EstadoCaso,
    HistorialEstadoCaso,
    NivelIntensidad,
    PrioridadCaso,
    TipoAntecedente,
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

        status = ClinicalCaseStatus(
            id=model.estado_caso.id_estado_caso,
            code=model.estado_caso.codigo,
            name=model.estado_caso.nombre,
        )

        priority = ClinicalCasePriority(
            id=model.prioridad.id_prioridad,
            code=model.prioridad.codigo,
            name=model.prioridad.nombre,
            level=model.prioridad.nivel,
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
            id_case=model.id_caso,
            patient_id=model.paciente_id,
            code=model.codigo_caso,
            status=status,
            priority=priority,
            responsible_oncologist_uuid=
                model.oncologo_responsable_uuid,
            opening_date=model.fecha_apertura,
            closing_date=model.fecha_cierre,
            consultation_reason=model.motivo_consulta,
            general_observation=
                model.observacion_general,
            patient_name=patient_name,
        )


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


    @staticmethod
    def _get_case_model(
        case_id: UUID,
    ) -> CasoClinico:

        case = (
            CasoClinico
            .objects
            .select_related(
                "paciente",
            )
            .filter(
                id_caso=case_id,
            )
            .first()
        )

        if case is None:
            raise ValueError(
                "El caso clínico no existe."
            )

        return case


    # ======================================================
    # CREAR CASO
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

        estado = EstadoCaso.objects.get(
            codigo="REGISTRADO",
        )

        prioridad = PrioridadCaso.objects.get(
            id_prioridad=priority_id,
        )

        case_uuid = uuid.uuid4()

        codigo = (
            f"CAS-"
            f"{timezone.now().year}-"
            f"{case_uuid.hex[:8].upper()}"
        )

        model = CasoClinico.objects.create(
            id_caso=case_uuid,
            paciente_id=patient_id,
            estado_caso=estado,
            prioridad=prioridad,
            codigo_caso=codigo,
            oncologo_responsable_uuid=
                responsible_oncologist_uuid,
            motivo_consulta=
                consultation_reason,
            observacion_general=
                general_observation,
        )

        model = (
            self
            ._base_queryset()
            .get(
                id_caso=model.id_caso,
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
                id_caso=case_id,
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
    ) -> list[ClinicalCase]:

        queryset = (
            self
            ._base_queryset()
            .filter(
                paciente_id=patient_id,
            )
            .order_by(
                "-fecha_apertura",
            )
        )

        return [
            self._to_entity(model)
            for model in queryset
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

            value = search.strip()

            queryset = queryset.filter(
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

        if status_code:

            queryset = queryset.filter(
                estado_caso__codigo=
                    status_code,
            )

        if priority_code:

            queryset = queryset.filter(
                prioridad__codigo=
                    priority_code,
            )

        if patient_id:

            queryset = queryset.filter(
                paciente_id=patient_id,
            )

        if responsible_oncologist_uuid:

            queryset = queryset.filter(
                oncologo_responsable_uuid=
                    responsible_oncologist_uuid,
            )

        if opening_date:

            queryset = queryset.filter(
                fecha_apertura__date=
                    opening_date,
            )

        queryset = queryset.order_by(
            "-fecha_apertura",
        )

        total = queryset.count()

        start = (
            (page - 1)
            *
            page_size
        )

        end = (
            start
            +
            page_size
        )

        models = queryset[
            start:end
        ]

        return (
            [
                self._to_entity(model)
                for model in models
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
                id_caso=case_id,
            )
        )

        HistorialEstadoCaso.objects.create(
            caso=case,
            estado_anterior=None,
            estado_nuevo=
                case.estado_caso,
            usuario_uuid=user_uuid,
            observacion=(
                observation
                or
                "Registro inicial del caso clínico."
            ),
        )


    # ======================================================
    # CATALOGOS
    # ======================================================

    def list_catalogs(
        self,
    ) -> dict:

        statuses = [
            {
                "id":
                    item.id_estado_caso,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
            }
            for item
            in EstadoCaso.objects.all().order_by(
                "id_estado_caso"
            )
        ]

        priorities = [
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
            in PrioridadCaso.objects.all().order_by(
                "nivel"
            )
        ]

        antecedent_types = [
            {
                "id":
                    item.id_tipo_antecedente,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
                "description":
                    item.descripcion,
            }
            for item
            in TipoAntecedente.objects.all().order_by(
                "nombre"
            )
        ]

        symptoms = [
            {
                "id":
                    item.id_sintoma,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
                "description":
                    item.descripcion,
            }
            for item
            in CatalogoSintoma.objects.all().order_by(
                "nombre"
            )
        ]

        intensity_levels = [
            {
                "id":
                    item.id_nivel_intensidad,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
                "level":
                    item.nivel,
            }
            for item
            in NivelIntensidad.objects.all().order_by(
                "nivel"
            )
        ]

        signs = [
            {
                "id":
                    item.id_signo,
                "code":
                    item.codigo,
                "name":
                    item.nombre,
                "description":
                    item.descripcion,
            }
            for item
            in CatalogoSigno.objects.all().order_by(
                "nombre"
            )
        ]

        return {
            "statuses":
                statuses,
            "priorities":
                priorities,
            "antecedent_types":
                antecedent_types,
            "symptoms":
                symptoms,
            "intensity_levels":
                intensity_levels,
            "signs":
                signs,
        }


    # ======================================================
    # ANTECEDENTES
    # ======================================================

    def list_antecedents(
        self,
        case_id: UUID,
    ) -> list[dict]:

        case = self._get_case_model(
            case_id,
        )

        queryset = (
            AntecedenteClinico
            .objects
            .select_related(
                "tipo_antecedente",
            )
            .filter(
                paciente_id=
                    case.paciente_id,
                vigente=True,
            )
            .order_by(
                "-fecha_registro",
            )
        )

        return [
            {
                "id_antecedent":
                    str(item.id_antecedente),

                "type": {
                    "id":
                        item.tipo_antecedente
                        .id_tipo_antecedente,

                    "code":
                        item.tipo_antecedente.codigo,

                    "name":
                        item.tipo_antecedente.nombre,
                },

                "description":
                    item.descripcion,

                "author_uuid":
                    (
                        str(
                            item.registrado_por_uuid
                        )
                        if
                        item.registrado_por_uuid
                        else None
                    ),

                "registered_at":
                    item.fecha_registro.isoformat(),

                "active":
                    item.vigente,
            }
            for item in queryset
        ]


    @transaction.atomic
    def create_antecedent(
        self,
        *,
        case_id: UUID,
        antecedent_type_id: int,
        description: str,
        author_uuid: UUID,
    ) -> dict:

        case = self._get_case_model(
            case_id,
        )

        antecedent_type = (
            TipoAntecedente
            .objects
            .filter(
                id_tipo_antecedente=
                    antecedent_type_id,
            )
            .first()
        )

        if antecedent_type is None:
            raise ValueError(
                "El tipo de antecedente no existe."
            )

        item = (
            AntecedenteClinico
            .objects
            .create(
                paciente_id=
                    case.paciente_id,

                tipo_antecedente=
                    antecedent_type,

                descripcion=
                    description.strip(),

                registrado_por_uuid=
                    author_uuid,

                vigente=True,
            )
        )

        return {
            "id_antecedent":
                str(item.id_antecedente),

            "type": {
                "id":
                    antecedent_type.id_tipo_antecedente,

                "code":
                    antecedent_type.codigo,

                "name":
                    antecedent_type.nombre,
            },

            "description":
                item.descripcion,

            "author_uuid":
                str(author_uuid),

            "registered_at":
                item.fecha_registro.isoformat(),

            "active":
                item.vigente,
        }


    # ======================================================
    # SINTOMAS
    # ======================================================

    def list_symptoms(
        self,
        case_id: UUID,
    ) -> list[dict]:

        self._get_case_model(
            case_id,
        )

        queryset = (
            CasoSintoma
            .objects
            .select_related(
                "sintoma",
                "intensidad",
            )
            .filter(
                caso_id=case_id,
            )
            .order_by(
                "-fecha_registro",
            )
        )

        return [
            {
                "id_case_symptom":
                    str(
                        item.id_caso_sintoma
                    ),

                "symptom": {
                    "id":
                        item.sintoma.id_sintoma,

                    "code":
                        item.sintoma.codigo,

                    "name":
                        item.sintoma.nombre,
                },

                "intensity":
                    (
                        {
                            "id":
                                item.intensidad
                                .id_nivel_intensidad,

                            "code":
                                item.intensidad.codigo,

                            "name":
                                item.intensidad.nombre,

                            "level":
                                item.intensidad.nivel,
                        }
                        if item.intensidad
                        else None
                    ),

                "start_date":
                    (
                        item.fecha_inicio.isoformat()
                        if item.fecha_inicio
                        else None
                    ),

                "observation":
                    item.observacion,

                "author_uuid":
                    (
                        str(
                            item.registrado_por_uuid
                        )
                        if item.registrado_por_uuid
                        else None
                    ),

                "registered_at":
                    item.fecha_registro.isoformat(),
            }
            for item in queryset
        ]


    @transaction.atomic
    def create_symptom(
        self,
        *,
        case_id: UUID,
        symptom_id: int,
        intensity_id: int | None,
        start_date: date | None,
        observation: str | None,
        author_uuid: UUID,
    ) -> dict:

        self._get_case_model(
            case_id,
        )

        symptom = (
            CatalogoSintoma
            .objects
            .filter(
                id_sintoma=symptom_id,
            )
            .first()
        )

        if symptom is None:
            raise ValueError(
                "El síntoma seleccionado no existe."
            )

        intensity = None

        if intensity_id is not None:

            intensity = (
                NivelIntensidad
                .objects
                .filter(
                    id_nivel_intensidad=
                        intensity_id,
                )
                .first()
            )

            if intensity is None:
                raise ValueError(
                    "El nivel de intensidad no existe."
                )

        try:

            item = CasoSintoma.objects.create(
                caso_id=case_id,
                sintoma=symptom,
                intensidad=intensity,
                fecha_inicio=start_date,
                observacion=(
                    observation.strip()
                    if observation
                    else None
                ),
                registrado_por_uuid=
                    author_uuid,
            )

        except IntegrityError as error:

            raise ValueError(
                "Este síntoma ya se encuentra "
                "registrado en el caso."
            ) from error

        return {
            "id_case_symptom":
                str(item.id_caso_sintoma),

            "symptom": {
                "id":
                    symptom.id_sintoma,

                "code":
                    symptom.codigo,

                "name":
                    symptom.nombre,
            },

            "intensity":
                (
                    {
                        "id":
                            intensity.id_nivel_intensidad,

                        "code":
                            intensity.codigo,

                        "name":
                            intensity.nombre,

                        "level":
                            intensity.nivel,
                    }
                    if intensity
                    else None
                ),

            "start_date":
                (
                    start_date.isoformat()
                    if start_date
                    else None
                ),

            "observation":
                item.observacion,

            "author_uuid":
                str(author_uuid),

            "registered_at":
                item.fecha_registro.isoformat(),
        }


    # ======================================================
    # SIGNOS
    # ======================================================

    def list_signs(
        self,
        case_id: UUID,
    ) -> list[dict]:

        self._get_case_model(
            case_id,
        )

        queryset = (
            CasoSigno
            .objects
            .select_related(
                "signo",
            )
            .filter(
                caso_id=case_id,
            )
            .order_by(
                "-fecha_observacion",
            )
        )

        return [
            {
                "id_case_sign":
                    str(
                        item.id_caso_signo
                    ),

                "sign": {
                    "id":
                        item.signo.id_signo,

                    "code":
                        item.signo.codigo,

                    "name":
                        item.signo.nombre,
                },

                "finding_description":
                    item.descripcion_hallazgo,

                "author_uuid":
                    str(
                        item.observado_por_uuid
                    ),

                "observed_at":
                    item.fecha_observacion.isoformat(),
            }
            for item in queryset
        ]


    @transaction.atomic
    def create_sign(
        self,
        *,
        case_id: UUID,
        sign_id: int,
        finding_description: str | None,
        author_uuid: UUID,
    ) -> dict:

        self._get_case_model(
            case_id,
        )

        sign = (
            CatalogoSigno
            .objects
            .filter(
                id_signo=sign_id,
            )
            .first()
        )

        if sign is None:
            raise ValueError(
                "El signo seleccionado no existe."
            )

        try:

            item = CasoSigno.objects.create(
                caso_id=case_id,
                signo=sign,
                descripcion_hallazgo=(
                    finding_description.strip()
                    if finding_description
                    else None
                ),
                observado_por_uuid=
                    author_uuid,
            )

        except IntegrityError as error:

            raise ValueError(
                "Este signo ya se encuentra "
                "registrado en el caso."
            ) from error

        return {
            "id_case_sign":
                str(item.id_caso_signo),

            "sign": {
                "id":
                    sign.id_signo,

                "code":
                    sign.codigo,

                "name":
                    sign.nombre,
            },

            "finding_description":
                item.descripcion_hallazgo,

            "author_uuid":
                str(author_uuid),

            "observed_at":
                item.fecha_observacion.isoformat(),
        }


    # ======================================================
    # OBSERVACIONES
    # ======================================================

    def list_observations(
        self,
        case_id: UUID,
    ) -> list[dict]:

        self._get_case_model(
            case_id,
        )

        queryset = (
            CasoObservacion
            .objects
            .filter(
                caso_id=case_id,
                activo=True,
            )
            .order_by(
                "-fecha_registro",
            )
        )

        return [
            {
                "id_observation":
                    str(
                        item.id_observacion
                    ),

                "content":
                    item.contenido,

                "author_uuid":
                    str(
                        item.registrado_por_uuid
                    ),

                "registered_at":
                    item.fecha_registro.isoformat(),

                "active":
                    item.activo,
            }
            for item in queryset
        ]


    @transaction.atomic
    def create_observation(
        self,
        *,
        case_id: UUID,
        content: str,
        author_uuid: UUID,
    ) -> dict:

        self._get_case_model(
            case_id,
        )

        item = (
            CasoObservacion
            .objects
            .create(
                caso_id=case_id,

                contenido=
                    content.strip(),

                registrado_por_uuid=
                    author_uuid,

                activo=True,
            )
        )

        return {
            "id_observation":
                str(
                    item.id_observacion
                ),

            "content":
                item.contenido,

            "author_uuid":
                str(author_uuid),

            "registered_at":
                item.fecha_registro.isoformat(),

            "active":
                item.activo,
        }