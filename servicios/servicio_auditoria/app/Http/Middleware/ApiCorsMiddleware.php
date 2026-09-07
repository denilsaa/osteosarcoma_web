<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;


class ApiCorsMiddleware
{
    /**
     * Orígenes permitidos para consumir
     * la API de Auditoría.
     */
    private const ALLOWED_ORIGINS = [
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ];


    public function handle(
        Request $request,
        Closure $next
    ): Response {

        /*
        |--------------------------------------------------------------------------
        | SOLO API
        |--------------------------------------------------------------------------
        */

        if (! $request->is('api/*')) {
            return $next($request);
        }


        $origin = $request->headers->get(
            'Origin'
        );


        /*
        |--------------------------------------------------------------------------
        | PREFLIGHT OPTIONS
        |--------------------------------------------------------------------------
        |
        | El navegador envía OPTIONS antes de requests que incluyen
        | Authorization.
        |
        */

        if ($request->isMethod('OPTIONS')) {

            $response = response(
                '',
                204
            );

            return $this->addCorsHeaders(
                $response,
                $origin
            );
        }


        /*
        |--------------------------------------------------------------------------
        | REQUEST NORMAL
        |--------------------------------------------------------------------------
        */

        $response = $next(
            $request
        );


        return $this->addCorsHeaders(
            $response,
            $origin
        );
    }


    /**
     * Agrega los headers CORS únicamente
     * cuando el Origin está permitido.
     */
    private function addCorsHeaders(
        Response $response,
        ?string $origin
    ): Response {

        if (
            $origin === null
            ||
            ! in_array(
                $origin,
                self::ALLOWED_ORIGINS,
                true
            )
        ) {
            return $response;
        }


        $response->headers->set(
            'Access-Control-Allow-Origin',
            $origin
        );


        $response->headers->set(
            'Access-Control-Allow-Credentials',
            'true'
        );


        $response->headers->set(
            'Access-Control-Allow-Methods',
            'GET, POST, PUT, PATCH, DELETE, OPTIONS'
        );


        $response->headers->set(
            'Access-Control-Allow-Headers',
            'Authorization, Content-Type, Accept, Origin, X-Requested-With'
        );


        $response->headers->set(
            'Access-Control-Max-Age',
            '3600'
        );


        $response->headers->set(
            'Vary',
            'Origin'
        );


        return $response;
    }
}