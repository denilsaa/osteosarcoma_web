import os

import pika
from django.db import connection
from django.http import JsonResponse


def comprobar_postgresql():
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1;")
        cursor.fetchone()


def comprobar_rabbitmq():
    credenciales = pika.PlainCredentials(
        os.environ["RABBITMQ_USER"],
        os.environ["RABBITMQ_PASSWORD"],
    )

    parametros = pika.ConnectionParameters(
        host=os.environ["RABBITMQ_HOST"],
        port=int(os.environ.get("RABBITMQ_PORT", "5672")),
        credentials=credenciales,
        connection_attempts=3,
        retry_delay=1,
    )

    conexion = pika.BlockingConnection(parametros)

    canal = conexion.channel()

    canal.queue_declare(
        queue="analisis_radiografia",
        durable=True,
    )

    conexion.close()


def health_check(request):
    estado_bd = "desconectada"
    estado_rabbitmq = "desconectado"

    try:
        comprobar_postgresql()
        estado_bd = "conectada"
    except Exception:
        pass

    try:
        comprobar_rabbitmq()
        estado_rabbitmq = "conectado"
    except Exception:
        pass

    correcto = (
        estado_bd == "conectada"
        and estado_rabbitmq == "conectado"
    )

    return JsonResponse(
        {
            "servicio": "servicio_ia",
            "estado": "ok" if correcto else "error",
            "base_datos": estado_bd,
            "rabbitmq": estado_rabbitmq,
        },
        status=200 if correcto else 503,
    )