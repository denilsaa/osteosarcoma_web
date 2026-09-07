from uuid import UUID

from rest_framework.decorators import (
    api_view,
)
from rest_framework.request import (
    Request,
)
from rest_framework.response import (
    Response,
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


@api_view(
    [
        "GET",
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


    except Exception as error:

        response = (
            domain_error_response(
                error
            )
        )


        if response is not None:

            return response


        raise