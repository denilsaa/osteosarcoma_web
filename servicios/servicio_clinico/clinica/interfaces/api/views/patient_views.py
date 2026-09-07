from uuid import UUID

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from clinica.application.dto import (
    CreatePatientDTO,
    PatientFiltersDTO,
    PossibleDuplicateDTO,
    UpdatePatientDTO,
)
from clinica.bootstrap.container import get_container
from clinica.infrastructure.security import (
    RequestActorExtractor,
)
from clinica.interfaces.api.error_handler import (
    domain_error_response,
)
from clinica.interfaces.api.presenters import (
    PatientPresenter,
)
from clinica.interfaces.api.serializers import (
    CreatePatientRequestSerializer,
    PatientListQuerySerializer,
    PossibleDuplicateQuerySerializer,
    UpdatePatientRequestSerializer,
)


# ==========================================================
# UTILIDADES HTTP
# ==========================================================


def _query_params_to_dict(
    request,
) -> dict:
    """
    Convierte QueryDict a dict normal.

    Permite conservar correctamente los tres estados
    de filtros booleanos opcionales:

    active=true  -> True
    active=false -> False
    ausente      -> None
    """

    return {
        key: value
        for key, value
        in request.query_params.items()
    }


# ==========================================================
# CATÁLOGOS
# ==========================================================


@api_view(["GET"])
def patient_catalogs_view(
    request,
):
    container = get_container()

    result = (
        container
        .get_patient_catalogs
        .execute()
    )

    return Response(
        {
            "data": result,
        }
    )


# ==========================================================
# LISTADO / BÚSQUEDA / FILTROS / PAGINACIÓN
# ==========================================================


