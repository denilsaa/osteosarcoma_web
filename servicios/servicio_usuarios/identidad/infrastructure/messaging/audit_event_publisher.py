import json
import logging
import os

import pika


from identidad.domain.events.audit_event import (
    AuditEvent,
)

from identidad.infrastructure.messaging.rabbitmq_connection import (
    crear_conexion_rabbitmq,
)


logger = logging.getLogger(
    __name__
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

AUDIT_EXCHANGE = os.getenv(

    "AUDIT_EXCHANGE",

    "osteosarcoma.events",

)


# ==========================================================
# PUBLISHER
# ==========================================================

class AuditEventPublisher:
    """
    Publica eventos de auditoría en RabbitMQ.

    Exchange:
        osteosarcoma.events

    Tipo:
        topic

    Ejemplo routing key:
        usuarios.audit.v1
    """


    def publish(
        self,
        event: AuditEvent,
    ):

        connection = None


        try:

            connection = (
                crear_conexion_rabbitmq()
            )


            channel = (
                connection.channel()
            )


            # ==============================================
            # EXCHANGE DURABLE
            # ==============================================

            channel.exchange_declare(

                exchange=
                    AUDIT_EXCHANGE,

                exchange_type=
                    "topic",

                durable=
                    True,

                auto_delete=
                    False,

            )


            # ==============================================
            # CONFIRMACIÓN DEL BROKER
            # ==============================================

            channel.confirm_delivery()


            body = (

                json.dumps(

                    event.to_dict(),

                    ensure_ascii=False,

                    default=str,

                )

                .encode(
                    "utf-8"
                )

            )


            properties = (
                pika.BasicProperties(

                    content_type=
                        "application/json",

                    content_encoding=
                        "utf-8",

                    delivery_mode=
                        pika.DeliveryMode.Persistent,

                    message_id=
                        event.event_id,

                    type=
                        "audit.event.v1",

                    headers={
                        "event_version":
                            event.event_version,

                        "x-retry-count":
                            0,
                    },

                )
            )


            # ==============================================
            # PUBLICAR
            # ==============================================

            channel.basic_publish(

                exchange=
                    AUDIT_EXCHANGE,

                routing_key=
                    event.routing_key,

                body=
                    body,

                properties=
                    properties,

                mandatory=
                    False,

            )


            logger.info(

                (
                    "Evento de auditoría %s "
                    "publicado con routing key %s"
                ),

                event.event_id,

                event.routing_key,

            )


            return {

                "ok":
                    True,

                "transport":
                    "rabbitmq",

                "event_id":
                    event.event_id,

                "routing_key":
                    event.routing_key,

            }


        except Exception as error:

            logger.warning(

                (
                    "No fue posible publicar "
                    "evento de Auditoría "
                    "en RabbitMQ: %s"
                ),

                error,

            )


            return {

                "ok":
                    False,

                "transport":
                    "rabbitmq",

                "event_id":
                    event.event_id,

                "error":
                    str(
                        error
                    ),

            }


        finally:

            if (
                connection
                and
                connection.is_open
            ):

                try:

                    connection.close()

                except Exception:

                    pass