<?php

return [

    // ======================================================
    // RABBITMQ
    // ======================================================

    'rabbitmq' => [

        'host' => env(
            'RABBITMQ_HOST',
            'rabbitmq'
        ),

        'port' => (int) env(
            'RABBITMQ_PORT',
            5672
        ),

        'user' => env(
            'RABBITMQ_USER',
            'guest'
        ),

        'password' => env(
            'RABBITMQ_PASSWORD',
            'guest'
        ),

        'vhost' => env(
            'RABBITMQ_VHOST',
            '/'
        ),

        'heartbeat' => (int) env(
            'RABBITMQ_HEARTBEAT',
            30
        ),

        'connection_timeout' => (float) env(
            'RABBITMQ_CONNECTION_TIMEOUT',
            3
        ),

        'read_write_timeout' => (float) env(
            'RABBITMQ_READ_WRITE_TIMEOUT',
            60
        ),

    ],


    // ======================================================
    // EXCHANGE PRINCIPAL
    // ======================================================

    'exchange' => env(
        'AUDIT_EXCHANGE',
        'osteosarcoma.events'
    ),

    'queue' => env(
        'AUDIT_QUEUE',
        'auditoria.eventos.v1'
    ),

    'binding' => env(
        'AUDIT_BINDING',
        '*.audit.v1'
    ),


    // ======================================================
    // REINTENTOS
    // ======================================================

    'retry_exchange' => env(
        'AUDIT_RETRY_EXCHANGE',
        'osteosarcoma.audit.retry'
    ),

    'retry_queue' => env(
        'AUDIT_RETRY_QUEUE',
        'auditoria.eventos.retry.v1'
    ),

    'retry_delay_ms' => (int) env(
        'AUDIT_RETRY_DELAY_MS',
        5000
    ),

    'max_retries' => (int) env(
        'AUDIT_MAX_RETRIES',
        3
    ),


    // ======================================================
    // DEAD LETTER QUEUE
    // ======================================================

    'dlx_exchange' => env(
        'AUDIT_DLX_EXCHANGE',
        'osteosarcoma.audit.dlx'
    ),

    'dlq' => env(
        'AUDIT_DLQ',
        'auditoria.eventos.dlq.v1'
    ),

];