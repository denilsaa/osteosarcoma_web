"""Pruebas sin pacientes reales para el contrato de notificaciones IA."""
import json
from uuid import uuid4
from unittest.mock import patch
from django.test import SimpleTestCase
from clinica.application.services.ia_notification_events import decode_event
from clinica.application.services.clinical_notifications_service import build_ia_notification
from clinica.infrastructure.persistence.models import CasoClinico


class IAEventTests(SimpleTestCase):
    def setUp(self):
        self.payload = dict(event_id=str(uuid4()), request_id=str(uuid4()), case_id=str(uuid4()),
                            event_type="IA_ANALISIS_FINALIZADO", version=1, state="COMPLETADO")

    def test_contract_accepted(self):
        self.assertEqual(decode_event(json.dumps(self.payload))["state"], "COMPLETADO")

    def test_fallido_is_valid(self):
        self.payload["state"] = "FALLIDO"
        self.assertEqual(decode_event(json.dumps(self.payload))["state"], "FALLIDO")

    def test_invalid_version_rejected(self):
        self.payload["version"] = 2
        with self.assertRaises(ValueError): decode_event(json.dumps(self.payload))

    def test_forbidden_patient_data_rejected(self):
        self.payload["patient_name"] = "Nombre no permitido"
        with self.assertRaises(ValueError): decode_event(json.dumps(self.payload))

    def test_invalid_id_rejected(self):
        self.payload["case_id"] = "oops"
        with self.assertRaises(ValueError): decode_event(json.dumps(self.payload))

    def test_notification_uses_case_only(self):
        case = CasoClinico(id_caso=uuid4(), codigo_caso="CAS-PRUEBA", oncologo_responsable_uuid=uuid4())
        note = build_ia_notification(self.payload, case)
        self.assertEqual(note.destinatario_uuid, case.oncologo_responsable_uuid)
        self.assertEqual(note.tipo, "IA_RESULTADO")
        self.assertNotIn("paciente", note.mensaje.lower())

    def test_unassigned_case_is_ignored(self):
        case = CasoClinico(id_caso=uuid4(), codigo_caso="CAS-PRUEBA", oncologo_responsable_uuid=None)
        self.assertIsNone(build_ia_notification(self.payload, case))
