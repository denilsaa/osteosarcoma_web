"""Integridad del recibo idempotente de casos diferidos."""
from datetime import date
from uuid import uuid4
from django.db import IntegrityError, transaction
from django.test import TestCase
from clinica.infrastructure.persistence.models import AltaCasoOffline, CasoClinico, Paciente, Sexo, EstadoCaso, PrioridadCaso

class AltaCasoOfflineTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        sex = Sexo.objects.first() or Sexo.objects.create(codigo="SEX_SYNC_CASE", nombre="Prueba")
        patient = Paciente.objects.create(nombres="Paciente Sync Caso", apellido_paterno="Prueba", fecha_nacimiento=date(2001, 1, 1), sexo=sex)
        status = EstadoCaso.objects.first() or EstadoCaso.objects.create(codigo="REGISTRADO", nombre="Registrado")
        priority = PrioridadCaso.objects.first() or PrioridadCaso.objects.create(codigo="MEDIA", nombre="Media", nivel=2)
        cls.case = CasoClinico.objects.create(paciente=patient, estado_caso=status, prioridad=priority, codigo_caso="CAS-OFF-TEST-001", motivo_consulta="Prueba caso offline")

    def test_recibo_asocia_actor_hash_y_caso(self):
        op, actor = uuid4(), uuid4()
        AltaCasoOffline.objects.create(operacion_uuid=op, actor_uuid=actor, payload_sha256="a"*64, caso=self.case)
        saved = AltaCasoOffline.objects.get(pk=op)
        self.assertEqual(saved.actor_uuid, actor)
        self.assertEqual(saved.caso_id, self.case.pk)

    def test_no_permite_duplicar_uuid_de_operacion(self):
        op = uuid4()
        AltaCasoOffline.objects.create(operacion_uuid=op, actor_uuid=uuid4(), payload_sha256="a"*64, caso=self.case)
        with self.assertRaises(IntegrityError), transaction.atomic():
            AltaCasoOffline.objects.create(operacion_uuid=op, actor_uuid=uuid4(), payload_sha256="b"*64, caso=self.case)
        self.assertEqual(AltaCasoOffline.objects.filter(pk=op).count(), 1)
