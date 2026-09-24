<?php

namespace App\Application\Radiography;

use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use InvalidArgumentException;
use RuntimeException;
use Throwable;

final class RadiographyAiGate
{
    public function assertRadiography(
        UploadedFile $file
    ): void {
        /*
        |--------------------------------------------------------------------------
        | PUERTA IA OBLIGATORIA - EFFICIENTNET
        |--------------------------------------------------------------------------
        |
        | Toda imagen que pretenda registrarse como radiografía debe pasar
        | obligatoriamente por EfficientNet.
        |
        | No existe interruptor para omitir esta validación.
        |
        | Comportamiento FAIL-CLOSED:
        |
        | - IA no disponible       -> BLOQUEAR
        | - respuesta inválida     -> BLOQUEAR
        | - no es radiografía      -> BLOQUEAR
        | - probabilidad < umbral  -> BLOQUEAR
        | - radiografía válida     -> CONTINUAR
        |
        */

        $path =
            $file->getRealPath();


        if (
            $path === false
            ||
            ! is_file(
                $path
            )
            ||
            ! is_readable(
                $path
            )
        ) {
            Log::error(
                '[RADIOGRAPHY_AI_GATE] Archivo temporal no accesible.',
                [
                    'archivo' =>
                        $file->getClientOriginalName(),
                ]
            );

            throw new RuntimeException(
                'No fue posible acceder al archivo para validarlo con EfficientNet.'
            );
        }


        Log::info(
            '[RADIOGRAPHY_AI_GATE] Inicio de validación obligatoria.',
            [
                'archivo' =>
                    $file->getClientOriginalName(),

                'tamano_bytes' =>
                    $file->getSize(),

                'mime_cliente' =>
                    $file->getClientMimeType(),

                'extension' =>
                    $file->getClientOriginalExtension(),
            ]
        );


        $handle =
            fopen(
                $path,
                'rb'
            );


        if (
            $handle === false
        ) {
            throw new RuntimeException(
                'No fue posible abrir la imagen para validarla con EfficientNet.'
            );
        }


        try {
            $response =
                Http::acceptJson()
                    ->timeout(
                        (int)
                        config(
                            'services.ia.timeout_seconds',
                            30
                        )
                    )
                    ->connectTimeout(
                        (int)
                        config(
                            'services.ia.connect_timeout_seconds',
                            5
                        )
                    )
                    ->attach(
                        'file',
                        $handle,
                        $file->getClientOriginalName(),
                    )
                    ->post(
                        rtrim(
                            (string)
                            config(
                                'services.ia.base_url',
                                'http://servicio-ia:8000/api'
                            ),
                            '/'
                        )
                        .'/validaciones/radiografia/'
                    );

        } catch (
            Throwable $exception
        ) {
            Log::error(
                '[RADIOGRAPHY_AI_GATE] Error comunicando con servicio IA.',
                [
                    'archivo' =>
                        $file->getClientOriginalName(),

                    'error' =>
                        $exception->getMessage(),
                ]
            );

            throw new RuntimeException(
                'No fue posible comunicarse con EfficientNet. Por seguridad, la radiografía no fue registrada.',
                0,
                $exception
            );

        } finally {
            if (
                is_resource(
                    $handle
                )
            ) {
                fclose(
                    $handle
                );
            }
        }


        Log::info(
            '[RADIOGRAPHY_AI_GATE] Respuesta HTTP del servicio IA.',
            [
                'archivo' =>
                    $file->getClientOriginalName(),

                'status' =>
                    $response->status(),
            ]
        );


        if (
            $response->status()
            ===
            503
        ) {
            throw new RuntimeException(
                'El modelo EfficientNet no está disponible en este momento. Por seguridad, no se registró el archivo.'
            );
        }


        if (
            $response->status()
            ===
            422
        ) {
            throw new InvalidArgumentException(
                (string)
                data_get(
                    $response->json(),
                    'error.message',
                    'La imagen enviada no pudo ser validada como radiografía.'
                )
            );
        }


        if (
            ! $response->successful()
        ) {
            Log::error(
                '[RADIOGRAPHY_AI_GATE] Servicio IA respondió con error.',
                [
                    'archivo' =>
                        $file->getClientOriginalName(),

                    'status' =>
                        $response->status(),

                    'body' =>
                        $response->body(),
                ]
            );

            throw new RuntimeException(
                'No fue posible validar el archivo mediante EfficientNet. Por seguridad, no fue registrado.'
            );
        }


        $data =
            data_get(
                $response->json(),
                'data'
            );


        if (
            ! is_array(
                $data
            )
        ) {
            throw new RuntimeException(
                'EfficientNet devolvió una respuesta inválida. Por seguridad, el archivo no fue registrado.'
            );
        }


        $rawDecision =
            $data[
                'es_radiografia'
            ]
            ??
            null;


        $isRadiography =
            filter_var(
                $rawDecision,
                FILTER_VALIDATE_BOOLEAN,
                FILTER_NULL_ON_FAILURE
            );


        if (
            $isRadiography === null
        ) {
            throw new RuntimeException(
                'EfficientNet devolvió una decisión radiográfica inválida.'
            );
        }


        $probabilityRadiography =
            isset(
                $data[
                    'probabilidad_radiografia'
                ]
            )
                ? (float)
                    $data[
                        'probabilidad_radiografia'
                    ]
                : null;


        $probabilityNonRadiography =
            isset(
                $data[
                    'probabilidad_no_radiografia'
                ]
            )
                ? (float)
                    $data[
                        'probabilidad_no_radiografia'
                    ]
                : null;


        $threshold =
            isset(
                $data[
                    'umbral'
                ]
            )
                ? (float)
                    $data[
                        'umbral'
                    ]
                : 0.90;


        Log::info(
            '[RADIOGRAPHY_AI_GATE] Resultado EfficientNet.',
            [
                'archivo' =>
                    $file->getClientOriginalName(),

                'es_radiografia' =>
                    $isRadiography,

                'probabilidad_radiografia' =>
                    $probabilityRadiography,

                'probabilidad_no_radiografia' =>
                    $probabilityNonRadiography,

                'umbral' =>
                    $threshold,

                'arquitectura' =>
                    $data[
                        'arquitectura'
                    ]
                    ??
                    null,

                'familia_modelo' =>
                    $data[
                        'familia_modelo'
                    ]
                    ??
                    null,
            ]
        );


        /*
        |--------------------------------------------------------------------------
        | DOBLE COMPROBACIÓN
        |--------------------------------------------------------------------------
        |
        | No basta solamente con es_radiografia=true.
        |
        | También exigimos que la probabilidad informada por EfficientNet
        | alcance el umbral configurado por el propio modelo.
        |
        */

        if (
            $isRadiography !== true
            ||
            $probabilityRadiography === null
            ||
            $probabilityRadiography < $threshold
        ) {
            Log::warning(
                '[RADIOGRAPHY_AI_GATE] Archivo RECHAZADO por EfficientNet.',
                [
                    'archivo' =>
                        $file->getClientOriginalName(),

                    'es_radiografia' =>
                        $isRadiography,

                    'probabilidad_radiografia' =>
                        $probabilityRadiography,

                    'probabilidad_no_radiografia' =>
                        $probabilityNonRadiography,

                    'umbral' =>
                        $threshold,
                ]
            );

            throw new InvalidArgumentException(
                'La imagen subida no fue identificada como una radiografía. Seleccione una radiografía válida para continuar.'
            );
        }


        Log::info(
            '[RADIOGRAPHY_AI_GATE] Archivo ACEPTADO por EfficientNet.',
            [
                'archivo' =>
                    $file->getClientOriginalName(),

                'probabilidad_radiografia' =>
                    $probabilityRadiography,

                'umbral' =>
                    $threshold,
            ]
        );
    }
}