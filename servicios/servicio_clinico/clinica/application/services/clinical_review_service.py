"""Reglas de valoración profesional; no interpretan automáticamente las imágenes."""
from django.db import transaction
from clinica.infrastructure.persistence.models import (
    CasoClinico, CriterioValoracion, HistorialGestionCaso, ValoracionEspecialista,
)
from clinica.infrastructure.security import ClinicalAuthorizationError, ClinicalCaseAccess

ALLOWED_STATES = frozenset({"EN_ANALISIS", "REVISADO"})


def require_reviewer(actor, case):
    """Una valoración solo puede ser firmada por el médico asignado."""
    if (case.oncologo_responsable_uuid is None or
            case.oncologo_responsable_uuid != actor.usuario_uuid):
        raise ClinicalAuthorizationError(
            "Solo el oncólogo responsable puede registrar la valoración del caso."
        )
    if (str(actor.rol or "").upper() not in ClinicalCaseAccess.ALLOWED_ROLES):
        raise ClinicalAuthorizationError("Rol no autorizado para valoración clínica.")


def valuation_to_dict(item):
    return {
        "id_valuation": str(item.id_valoracion),
        "criterion": {
            "id": item.criterio_id,
            "code": item.criterio.codigo,
            "name": item.criterio.nombre,
        },
        "oncologist_uuid": str(item.oncologo_uuid),
        "observation": item.observacion,
        "ai_result_uuid": str(item.resultado_ia_uuid) if item.resultado_ia_uuid else None,
        "created_at": item.fecha_valoracion.isoformat(),
    }


def list_valuations(case_id):
    queryset = (ValoracionEspecialista.objects.select_related("criterio")
                .filter(caso_id=case_id)
                .order_by("-fecha_valoracion", "-id_valoracion"))
    return [valuation_to_dict(item) for item in queryset]


@transaction.atomic
def register_valuation(*, case_id, actor, criterion_id, observation):
    case = (CasoClinico.objects.select_for_update()
            .select_related("estado_caso").filter(id_caso=case_id).first())
    if case is None:
        raise ValueError("El caso clínico no existe.")
    require_reviewer(actor, case)
    if case.estado_caso.codigo not in ALLOWED_STATES:
        raise ValueError("La valoración solo se registra en EN_ANALISIS o REVISADO.")
    criterion = CriterioValoracion.objects.filter(id_criterio=criterion_id).first()
    if criterion is None:
        raise ValueError("El criterio de valoración no existe.")
    # La valoración es inmutable: una reevaluación genera una nueva entrada histórica.
    item = ValoracionEspecialista.objects.create(
        caso=case, criterio=criterion, oncologo_uuid=actor.usuario_uuid,
        observacion=observation.strip(), resultado_ia_uuid=None,
    )
    return valuation_to_dict(item)


def has_current_doctor_valuation(case):
    if case.oncologo_responsable_uuid is None:
        return False
    # Una nueva asignación invalida la firma anterior para fines de cierre.
    # El historial de valoraciones se conserva; solo cambia la regla de elegibilidad.
    latest_assignment = (HistorialGestionCaso.objects
                         .filter(caso_id=case.pk, tipo_cambio="RESPONSABLE")
                         .order_by("-fecha_cambio", "-id_gestion")
                         .first())
    valuations = ValoracionEspecialista.objects.filter(
        caso_id=case.pk,
        oncologo_uuid=case.oncologo_responsable_uuid,
    ).exclude(observacion__isnull=True).exclude(observacion="")
    if latest_assignment is not None:
        valuations = valuations.filter(fecha_valoracion__gte=latest_assignment.fecha_cambio)
    return valuations.exists()


def assert_case_can_close(case):
    """Impide un cierre sin valoración del médico actualmente asignado."""
    if not has_current_doctor_valuation(case):
        raise ValueError(
            "Para cerrar el caso debe existir una valoración firmada "
            "por el oncólogo responsable actual."
        )
