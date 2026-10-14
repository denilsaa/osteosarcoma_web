"""Pruebas aisladas sin datos reales ni dependencia de PostgreSQL."""
from unittest.mock import patch
from uuid import uuid4
from django.test import SimpleTestCase
from clinica.application.services.clinical_notifications_service import build_management_notifications
from clinica.infrastructure.persistence.models import CasoClinico, HistorialGestionCaso


class NotificationBuildingTests(SimpleTestCase):
    def setUp(self):
        self.actor = uuid4()
        self.case = CasoClinico(id_caso=uuid4(), codigo_caso="CAS-PRUEBA-01", oncologo_responsable_uuid=self.actor)

    def test_assignment_notification(self):
        items = build_management_notifications(self.case, [HistorialGestionCaso(tipo_cambio="RESPONSABLE")])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].destinatario_uuid, self.actor)
        self.assertEqual(items[0].tipo, "ASIGNACION")
        self.assertNotIn("paciente", items[0].mensaje.lower())

    def test_priority_notification(self):
        items = build_management_notifications(self.case, [HistorialGestionCaso(tipo_cambio="PRIORIDAD")])
        self.assertEqual(items[0].tipo, "PRIORIDAD")

    def test_unassigned_case_has_no_notifications(self):
        self.case.oncologo_responsable_uuid = None
        self.assertEqual(build_management_notifications(self.case, [HistorialGestionCaso(tipo_cambio="PRIORIDAD")]), [])

    def test_two_changes_generate_two_distinct_events(self):
        items = build_management_notifications(self.case, [HistorialGestionCaso(tipo_cambio="RESPONSABLE"), HistorialGestionCaso(tipo_cambio="PRIORIDAD")])
        self.assertEqual({n.tipo for n in items}, {"ASIGNACION", "PRIORIDAD"})

    def test_unrecognized_event_is_ignored(self):
        self.assertEqual(build_management_notifications(self.case, [HistorialGestionCaso(tipo_cambio="DESCONOCIDO")]), [])


class AccessTests(SimpleTestCase):
    def test_query_scoped_to_user(self):
        from clinica.application.services.clinical_notifications_service import fetch_notifications
        recipient = uuid4()
        with patch("clinica.application.services.clinical_notifications_service.NotificacionClinica.objects") as objects:
            queryset = objects.filter.return_value
            queryset.filter.return_value.count.return_value = 2
            queryset.order_by.return_value.__getitem__.return_value = []
            unread, items = fetch_notifications(recipient)
            self.assertEqual(unread, 2)
            self.assertEqual(items, [])
            objects.filter.assert_called_once_with(destinatario_uuid=recipient)

