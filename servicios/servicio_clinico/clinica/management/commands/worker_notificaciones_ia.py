"""Consumidor duradero de eventos IA para la bandeja de notificaciones clínicas."""
import logging
import os
import time

import pika
from django.core.management.base import BaseCommand
from django.db import close_old_connections
from clinica.application.services.ia_notification_events import QUEUE, decode_event
from clinica.application.services.clinical_notifications_service import register_ia_event

logger = logging.getLogger(__name__)


def rabbit_connection():
    return pika.BlockingConnection(pika.ConnectionParameters(
        host=os.environ.get("RABBITMQ_HOST", "rabbitmq"),
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        credentials=pika.PlainCredentials(os.environ["RABBITMQ_USER"], os.environ["RABBITMQ_PASSWORD"]),
        heartbeat=120, socket_timeout=5, blocked_connection_timeout=5,
        connection_attempts=2,
    ))


class Command(BaseCommand):
    help = "Recibe resultados IA y crea avisos clínicos personales idempotentes."

    def handle(self, *args, **options):
        while True:
            conn = None
            try:
                conn = rabbit_connection()
                ch = conn.channel()
                ch.queue_declare(queue=QUEUE, durable=True)
                ch.basic_qos(prefetch_count=1)
                self.stdout.write("Notificaciones clínicas IA conectadas a RabbitMQ")

                def consume(channel, method, properties, body):
                    close_old_connections()
                    try:
                        event = decode_event(body)
                    except (ValueError, TypeError, KeyError, UnicodeDecodeError):
                        logger.warning("Evento IA rechazado por formato")
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        return
                    try:
                        status = register_ia_event(event)
                        if status == "UNKNOWN_CASE":
                            logger.warning("Evento IA para un caso inexistente; descartado")
                        channel.basic_ack(delivery_tag=method.delivery_tag)
                        self.stdout.write(f"Evento IA recibido: {status}")
                    except Exception:
                        logger.exception("Error al persistir aviso IA; se reintentará")
                        time.sleep(4)
                        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                    finally:
                        close_old_connections()

                ch.basic_consume(queue=QUEUE, on_message_callback=consume, auto_ack=False)
                ch.start_consuming()
            except (OSError, pika.exceptions.AMQPError):
                logger.warning("Sin conexión RabbitMQ para avisos; reintentando")
                time.sleep(4)
            finally:
                if conn is not None and conn.is_open:
                    conn.close()
