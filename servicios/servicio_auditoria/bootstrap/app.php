<?php

use App\Http\Middleware\ApiCorsMiddleware;
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Exceptions;
use Illuminate\Foundation\Configuration\Middleware;
use Illuminate\Http\Request;


return Application::configure(
    basePath: dirname(__DIR__)
)
    ->withRouting(
        web: __DIR__.'/../routes/web.php',
        api: __DIR__.'/../routes/api.php',
        commands: __DIR__.'/../routes/console.php',
        health: '/up',
    )

    ->withMiddleware(
        function (
            Middleware $middleware
        ): void {

            /*
            |--------------------------------------------------------------------------
            | CORS DE AUDITORÍA
            |--------------------------------------------------------------------------
            |
            | Se coloca antes del resto del stack para responder correctamente
            | los preflight OPTIONS del frontend React.
            |
            */

            $middleware->prepend(
                ApiCorsMiddleware::class
            );

        }
    )

    ->withExceptions(
        function (
            Exceptions $exceptions
        ): void {

            $exceptions->shouldRenderJsonWhen(
                fn (
                    Request $request
                ) =>
                    $request->is(
                        'api/*'
                    )
                    ||
                    $request->expectsJson(),
            );

        }
    )

    ->create();