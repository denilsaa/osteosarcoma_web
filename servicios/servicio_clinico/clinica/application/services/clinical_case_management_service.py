
"""Gestión de responsables y prioridades, exclusiva de jefatura."""
from django.db import transaction
from django.db.models import Count
from clinica.application.services.clinical_notifications_service import record_management_notifications
from clinica.infrastructure.persistence.models import (
    CasoClinico, HistorialGestionCaso, PrioridadCaso,
)
from clinica.infrastructure.security import (
    ClinicalAuthorizationError, ClinicalCaseAccess,
)


def require_head(actor):
    if not ClinicalCaseAccess.is_head(actor) or actor.usuario_uuid is None:
        raise ClinicalAuthorizationError(
            "Solo el jefe de oncología puede gestionar asignaciones y prioridades."
        )


def validate_destination(data, expected_uuid):
    """Validar respuesta del servicio de usuarios; no confiar en UUID enviado."""
    if not isinstance(data, dict) or str(data.get("id_usuario", "")).lower() != str(expected_uuid):
        raise ValueError("No se pudo verificar el oncólogo de destino.")
    if str(data.get("estado", "")).upper() != "ACTIVO":
        raise ValueError("El profesional de destino no está activo.")
    if str(data.get("rol_codigo", "")).upper() not in {"ONCOLOGO", "JEFE_ONCOLOGIA"}:
        raise ValueError("El usuario de destino no tiene un rol clínico autorizado.")


@transaction.atomic
def update_case_management(*, case_id, actor, new_doctor_uuid=None,
                           new_priority_id=None, reason):
    require_head(actor)
    case = (CasoClinico.objects.select_for_update()
            .select_related("estado_caso", "prioridad")
            .filter(id_caso=case_id).first())
    if case is None:
        raise ValueError("El caso clínico no existe.")
    if case.estado_caso.codigo == "CERRADO":
        raise ValueError("No se pueden modificar casos cerrados.")
    updates = []
    if new_doctor_uuid is not None and new_doctor_uuid != case.oncologo_responsable_uuid:
        updates.append(("RESPONSABLE", str(case.oncologo_responsable_uuid or ""), str(new_doctor_uuid)))
        case.oncologo_responsable_uuid = new_doctor_uuid
    if new_priority_id is not None and new_priority_id != case.prioridad_id:
        priority = PrioridadCaso.objects.filter(id_prioridad=new_priority_id).first()
        if priority is None:
            raise ValueError("La prioridad seleccionada no existe.")
        updates.append(("PRIORIDAD", str(case.prioridad_id), str(priority.pk)))
        case.prioridad = priority
    if not updates:
        raise ValueError("No se registraron cambios en el caso.")
    case.save(update_fields=["oncologo_responsable_uuid", "prioridad"])
    rows = [HistorialGestionCaso(
        caso=case, tipo_cambio=kind, valor_anterior=old,
        valor_nuevo=new, actor_uuid=actor.usuario_uuid, motivo=reason.strip(),
    ) for kind, old, new in updates]
    HistorialGestionCaso.objects.bulk_create(rows)
    record_management_notifications(case, rows)
    return [{"type": kind, "previous": old, "current": new}
            for kind, old, new in updates]


def list_management_history(case_id):
    items = HistorialGestionCaso.objects.filter(caso_id=case_id).order_by("-fecha_cambio", "-id_gestion")[:100]
    return [{
        "id": obj.id_gestion, "type": obj.tipo_cambio,
        "previous": obj.valor_anterior, "current": obj.valor_nuevo,
        "actor_uuid": str(obj.actor_uuid), "reason": obj.motivo,
        "changed_at": obj.fecha_cambio.isoformat(),
    } for obj in items]


def supervision_summary():
    """Totales agregados, sin identificar pacientes."""
    return {
        "total": CasoClinico.objects.count(),
        "unassigned": CasoClinico.objects.filter(oncologo_responsable_uuid__isnull=True).count(),
        "by_status": list(CasoClinico.objects.values(
            "estado_caso__codigo", "estado_caso__nombre"
        ).annotate(total=Count("id_caso")).order_by("estado_caso__codigo")),
        "by_priority": list(CasoClinico.objects.values(
            "prioridad__codigo", "prioridad__nombre"
        ).annotate(total=Count("id_caso")).order_by("prioridad__nivel")),
    }
