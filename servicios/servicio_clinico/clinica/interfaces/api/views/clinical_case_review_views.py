"""API de valoraciones clínicas; accesible solo con JWT y permisos por caso."""
import logging
from uuid import UUID
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.decorators import api_view
from rest_framework.response import Response
from clinica.application.dto import AuditEventDTO
from clinica.application.services.clinical_review_service import (
    list_valuations, register_valuation,
)
from clinica.bootstrap.container import get_container
from clinica.infrastructure.persistence.models import CriterioValoracion
from clinica.infrastructure.security import (
    ClinicalAuthenticationError, ClinicalAuthorizationError, ClinicalCaseAccess,
)
from clinica.interfaces.api.error_handler import domain_error_response

logger = logging.getLogger(__name__)


class RegisterValuationSerializer(serializers.Serializer):
    criterion_id = serializers.IntegerField(min_value=1)
    observation = serializers.CharField(min_length=15, max_length=4000, trim_whitespace=True)


def _error(exc):
    if isinstance(exc, ValidationError):
        return Response({"error": exc.detail}, status=400)
    if isinstance(exc, ClinicalAuthenticationError):
        return Response({"error": str(exc)}, status=401)
    if isinstance(exc, ClinicalAuthorizationError):
        return Response({"error": str(exc)}, status=403)
    if isinstance(exc, ValueError):
        return Response({"error": str(exc)}, status=400)
    try:
        response = domain_error_response(exc)
        if response is not None:
            return response
    except Exception:
        pass
    logger.error("Error en revisión clínica", exc_info=(type(exc), exc, exc.__traceback__))
    return Response({"error": "No fue posible procesar la valoración."}, status=500)


def _authorized_case(request, case_id: UUID):
    actor = ClinicalCaseAccess.get_actor(request)
    case = get_container().get_clinical_case.execute(case_id)
    ClinicalCaseAccess.assert_case_access(actor, case)
    return actor, case


def _audit_created(actor, case_id, valuation):
    try:
        ok = get_container().audit_event_publisher.publish(AuditEventDTO(
            service="CLINICO", module="VALORACIONES", action="CREAR",
            result="EXITOSO", entity_type="VALORACION_ESPECIALISTA",
            entity_id=valuation["id_valuation"], actor=actor,
            description="El médico responsable registró una valoración clínica.",
            detail={"case_id": str(case_id),
                    "criterion": valuation["criterion"]["code"]},
        ))
        if not ok:
            logger.warning("El evento de auditoría de valoración no se publicó")
    except Exception:
        logger.exception("No se pudo publicar auditoría de valoración clínica")


@api_view(["GET"])
def clinical_case_valuation_catalog_view(request):
    try:
        ClinicalCaseAccess.get_actor(request)
        queryset = CriterioValoracion.objects.all().order_by("id_criterio")
        return Response({"data": [
            {"id": x.id_criterio, "code": x.codigo,
             "name": x.nombre, "description": x.descripcion}
            for x in queryset
        ]})
    except Exception as exc:
        return _error(exc)


@api_view(["GET", "POST"])
def clinical_case_valuations_view(request, case_id: UUID):
    try:
        actor, _ = _authorized_case(request, case_id)
        if request.method == "GET":
            data = list_valuations(case_id)
            return Response({"data": data, "total": len(data)})
        serializer = RegisterValuationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = register_valuation(
            case_id=case_id, actor=actor,
            criterion_id=serializer.validated_data["criterion_id"],
            observation=serializer.validated_data["observation"],
        )
        transaction.on_commit(lambda: _audit_created(actor, case_id, result))
        return Response({"message": "Valoración clínica registrada.", "data": result}, status=201)
    except Exception as exc:
        return _error(exc)
