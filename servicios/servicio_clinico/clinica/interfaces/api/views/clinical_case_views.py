from datetime import (
    date,
)

from uuid import (
    UUID,
)

from rest_framework.decorators import (
    api_view,
)

from rest_framework.request import (
    Request,
)

from rest_framework.response import (
    Response,
)

from clinica.application.dto import (
    AdvanceClinicalCaseStatusDTO,
    ClinicalCaseFiltersDTO,
    CreateClinicalAntecedentDTO,
    CreateClinicalCaseDTO,
    CreateClinicalObservationDTO,
    CreateClinicalSignDTO,
    CreateClinicalSymptomDTO,
)

from clinica.bootstrap.container import (
    get_container,
)

from clinica.infrastructure.security import (
    ClinicalAuthenticationError,
    ClinicalAuthorizationError,
    ClinicalCaseAccess,
)

from clinica.interfaces.api.error_handler import (
    domain_error_response,
)

from clinica.interfaces.api.presenters.clinical_case_presenter import (
    ClinicalCasePresenter,
)

from clinica.interfaces.api.serializers.clinical_case_serializers import (
    AdvanceClinicalCaseStatusSerializer,
    CreateClinicalAntecedentSerializer,
    CreateClinicalCaseSerializer,
    CreateClinicalObservationSerializer,
    CreateClinicalSignSerializer,
    CreateClinicalSymptomSerializer,
)


# ==========================================================
# HELPERS
# ==========================================================

def _get_actor(
    request: Request,
):

    return (
        ClinicalCaseAccess
        .get_actor(
            request
        )
    )


def _get_actor_uuid(
    request: Request,
) -> UUID:

    actor = _get_actor(
        request
    )

    actor_uuid = (
        actor.usuario_uuid
    )

    if actor_uuid is None:
        raise ClinicalAuthenticationError(
            "No fue posible identificar "
            "al usuario autenticado."
        )

    return actor_uuid


def _error_response(
    error: Exception,
):

    response = (
        domain_error_response(
            error
        )
    )

    if response is not None:
        return response

    if isinstance(
        error,
        ClinicalAuthenticationError,
    ):

        return Response(
            {
                "error":
                    str(error)
            },
            status=401,
        )

    if isinstance(
        error,
        ClinicalAuthorizationError,
    ):

        return Response(
            {
                "error":
                    str(error)
            },
            status=403,
        )

    if isinstance(
        error,
        ValueError,
    ):

        return Response(
            {
                "error":
                    str(error)
            },
            status=400,
        )

    raise error


