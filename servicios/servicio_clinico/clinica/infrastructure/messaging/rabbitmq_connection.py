import os

import pika


class RabbitMQConnectionFactory:
    @staticmethod
    def create():
        host = os.getenv(
            "RABBITMQ_HOST",
            "rabbitmq",
        )

        port = int(
            os.getenv(
                "RABBITMQ_PORT",
                "5672",
            )
        )

        user = os.getenv(
            "RABBITMQ_USER",
            "guest",
        )

        password = os.getenv(
            "RABBITMQ_PASSWORD",
            "guest",
        )

        virtual_host = os.getenv(
            "RABBITMQ_VHOST",
            "/",
        )

        credentials = (
            pika.PlainCredentials(
                user,
                password,
            )
        )

        parameters = (
            pika.ConnectionParameters(
                host=host,
                port=port,
                virtual_host=virtual_host,
                credentials=credentials,
                heartbeat=30,
                blocked_connection_timeout=10,
                connection_attempts=3,
                retry_delay=2,
            )
        )

        return (
            pika.BlockingConnection(
                parameters
            )
        )