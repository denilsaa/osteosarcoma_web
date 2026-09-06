<?php

namespace App\Application\Audit;


use App\Domain\Audit\AuditEvent;

use App\Domain\Audit\AuditEventRepository;


final class StoreAuditEvent
{
    public function __construct(

        private readonly
        AuditEventRepository $repository

    ) {
    }


    public function execute(
        array $payload
    ): array {

        $event = (

            AuditEvent::fromArray(
                $payload
            )

        );


        $stored = (

            $this->repository->store(
                $event
            )

        );


        return [

            'event_id' =>
                $event->eventId,

            'stored' =>
                $stored,

            'duplicate' =>
                !$stored,

        ];
    }
}