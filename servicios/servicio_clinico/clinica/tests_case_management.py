
"""Reglas de Fase 2B sin datos reales de pacientes."""
from types import SimpleNamespace
from uuid import uuid4
from django.test import SimpleTestCase
from clinica.application.services.clinical_case_management_service import (
    require_head, validate_destination,
)
from clinica.infrastructure.security import ClinicalAuthorizationError
from clinica.interfaces.api.views.clinical_case_management_views import ChangeManagementSerializer


class ManagementRulesTests(SimpleTestCase):
    def setUp(self):
        self.uuid = uuid4()
        self.head = SimpleNamespace(rol="JEFE_ONCOLOGIA", usuario_uuid=uuid4())

    def test_head_can_manage(self):
        require_head(self.head)

    def test_oncologist_cannot_manage(self):
        with self.assertRaises(ClinicalAuthorizationError):
            require_head(SimpleNamespace(rol="ONCOLOGO", usuario_uuid=uuid4()))

    def test_active_oncologist_valid(self):
        validate_destination({"id_usuario": str(self.uuid), "rol_codigo": "ONCOLOGO", "estado": "ACTIVO"}, self.uuid)

    def test_inactive_oncologist_rejected(self):
        with self.assertRaisesRegex(ValueError, "activo"):
            validate_destination({"id_usuario": str(self.uuid), "rol_codigo": "ONCOLOGO", "estado": "INACTIVO"}, self.uuid)

    def test_wrong_identity_rejected(self):
        with self.assertRaises(ValueError):
            validate_destination({"id_usuario": str(uuid4()), "rol_codigo": "ONCOLOGO", "estado": "ACTIVO"}, self.uuid)

    def test_invalid_role_rejected(self):
        with self.assertRaises(ValueError):
            validate_destination({"id_usuario": str(self.uuid), "rol_codigo": "PACIENTE", "estado": "ACTIVO"}, self.uuid)

    def test_reason_required(self):
        form = ChangeManagementSerializer(data={"priority_id": 1, "reason": "x"})
        self.assertFalse(form.is_valid())

    def test_at_least_one_change_required(self):
        form = ChangeManagementSerializer(data={"reason": "Revisión del caso actual"})
        self.assertFalse(form.is_valid())

    def test_valid_change(self):
        form = ChangeManagementSerializer(data={"priority_id": 1, "reason": "Repriorización por evaluación médica"})
        self.assertTrue(form.is_valid(), form.errors)


class AssignmentReviewTests(SimpleTestCase):
    def test_closure_checks_valuation_after_last_reassignment(self):
        from datetime import datetime, timezone
        from unittest.mock import patch
        from clinica.application.services.clinical_review_service import has_current_doctor_valuation
        doctor = uuid4()
        case = SimpleNamespace(pk=uuid4(), oncologo_responsable_uuid=doctor)
        timestamp = datetime(2026, 10, 9, tzinfo=timezone.utc)
        with patch(
            "clinica.application.services.clinical_review_service.HistorialGestionCaso.objects"
        ) as management, patch(
            "clinica.application.services.clinical_review_service.ValoracionEspecialista.objects"
        ) as valuations:
            management.filter.return_value.order_by.return_value.first.return_value = (
                SimpleNamespace(fecha_cambio=timestamp)
            )
            queryset = valuations.filter.return_value.exclude.return_value.exclude.return_value
            queryset.filter.return_value.exists.return_value = True
            self.assertTrue(has_current_doctor_valuation(case))
            queryset.filter.assert_called_once_with(fecha_valoracion__gte=timestamp)

class InterserviceHostnameTests(SimpleTestCase):
    """Verifica el destino del validador sin realizar peticiones externas."""

    def test_destination_uses_valid_docker_hostname_and_auth(self):
        import io
        import json
        from unittest.mock import patch
        from clinica.interfaces.api.views.clinical_case_management_views import (
            _validate_active_oncologist,
        )

        oncologist_uuid = uuid4()
        result = {
            "id_usuario": str(oncologist_uuid),
            "rol_codigo": "ONCOLOGO",
            "estado": "ACTIVO",
        }
        response = io.BytesIO(json.dumps(result).encode("utf-8"))
        actor_request = SimpleNamespace(headers={"Authorization": "Bearer test-token"})
        with patch(
            "clinica.interfaces.api.views.clinical_case_management_views.urllib.request.urlopen",
            return_value=response,
        ) as mock_open:
            _validate_active_oncologist(actor_request, oncologist_uuid)
        request = mock_open.call_args.args[0]
        self.assertEqual(
            request.full_url,
            f"http://servicio-usuarios:8000/api/oncologos/{oncologist_uuid}/",
        )
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")

