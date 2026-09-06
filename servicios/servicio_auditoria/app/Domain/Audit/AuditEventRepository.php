<?php

namespace App\Domain\Audit;


interface AuditEventRepository
{
    /**
     * true:
     *     evento almacenado.
     *
     * false:
     *     evento ya existía.
     *
     * El event_id actúa como clave de idempotencia.
     */

    public function store(
        AuditEvent $event
    ): bool;
}