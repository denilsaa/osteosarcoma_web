"""Bandeja personal de notificaciones clínicas autenticada por JWT."""
from uuid import UUID
from rest_framework.decorators import api_view
from rest_framework.response import Response
from clinica.application.services.clinical_notifications_service import (
    fetch_notifications, read_notification,
)
from clinica.infrastructure.security import (
    ClinicalCaseAccess, ClinicalAuthenticationError, ClinicalAuthorizationError,
)


def _actor_or_error(request):
    try:
        actor = ClinicalCaseAccess.get_actor(request)
        if actor.usuario_uuid is None:
            return None, Response({"error": "No hay identidad de usuario válida."}, status=401)
        return actor, None
    except ClinicalAuthenticationError as exc:
        return None, Response({"error": str(exc)}, status=401)
    except ClinicalAuthorizationError as exc:
        return None, Response({"error": str(exc)}, status=403)


@api_view(["GET"])
def clinical_notifications_view(request):
    actor, error = _actor_or_error(request)
    if error is not None:
        return error
    unread, items = fetch_notifications(actor.usuario_uuid)
    return Response({"data": items, "unread": unread})


@api_view(["PATCH"])
def clinical_notification_read_view(request, notification_id: UUID):
    actor, error = _actor_or_error(request)
    if error is not None:
        return error
    if not read_notification(actor.usuario_uuid, notification_id):
        return Response({"error": "Notificación no encontrada."}, status=404)
    return Response({"message": "Notificación marcada como leída."})
