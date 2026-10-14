"""Pruebas sin datos reales de pacientes para valoración clínica y cierre."""
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4
from django.test import SimpleTestCase
from clinica.application.services.clinical_review_service import (
    assert_case_can_close, require_reviewer,
)
from clinica.infrastructure.security import ClinicalAuthorizationError
from clinica.interfaces.api.views.clinical_case_review_views import RegisterValuationSerializer


class ProfessionalReviewRulesTests(SimpleTestCase):
    def setUp(self):
        self.doctor_id = uuid4()
        self.actor = SimpleNamespace(usuario_uuid=self.doctor_id, rol="ONCOLOGO")
        self.case = SimpleNamespace(oncologo_responsable_uuid=self.doctor_id)

    def test_assigned_doctor_can_review(self):
        require_reviewer(self.actor, self.case)

    def test_different_doctor_cannot_review(self):
        self.case.oncologo_responsable_uuid = uuid4()
        with self.assertRaises(ClinicalAuthorizationError):
            require_reviewer(self.actor, self.case)

    def test_unassigned_case_cannot_be_reviewed(self):
        self.case.oncologo_responsable_uuid = None
        with self.assertRaises(ClinicalAuthorizationError):
            require_reviewer(self.actor, self.case)

    def test_head_can_review_only_when_assigned(self):
        self.actor.rol = "JEFE_ONCOLOGIA"
        require_reviewer(self.actor, self.case)
        self.case.oncologo_responsable_uuid = uuid4()
        with self.assertRaises(ClinicalAuthorizationError):
            require_reviewer(self.actor, self.case)

    def test_closure_blocked_without_valuation(self):
        with patch(
            "clinica.application.services.clinical_review_service.has_current_doctor_valuation",
            return_value=False,
        ):
            with self.assertRaisesRegex(ValueError, "oncólogo responsable"):
                assert_case_can_close(self.case)

    def test_closure_allowed_with_valuation(self):
        with patch(
            "clinica.application.services.clinical_review_service.has_current_doctor_valuation",
            return_value=True,
        ):
            assert_case_can_close(self.case)

    def test_observation_minimum_length(self):
        ser = RegisterValuationSerializer(data={"criterion_id": 1, "observation": "Corto"})
        self.assertFalse(ser.is_valid())
        self.assertIn("observation", ser.errors)

    def test_complete_valuation_is_accepted(self):
        ser = RegisterValuationSerializer(data={
            "criterion_id": 1,
            "observation": "Hallazgos radiográficos requieren revisión clínica.",
        })
        self.assertTrue(ser.is_valid(), ser.errors)
