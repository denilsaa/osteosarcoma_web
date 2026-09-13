<?php

namespace App\Infrastructure\Security;

use Illuminate\Auth\Access\AuthorizationException;
use Illuminate\Auth\AuthenticationException;
use Illuminate\Http\Client\ConnectionException;
use Illuminate\Support\Facades\Http;
use InvalidArgumentException;
use RuntimeException;

final class ClinicalCaseAccessVerifier
{
    public static function assertCanAccess(
        string $caseUuid,
        ?string $authorization
    ): void {
        if (! self::isUuid($caseUuid)) {
            throw new InvalidArgumentException(
                'El identificador del caso clínico no es un UUID válido.'
            );
        }

        /*
        |--------------------------------------------------------------------------
        | EXTRAER TOKEN
        |--------------------------------------------------------------------------
        |
        | Radiografías no vuelve a validar criptográficamente el JWT.
        | El mismo Bearer token se reenvía a servicio_clinico.
        |
        */

        $token = RequestActorExtractor::bearerToken(
            $authorization
        );


        /*
        |--------------------------------------------------------------------------
        | URL DEL SERVICIO CLÍNICO
        |--------------------------------------------------------------------------
        |
        | IMPORTANTE:
        |
        | Docker Compose puede tener servicios con "_", pero Django rechaza
        | ese valor dentro del header Host porque "_" no es válido según
        | RFC 1034/1035.
        |
        | Por eso utilizamos SIEMPRE el alias DNS:
        |
        | servicio-clinico
        |
        */

        $configuredBaseUrl = (string) config(
            'services.clinico.base_url',
            'http://servicio-clinico:8000/api'
        );

        /*
         * Protección adicional:
         * Si quedó alguna configuración antigua con servicio_clinico,
         * la corregimos antes de realizar la petición.
         */

        $configuredBaseUrl = str_replace(
            'servicio_clinico',
            'servicio-clinico',
            $configuredBaseUrl
        );

        $baseUrl = rtrim(
            $configuredBaseUrl,
            '/'
        );


        /*
        |--------------------------------------------------------------------------
        | VALIDAR ACCESO EN SERVICIO CLÍNICO
        |--------------------------------------------------------------------------
        */

        try {
            $response = Http::withToken(
                $token
            )
                ->acceptJson()
                ->connectTimeout(3)
                ->timeout(8)
                ->get(
                    $baseUrl
                    . '/casos/'
                    . $caseUuid
                    . '/'
                );

        } catch (ConnectionException $exception) {
            throw new RuntimeException(
                'CLINICAL_SERVICE_UNAVAILABLE: '
                . 'No fue posible conectar con el servicio clínico.',
                previous: $exception
            );
        }


        /*
        |--------------------------------------------------------------------------
        | ACCESO PERMITIDO
        |--------------------------------------------------------------------------
        */

        if ($response->successful()) {
            return;
        }


        /*
        |--------------------------------------------------------------------------
        | MENSAJE DEVUELTO POR CLÍNICO
        |--------------------------------------------------------------------------
        */

        $json = $response->json();

        $message = (string) (
            data_get(
                $json,
                'error.message'
            )
            ??
            data_get(
                $json,
                'detail'
            )
            ??
            data_get(
                $json,
                'message'
            )
            ??
            'No fue posible validar el acceso al caso clínico.'
        );


        /*
        |--------------------------------------------------------------------------
        | 401 - NO AUTENTICADO
        |--------------------------------------------------------------------------
        */

        if ($response->status() === 401) {
            throw new AuthenticationException(
                $message
            );
        }


        /*
        |--------------------------------------------------------------------------
        | 403 - SIN PERMISOS
        |--------------------------------------------------------------------------
        */

        if ($response->status() === 403) {
            throw new AuthorizationException(
                $message
            );
        }


        /*
        |--------------------------------------------------------------------------
        | 404 - CASO NO ENCONTRADO
        |--------------------------------------------------------------------------
        */

        if ($response->status() === 404) {
            throw new RuntimeException(
                'CLINICAL_CASE_NOT_FOUND: '
                . $message
            );
        }


        /*
        |--------------------------------------------------------------------------
        | OTRO ERROR DEL SERVICIO CLÍNICO
        |--------------------------------------------------------------------------
        */

        throw new RuntimeException(
            'CLINICAL_SERVICE_ERROR: HTTP '
            . $response->status()
            . ' - '
            . $message
        );
    }


    private static function isUuid(
        string $value
    ): bool {
        return preg_match(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-'
            . '[1-5][0-9a-f]{3}-'
            . '[89ab][0-9a-f]{3}-'
            . '[0-9a-f]{12}$/i',
            $value
        ) === 1;
    }
}