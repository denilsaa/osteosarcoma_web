"""Contrato mínimo de eventos de IA. No incorpora radiografías ni datos de pacientes."""
import json

QUEUE = "clinica.ia.resultados.v1"
EVENT_TYPE = "IA_ANALISIS_FINALIZADO"
EVENT_VERSION = 1
ALLOWED_STATES = {"COMPLETADO", "FALLIDO"}


def build_event(event):
    if event.estado not in ALLOWED_STATES:
        raise ValueError("Estado de IA no terminal")
    return {
        "event_id": str(event.id_evento),
        "event_type": EVENT_TYPE,
        "version": EVENT_VERSION,
        "request_id": str(event.solicitud_id),
        "case_id": str(event.caso_uuid),
        "state": event.estado,
    }


def serialize_event(event):
    return json.dumps(build_event(event), separators=(",", ":")).encode("utf-8")
