<?php

namespace App\Infrastructure\Persistence;


use App\Domain\Audit\AuditEvent;

use App\Domain\Audit\AuditEventRepository;


use Carbon\Carbon;

use DomainException;


use Illuminate\Database\QueryException;

use Illuminate\Support\Facades\DB;


final class PostgresAuditEventRepository
    implements AuditEventRepository
{

    public function store(
        AuditEvent $event
    ): bool {

        // ==================================================
        // IDEMPOTENCIA
        // ==================================================

        $existe = (

            DB::table(
                'eventos_auditoria'
            )

            ->where(
                'id_evento',
                $event->eventId
            )

            ->exists()

        );


        if (
            $existe
        ) {

            return false;

        }


        // ==================================================
        // SERVICIO
        // ==================================================

        $servicio = (

            DB::table(
                'servicios_auditados'
            )

            ->where(
                'codigo',
                $event->service
            )

            ->where(
                'activo',
                true
            )

            ->first()

        );


        if (
            !$servicio
        ) {

            throw new DomainException(

                "Servicio {$event->service} "
                . 'no registrado en Auditoría.'

            );

        }


        // ==================================================
        // MÓDULO
        // ==================================================

        $modulo = (

            DB::table(
                'modulos_auditoria'
            )

            ->where(
                'id_servicio',
                $servicio->id_servicio
            )

            ->where(
                'codigo',
                $event->module
            )

            ->where(
                'activo',
                true
            )

            ->first()

        );


        if (
            !$modulo
        ) {

            throw new DomainException(

                "Módulo {$event->module} "
                . 'no registrado para '
                . "{$event->service}."

            );

        }


        // ==================================================
        // ACCIÓN
        // ==================================================

        $accion = (

            DB::table(
                'tipos_accion_auditoria'
            )

            ->where(
                'codigo',
                $event->action
            )

            ->first()

        );


        if (
            !$accion
        ) {

            throw new DomainException(

                "Acción {$event->action} "
                . 'no registrada en Auditoría.'

            );

        }


        // ==================================================
        // RESULTADO
        // ==================================================

        $resultado = (

            DB::table(
                'resultados_auditoria'
            )

            ->where(
                'codigo',
                $event->result
            )

            ->first()

        );


        if (
            !$resultado
        ) {

            throw new DomainException(

                "Resultado {$event->result} "
                . 'no registrado en Auditoría.'

            );

        }


        // ==================================================
        // DETALLE
        // ==================================================

        $detalle = (
            $event->detail
        );


        if (
            $event->actorName
            !==
            null
        ) {

            $detalle[
                'actor_nombre'
            ] = (
                $event->actorName
            );

        }


        if (
            $event->actorRole
            !==
            null
        ) {

            $detalle[
                'actor_rol'
            ] = (
                $event->actorRole
            );

        }


        if (
            $event->description
            !==
            null
        ) {

            $detalle[
                'descripcion'
            ] = (
                $event->description
            );

        }


        if (
            $event->reason
            !==
            null
        ) {

            $detalle[
                'motivo'
            ] = (
                $event->reason
            );

        }


        $detalle[
            'event_version'
        ] = (
            $event->eventVersion
        );


        // ==================================================
        // TRANSACCIÓN
        // ==================================================

        try {

            DB::transaction(

                function () use (
                    $event,
                    $servicio,
                    $modulo,
                    $accion,
                    $resultado,
                    $detalle
                ) {

                    // ======================================
                    // EVENTO
                    // ======================================

                    DB::table(
                        'eventos_auditoria'
                    )
                    ->insert([

                        'id_evento' =>
                            $event->eventId,

                        'actor_usuario_uuid' =>
                            $event->actorUserId,

                        'id_servicio' =>
                            $servicio->id_servicio,

                        'id_modulo' =>
                            $modulo->id_modulo,

                        'id_tipo_accion' =>
                            $accion->id_tipo_accion,

                        'id_resultado' =>
                            $resultado->id_resultado,

                        'entidad_tipo' =>
                            $event->entityType,

                        'entidad_id' =>
                            $event->entityId,

                        'correlation_id' =>
                            $event->correlationId,

                        'direccion_ip' =>
                            $event->ipAddress,

                        'user_agent' =>
                            $event->userAgent,

                        'detalle_json' =>
                            json_encode(
                                $detalle,
                                JSON_UNESCAPED_UNICODE
                                |
                                JSON_UNESCAPED_SLASHES
                            ),

                        'fecha_evento' =>
                            Carbon::parse(
                                $event->occurredAt
                            )
                            ->utc(),

                    ]);


                    // ======================================
                    // CAMBIOS
                    // ======================================

                    foreach (
                        $event->changes
                        as $change
                    ) {

                        if (
                            !is_array(
                                $change
                            )
                        ) {

                            continue;

                        }


                        $field = trim(

                            (string) (

                                $change[
                                    'campo'
                                ]

                                ??

                                $change[
                                    'field'
                                ]

                                ??

                                ''

                            )

                        );


                        if (
                            $field === ''
                        ) {

                            continue;

                        }


                        DB::table(
                            'cambios_auditoria'
                        )
                        ->insert([

                            'id_evento' =>
                                $event->eventId,

                            'campo' =>
                                $field,

                            'valor_anterior' =>
                                $this->toAuditText(

                                    $change[
                                        'valor_anterior'
                                    ]

                                    ??

                                    $change[
                                        'old'
                                    ]

                                    ??

                                    null

                                ),

                            'valor_nuevo' =>
                                $this->toAuditText(

                                    $change[
                                        'valor_nuevo'
                                    ]

                                    ??

                                    $change[
                                        'new'
                                    ]

                                    ??

                                    null

                                ),

                        ]);

                    }

                }

            );


            return true;

        }

        catch (
            QueryException $error
        ) {

            // ==============================================
            // IDEMPOTENCIA POR UUID REPETIDO
            // ==============================================

            if (

                (string) $error->getCode()
                ===
                '23505'

                &&

                DB::table(
                    'eventos_auditoria'
                )

                ->where(
                    'id_evento',
                    $event->eventId
                )

                ->exists()

            ) {

                return false;

            }


            throw $error;

        }
    }


    // ======================================================
    // SERIALIZAR CAMBIO
    // ======================================================

    private function toAuditText(
        mixed $value
    ): ?string {

        if (
            $value === null
        ) {

            return null;

        }


        if (
            is_bool(
                $value
            )
        ) {

            return (
                $value
                    ? 'true'
                    : 'false'
            );

        }


        if (

            is_array(
                $value
            )

            ||

            is_object(
                $value
            )

        ) {

            return json_encode(

                $value,

                JSON_UNESCAPED_UNICODE

                |

                JSON_UNESCAPED_SLASHES

            );

        }


        return (
            (string) $value
        );
    }
}