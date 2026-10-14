"""Contrato de eventos de IA; valida datos antes de escribir registros."""
import json
from uuid import UUID

QUEUE = "clinica.ia.resultados.v1"


def decode_event(body):
    raw = json.loads(body)
    if not isinstance(raw, dict):
        raise ValueError("Evento mal formado")
    if (raw.get("event_type") != "IA_ANALISIS_FINALIZADO"
            or raw.get("version") != 1
            or raw.get("state") not in ("COMPLETADO", "FALLIDO")):
        raise ValueError("Versión o estado inválido")
    # UUID canónico y payload limitado; nunca aceptar nombres o datos radiográficos.
    if set(raw) != {"event_id", "event_type", "version", "request_id", "case_id", "state"}:
        raise ValueError("Campos no autorizados")
    for key in ("event_id", "request_id", "case_id"):
        raw[key] = str(UUID(str(raw[key])))
    return raw
