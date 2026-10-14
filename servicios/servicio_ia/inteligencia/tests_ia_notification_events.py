from unittest.mock import Mock
from uuid import uuid4
from django.test import SimpleTestCase
from inteligencia.notification_events import build_event, serialize_event

class IAOutboxTests(SimpleTestCase):
    def setUp(self):
        self.event = Mock(
            id_evento=uuid4(), solicitud_id=uuid4(), caso_uuid=uuid4(), estado="COMPLETADO"
        )

    def test_minimal_event_contract(self):
        event = build_event(self.event)
        self.assertEqual(set(event), {"event_id", "event_type", "version", "request_id", "case_id", "state"})

    def test_serialization_is_bytes(self):
        self.assertIsInstance(serialize_event(self.event), bytes)

    def test_bad_state_not_published(self):
        self.event.estado = "PROCESANDO"
        with self.assertRaises(ValueError): build_event(self.event)
