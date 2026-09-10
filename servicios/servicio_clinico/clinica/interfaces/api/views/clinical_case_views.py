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
    ClinicalCaseFiltersDTO,
    CreateClinicalCaseDTO,
)

from clinica.bootstrap.container import (
    get_container,
)

from clinica.interfaces.api.error_handler import (
    domain_error_response,
)

from clinica.interfaces.api.presenters.clinical_case_presenter import (
    ClinicalCasePresenter,
)

from clinica.interfaces.api.serializers.clinical_case_serializers import (
    CreateClinicalCaseSerializer,
)


# ==========================================================
# OBTENER UUID DEL ACTOR
# ==========================================================

def _actor_uuid(
    request:
        Request,
) -> UUID:

    # ------------------------------------------------------
    # 1. JWT / request.auth
    # ------------------------------------------------------

    auth = (
        request.auth
    )


    if auth:

        if isinstance(
            auth,
            dict,
        ):

            for key in (
                "id_usuario",
                "user_id",
                "sub",
            ):

                value = (
                    auth.get(
                        key,
                    )
                )


                if value:

                    return UUID(
                        str(
                            value,
                        )
                    )


        try:

            payload = (
                auth.payload
            )


            for key in (
                "id_usuario",
                "user_id",
                "sub",
            ):

                value = (
                    payload.get(
                        key,
                    )
                )


                if value:

                    return UUID(
                        str(
                            value,
                        )
                    )

        except (
            AttributeError,
            TypeError,
            ValueError,
        ):

            pass


    # ------------------------------------------------------
    # 2. request.user
    # ------------------------------------------------------

    user = (
        request.user
    )


    for attribute in (
        "id_usuario",
        "id",
        "pk",
    ):

        value = (
            getattr(
                user,
                attribute,
                None,
            )
        )


        if value:

            try:

                return UUID(
                    str(
                        value,
                    )
                )

            except ValueError:

                pass


    raise ValueError(
        "No fue posible identificar al usuario autenticado."
    )


# ==========================================================
# CASOS DEL PACIENTE
# GET + POST
# ==========================================================

@api_view(
    [
        "GET",
        "POST",
    ]
)
def patient_cases_view(
    request:
        Request,

    patient_id:
        UUID,
):

    container = (
        get_container()
    )


    try:

        # ==================================================
        # GET
        # ==================================================

        if (
            request.method
            ==
            "GET"
        ):

            cases = (
                container
                .list_patient_cases
                .execute(
                    patient_id
                )
            )


            return Response(
                ClinicalCasePresenter
                .list(
                    cases
                ),
                status=200,
            )


        # ==================================================
        # POST
        # ==================================================

        serializer = (
            CreateClinicalCaseSerializer(
                data=
                    request.data,
            )
        )


        serializer.is_valid(
            raise_exception=True
        )


        data = (
            serializer
            .validated_data
        )


        actor_uuid = (
            _actor_uuid(
                request,
            )
        )


        responsible_uuid = (
            data.get(
                "responsible_oncologist_uuid",
            )
            or
            actor_uuid
        )


        dto = (
            CreateClinicalCaseDTO(
                patient_id=
                    patient_id,

                priority_id=
                    data[
                        "priority_id"
                    ],

                responsible_oncologist_uuid=
                    responsible_uuid,

                consultation_reason=
                    data[
                        "consultation_reason"
                    ],

                general_observation=
                    data.get(
                        "general_observation"
                    )
                    or
                    None,
            )
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
                    "Caso clínico registrado correctamente.",

                "data":
                    ClinicalCasePresenter
                    .detail(
                        case
                    ),
            },
            status=201,
        )


    except Exception as error:

        response = (
            domain_error_response(
                error
            )
        )


        if response is not None:

            return response


        if isinstance(
            error,
            ValueError,
        ):

            return Response(
                {
                    "error":
                        str(
                            error
                        )
                },
                status=400,
            )


        raise


# ==========================================================
# LISTADO GENERAL
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_list_view(
    request:
        Request,
):

    container = (
        get_container()
    )


    try:

        search = (
            request
            .query_params
            .get(
                "search",
            )
            or
            None
        )


        status_code = (
            request
            .query_params
            .get(
                "status_code",
            )
            or
            None
        )


        priority_code = (
            request
            .query_params
            .get(
                "priority_code",
            )
            or
            None
        )


        patient_id_raw = (
            request
            .query_params
            .get(
                "patient_id",
            )
        )


        oncologist_raw = (
            request
            .query_params
            .get(
                "responsible_oncologist_uuid",
            )
        )


        opening_date_raw = (
            request
            .query_params
            .get(
                "opening_date",
            )
        )


        page = int(
            request
            .query_params
            .get(
                "page",
                1,
            )
        )


        page_size = int(
            request
            .query_params
            .get(
                "page_size",
                10,
            )
        )


        patient_id = (
            UUID(
                patient_id_raw
            )
            if patient_id_raw
            else None
        )


        oncologist_id = (
            UUID(
                oncologist_raw
            )
            if oncologist_raw
            else None
        )


        opening_date = (
            date.fromisoformat(
                opening_date_raw
            )
            if opening_date_raw
            else None
        )


        filters = (
            ClinicalCaseFiltersDTO(
                search=
                    search,

                status_code=
                    status_code,

                priority_code=
                    priority_code,

                patient_id=
                    patient_id,

                responsible_oncologist_uuid=
                    oncologist_id,

                opening_date=
                    opening_date,

                page=
                    page,

                page_size=
                    page_size,
            )
        )


        result = (
            container
            .list_clinical_cases
            .execute(
                filters,
            )
        )


        return Response(
            ClinicalCasePresenter
            .paginated(
                cases=
                    result[
                        "cases"
                    ],

                pagination=
                    result[
                        "pagination"
                    ],
            ),
            status=200,
        )


    except (
        ValueError,
        TypeError,
    ) as error:

        return Response(
            {
                "error":
                    str(
                        error
                    )
            },
            status=400,
        )


# ==========================================================
# DETALLE
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_detail_view(
    request:
        Request,

    case_id:
        UUID,
):

    container = (
        get_container()
    )


    try:

        case = (
            container
            .get_clinical_case
            .execute(
                case_id,
            )
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


    except ValueError as error:

        return Response(
            {
                "error":
                    str(
                        error
                    )
            },
            status=404,
        )


# ==========================================================
# CATÁLOGOS
# ==========================================================

@api_view(
    [
        "GET",
    ]
)
def clinical_case_catalogs_view(
    request:
        Request,
):

    container = (
        get_container()
    )


    return Response(
        {
            "data":
                container
                .get_clinical_case_catalogs
                .execute()
        },
        status=200,
    )