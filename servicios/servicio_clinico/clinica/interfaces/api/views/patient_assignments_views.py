"""Administración explícita de asignaciones, exclusiva de JEFE_ONCOLOGIA."""
from uuid import UUID
from django.db import transaction, IntegrityError
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from clinica.infrastructure.security.patient_access import PatientAccess
from clinica.infrastructure.persistence.models import Paciente, AsignacionPaciente, CasoClinico
from clinica.infrastructure.security import ClinicalAuthenticationError, ClinicalAuthorizationError
from clinica.interfaces.api.error_handler import domain_error_response
from .clinical_case_management_views import _validate_active_oncologist


class AsignarPacienteSerializer(serializers.Serializer):
    oncologo_uuid = serializers.UUIDField()
    motivo = serializers.CharField(min_length=10, max_length=500, trim_whitespace=True)


class RevocarPacienteSerializer(serializers.Serializer):
    motivo = serializers.CharField(min_length=10, max_length=500, trim_whitespace=True)


def _response_error(exc):
    if isinstance(exc, serializers.ValidationError):
        return Response({"error": exc.detail}, status=400)
    if isinstance(exc, (ClinicalAuthenticationError, ClinicalAuthorizationError, ValueError, IntegrityError)):
        return domain_error_response(exc)
    raise exc


def _serialize(item):
    return {
        "id_asignacion": str(item.id_asignacion),
        "oncologo_uuid": str(item.oncologo_uuid),
        "activa": item.activa,
        "motivo": item.motivo,
        "fecha_asignacion": item.fecha_asignacion,
        "fecha_revocacion": item.fecha_revocacion,
        "motivo_revocacion": item.motivo_revocacion,
    }


@api_view(["GET", "POST"])
def patient_assignments_view(request, patient_id: UUID):
    try:
        actor = PatientAccess.actor(request)
        PatientAccess.require_head(actor)
        if not Paciente.objects.filter(id_paciente=patient_id).exists():
            return Response({"error": "Paciente no encontrado."}, status=404)
        if request.method == "GET":
            history = AsignacionPaciente.objects.filter(paciente_id=patient_id).order_by("-fecha_asignacion")
            return Response({"data": [_serialize(item) for item in history]})

        payload = AsignarPacienteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        doctor_id = payload.validated_data["oncologo_uuid"]
        reason = payload.validated_data["motivo"]
        _validate_active_oncologist(request, doctor_id)
        with transaction.atomic():
            if AsignacionPaciente.objects.select_for_update().filter(
                paciente_id=patient_id, oncologo_uuid=doctor_id, activa=True,
            ).exists():
                return Response({"error": "El oncólogo ya está asignado al paciente."}, status=409)
            assignment = AsignacionPaciente.objects.create(
                paciente_id=patient_id, oncologo_uuid=doctor_id,
                asignado_por_uuid=actor.usuario_uuid, motivo=reason,
            )
        return Response({"message": "Paciente asignado correctamente.", "data": _serialize(assignment)}, status=201)
    except ConnectionError:
        return Response({"error": "No fue posible verificar al oncólogo en el servicio de usuarios."}, status=503)
    except Exception as exc:
        return _response_error(exc)


@api_view(["POST"])
def patient_assignment_revoke_view(request, patient_id: UUID, oncologist_id: UUID):
    try:
        actor = PatientAccess.actor(request)
        PatientAccess.require_head(actor)
        payload = RevocarPacienteSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        if CasoClinico.objects.filter(
            paciente_id=patient_id, oncologo_responsable_uuid=oncologist_id,
        ).exclude(estado_caso__codigo="CERRADO").exists():
            return Response({"error": "Primero reasigne los casos clínicos abiertos de este profesional."}, status=409)
        with transaction.atomic():
            active = list(AsignacionPaciente.objects.select_for_update().filter(
                paciente_id=patient_id, oncologo_uuid=oncologist_id, activa=True,
            ))
            if not active:
                return Response({"error": "No existe una asignación activa."}, status=404)
            for item in active:
                item.activa = False
                item.fecha_revocacion = timezone.now()
                item.revocado_por_uuid = actor.usuario_uuid
                item.motivo_revocacion = payload.validated_data["motivo"]
                item.save(update_fields=["activa", "fecha_revocacion", "revocado_por_uuid", "motivo_revocacion"])
        return Response({"message": "Asignación revocada. Se conserva el historial."})
    except Exception as exc:
        return _response_error(exc)
