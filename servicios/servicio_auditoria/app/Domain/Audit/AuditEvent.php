<?php

namespace App\Domain\Audit;

use InvalidArgumentException;


final class AuditEvent
{
    public function __construct(

        public readonly string $eventId,

        public readonly int $eventVersion,

        public readonly string $occurredAt,

        public readonly string $service,

        public readonly string $module,

        public readonly string $action,

        public readonly string $result,

        public readonly ?string $actorUserId,

        public readonly ?string $actorName,

        public readonly ?string $actorRole,

        public readonly ?string $entityType,

        public readonly ?string $entityId,

        public readonly ?string $correlationId,

        public readonly ?string $ipAddress,

        public readonly ?string $userAgent,

        public readonly ?string $description,

        public readonly ?string $reason,

        public readonly array $detail,

        public readonly array $changes,

    ) {
    }


    // ======================================================
    // CREAR DESDE PAYLOAD
    // ======================================================

    public static function fromArray(
        array $payload
    ): self {

        $eventId = trim(
            (string) (
                $payload['event_id']
                ?? ''
            )
        );


        if (
            !self::isUuid(
                $eventId
            )
        ) {

            throw new InvalidArgumentException(
                'event_id debe ser un UUID válido.'
            );

        }


        $eventVersion = (int) (
            $payload['event_version']
            ?? 0
        );


        if (
            $eventVersion !== 1
        ) {

            throw new InvalidArgumentException(
                'Versión de evento no soportada.'
            );

        }


        $service = self::requiredCode(
            $payload['service']
            ?? null,
            'service'
        );


        $module = self::requiredCode(
            $payload['module']
            ?? null,
            'module'
        );


        $action = self::requiredCode(
            $payload['action']
            ?? null,
            'action'
        );


        $result = self::requiredCode(
            $payload['result']
            ?? null,
            'result'
        );


        $actor = (
            is_array(
                $payload['actor']
                ?? null
            )
                ? $payload['actor']
                : []
        );


        $entity = (
            is_array(
                $payload['entity']
                ?? null
            )
                ? $payload['entity']
                : []
        );


        $context = (
            is_array(
                $payload['context']
                ?? null
            )
                ? $payload['context']
                : []
        );


        return new self(

            eventId:
                $eventId,

            eventVersion:
                $eventVersion,

            occurredAt:
                trim(
                    (string) (
                        $payload['occurred_at']
                        ?? gmdate('c')
                    )
                ),

            service:
                $service,

            module:
                $module,

            action:
                $action,

            result:
                $result,

            actorUserId:
                self::optionalText(
                    $actor['user_id']
                    ?? null
                ),

            actorName:
                self::optionalText(
                    $actor['name']
                    ?? null
                ),

            actorRole:
                self::optionalText(
                    $actor['role']
                    ?? null
                ),

            entityType:
                self::optionalUpper(
                    $entity['type']
                    ?? null
                ),

            entityId:
                self::optionalText(
                    $entity['id']
                    ?? null
                ),

            correlationId:
                self::optionalText(
                    $payload['correlation_id']
                    ?? null
                ),

            ipAddress:
                self::optionalText(
                    $context['ip_address']
                    ?? null
                ),

            userAgent:
                self::optionalText(
                    $context['user_agent']
                    ?? null
                ),

            description:
                self::optionalText(
                    $payload['description']
                    ?? null
                ),

            reason:
                self::optionalText(
                    $payload['reason']
                    ?? null
                ),

            detail:
                (
                    is_array(
                        $payload['detail']
                        ?? null
                    )
                        ? $payload['detail']
                        : []
                ),

            changes:
                (
                    is_array(
                        $payload['changes']
                        ?? null
                    )
                        ? $payload['changes']
                        : []
                ),

        );
    }


    // ======================================================
    // CÓDIGO OBLIGATORIO
    // ======================================================

    private static function requiredCode(
        mixed $value,
        string $field
    ): string {

        $value = strtoupper(
            trim(
                (string) $value
            )
        );


        if (
            $value === ''
        ) {

            throw new InvalidArgumentException(
                "El campo {$field} es obligatorio."
            );

        }


        return $value;
    }


    // ======================================================
    // TEXTO OPCIONAL
    // ======================================================

    private static function optionalText(
        mixed $value
    ): ?string {

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


    // ======================================================
    // CÓDIGO OPCIONAL
    // ======================================================

    private static function optionalUpper(
        mixed $value
    ): ?string {

        $value = self::optionalText(
            $value
        );


        if (
            $value === null
        ) {

            return null;

        }


        return strtoupper(
            $value
        );
    }


    // ======================================================
    // UUID
    // ======================================================

    private static function isUuid(
        string $value
    ): bool {

        return (

            preg_match(

                '/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$/',

                $value

            )

            === 1

        );
    }
}