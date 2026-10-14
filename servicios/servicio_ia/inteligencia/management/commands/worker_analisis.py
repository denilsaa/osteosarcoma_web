"""Worker de inferencia. Ejecutar solo dentro de servicio_ia_worker con la misma DB y MEDIA_ROOT."""
import json
import logging
import time
from uuid import UUID

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand
from django.db import close_old_connections, transaction
from django.test.client import RequestFactory
from django.utils import timezone

from inteligencia.analisis_async import DEAD_QUEUE, QUEUE, RETRY_QUEUE, declare_queues, rabbit_connection
from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator
from inteligencia.models import SolicitudAnalisisIA, EventoNotificacionIA
from inteligencia.views import validar_radiografia
import pika

logger = logging.getLogger(__name__)


def registrar(job, estado, detalle):
    now = timezone.now()
    job.historial = [*(job.historial or []), {'estado': estado, 'fecha': now.isoformat(), 'intento': job.intentos, 'detalle': detalle}]
    job.estado = estado
    if estado == 'PROCESANDO':
        job.fecha_inicio = now
        job.fecha_fin = None
        job.intentos += 1
    elif estado in {'COMPLETADO', 'FALLIDO'}:
        job.fecha_fin = now
        if job.fecha_inicio:
            job.duracion_segundos = round((now - job.fecha_inicio).total_seconds(), 3)
    job.save()


def execute_job(job_id):
    """Ejecuta una inferencia como máximo una vez por mensaje; idempotencia ante redelivery."""
    with transaction.atomic():
        job = SolicitudAnalisisIA.objects.select_for_update().filter(id_solicitud=job_id).first()
        if job is None or job.estado in {'COMPLETADO', 'FALLIDO'}:
            return 'IGNORE'
        if job.estado == 'PROCESANDO':
            # Con un único worker, una reentrega implica que la ejecución anterior se interrumpió.
            registrar(job, 'PENDIENTE', 'Recuperación tras interrupción de worker')
        if job.intentos >= 3:
            registrar(job, 'FALLIDO', 'Se agotaron los intentos de análisis')
            EventoNotificacionIA.objects.get_or_create(
                solicitud=job, defaults={'caso_uuid': job.caso_uuid, 'estado': 'FALLIDO'}
            )
            return 'FAILED'
        registrar(job, 'PROCESANDO', 'Inicio de inferencia')

    try:
        validator = OsteosarcomaValidator()
        if not validator.available or validator.version != job.version_modelo:
            raise RuntimeError('VERSION_OR_MODEL_UNAVAILABLE')
        with job.archivo.open('rb') as file:
            content = file.read()
        filename = job.archivo.name.rsplit('/', 1)[-1]
        upload = SimpleUploadedFile(filename, content)
        request = RequestFactory().post('/api/validaciones/radiografia/', {
            'file': upload,
            'radiografia_uuid': str(job.radiografia_uuid),
            'caso_uuid': str(job.caso_uuid),
            'solicitado_por_uuid': str(job.solicitado_por_uuid),
            'solicitud_uuid': str(job.id_solicitud),
        })
        request._trusted_worker = True  # Creado en memoria, no desde cabeceras HTTP.
        response = validar_radiografia(request)
        body = json.loads(response.content)
        if response.status_code != 200:
            error = body.get('error', {})
            # La imagen rechazada por calidad sigue siendo resultado trazable si response=200.
            if response.status_code == 422:
                raise ValueError(error.get('code', 'INVALID_IMAGE'))
            raise RuntimeError(error.get('code', 'INFERENCE_FAILED'))
        persistence = body.get('data', {}).get('persistencia') or {}
        if not persistence.get('id_analisis'):
            raise RuntimeError('RESULT_NOT_PERSISTED')
        # Calcular Grad-CAM sin cambiar el diagnóstico guardado. Antes de marcar
        # COMPLETADO para que el frontend encuentre el archivo al consultar.
        try:
            from inteligencia.gradcam_clinico import generar_gradcam
            generar_gradcam(job_id, content, filename, body.get('data') or {}, job.version_modelo)
        except Exception:
            logger.warning('Grad-CAM no disponible para la solicitud (fallo controlado)')
        with transaction.atomic():
            fresh = SolicitudAnalisisIA.objects.select_for_update().get(pk=job_id)
            fresh.analisis_id = UUID(str(persistence['id_analisis']))
            registrar(fresh, 'COMPLETADO', 'Resultado registrado en el servicio de IA')
            EventoNotificacionIA.objects.get_or_create(
                solicitud=fresh, defaults={'caso_uuid': fresh.caso_uuid, 'estado': 'COMPLETADO'}
            )
        job.archivo.delete(save=False)
        return 'COMPLETED'
    except Exception as exc:
        # Solo códigos, no nombres de pacientes ni excepciones con datos sensibles.
        code = str(exc) if str(exc) in {
            'VERSION_OR_MODEL_UNAVAILABLE', 'RESULT_NOT_PERSISTED',
            'INFERENCE_FAILED', 'AI_ANALYSIS_PERSISTENCE_ERROR',
        } else 'INVALID_IMAGE' if isinstance(exc, ValueError) else 'PROCESSING_ERROR'
        # Fallos permanentes: no repetir tres veces la misma inferencia.
        # Los fallos operativos transitorios mantienen los reintentos limitados.
        permanent_codes = {
            'AI_ANALYSIS_PERSISTENCE_ERROR',
            'RESULT_NOT_PERSISTED',
            'VERSION_OR_MODEL_UNAVAILABLE',
            'INVALID_IMAGE',
        }
        with transaction.atomic():
            fresh = SolicitudAnalisisIA.objects.select_for_update().get(pk=job_id)
            fresh.error_codigo = code
            if code in permanent_codes or fresh.intentos >= 3:
                registrar(fresh, 'FALLIDO', 'Análisis no completado; requiere revisión técnica')
                EventoNotificacionIA.objects.get_or_create(
                    solicitud=fresh, defaults={'caso_uuid': fresh.caso_uuid, 'estado': 'FALLIDO'}
                )
                action = 'FAILED'
            else:
                registrar(fresh, 'PENDIENTE', 'Nuevo intento programado')
                action = 'RETRY'
        if action == 'FAILED':
            job.archivo.delete(save=False)
        return action


