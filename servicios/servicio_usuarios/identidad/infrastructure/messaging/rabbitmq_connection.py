import os

import pika


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

RABBITMQ_HOST = os.getenv(
    "RABBITMQ_HOST",
    "rabbitmq",
)

RABBITMQ_PORT = int(
    os.getenv(
        "RABBITMQ_PORT",
        "5672",
    )
)

RABBITMQ_USER = os.getenv(
    "RABBITMQ_USER",
    "guest",
)

RABBITMQ_PASSWORD = os.getenv(
    "RABBITMQ_PASSWORD",
    "guest",
)

RABBITMQ_VHOST = os.getenv(
    "RABBITMQ_VHOST",
    "/",
)


# ==========================================================
# CONEXIÓN
# ==========================================================

def crear_conexion_rabbitmq():
    """
    Crea una conexión de corta duración.

    La operación principal del sistema NO depende
    de que Auditoría esté disponible.

    RabbitMQ actúa como intermediario.
    """

    credentials = (
        pika.PlainCredentials(
            username=
                RABBITMQ_USER,

            password=
                RABBITMQ_PASSWORD,
        )
    )


    parameters = (
        pika.ConnectionParameters(

            host=
                RABBITMQ_HOST,

            port=
                RABBITMQ_PORT,

            virtual_host=
                RABBITMQ_VHOST,

            credentials=
                credentials,

            connection_attempts=
                1,

            retry_delay=
                0,

            socket_timeout=
                2,

            blocked_connection_timeout=
                2,

            heartbeat=
                30,

        )
    )


    return (
        pika.BlockingConnection(
            parameters
        )
    )