@api_view(["GET"])
def patient_list_view(
    request,
):
    query_data = (
        _query_params_to_dict(
            request
        )
    )

    serializer = (
        PatientListQuerySerializer(
            data=query_data,
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    data = serializer.validated_data

    dto = PatientFiltersDTO(
        search=data.get(
            "search"
        ),

        sex_code=data.get(
            "sex_code"
        ),

        active=data.get(
            "active"
        ),

        document_type_code=data.get(
            "document_type_code"
        ),

        page=data.get(
            "page",
            1,
        ),

        page_size=data.get(
            "page_size",
            10,
        ),
    )

    container = get_container()

    result = (
        container
        .list_patients
        .execute(dto)
    )

    return Response(
        {
            "data": [
                PatientPresenter.summary(
                    patient
                )
                for patient
                in result[
                    "patients"
                ]
            ],

            "pagination": {
                "page":
                    result["page"],

                "page_size":
                    result[
                        "page_size"
                    ],

                "total":
                    result["total"],

                "total_pages":
                    result[
                        "total_pages"
                    ],
            },
        }
    )


# ==========================================================
# REGISTRAR PACIENTE
# ==========================================================


@api_view(["POST"])
def patient_create_view(
    request,
):
    serializer = (
        CreatePatientRequestSerializer(
            data=request.data
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    data = serializer.validated_data

    dto = CreatePatientDTO(
        first_names=
            data["first_names"],

        paternal_surname=
            data[
                "paternal_surname"
            ],

        maternal_surname=
            data.get(
                "maternal_surname"
            ),

        birth_date=
            data["birth_date"],

        sex_id=
            data["sex_id"],

        document_type_id=
            data[
                "document_type_id"
            ],

        document_number=
            data[
                "document_number"
            ],

        complement=
            data.get(
                "complement"
            ),

        issued_in=
            data.get(
                "issued_in"
            ),

        contact_type_id=
            data.get(
                "contact_type_id"
            ),

        contact_value=
            data.get(
                "contact_value"
            ),
    )

    container = get_container()

    try:
        # ==================================================
        # 1. EJECUTAR CASO DE USO
        # ==================================================

        patient = (
            container
            .create_patient
            .execute(dto)
        )

        # ==================================================
        # 2. OBTENER ACTOR DEL REQUEST
        # ==================================================

        actor = (
            RequestActorExtractor
            .extract(
                request
            )
        )

        # ==================================================
        # 3. PUBLICAR EVENTO
        #
        # Clínico NO almacena auditoría.
        # Únicamente informa lo ocurrido.
        # ==================================================

        audit_published = (
            container
            .audit_service
            .patient_created(
                patient=patient,
                actor=actor,
            )
        )

        if not audit_published:
            print(
                "[CLINICO][EVENTOS] "
                "Paciente registrado, "
                "pero no fue posible "
                "publicar el evento."
            )

    except Exception as exc:
        return domain_error_response(
            exc
        )

    return Response(
        {
            "message":
                (
                    "Paciente registrado "
                    "correctamente."
                ),

            "data":
                PatientPresenter.detail(
                    patient
                ),
        },
        status=
            status.HTTP_201_CREATED,
    )


# ==========================================================
# DETALLE DEL PACIENTE
# ==========================================================


@api_view(["GET"])
def patient_detail_view(
    request,
    patient_id,
):
    try:
        patient = (
            get_container()
            .get_patient
            .execute(
                UUID(
                    str(
                        patient_id
                    )
                )
            )
        )

    except Exception as exc:
        return domain_error_response(
            exc
        )

    return Response(
        {
            "data":
                PatientPresenter.detail(
                    patient
                ),
        }
    )


# ==========================================================
# EDITAR PACIENTE
# ==========================================================


@api_view(["PATCH"])
def patient_update_view(
    request,
    patient_id,
):
    serializer = (
        UpdatePatientRequestSerializer(
            data=request.data
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    data = serializer.validated_data

    dto = UpdatePatientDTO(
        patient_id=UUID(
            str(
                patient_id
            )
        ),

        reason=
            data["reason"],

        first_names=
            data.get(
                "first_names"
            ),

        paternal_surname=
            data.get(
                "paternal_surname"
            ),

        maternal_surname=
            data.get(
                "maternal_surname"
            ),

        birth_date=
            data.get(
                "birth_date"
            ),

        sex_id=
            data.get(
                "sex_id"
            ),

        active=
            data.get(
                "active"
            ),
    )

    container = get_container()

    try:
        # ==================================================
        # 1. EJECUTAR CASO DE USO
        #
        # Este devuelve:
        # - paciente actualizado
        # - motivo
        # - anterior/nuevo
        # ==================================================

        result = (
            container
            .update_patient
            .execute(dto)
        )

        # ==================================================
        # 2. OBTENER ACTOR
        # ==================================================

        actor = (
            RequestActorExtractor
            .extract(
                request
            )
        )

        # ==================================================
        # 3. PUBLICAR EVENTO
        # ==================================================

        audit_published = (
            container
            .audit_service
            .patient_updated(
                patient=
                    result[
                        "patient"
                    ],

                actor=
                    actor,

                reason=
                    result[
                        "reason"
                    ],

                changes=
                    result[
                        "changes"
                    ],
            )
        )

        if not audit_published:
            print(
                "[CLINICO][EVENTOS] "
                "Paciente actualizado, "
                "pero no fue posible "
                "publicar el evento."
            )

    except Exception as exc:
        return domain_error_response(
            exc
        )

    return Response(
        {
            "message":
                (
                    "Paciente actualizado "
                    "correctamente."
                ),

            "data":
                PatientPresenter.detail(
                    result[
                        "patient"
                    ]
                ),

            "changes": [
                {
                    "field":
                        change.field,

                    "old_value":
                        change.old_value,

                    "new_value":
                        change.new_value,
                }
                for change
                in result[
                    "changes"
                ]
            ],

            "reason":
                result[
                    "reason"
                ],
        }
    )


# ==========================================================
# POSIBLES DUPLICADOS
# ==========================================================


@api_view(["GET"])
def patient_duplicates_view(
    request,
):
    query_data = (
        _query_params_to_dict(
            request
        )
    )

    serializer = (
        PossibleDuplicateQuerySerializer(
            data=query_data
        )
    )

    serializer.is_valid(
        raise_exception=True
    )

    data = serializer.validated_data

    dto = PossibleDuplicateDTO(
        document_type_id=
            data.get(
                "document_type_id"
            ),

        document_number=
            data.get(
                "document_number"
            ),

        first_names=
            data.get(
                "first_names"
            ),

        paternal_surname=
            data.get(
                "paternal_surname"
            ),

        maternal_surname=
            data.get(
                "maternal_surname"
            ),

        birth_date=
            data.get(
                "birth_date"
            ),
    )

    try:
        patients = (
            get_container()
            .find_patient_duplicates
            .execute(dto)
        )

    except Exception as exc:
        return domain_error_response(
            exc
        )

    return Response(
        {
            "data": [
                PatientPresenter.summary(
                    patient
                )
                for patient
                in patients
            ],

            "meta": {
                "has_possible_duplicates":
                    len(
                        patients
                    ) > 0,

                "total":
                    len(
                        patients
                    ),
            },
        }
    )