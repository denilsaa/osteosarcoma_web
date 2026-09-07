import json
import os
import uuid
from datetime import (
    datetime,
    timezone,
)

import pika

from clinica.application.dto import (
    AuditEventDTO,
)
from clinica.application.ports import (
    AuditEventPort,
)

from .rabbitmq_connection import (
    RabbitMQConnectionFactory,
)


class RabbitMQAuditEventPublisher(
    AuditEventPort
):
    """
    Adaptador RabbitMQ del puerto AuditEventPort.

    Responsabilidades:
    - recibir DTOs propios de Application;
    - traducirlos al contrato de integración
      esperado por servicio_auditoria;
    - publicar mediante RabbitMQ.

    Este servicio NO:
    - almacena auditoría;
    - consulta PostgreSQL de Auditoría;
    - conoce los repositorios internos de Auditoría.
    """

    def __init__(
        self,
    ):
        self.exchange = os.getenv(
            "AUDIT_EXCHANGE",
            "osteosarcoma.events",
        )

        self.routing_key = os.getenv(
            "AUDIT_ROUTING_KEY",
            "clinico.audit.v1",
        )

    # ==========================================================
    # DETALLE ADICIONAL
    # ==========================================================

    @staticmethod
    def _build_detail(
        event: AuditEventDTO,
    ) -> dict:

        detail = {
            "event_version": 1,
        }

        if event.detail:
            detail.update(
                event.detail
            )

        return detail

    # ==========================================================
    # CAMBIOS
    # ==========================================================

    @staticmethod
    def _build_changes(
        event: AuditEventDTO,
    ) -> list[dict]:
        """
        Application:
            field
            old_value
            new_value

        Contrato Auditoría:
            campo
            valor_anterior
            valor_nuevo
        """

        return [
            {
                "campo":
                    change.field,

                "valor_anterior":
                    change.old_value,

                "valor_nuevo":
                    change.new_value,
            }
            for change
            in event.changes
        ]

    # ==========================================================
    # ACTOR
    # ==========================================================

    @staticmethod
    def _build_actor(
        event: AuditEventDTO,
    ) -> dict:

        user_id = None

        if event.actor.usuario_uuid:
            user_id = str(
                event.actor.usuario_uuid
            )

        return {
            # Nombres exigidos por AuditEvent.php
            "user_id":
                user_id,

            "name":
                event.actor.nombre,

            "role":
                event.actor.rol,
        }

    # ==========================================================
    # CONTEXTO HTTP
    # ==========================================================

    @staticmethod
    def _build_context(
        event: AuditEventDTO,
    ) -> dict:

        return {
            # Nombres exigidos por AuditEvent.php
            "ip_address":
                event.actor.ip,

            "user_agent":
                event.actor.user_agent,
        }

    # ==========================================================
    # PAYLOAD DE INTEGRACIÓN
    # ==========================================================

    def _build_payload(
        self,
        event: AuditEventDTO,
        event_id: str,
    ) -> dict:

        return {
            # ==================================================
            # IDENTIDAD DEL EVENTO
            # ==================================================

            "event_id":
                event_id,

            "event_version":
                1,

            "occurred_at":
                datetime.now(
                    timezone.utc
                ).isoformat(),

            # ==================================================
            # CLASIFICACIÓN
            # ==================================================

            "service":
                event.service,

            "module":
                event.module,

            "action":
                event.action,

            "result":
                event.result,

            # ==================================================
            # ACTOR
            #
            # Contrato esperado por servicio_auditoria:
            # actor.user_id
            # actor.name
            # actor.role
            # ==================================================

            "actor":
                self._build_actor(
                    event
                ),

            # ==================================================
            # ENTIDAD
            # ==================================================

            "entity": {
                "type":
                    event.entity_type,

                "id":
                    event.entity_id,
            },

            # ==================================================
            # CONTEXTO HTTP
            #
            # Contrato esperado:
            # context.ip_address
            # context.user_agent
            # ==================================================

            "context":
                self._build_context(
                    event
                ),

            # ==================================================
            # CORRELACIÓN
            # ==================================================

            "correlation_id":
                event.correlation_id,

            # ==================================================
            # DESCRIPCIÓN / MOTIVO
            #
            # AuditEvent.php los consume en primer nivel.
            # ==================================================

            "description":
                event.description,

            "reason":
                event.reason,

            # ==================================================
            # DETALLE EXTRA
            # ==================================================

            "detail":
                self._build_detail(
                    event
                ),

            # ==================================================
            # CAMBIOS
            # ==================================================

            "changes":
                self._build_changes(
                    event
                ),
        }

    # ==========================================================
    # PUBLICAR
    # ==========================================================

    def publish(
        self,
        event: AuditEventDTO,
    ) -> bool:

        connection = None

        try:
            event_id = str(
                uuid.uuid4()
            )

            payload = (
                self._build_payload(
                    event,
                    event_id,
                )
            )

            connection = (
                RabbitMQConnectionFactory
                .create()
            )

            channel = (
                connection.channel()
            )

            channel.exchange_declare(
                exchange=
                    self.exchange,

                exchange_type=
                    "topic",

                durable=True,
            )

            channel.basic_publish(
                exchange=
                    self.exchange,

                routing_key=
                    self.routing_key,

                body=
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                    ).encode(
                        "utf-8"
                    ),

                properties=
                    pika.BasicProperties(
                        content_type=
                            "application/json",

                        content_encoding=
                            "utf-8",

                        delivery_mode=
                            2,

                        message_id=
                            event_id,

                        correlation_id=
                            event.correlation_id,

                        timestamp=
                            int(
                                datetime.now(
                                    timezone.utc
                                ).timestamp()
                            ),
                    ),
            )

            return True

        except Exception as exc:
            print(
                "[CLINICO][EVENTOS] "
                "No fue posible publicar "
                "el evento de integración: "
                f"{exc}"
            )

            return False

        finally:
            if (
                connection is not None
                and connection.is_open
            ):
                connection.close()