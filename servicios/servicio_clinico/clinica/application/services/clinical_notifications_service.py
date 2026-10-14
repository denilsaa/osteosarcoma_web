"""Notificaciones internas: datos mínimos, eventos idempotentes y acceso por destinatario."""
from django.db import transaction
from django.utils import timezone
from clinica.infrastructure.persistence.models.notification_models import NotificacionClinica


def build_management_notifications(case, history_rows):
    """La alerta pertenece al historial administrativo, no a un nombre de paciente.

    Caso con ambos cambios: dos eventos separados para facilitar la trazabilidad.
    No notificar al usuario anterior en las reasignaciones.
    """
    result = []
    recipient = case.oncologo_responsable_uuid
    if not recipient:
        return result
    for event in history_rows:
        if event.tipo_cambio == "RESPONSABLE":
            title = "Nuevo caso asignado"
            message = f"Se te asignó el caso {case.codigo_caso}."
            category = "ASIGNACION"
        elif event.tipo_cambio == "PRIORIDAD":
            title = "Prioridad del caso actualizada"
            message = f"Se actualizó la prioridad del caso {case.codigo_caso}."
            category = "PRIORIDAD"
        else:
            continue
        result.append(NotificacionClinica(
            destinatario_uuid=recipient, caso=case, evento_gestion=event,
            tipo=category, titulo=title, mensaje=message,
        ))
    return result


def record_management_notifications(case, rows):
    """Se ejecuta en la misma transacción del historial de gestión."""
    alerts = build_management_notifications(case, rows)
    if alerts:
        NotificacionClinica.objects.bulk_create(alerts)


def fetch_notifications(actor_uuid, limit=30):
    qs = NotificacionClinica.objects.filter(destinatario_uuid=actor_uuid)
    unread = qs.filter(fecha_lectura__isnull=True).count()
    items = qs.order_by("-fecha_creacion", "-id_notificacion")[:limit]
    return unread, [
        {
            "id": str(n.id_notificacion), "type": n.tipo,
            "title": n.titulo, "message": n.mensaje,
            "case_id": str(n.caso_id),
            "created_at": n.fecha_creacion.isoformat(),
            "read_at": n.fecha_lectura.isoformat() if n.fecha_lectura else None,
        }
        for n in items
    ]


@transaction.atomic
def read_notification(actor_uuid, notification_id):
    """No revela a otro profesional si una notificación ajena existe."""
    notification = (NotificacionClinica.objects.select_for_update()
                    .filter(id_notificacion=notification_id, destinatario_uuid=actor_uuid).first())
    if notification is None:
        return False
    if notification.fecha_lectura is None:
        notification.fecha_lectura = timezone.now()
        notification.save(update_fields=["fecha_lectura"])
    return True


def build_ia_notification(event, case):
    """Notificar solo al responsable *actual*. No incluir paciente ni diagnóstico."""
    if not case.oncologo_responsable_uuid:
        return None
    if event["state"] == "COMPLETADO":
        kind, title, message = ("IA_RESULTADO", "Análisis de IA completado",
                                f"El análisis del caso {case.codigo_caso} está disponible para revisión.")
    elif event["state"] == "FALLIDO":
        kind, title, message = ("IA_FALLIDO", "Análisis de IA no completado",
                                f"El análisis del caso {case.codigo_caso} requiere revisión técnica.")
    else:
        raise ValueError("Estado no válido")
    return NotificacionClinica(
        destinatario_uuid=case.oncologo_responsable_uuid,
        caso=case, evento_ia_uuid=event["event_id"],
        tipo=kind, titulo=title, mensaje=message,
    )


@transaction.atomic
def register_ia_event(event):
    """Inserción idempotente, con restricción UNIQUE sobre evento_ia_uuid."""
    from clinica.infrastructure.persistence.models import CasoClinico
    case = CasoClinico.objects.select_for_update().filter(id_caso=event["case_id"]).first()
    if case is None:
        return "UNKNOWN_CASE"
    if NotificacionClinica.objects.filter(evento_ia_uuid=event["event_id"]).exists():
        return "DUPLICATE"
    notification = build_ia_notification(event, case)
    if notification is None:
        return "NO_RECIPIENT"
    # La inserción es atómica y la restricción única previene duplicados tras redelivery.
    NotificacionClinica.objects.create(
        destinatario_uuid=notification.destinatario_uuid,
        caso=notification.caso, evento_ia_uuid=notification.evento_ia_uuid,
        tipo=notification.tipo, titulo=notification.titulo, mensaje=notification.mensaje,
    )
    return "CREATED"
