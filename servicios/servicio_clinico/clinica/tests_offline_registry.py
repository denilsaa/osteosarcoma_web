"""Comprobaciones de integridad del registro de operaciones diferidas."""
from datetime import date
from uuid import uuid4
from django.db import IntegrityError, transaction
from django.test import TestCase
from clinica.infrastructure.persistence.models import (
    AltaPacienteOffline, Paciente, Sexo,
)


class AltaPacienteOfflineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sexo = Sexo.objects.first() or Sexo.objects.create(codigo="SEX_SYNC", nombre="Prueba")
        cls.patient = Paciente.objects.create(
            nombres="Paciente Sync", apellido_paterno="Prueba",
            fecha_nacimiento=date(2001, 1, 1), sexo=sexo,
        )

    def test_operacion_guarda_actor_hash_y_paciente(self):
        ident = uuid4()
        actor = uuid4()
        record = AltaPacienteOffline.objects.create(
            operacion_uuid=ident, actor_uuid=actor,
            payload_sha256="a" * 64, paciente=self.patient,
        )
        saved = AltaPacienteOffline.objects.get(pk=ident)
        self.assertEqual(saved.actor_uuid, actor)
        self.assertEqual(saved.paciente_id, self.patient.pk)
        self.assertEqual(saved.payload_sha256, record.payload_sha256)

    def test_misma_operacion_no_puede_guardarse_dos_veces(self):
        ident = uuid4()
        AltaPacienteOffline.objects.create(
            operacion_uuid=ident, actor_uuid=uuid4(),
            payload_sha256="a" * 64, paciente=self.patient,
        )
        with self.assertRaises(IntegrityError), transaction.atomic():
            AltaPacienteOffline.objects.create(
                operacion_uuid=ident, actor_uuid=uuid4(),
                payload_sha256="b" * 64, paciente=self.patient,
            )
        self.assertEqual(AltaPacienteOffline.objects.filter(pk=ident).count(), 1)
