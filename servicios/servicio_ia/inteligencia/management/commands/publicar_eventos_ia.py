"""Publicador persistente (outbox) de resultados. No publicar antes del commit clínico."""
import logging
import time

import pika
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from django.utils import timezone
from inteligencia.analisis_async import rabbit_connection
from inteligencia.models import EventoNotificacionIA
from inteligencia.notification_events import QUEUE, serialize_event

logger = logging.getLogger(__name__)


def publish_pending(channel, limit=50):
    count = 0
    pending = list(EventoNotificacionIA.objects.filter(
        publicado_en__isnull=True).order_by("fecha_creacion")[:limit])
    for event in pending:
        confirmed = channel.basic_publish(
            exchange="", routing_key=QUEUE, body=serialize_event(event),
            mandatory=True, properties=pika.BasicProperties(
                delivery_mode=2, content_type="application/json", message_id=str(event.id_evento),
            ),
        )
        if confirmed is False:
            raise RuntimeError("Publicación no confirmada")
        EventoNotificacionIA.objects.filter(
            pk=event.pk, publicado_en__isnull=True
        ).update(publicado_en=timezone.now(), intentos_publicacion=event.intentos_publicacion + 1)
        count += 1
    return count


class Command(BaseCommand):
    help = "Publica en RabbitMQ eventos finales de análisis registrados en el outbox."

    def handle(self, *args, **options):
        while True:
            conn = None
            try:
                close_old_connections()
                conn = rabbit_connection()
                channel = conn.channel()
                channel.queue_declare(queue=QUEUE, durable=True)
                channel.confirm_delivery()
                self.stdout.write("Publicador de resultados IA conectado a RabbitMQ")
                while True:
                    close_old_connections()
                    count = publish_pending(channel)
                    if count:
                        self.stdout.write(f"Eventos IA publicados: {count}")
                    time.sleep(1 if count else 3)
            except (OSError, pika.exceptions.AMQPError, RuntimeError) as exc:
                logger.warning("Publicación pendiente; reintentará: %s", type(exc).__name__)
                time.sleep(4)
            finally:
                if conn is not None and conn.is_open:
                    conn.close()
