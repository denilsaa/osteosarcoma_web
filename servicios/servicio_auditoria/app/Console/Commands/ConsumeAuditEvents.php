<?php

namespace App\Console\Commands;


use App\Infrastructure\Messaging\RabbitMqAuditConsumer;

use Illuminate\Console\Command;

use Throwable;


final class ConsumeAuditEvents
    extends Command
{

    // ======================================================
    // COMANDO
    // ======================================================

    protected $signature =
        'audit:consume';


    protected $description =
        (
            'Consume eventos de Auditoría '
            . 'desde RabbitMQ.'
        );


    // ======================================================
    // CONSTRUCTOR
    // ======================================================

    public function __construct(

        private readonly
        RabbitMqAuditConsumer $consumer

    ) {

        parent::__construct();

    }


    // ======================================================
    // EJECUTAR
    // ======================================================

    public function handle(): int
    {

        $this->info(
            'Iniciando worker de Auditoría...'
        );


        try {

            return (
                $this->consumer->run()
            );

        }

        catch (
            Throwable $error
        ) {

            $this->error(

                'Worker detenido: '
                . $error->getMessage()

            );


            report(
                $error
            );


            return (
                self::FAILURE
            );

        }
    }
}