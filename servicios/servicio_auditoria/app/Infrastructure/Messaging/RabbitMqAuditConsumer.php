<?php

namespace App\Infrastructure\Messaging;


use App\Application\Audit\StoreAuditEvent;

use Illuminate\Support\Facades\Log;

use InvalidArgumentException;
use JsonException;

use PhpAmqpLib\Connection\AMQPStreamConnection;

use PhpAmqpLib\Message\AMQPMessage;

use PhpAmqpLib\Wire\AMQPTable;

use Throwable;


final class RabbitMqAuditConsumer
{
    public function __construct(

        private readonly
        StoreAuditEvent $storeAuditEvent

    ) {
    }


    // ======================================================
    // INICIAR CONSUMIDOR
    // ======================================================

    public function run(): int
    {
        $connection = null;
        $channel = null;


        try {

            $connection = (
                $this->createConnection()
            );


            $channel = (
                $connection->channel()
            );


            // ==============================================
            // TOPOLOGÍA
            // ==============================================

            $this->declareTopology(
                $channel
            );


            // ==============================================
            // PROCESAR UN EVENTO POR VEZ
            // ==============================================

            $channel->basic_qos(

                0,

                1,

                false

            );


            $queue = (
                config(
                    'audit.queue'
                )
            );


            Log::info(

                'Worker de Auditoría iniciado.',

                [
                    'queue' =>
                        $queue,

                    'binding' =>
                        config(
                            'audit.binding'
                        ),
                ]

            );


            // ==============================================
            // CONSUMIDOR
            // ==============================================

            $channel->basic_consume(

                $queue,

                '',

                false,

                false,

                false,

                false,

                function (
                    AMQPMessage $message
                ): void {

                    $this->handleMessage(
                        $message
                    );

                }

            );


            // ==============================================
            // LOOP
            // ==============================================

            while (
                $channel->is_consuming()
            ) {

                $channel->wait();

            }


            return 0;

        }

        catch (
            Throwable $error
        ) {

            Log::error(

                'El worker de Auditoría se detuvo.',

                [
                    'error' =>
                        $error->getMessage(),

                    'tipo' =>
                        get_class(
                            $error
                        ),
                ]

            );


            throw $error;

        }

        finally {

            if (
                $channel !== null
            ) {

                try {

                    $channel->close();

                }

                catch (
                    Throwable
                ) {
                }

            }


            if (
                $connection !== null
            ) {

                try {

                    $connection->close();

                }

                catch (
                    Throwable
                ) {
                }

            }

        }
    }


    // ======================================================
    // PROCESAR MENSAJE
    // ======================================================

