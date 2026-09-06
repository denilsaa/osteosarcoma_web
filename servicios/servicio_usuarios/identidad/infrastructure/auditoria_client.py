"""
Fachada temporal de compatibilidad para Auditoría.

IMPORTANTE:

Este módulo YA NO realiza llamadas HTTP a
servicio_auditoria.

Ahora transforma la llamada existente en un
AuditEvent y lo publica en RabbitMQ.

Esto permite migrar gradualmente las vistas
sin romper la funcionalidad existente.
"""


from identidad.domain.events.audit_event import (
    AuditEvent,
)

from identidad.infrastructure.messaging.audit_event_publisher import (
    AuditEventPublisher,
)


# ==========================================================
# PUBLISHER
# ==========================================================

_publisher = (
    AuditEventPublisher()
)


# ==========================================================
# REGISTRAR EVENTO
# ==========================================================

def registrar_evento_auditoria(
    *,
    actor_usuario_uuid=None,
    actor_nombre=None,
    actor_rol=None,

    servicio,
    modulo,
    accion,
    resultado,

    entidad_tipo=None,
    entidad_id=None,

    correlation_id=None,

    direccion_ip=None,
    user_agent=None,

    descripcion=None,
    motivo=None,

    detalle_json=None,
    cambios=None,
):
    """
    Publica un evento de auditoría mediante RabbitMQ.

    Mantiene la misma firma que utilizaban
    las vistas actuales de servicio_usuarios.
    """

    try:

        event = AuditEvent.create(

            service=
                servicio,

            module=
                modulo,

            action=
                accion,

            result=
                resultado,

            actor_user_id=
                actor_usuario_uuid,

            actor_name=
                actor_nombre,

            actor_role=
                actor_rol,

            entity_type=
                entidad_tipo,

            entity_id=
                entidad_id,

            correlation_id=
                correlation_id,

            ip_address=
                direccion_ip,

            user_agent=
                user_agent,

            description=
                descripcion,

            reason=
                motivo,

            detail=(
                detalle_json
                if isinstance(
                    detalle_json,
                    dict,
                )
                else {}
            ),

            changes=(
                cambios
                if isinstance(
                    cambios,
                    list,
                )
                else []
            ),

        )


        return (
            _publisher.publish(
                event
            )
        )


    except Exception as error:

        # Auditoría nunca debe romper
        # la operación funcional principal.

        return {

            "ok":
                False,

            "transport":
                "rabbitmq",

            "error":
                str(
                    error
                ),

        }