# ==========================================================
# CASOS DEL PACIENTE
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def patient_cases_view(
    request: Request,
    patient_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        if request.method == "GET":

            cases = (
                container
                .list_patient_cases
                .execute(
                    patient_id
                )
            )

            cases = (
                ClinicalCaseAccess
                .filter_cases_for_actor(
                    actor,
                    cases,
                )
            )

            return Response(
                ClinicalCasePresenter.list(
                    cases
                ),
                status=200,
            )

        serializer = (
            CreateClinicalCaseSerializer(
                data=request.data,
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor_uuid = (
            actor.usuario_uuid
        )

        responsible_uuid = (
            ClinicalCaseAccess
            .resolve_responsible_for_create(
                actor,
                data.get(
                    "responsible_oncologist_uuid"
                ),
            )
        )

        dto = CreateClinicalCaseDTO(
            patient_id=
                patient_id,

            priority_id=
                data["priority_id"],

            responsible_oncologist_uuid=
                responsible_uuid,

            consultation_reason=
                data["consultation_reason"],

            general_observation=
                data.get(
                    "general_observation"
                )
                or None,
        )

        case = (
            container
            .create_clinical_case
            .execute(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Caso clínico registrado "
                        "correctamente."
                    ),

                "data":
                    ClinicalCasePresenter
                    .detail(
                        case
                    ),
            },
            status=201,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# LISTADO GENERAL
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_list_view(
    request: Request,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        search = (
            request.query_params.get(
                "search"
            )
            or None
        )

        status_code = (
            request.query_params.get(
                "status_code"
            )
            or None
        )

        priority_code = (
            request.query_params.get(
                "priority_code"
            )
            or None
        )

        patient_id_raw = (
            request.query_params.get(
                "patient_id"
            )
        )

        oncologist_raw = (
            request.query_params.get(
                "responsible_oncologist_uuid"
            )
        )

        opening_date_raw = (
            request.query_params.get(
                "opening_date"
            )
        )

        page = int(
            request.query_params.get(
                "page",
                1,
            )
        )

        page_size = int(
            request.query_params.get(
                "page_size",
                10,
            )
        )

        patient_id = (
            UUID(patient_id_raw)
            if patient_id_raw
            else None
        )

        oncologist_id = (
            UUID(oncologist_raw)
            if oncologist_raw
            else None
        )

        oncologist_id = (
            ClinicalCaseAccess
            .resolve_list_oncologist_filter(
                actor,
                oncologist_id,
            )
        )

        opening_date = (
            date.fromisoformat(
                opening_date_raw
            )
            if opening_date_raw
            else None
        )

        filters = ClinicalCaseFiltersDTO(
            search=search,
            status_code=status_code,
            priority_code=priority_code,
            patient_id=patient_id,
            responsible_oncologist_uuid=
                oncologist_id,
            opening_date=opening_date,
            page=page,
            page_size=page_size,
        )

        result = (
            container
            .list_clinical_cases
            .execute(
                filters
            )
        )

        return Response(
            ClinicalCasePresenter
            .paginated(
                cases=
                    result["cases"],

                pagination=
                    result["pagination"],
            ),
            status=200,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# DETALLE DEL CASO
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_detail_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        return Response(
            {
                "data":
                    ClinicalCasePresenter
                    .detail(
                        case
                    )
            },
            status=200,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# CATALOGOS
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_catalogs_view(
    request: Request,
):

    del request

    container = get_container()

    return Response(
        {
            "data":
                container
                .get_clinical_case_catalogs
                .execute()
        },
        status=200,
    )


# ==========================================================
# HISTORIAL DE ESTADOS
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_status_history_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        history = (
            container
            .get_clinical_case_status_history
            .execute(
                case_id
            )
        )

        return Response(
            {
                "data":
                    history,

                "total":
                    len(
                        history
                    ),
            },
            status=200,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# AVANZAR ESTADO
# ==========================================================

@api_view(
    [
        "PATCH",
    ]
)
def clinical_case_advance_status_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        serializer = (
            AdvanceClinicalCaseStatusSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        actor_uuid = (
            actor.usuario_uuid
        )

        dto = (
            AdvanceClinicalCaseStatusDTO(
                case_id=
                    case_id,

                observation=
                    (
                        data.get(
                            "observation"
                        )
                        or None
                    ),
            )
        )

        case = (
            container
            .advance_clinical_case_status
            .execute(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Estado del caso clínico "
                        "actualizado correctamente."
                    ),

                "data":
                    ClinicalCasePresenter
                    .detail(
                        case
                    ),
            },
            status=200,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# ANTECEDENTES
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def clinical_case_antecedents_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        if request.method == "GET":

            items = (
                container
                .clinical_case_information
                .list_antecedents(
                    case_id
                )
            )

            return Response(
                {
                    "data":
                        items,

                    "total":
                        len(
                            items
                        ),
                },
                status=200,
            )

        serializer = (
            CreateClinicalAntecedentSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor_uuid = (
            actor.usuario_uuid
        )

        dto = (
            CreateClinicalAntecedentDTO(
                case_id=
                    case_id,

                antecedent_type_id=
                    data[
                        "antecedent_type_id"
                    ],

                description=
                    data[
                        "description"
                    ],
            )
        )

        item = (
            container
            .clinical_case_information
            .create_antecedent(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Antecedente registrado "
                        "correctamente."
                    ),

                "data":
                    item,
            },
            status=201,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# SINTOMAS
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def clinical_case_symptoms_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        if request.method == "GET":

            items = (
                container
                .clinical_case_information
                .list_symptoms(
                    case_id
                )
            )

            return Response(
                {
                    "data":
                        items,

                    "total":
                        len(
                            items
                        ),
                },
                status=200,
            )

        serializer = (
            CreateClinicalSymptomSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor_uuid = (
            actor.usuario_uuid
        )

        dto = (
            CreateClinicalSymptomDTO(
                case_id=
                    case_id,

                symptom_id=
                    data[
                        "symptom_id"
                    ],

                intensity_id=
                    data.get(
                        "intensity_id"
                    ),

                start_date=
                    data.get(
                        "start_date"
                    ),

                observation=
                    (
                        data.get(
                            "observation"
                        )
                        or None
                    ),
            )
        )

        item = (
            container
            .clinical_case_information
            .create_symptom(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Síntoma registrado "
                        "correctamente."
                    ),

                "data":
                    item,
            },
            status=201,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# SIGNOS
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def clinical_case_signs_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        if request.method == "GET":

            items = (
                container
                .clinical_case_information
                .list_signs(
                    case_id
                )
            )

            return Response(
                {
                    "data":
                        items,

                    "total":
                        len(
                            items
                        ),
                },
                status=200,
            )

        serializer = (
            CreateClinicalSignSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor_uuid = (
            actor.usuario_uuid
        )

        dto = (
            CreateClinicalSignDTO(
                case_id=
                    case_id,

                sign_id=
                    data[
                        "sign_id"
                    ],

                finding_description=
                    (
                        data.get(
                            "finding_description"
                        )
                        or None
                    ),
            )
        )

        item = (
            container
            .clinical_case_information
            .create_sign(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Signo registrado "
                        "correctamente."
                    ),

                "data":
                    item,
            },
            status=201,
        )

    except Exception as error:

        return _error_response(
            error
        )


# ==========================================================
# OBSERVACIONES
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def clinical_case_observations_view(
    request: Request,
    case_id: UUID,
):

    container = get_container()

    try:

        actor = _get_actor(
            request
        )

        case = (
            container
            .get_clinical_case
            .execute(
                case_id
            )
        )

        ClinicalCaseAccess.assert_case_access(
            actor,
            case,
        )

        if request.method == "GET":

            items = (
                container
                .clinical_case_information
                .list_observations(
                    case_id
                )
            )

            return Response(
                {
                    "data":
                        items,

                    "total":
                        len(
                            items
                        ),
                },
                status=200,
            )

        serializer = (
            CreateClinicalObservationSerializer(
                data=request.data
            )
        )

        serializer.is_valid(
            raise_exception=True
        )

        data = serializer.validated_data

        actor_uuid = (
            actor.usuario_uuid
        )

        dto = (
            CreateClinicalObservationDTO(
                case_id=
                    case_id,

                content=
                    data[
                        "content"
                    ],
            )
        )

        item = (
            container
            .clinical_case_information
            .create_observation(
                dto,
                actor_uuid=
                    actor_uuid,
            )
        )

        return Response(
            {
                "message":
                    (
                        "Observación registrada "
                        "correctamente."
                    ),

                "data":
                    item,
            },
            status=201,
        )

    except Exception as error:

        return _error_response(
            error
        )