    private function handleMessage(
        AMQPMessage $message
    ): void {

        $channel = (
            $message->getChannel()
        );


        $deliveryTag = (
            $message->getDeliveryTag()
        );


        $routingKey = (

            $message->getRoutingKey()

            ?: 'unknown.audit.v1'

        );


        try {

            // ==============================================
            // JSON
            // ==============================================

            $payload = json_decode(

                $message->getBody(),

                true,

                512,

                JSON_THROW_ON_ERROR

            );


            if (
                !is_array(
                    $payload
                )
            ) {

                throw new InvalidArgumentException(

                    'El evento debe contener un objeto JSON.'

                );

            }


            // ==============================================
            // CASO DE USO
            // ==============================================

            $resultado = (

                $this
                ->storeAuditEvent
                ->execute(
                    $payload
                )

            );


            // ==============================================
            // ACK
            // ==============================================

            $channel->basic_ack(
                $deliveryTag
            );


            Log::info(

                'Evento de Auditoría procesado.',

                [
                    'event_id' =>
                        $resultado[
                            'event_id'
                        ]
                        ?? null,

                    'stored' =>
                        $resultado[
                            'stored'
                        ]
                        ?? null,

                    'duplicate' =>
                        $resultado[
                            'duplicate'
                        ]
                        ?? null,

                    'routing_key' =>
                        $routingKey,
                ]

            );

        }

        // ==================================================
        // PAYLOAD INVÁLIDO
        // ==================================================

        catch (
            JsonException
            |
            InvalidArgumentException $error
        ) {

            Log::warning(

                (
                    'Evento inválido. '
                    . 'Se enviará directamente a DLQ.'
                ),

                [
                    'routing_key' =>
                        $routingKey,

                    'error' =>
                        $error->getMessage(),
                ]

            );


            try {

                $this->sendToDlq(

                    original:
                        $message,

                    routingKey:
                        $routingKey,

                    error:
                        $error->getMessage()

                );


                $channel->basic_ack(
                    $deliveryTag
                );

            }

            catch (
                Throwable $dlqError
            ) {

                Log::error(

                    'No se pudo enviar el evento inválido a DLQ.',

                    [
                        'error' =>
                            $dlqError
                            ->getMessage(),
                    ]

                );


                $channel->basic_nack(

                    $deliveryTag,

                    false,

                    true

                );

            }

        }

        // ==================================================
        // ERROR TEMPORAL
        // ==================================================

        catch (
            Throwable $error
        ) {

            $retryCount = (
                $this->getRetryCount(
                    $message
                )
            );


            $maxRetries = (
                (int) config(
                    'audit.max_retries',
                    3
                )
            );


            // ==============================================
            // REINTENTAR
            // ==============================================

            if (
                $retryCount
                <
                $maxRetries
            ) {

                $nuevoIntento = (
                    $retryCount
                    +
                    1
                );


                Log::warning(

                    'Evento de Auditoría será reintentado.',

                    [
                        'routing_key' =>
                            $routingKey,

                        'intento' =>
                            $nuevoIntento,

                        'maximo' =>
                            $maxRetries,

                        'error' =>
                            $error->getMessage(),
                    ]

                );


                try {

                    $this->sendToRetry(

                        original:
                            $message,

                        routingKey:
                            $routingKey,

                        retryCount:
                            $nuevoIntento

                    );


                    $channel->basic_ack(
                        $deliveryTag
                    );


                    return;

                }

                catch (
                    Throwable $retryError
                ) {

                    Log::error(

                        (
                            'No se pudo publicar '
                            . 'el mensaje de reintento.'
                        ),

                        [
                            'error' =>
                                $retryError
                                ->getMessage(),
                        ]

                    );


                    $channel->basic_nack(

                        $deliveryTag,

                        false,

                        true

                    );


                    return;

                }

            }


            // ==============================================
            // AGOTÓ REINTENTOS
            // ==============================================

            Log::error(

                (
                    'Evento de Auditoría agotó '
                    . 'todos los reintentos.'
                ),

                [
                    'routing_key' =>
                        $routingKey,

                    'intentos' =>
                        $retryCount,

                    'error' =>
                        $error->getMessage(),
                ]

            );


            try {

                $this->sendToDlq(

                    original:
                        $message,

                    routingKey:
                        $routingKey,

                    error:
                        $error->getMessage()

                );


                $channel->basic_ack(
                    $deliveryTag
                );

            }

            catch (
                Throwable $dlqError
            ) {

                Log::error(

                    (
                        'No fue posible enviar '
                        . 'el mensaje a DLQ.'
                    ),

                    [
                        'error' =>
                            $dlqError
                            ->getMessage(),
                    ]

                );


                $channel->basic_nack(

                    $deliveryTag,

                    false,

                    true

                );

            }

        }
    }


    // ======================================================
    // CONEXIÓN RABBITMQ
    // ======================================================

    private function createConnection():
        AMQPStreamConnection
    {

        return new AMQPStreamConnection(

            config(
                'audit.rabbitmq.host'
            ),

            (int) config(
                'audit.rabbitmq.port'
            ),

            config(
                'audit.rabbitmq.user'
            ),

            config(
                'audit.rabbitmq.password'
            ),

            config(
                'audit.rabbitmq.vhost'
            ),

            false,

            'AMQPLAIN',

            null,

            'en_US',

            (float) config(
                'audit.rabbitmq.connection_timeout',
                3
            ),

            (float) config(
                'audit.rabbitmq.read_write_timeout',
                60
            ),

            null,

            false,

            (int) config(
                'audit.rabbitmq.heartbeat',
                30
            )

        );
    }


    // ======================================================
    // TOPOLOGÍA
    // ======================================================

