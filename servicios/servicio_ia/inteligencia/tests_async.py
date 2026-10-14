"""Pruebas que deben ejecutarse dentro del contenedor con PostgreSQL de test."""
from unittest.mock import patch
from uuid import uuid4

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import JsonResponse
from django.test import TestCase, override_settings

from inteligencia.analisis_async import require_actor
from inteligencia.management.commands.worker_analisis import execute_job
from inteligencia.models import AnalisisRadiografiaIA, SolicitudAnalisisIA


ACTOR = {'usuario_id': str(uuid4()), 'rol': 'ONCOLOGO'}


class SolicitudesAsyncTests(TestCase):
    def test_no_acepta_anonimo(self):
        from django.test.client import RequestFactory
        with self.assertRaises(PermissionError):
            require_actor(RequestFactory().get('/api/analisis/solicitudes/'))

    @patch('inteligencia.analisis_async.publish_task')
    @patch('inteligencia.analisis_async.check_case_and_file', return_value='7e6b658f2560db81336e8b6cc4d5c86661d14ab362a22c81a40ebf886a6ee0fb')
    @patch('inteligencia.analisis_async.require_actor', return_value=ACTOR)
    @patch('inteligencia.inference.osteosarcoma_validator.OsteosarcomaValidator')
    def test_encola_y_evita_duplicados(self, validator, actor, check, publish):
        validator.return_value.available = True
        validator.return_value.version = 'osteosarcoma_finetuned_v1'
        caso, radio = uuid4(), uuid4()
        payload = {
            'caso_uuid': str(caso), 'radiografia_uuid': str(radio),
            'file': SimpleUploadedFile('radiografia.png', b'archivo-de-prueba'),
        }
        first = self.client.post('/api/analisis/solicitudes/', payload, HTTP_AUTHORIZATION='Bearer mock')
        self.assertEqual(first.status_code, 202)
        job_id = first.json()['data']['id_solicitud']
        self.assertEqual(first.json()['data']['estado'], 'PENDIENTE')
        payload['file'] = SimpleUploadedFile('radiografia.png', b'archivo-de-prueba')
        second = self.client.post('/api/analisis/solicitudes/', payload, HTTP_AUTHORIZATION='Bearer mock')
        self.assertEqual(second.status_code, 200)
        self.assertTrue(second.json()['duplicada'])
        self.assertEqual(second.json()['data']['id_solicitud'], job_id)
        publish.assert_called_once()

    @patch('inteligencia.management.commands.worker_analisis.validar_radiografia')
    @patch('inteligencia.management.commands.worker_analisis.OsteosarcomaValidator')
    def test_worker_completa_una_sola_vez(self, validator, inference):
        validator.return_value.available = True
        validator.return_value.version = 'v1'
        job = SolicitudAnalisisIA.objects.create(
            caso_uuid=uuid4(), radiografia_uuid=uuid4(), solicitado_por_uuid=uuid4(),
            version_modelo='v1', historial=[],
        )
        job.archivo.save('muestra.png', ContentFile(b'contenido'), save=True)
        analysis = AnalisisRadiografiaIA.objects.create(
            radiografia_uuid=job.radiografia_uuid, caso_uuid=job.caso_uuid,
            resultado_json={'es_radiografia': True},
        )
        inference.return_value = JsonResponse({'data': {'persistencia': {'id_analisis': str(analysis.id_analisis)}}})
        self.assertEqual(execute_job(job.id_solicitud), 'COMPLETED')
        self.assertEqual(execute_job(job.id_solicitud), 'IGNORE')
        job.refresh_from_db()
        self.assertEqual(job.estado, 'COMPLETADO')
        self.assertEqual(job.intentos, 1)
        self.assertEqual(job.analisis_id, analysis.id_analisis)

    @patch('inteligencia.management.commands.worker_analisis.validar_radiografia', side_effect=RuntimeError('fallo'))
    @patch('inteligencia.management.commands.worker_analisis.OsteosarcomaValidator')
    def test_maximo_tres_intentos(self, validator, inference):
        validator.return_value.available = True
        validator.return_value.version = 'v1'
        job = SolicitudAnalisisIA.objects.create(
            caso_uuid=uuid4(), radiografia_uuid=uuid4(), solicitado_por_uuid=uuid4(),
            version_modelo='v1', historial=[],
        )
        job.archivo.save('muestra.png', ContentFile(b'contenido'), save=True)
        self.assertEqual(execute_job(job.id_solicitud), 'RETRY')
        self.assertEqual(execute_job(job.id_solicitud), 'RETRY')
        self.assertEqual(execute_job(job.id_solicitud), 'FAILED')
        job.refresh_from_db()
        self.assertEqual(job.estado, 'FALLIDO')
        self.assertEqual(job.intentos, 3)


class IdempotenciaPersistenciaTests(TestCase):
    def test_solicitud_uuid_esta_en_analisis_y_no_en_solicitud_legacy(self):
        from inteligencia.models import SolicitudInferencia
        self.assertIn('solicitud_uuid', {
            field.name for field in AnalisisRadiografiaIA._meta.get_fields()
        })
        self.assertNotIn('solicitud_uuid', {
            field.name for field in SolicitudInferencia._meta.get_fields()
        })

    def test_guarda_una_vez_aunque_se_repita_la_misma_solicitud(self):
        from inteligencia.views import _guardar_analisis_clinico
        request_id = uuid4()
        contexto = {
            'solicitud_uuid': request_id,
            'radiografia_uuid': uuid4(),
            'caso_uuid': uuid4(),
            'solicitado_por_uuid': uuid4(),
        }
        result = {'es_radiografia': True, 'analisis_osteosarcoma_evaluado': False}
        primero = _guardar_analisis_clinico(result, contexto)
        segundo = _guardar_analisis_clinico(result, contexto)
        self.assertEqual(primero['persistencia']['id_analisis'], segundo['persistencia']['id_analisis'])
        self.assertEqual(AnalisisRadiografiaIA.objects.filter(solicitud_uuid=request_id).count(), 1)

    @patch('inteligencia.management.commands.worker_analisis.validar_radiografia',
           return_value=JsonResponse({'error': {'code': 'AI_ANALYSIS_PERSISTENCE_ERROR'}}, status=500))
    @patch('inteligencia.management.commands.worker_analisis.OsteosarcomaValidator')
    def test_error_permanente_no_se_reintenta(self, validator, inference):
        validator.return_value.available = True
        validator.return_value.version = 'v1'
        job = SolicitudAnalisisIA.objects.create(
            caso_uuid=uuid4(), radiografia_uuid=uuid4(), solicitado_por_uuid=uuid4(),
            version_modelo='v1', historial=[],
        )
        job.archivo.save('muestra.png', ContentFile(b'contenido'), save=True)
        self.assertEqual(execute_job(job.id_solicitud), 'FAILED')
        job.refresh_from_db()
        self.assertEqual(job.estado, 'FALLIDO')
        self.assertEqual(job.intentos, 1)
