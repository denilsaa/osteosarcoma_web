import hashlib
import json

from uuid import (
    UUID,
)

from rest_framework import (
    status,
)

from rest_framework.decorators import (
    api_view,
)

from rest_framework.response import (
    Response,
)


from clinica.application.dto import (
    CreateEmergencyContactDTO,
    CreatePatientContactDTO,
    CreatePatientDTO,
    PatientFiltersDTO,
    PossibleDuplicateDTO,
    UpdatePatientDTO,
)

from clinica.bootstrap.container import (
    get_container,
)

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


from django.db import transaction, connection
from clinica.infrastructure.persistence.models import AsignacionPaciente, CasoClinico, AltaPacienteOffline
from clinica.infrastructure.security.patient_access import PatientAccess
from clinica.infrastructure.security.clinical_case_access import ClinicalCaseAccess


def _authenticate_patient_request(request):
    try:
        return PatientAccess.actor(request), None
    except Exception as exc:
        response = domain_error_response(exc)
        if response is not None:
            return None, response
        raise


def _check_patient_permission(actor, patient_id):
    try:
        PatientAccess.require(actor, patient_id)
        return None
    except Exception as exc:
        response = domain_error_response(exc)
        if response is not None:
            return response
        raise


def _present_detail_for_actor(patient, actor):
    result = PatientPresenter.detail(patient)
    if not ClinicalCaseAccess.is_head(actor):
        result["clinical_cases_count"] = CasoClinico.objects.filter(
            paciente_id=patient.id_patient,
            oncologo_responsable_uuid=actor.usuario_uuid,
        ).count()
    return result


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