    private function declareTopology(
        $channel
    ): void {

        $exchange = (
            config(
                'audit.exchange'
            )
        );


        $queue = (
            config(
                'audit.queue'
            )
        );


        $binding = (
            config(
                'audit.binding'
            )
        );


        $retryExchange = (
            config(
                'audit.retry_exchange'
            )
        );


        $retryQueue = (
            config(
                'audit.retry_queue'
            )
        );


        $dlxExchange = (
            config(
                'audit.dlx_exchange'
            )
        );


        $dlq = (
            config(
                'audit.dlq'
            )
        );


        // ==================================================
        // EXCHANGE PRINCIPAL
        // ==================================================

        $channel->exchange_declare(

            $exchange,

            'topic',

            false,

            true,

            false

        );


        // ==================================================
        // COLA PRINCIPAL
        // ==================================================

        $channel->queue_declare(

            $queue,

            false,

            true,

            false,

            false

        );


        $channel->queue_bind(

            $queue,

            $exchange,

            $binding

        );


        // ==================================================
        // EXCHANGE RETRY
        // ==================================================

        $channel->exchange_declare(

            $retryExchange,

            'topic',

            false,

            true,

            false

        );


        // ==================================================
        // RETRY QUEUE
        //
        // Cuando vence el TTL vuelve automáticamente al
        // exchange principal manteniendo routing key.
        // ==================================================

        $retryArguments = (

            new AMQPTable([

                'x-message-ttl' =>

                    (int) config(

                        'audit.retry_delay_ms',

                        5000

                    ),

                'x-dead-letter-exchange' =>

                    $exchange,

            ])

        );


        $channel->queue_declare(

            $retryQueue,

            false,

            true,

            false,

            false,

            false,

            $retryArguments

        );


        $channel->queue_bind(

            $retryQueue,

            $retryExchange,

            '*.audit.v1'

        );


        // ==================================================
        // DEAD LETTER EXCHANGE
        // ==================================================

        $channel->exchange_declare(

            $dlxExchange,

            'topic',

            false,

            true,

            false

        );


        // ==================================================
        // DEAD LETTER QUEUE
        // ==================================================

        $channel->queue_declare(

            $dlq,

            false,

            true,

            false,

            false

        );


        $channel->queue_bind(

            $dlq,

            $dlxExchange,

            '#'

        );
    }


    // ======================================================
    // OBTENER RETRY COUNT
    // ======================================================

    private function getRetryCount(
        AMQPMessage $message
    ): int {

        try {

            $headers = (

                $message->get(
                    'application_headers'
                )

            );


            if (
                !$headers
                instanceof
                AMQPTable
            ) {

                return 0;

            }


            $data = (
                $headers
                ->getNativeData()
            );


            return (

                (int) (

                    $data[
                        'x-retry-count'
                    ]

                    ?? 0

                )

            );

        }

        catch (
            Throwable
        ) {

            return 0;

        }
    }


    // ======================================================
    // PUBLICAR REINTENTO
    // ======================================================

    private function sendToRetry(

        AMQPMessage $original,

        string $routingKey,

        int $retryCount

    ): void {

        $channel = (
            $original->getChannel()
        );


        $properties = [

            'content_type' =>
                'application/json',

            'content_encoding' =>
                'utf-8',

            'delivery_mode' =>
                AMQPMessage::
                    DELIVERY_MODE_PERSISTENT,

            'type' =>
                'audit.event.v1',

            'application_headers' =>
                new AMQPTable([

                    'x-retry-count' =>
                        $retryCount,

                ]),

        ];


        $messageId = (
            $this->getMessageId(
                $original
            )
        );


        if (
            $messageId !== null
        ) {

            $properties[
                'message_id'
            ] = (
                $messageId
            );

        }


        $retryMessage = (

            new AMQPMessage(

                $original->getBody(),

                $properties

            )

        );


        $channel->basic_publish(

            $retryMessage,

            config(
                'audit.retry_exchange'
            ),

            $routingKey

        );
    }


    // ======================================================
    // PUBLICAR EN DLQ
    // ======================================================

    private function sendToDlq(

        AMQPMessage $original,

        string $routingKey,

        string $error

    ): void {

        $channel = (
            $original->getChannel()
        );


        $properties = [

            'content_type' =>
                'application/json',

            'content_encoding' =>
                'utf-8',

            'delivery_mode' =>
                AMQPMessage::
                    DELIVERY_MODE_PERSISTENT,

            'type' =>
                'audit.event.dlq.v1',

            'application_headers' =>
                new AMQPTable([

                    'audit_error' =>
                        $error,

                    'original_routing_key' =>
                        $routingKey,

                ]),

        ];


        $messageId = (
            $this->getMessageId(
                $original
            )
        );


        if (
            $messageId !== null
        ) {

            $properties[
                'message_id'
            ] = (
                $messageId
            );

        }


        $dlqMessage = (

            new AMQPMessage(

                $original->getBody(),

                $properties

            )

        );


        $channel->basic_publish(

            $dlqMessage,

            config(
                'audit.dlx_exchange'
            ),

            $routingKey

        );
    }


    // ======================================================
    // MESSAGE ID
    // ======================================================

    private function getMessageId(
        AMQPMessage $message
    ): ?string {

        try {

            $value = (
                $message->get(
                    'message_id'
                )
            );


            if (
                $value === null
            ) {

                return null;

            }


            $value = trim(
                (string) $value
            );


            return (
                $value !== ''
                    ? $value
                    : null
            );

        }

        catch (
            Throwable
        ) {

            return null;

        }
    }
}