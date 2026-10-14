"""Pruebas de aislamiento de pacientes (usar: manage.py test clinica.tests_patient_scope)."""
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import jwt
from django.test import Client, TestCase

from clinica.infrastructure.persistence.models import (
    AsignacionPaciente, CasoClinico, EstadoCaso, Paciente, PrioridadCaso, Sexo,
)
from clinica.infrastructure.security.patient_access import PatientAccess
from clinica.infrastructure.security import ClinicalAuthorizationError


class PatientScopeTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.onco1 = uuid4()
        cls.onco2 = uuid4()
        cls.head_id = uuid4()
        cls.sexo = Sexo.objects.first() or Sexo.objects.create(codigo="SEX_TEST", nombre="Prueba")
        cls.patient_a = Paciente.objects.create(
            nombres="PacienteA", apellido_paterno="Prueba", fecha_nacimiento=date(2001, 1, 1), sexo=cls.sexo,
        )
        cls.patient_b = Paciente.objects.create(
            nombres="PacienteB", apellido_paterno="Prueba", fecha_nacimiento=date(2002, 1, 1), sexo=cls.sexo,
        )
        AsignacionPaciente.objects.create(
            paciente=cls.patient_a, oncologo_uuid=cls.onco1, asignado_por_uuid=cls.onco1,
            motivo="Registro por el profesional responsable.",
        )

    def _actor(self, who, role="ONCOLOGO"):
        return SimpleNamespace(usuario_uuid=who, rol=role)

    def test_oncologo_solo_ve_su_paciente(self):
        a = self._actor(self.onco1)
        self.assertTrue(PatientAccess.can_access(a, self.patient_a.pk))
        self.assertFalse(PatientAccess.can_access(a, self.patient_b.pk))
        with self.assertRaises(ClinicalAuthorizationError):
            PatientAccess.require(a, self.patient_b.pk)

    def test_jefatura_puede_ver_todos(self):
        j = self._actor(self.head_id, "JEFE_ONCOLOGIA")
        self.assertTrue(PatientAccess.can_access(j, self.patient_a.pk))
        self.assertTrue(PatientAccess.can_access(j, self.patient_b.pk))

    def test_paciente_reasignado_se_incluye_en_lista(self):
        AsignacionPaciente.objects.create(
            paciente=self.patient_b, oncologo_uuid=self.onco1, asignado_por_uuid=self.head_id,
            motivo="Asignación por necesidades del servicio.",
        )
        ids = set(PatientAccess.scope(Paciente.objects.all(), self._actor(self.onco1)).values_list("pk", flat=True))
        self.assertEqual(ids, {self.patient_a.pk, self.patient_b.pk})

    def test_revocacion_corta_acceso_si_no_hay_casos(self):
        AsignacionPaciente.objects.filter(paciente=self.patient_a, oncologo_uuid=self.onco1).update(activa=False)
        self.assertFalse(PatientAccess.can_access(self._actor(self.onco1), self.patient_a.pk))

    def test_caso_asignado_conserva_acceso_a_paciente_historico(self):
        # Caso existente de migraciones previas: aún no tiene fila de asignación explícita.
        estado = EstadoCaso.objects.first() or EstadoCaso.objects.create(codigo="REGISTRADO", nombre="Registrado")
        prioridad = PrioridadCaso.objects.first() or PrioridadCaso.objects.create(codigo="BAJA", nombre="Baja", nivel=1)
        CasoClinico.objects.create(
            paciente=self.patient_b, estado_caso=estado, prioridad=prioridad,
            codigo_caso="TEST-ALCANCE-0001", motivo_consulta="Caso de prueba",
            oncologo_responsable_uuid=self.onco2,
        )
        self.assertTrue(PatientAccess.can_access(self._actor(self.onco2), self.patient_b.pk))
        self.assertFalse(PatientAccess.can_access(self._actor(self.onco1), self.patient_b.pk))

    def test_api_no_expone_detalle_paciente_ajeno(self):
        client = Client()
        now = datetime.now(timezone.utc)
        token = jwt.encode({
            "usuario_id": str(self.onco1), "rol": "ONCOLOGO", "type": "access",
            "sid": str(uuid4()), "iat": int(now.timestamp()),
            "exp": int((now + timedelta(hours=1)).timestamp()),
        }, "clave-clinica-prueba", algorithm="HS256")
        with patch.dict("os.environ", {"JWT_SIGNING_KEY": "clave-clinica-prueba"}):
            response = client.get(
                f"/api/pacientes/{self.patient_b.pk}/",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
        self.assertEqual(response.status_code, 403)
        self.assertNotIn("PacienteB", response.content.decode())