@api_view(
    [
        "GET",
    ]
)
def patient_catalogs_view(
    request,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error


    container = (
        get_container()
    )


    result = (
        container
        .get_patient_catalogs
        .execute()
    )


    return Response(
        {
            "data":
                result,
        },
        status=
            status.HTTP_200_OK,
    )


# ==========================================================
# LISTADO / BÚSQUEDA / FILTROS / PAGINACIÓN
# ==========================================================


@api_view(
    [
        "GET",
    ]
)
def patient_list_view(
    request,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    query_data = (
        _query_params_to_dict(
            request
        )
    )


    serializer = (
        PatientListQuerySerializer(
            data=
                query_data,
        )
    )


    serializer.is_valid(
        raise_exception=True
    )


    data = (
        serializer
        .validated_data
    )


    dto = (
        PatientFiltersDTO(
            search=
                data.get(
                    "search"
                ),

            sex_code=
                data.get(
                    "sex_code"
                ),

            active=
                data.get(
                    "active"
                ),

            document_type_code=
                data.get(
                    "document_type_code"
                ),

            page=
                data.get(
                    "page",
                    1,
                ),

            page_size=
                data.get(
                    "page_size",
                    10,
                ),
        )
    )


    container = (
        get_container()
    )


    result = (
        container
        .list_patients
        .execute(
            dto,
            authorized_oncologist_uuid=(
                None if ClinicalCaseAccess.is_head(actor) else actor.usuario_uuid
            ),
        )
    )


    return Response(
        {
            "data": [
                PatientPresenter
                .summary(
                    patient
                )

                for patient
                in result[
                    "patients"
                ]
            ],

            "pagination": {
                "page":
                    result[
                        "page"
                    ],

                "page_size":
                    result[
                        "page_size"
                    ],

                "total":
                    result[
                        "total"
                    ],

                "total_pages":
                    result[
                        "total_pages"
                    ],
            },
        },
        status=
            status.HTTP_200_OK,
    )


# ==========================================================
# REGISTRAR PACIENTE
# ==========================================================


@api_view(
    [
        "POST",
    ]
)
def patient_create_view(
    request,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    # ======================================================
    # VALIDAR REQUEST
    # ======================================================

    serializer = (
        CreatePatientRequestSerializer(
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


    # ======================================================
    # CONSTRUIR DTO
    # ======================================================

    dto = (
        CreatePatientDTO(
            first_names=
                data[
                    "first_names"
                ],

            paternal_surname=
                data[
                    "paternal_surname"
                ],

            maternal_surname=
                data.get(
                    "maternal_surname"
                ),

            birth_date=
                data[
                    "birth_date"
                ],

            sex_id=
                data[
                    "sex_id"
                ],

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

            contacts=[
                CreatePatientContactDTO(
                    contact_type_id=
                        item[
                            "contact_type_id"
                        ],

                    value=
                        item[
                            "value"
                        ],

                    primary=
                        item.get(
                            "primary",
                            False,
                        ),
                )

                for item
                in data.get(
                    "contacts",
                    [],
                )
            ],

            emergency_contacts=[
                CreateEmergencyContactDTO(
                    full_name=
                        item[
                            "full_name"
                        ],

                    relationship=
                        item[
                            "relationship"
                        ],

                    phone=
                        item[
                            "phone"
                        ],

                    email=
                        item.get(
                            "email"
                        ),

                    primary=
                        item.get(
                            "primary",
                            False,
                        ),
                )

                for item
                in data.get(
                    "emergency_contacts",
                    [],
                )
            ],
        )
    )


    container = (
        get_container()
    )

    # Una operación diferida puede reintentarse tras un timeout, incluso si el
    # primer POST sí llegó a crear al paciente. El UUID permite respuesta estable.
    op_raw = request.headers.get("X-Osteo-Operation-Id", "").strip()
    op_uuid = None
    payload_hash = ""
    if op_raw:
        try:
            op_uuid = UUID(op_raw)
            if str(op_uuid) != op_raw.lower():
                raise ValueError("UUID no canónico")
        except (ValueError, AttributeError):
            return Response({"detail": "Identificador de operación inválido."}, status=400)
        payload_hash = hashlib.sha256(json.dumps(
            request.data, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        ).encode("utf-8")).hexdigest()

    try:

        # ==================================================
        # 1. CREAR PACIENTE
        # ==================================================

        with transaction.atomic():
            # Bloqueo de reintentos concurrentes sobre la misma operación:
            # la primera solicitud confirma conjuntamente paciente y recibo.
            previo = None
            if op_uuid is not None:
                # Exclusión transaccional por UUID (PostgreSQL) contra dos POST
                # simultáneos: el segundo espera al primero antes de consultar.
                advisory_key = op_uuid.int % (2 ** 63)
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_xact_lock(%s)", [advisory_key])
                previo = AltaPacienteOffline.objects.select_for_update().filter(
                    operacion_uuid=op_uuid,
                ).first()
                if previo is not None:
                    if (str(previo.actor_uuid) != str(actor.usuario_uuid)
                            or previo.payload_sha256 != payload_hash):
                        return Response({"detail": "Identificador de operación reutilizado."}, status=409)
                    patient = container.get_patient.execute(previo.paciente_id)
                    return Response({
                        "message": "Paciente registrado previamente; reintento reconocido.",
                        "data": _present_detail_for_actor(patient, actor),
                    }, status=status.HTTP_200_OK)

            patient = container.create_patient.execute(dto)
            if not ClinicalCaseAccess.is_head(actor):
                AsignacionPaciente.objects.create(
                    paciente_id=patient.id_patient,
                    oncologo_uuid=actor.usuario_uuid,
                    asignado_por_uuid=actor.usuario_uuid,
                    motivo="Registro del paciente por su oncólogo responsable.",
                )
            if op_uuid is not None:
                AltaPacienteOffline.objects.create(
                    operacion_uuid=op_uuid,
                    actor_uuid=actor.usuario_uuid,
                    payload_sha256=payload_hash,
                    paciente_id=patient.id_patient,
                )


        # ==================================================
        # 2. OBTENER ACTOR
        # ==================================================

        # Se conserva el actor previamente validado mediante JWT.


        # ==================================================
        # 3. PUBLICAR EVENTO DE AUDITORÍA
        # ==================================================

        audit_published = (
            container
            .audit_service
            .patient_created(
                patient=
                    patient,

                actor=
                    actor,
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

        response = (
            domain_error_response(
                exc
            )
        )


        if response is not None:

            return response


        raise


    # ======================================================
    # RESPUESTA
    # ======================================================

    return Response(
        {
            "message":
                (
                    "Paciente registrado "
                    "correctamente."
                ),

            "data":
                PatientPresenter
                .detail(
                    patient
                ),
        },
        status=
            status.HTTP_201_CREATED,
    )


# ==========================================================
# DETALLE DEL PACIENTE
# ==========================================================


@api_view(
    [
        "GET",
    ]
)
def patient_detail_view(
    request,
    patient_id,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    denied = _check_patient_permission(actor, patient_id)
    if denied is not None:
        return denied


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

        response = (
            domain_error_response(
                exc
            )
        )


        if response is not None:

            return response


        raise


    return Response(
        {
            "data":
                _present_detail_for_actor(patient, actor),
        },
        status=
            status.HTTP_200_OK,
    )


# ==========================================================
# EDITAR PACIENTE
# ==========================================================


@api_view(
    [
        "PATCH",
    ]
)
def patient_update_view(
    request,
    patient_id,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    denied = _check_patient_permission(actor, patient_id)
    if denied is not None:
        return denied

    # Solo jefatura desactiva pacientes, no el oncólogo normal.
    if not ClinicalCaseAccess.is_head(actor) and "active" in request.data:
        return Response({"error": "Solo jefatura puede cambiar el estado del paciente."}, status=403)

    # ======================================================
    # VALIDAR REQUEST
    # ======================================================

    serializer = (
        UpdatePatientRequestSerializer(
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


    # ======================================================
    # DTO
    # ======================================================

    dto = (
        UpdatePatientDTO(
            patient_id=
                UUID(
                    str(
                        patient_id
                    )
                ),

            reason=
                data[
                    "reason"
                ],

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
    )


    container = (
        get_container()
    )


    try:

        # ==================================================
        # 1. ACTUALIZAR
        # ==================================================

        result = (
            container
            .update_patient
            .execute(
                dto
            )
        )


        # ==================================================
        # 2. ACTOR
        # ==================================================

        # Se conserva el actor previamente validado mediante JWT.


        # ==================================================
        # 3. AUDITORÍA
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

        response = (
            domain_error_response(
                exc
            )
        )


        if response is not None:

            return response


        raise


    # ======================================================
    # RESPUESTA
    # ======================================================

    return Response(
        {
            "message":
                (
                    "Paciente actualizado "
                    "correctamente."
                ),

            "data":
                _present_detail_for_actor(result["patient"], actor),

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
        },
        status=
            status.HTTP_200_OK,
    )


# ==========================================================
# POSIBLES DUPLICADOS
# ==========================================================


@api_view(
    [
        "GET",
    ]
)
def patient_duplicates_view(
    request,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    query_data = (
        _query_params_to_dict(
            request
        )
    )


    serializer = (
        PossibleDuplicateQuerySerializer(
            data=
                query_data,
        )
    )


    serializer.is_valid(
        raise_exception=True
    )


    data = (
        serializer
        .validated_data
    )


    dto = (
        PossibleDuplicateDTO(
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
    )


    try:

        patients = (
            get_container()
            .find_patient_duplicates
            .execute(
                dto
            )
        )


    except Exception as exc:

        response = (
            domain_error_response(
                exc
            )
        )


        if response is not None:

            return response


        raise


    patients = [patient for patient in patients if PatientAccess.can_access(actor, patient.id_patient)]

    return Response(
        {
            "data": [
                PatientPresenter
                .summary(
                    patient
                )

                for patient
                in patients
            ],

            "meta": {
                "has_possible_duplicates":
                    (
                        len(
                            patients
                        )
                        >
                        0
                    ),

                "total":
                    len(
                        patients
                    ),
            },
        },
        status=
            status.HTTP_200_OK,
    )


# ==========================================================
# FOTO DEL PACIENTE
# ==========================================================


@api_view(
    [
        "POST",
        "DELETE",
    ]
)
def patient_photo_view(
    request,
    patient_id,
):

    actor, auth_error = _authenticate_patient_request(request)
    if auth_error is not None:
        return auth_error

    container = (
        get_container()
    )


    try:

        patient_uuid = (
            UUID(
                str(
                    patient_id
                )
            )
        )


        denied = _check_patient_permission(actor, patient_uuid)
        if denied is not None:
            return denied

        # ==================================================
        # SUBIR / REEMPLAZAR FOTO
        # ==================================================

        if (
            request.method
            ==
            "POST"
        ):

            uploaded_file = (
                request
                .FILES
                .get(
                    "foto"
                )
            )


            if uploaded_file is None:

                return Response(
                    {
                        "error":
                            "Seleccione una imagen."
                    },
                    status=
                        status.HTTP_400_BAD_REQUEST,
                )


            patient = (
                container
                .update_patient_photo
                .execute(
                    patient_id=
                        patient_uuid,

                    uploaded_file=
                        uploaded_file,
                )
            )


            photo_url = (
                request
                .build_absolute_uri(
                    patient
                    .foto
                    .url
                )
                if patient.foto
                else None
            )


            return Response(
                {
                    "message":
                        (
                            "Foto del paciente "
                            "actualizada correctamente."
                        ),

                    "photo_url":
                        photo_url,
                },
                status=
                    status.HTTP_200_OK,
            )


        # ==================================================
        # ELIMINAR FOTO
        # ==================================================

        (
            container
            .delete_patient_photo
            .execute(
                patient_id=
                    patient_uuid,
            )
        )


        return Response(
            {
                "message":
                    (
                        "Foto del paciente "
                        "eliminada correctamente."
                    ),

                "photo_url":
                    None,
            },
            status=
                status.HTTP_200_OK,
        )


    except ValueError as exc:

        return Response(
            {
                "error":
                    str(
                        exc
                    )
            },
            status=
                status.HTTP_400_BAD_REQUEST,
        )


    except Exception as exc:

        response = (
            domain_error_response(
                exc
            )
        )


        if response is not None:

            return response


        raise