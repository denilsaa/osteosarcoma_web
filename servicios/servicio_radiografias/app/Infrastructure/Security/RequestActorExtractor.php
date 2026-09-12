<?php

namespace App\Infrastructure\Security;

use InvalidArgumentException;

final class RequestActorExtractor
{
    public static function extractUserUuid(
        ?string $authorization
    ): string {
        if (
            $authorization === null
            ||
            ! str_starts_with(
                strtolower($authorization),
                'bearer '
            )
        ) {
            throw new InvalidArgumentException(
                'No se encontró un token de autenticación.'
            );
        }

        $token = trim(
            substr(
                $authorization,
                7
            )
        );

        $parts = explode(
            '.',
            $token
        );

        if (count($parts) !== 3) {
            throw new InvalidArgumentException(
                'El token de autenticación no tiene un formato válido.'
            );
        }

        $payload = self::decodeBase64Url(
            $parts[1]
        );

        $data = json_decode(
            $payload,
            true
        );

        if (! is_array($data)) {
            throw new InvalidArgumentException(
                'No fue posible interpretar el token de autenticación.'
            );
        }

        $userUuid =
            $data['usuario_id']
            ??
            $data['id_usuario']
            ??
            $data['usuario_uuid']
            ??
            $data['user_id']
            ??
            $data['sub']
            ??
            null;

        if (
            ! is_string($userUuid)
            ||
            ! self::isUuid($userUuid)
        ) {
            throw new InvalidArgumentException(
                'No fue posible identificar al usuario autenticado.'
            );
        }

        return $userUuid;
    }


    private static function decodeBase64Url(
        string $value
    ): string {
        $value = strtr(
            $value,
            '-_',
            '+/'
        );

        $padding = strlen($value) % 4;

        if ($padding !== 0) {
            $value .= str_repeat(
                '=',
                4 - $padding
            );
        }

        $decoded = base64_decode(
            $value,
            true
        );

        if ($decoded === false) {
            throw new InvalidArgumentException(
                'El token de autenticación contiene un payload inválido.'
            );
        }

        return $decoded;
    }


    private static function isUuid(
        string $value
    ): bool {
        return preg_match(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i',
            $value
        ) === 1;
    }
}