class Command(BaseCommand):
    help = 'Procesa trabajos de IA desde RabbitMQ, hasta 3 intentos por trabajo.'

    def handle(self, *args, **options):
        while True:
            conn = None
            try:
                conn = rabbit_connection()
                channel = conn.channel()
                declare_queues(channel)
                channel.basic_qos(prefetch_count=1)
                channel.confirm_delivery()

                def on_message(ch, method, properties, body):
                    close_old_connections()
                    try:
                        job_id = UUID(str(json.loads(body)['solicitud_id']))
                    except (ValueError, KeyError, TypeError):
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    action = execute_job(job_id)
                    try:
                        if action in {'RETRY', 'FAILED'}:
                            queue = RETRY_QUEUE if action == 'RETRY' else DEAD_QUEUE
                            published = ch.basic_publish(
                                exchange='', routing_key=queue, body=body,
                                mandatory=True,
                                properties=pika.BasicProperties(delivery_mode=2, content_type='application/json', message_id=str(job_id)),
                            )
                            if published is False:
                                raise RuntimeError('No confirmado por RabbitMQ')
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                    except Exception:
                        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    finally:
                        close_old_connections()

                channel.basic_consume(queue=QUEUE, on_message_callback=on_message, auto_ack=False)
                self.stdout.write('Worker IA conectado a RabbitMQ (analisis_radiografia.v2)')
                channel.start_consuming()
            except (OSError, pika.exceptions.AMQPError) as exc:
                logger.warning('Conexión AMQP perdida; reintentando')
                time.sleep(4)
            finally:
                if conn is not None and conn.is_open:
                    conn.close()
