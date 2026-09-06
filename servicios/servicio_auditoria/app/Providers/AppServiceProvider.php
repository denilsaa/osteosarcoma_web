<?php

namespace App\Providers;


use App\Domain\Audit\AuditEventRepository;

use App\Infrastructure\Persistence\PostgresAuditEventRepository;


use Illuminate\Support\ServiceProvider;


class AppServiceProvider
    extends ServiceProvider
{

    public function register(): void
    {

        $this->app->bind(

            AuditEventRepository::class,

            PostgresAuditEventRepository::class

        );

    }


    public function boot(): void
    {
        //
    }
}