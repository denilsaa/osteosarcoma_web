
"""Endpoints de supervisión reservados a JEFE_ONCOLOGIA."""
import json
import logging
import urllib.error
import urllib.request
from uuid import UUID

from django.db import transaction
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from clinica.application.dto import AuditEventDTO
from clinica.application.services.clinical_case_management_service import (
    list_management_history, require_head, supervision_summary,
    update_case_management, validate_destination,
)
from clinica.bootstrap.container import get_container
from clinica.infrastructure.security import (
    ClinicalAuthenticationError, ClinicalAuthorizationError, ClinicalCaseAccess,
)
from clinica.interfaces.api.error_handler import domain_error_response
from clinica.interfaces.api.presenters.clinical_case_presenter import ClinicalCasePresenter

logger = logging.getLogger(__name__)


class ChangeManagementSerializer(serializers.Serializer):
    responsible_oncologist_uuid = serializers.UUIDField(required=False)
    priority_id = serializers.IntegerField(required=False, min_value=1)
    reason = serializers.CharField(min_length=10, max_length=1000, trim_whitespace=True)

    def validate(self, attrs):
        if "responsible_oncologist_uuid" not in attrs and "priority_id" not in attrs:
            raise serializers.ValidationError("Seleccione un responsable o una prioridad.")
        return attrs


def _error(exc):
    if isinstance(exc, serializers.ValidationError):
        return Response({"error": exc.detail}, status=400)
    if isinstance(exc, ClinicalAuthenticationError):
        return Response({"error": str(exc)}, status=401)
    if isinstance(exc, ClinicalAuthorizationError):
        return Response({"error": str(exc)}, status=403)
    if isinstance(exc, ValueError):
        return Response({"error": str(exc)}, status=400)
    response = domain_error_response(exc)
    if response is not None:
        return response
    logger.exception("Error en administración clínica")
    return Response({"error": "No fue posible gestionar el caso clínico."}, status=500)


def _validate_active_oncologist(request, oncologist_uuid):
    """Consulta autenticada al servicio de Usuarios dentro de la red Docker."""
    token = request.headers.get("Authorization", "")
    if not token.lower().startswith("bearer "):
        raise ClinicalAuthenticationError("Se requiere autorización válida.")
    # URL fija de microservicio, el usuario no controla el destino HTTP.
    url = f"http://servicio-usuarios:8000/api/oncologos/{oncologist_uuid}/"
    external_request = urllib.request.Request(
        url, headers={"Authorization": token, "Accept": "application/json"}, method="GET",
    )
    try:
        with urllib.request.urlopen(external_request, timeout=5) as response:
            info = json.load(response)
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            raise ValueError("El profesional seleccionado no existe.") from exc
        if exc.code in (401, 403):
            raise ClinicalAuthorizationError(
                "La cuenta no tiene permiso para verificar al profesional de destino."
            ) from exc
        raise ConnectionError("El servicio de usuarios no pudo validar la asignación.") from exc
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ConnectionError("El servicio de usuarios no está disponible.") from exc
    validate_destination(info, oncologist_uuid)


def _audit_management(actor, case_id, changed):
    try:
        get_container().audit_event_publisher.publish(AuditEventDTO(
            service="CLINICO", module="GESTION_CASOS", action="ACTUALIZAR",
            result="EXITOSO", entity_type="CASO_CLINICO", entity_id=str(case_id),
            actor=actor, description="Jefatura actualizó asignación o prioridad del caso.",
            detail={"changes": changed},
        ))
    except Exception:
        logger.exception("No se pudo publicar auditoría de gestión de caso")


@api_view(["GET"])
def clinical_case_supervision_view(request):
    try:
        actor = ClinicalCaseAccess.get_actor(request)
        require_head(actor)
        return Response({"data": supervision_summary()})
    except Exception as exc:
        return _error(exc)


@api_view(["GET", "PATCH"])
def clinical_case_management_view(request, case_id: UUID):
    try:
        actor = ClinicalCaseAccess.get_actor(request)
        require_head(actor)
        case = get_container().get_clinical_case.execute(case_id)
        ClinicalCaseAccess.assert_case_access(actor, case)
        if request.method == "GET":
            items = list_management_history(case_id)
            return Response({"data": items, "total": len(items)})
        serializer = ChangeManagementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if "responsible_oncologist_uuid" in data:
            _validate_active_oncologist(request, data["responsible_oncologist_uuid"])
        changed = update_case_management(
            case_id=case_id, actor=actor,
            new_doctor_uuid=data.get("responsible_oncologist_uuid"),
            new_priority_id=data.get("priority_id"), reason=data["reason"],
        )
        transaction.on_commit(lambda: _audit_management(actor, case_id, changed))
        updated = get_container().get_clinical_case.execute(case_id)
        return Response({
            "message": "La gestión del caso se actualizó correctamente.",
            "data": ClinicalCasePresenter.detail(updated), "changes": changed,
        })
    except ConnectionError as exc:
        return Response({"error": str(exc)}, status=503)
    except Exception as exc:
        return _error(exc)
