<?php

namespace App\Infrastructure\Security;

use Illuminate\Auth\AuthenticationException;

final class RequestActorExtractor
{
    private const ALLOWED_ROLES = [
        'JEFE_ONCOLOGIA',
        'ONCOLOGO',
    ];


    /**
     * Extrae los claims del actor DESPUÉS de que el mismo
     * Bearer token haya sido validado por servicio_clinico.
     *
     * IMPORTANTE:
     * servicio_radiografias no vuelve a validar la firma JWT.
     * La validación criptográfica y la autorización sobre el
     * caso pertenecen a servicio_clinico, que es la autoridad
     * del dominio clínico.
     *
     * @return array{
     *     user_uuid: string,
     *     role: string,
     *     session_uuid: string
     * }
     */
    public static function extractAuthenticatedActor(
        ?string $authorization
    ): array {
        $token = self::extractBearerToken(
            $authorization
        );

        $parts = explode(
            '.',
            $token
        );

        if (count($parts) !== 3) {
            throw new AuthenticationException(
                'El token de autenticación no tiene un formato válido.'
            );
        }

        $payload = self::decodeJsonPart(
            $parts[1],
            'payload'
        );

        if (($payload['type'] ?? null) !== 'access') {
            throw new AuthenticationException(
                'El token recibido no es un access token válido.'
            );
        }

        $userUuid = $payload['usuario_id'] ?? null;
        $role = $payload['rol'] ?? null;
        $sessionUuid = $payload['sid'] ?? null;

        if (
            ! is_string($userUuid)
            ||
            ! self::isUuid($userUuid)
        ) {
            throw new AuthenticationException(
                'No fue posible identificar al usuario autenticado.'
            );
        }

        if (
            ! is_string($sessionUuid)
            ||
            ! self::isUuid($sessionUuid)
        ) {
            throw new AuthenticationException(
                'El token no contiene una sesión válida.'
            );
        }

        if (
            ! is_string($role)
            ||
            ! in_array(
                $role,
                self::ALLOWED_ROLES,
                true
            )
        ) {
            throw new AuthenticationException(
                'El token no contiene un rol autorizado para el módulo clínico.'
            );
        }

        return [
            'user_uuid' => $userUuid,
            'role' => $role,
            'session_uuid' => $sessionUuid,
        ];
    }


    public static function extractUserUuid(
        ?string $authorization
    ): string {
        $actor = self::extractAuthenticatedActor(
            $authorization
        );

        return $actor['user_uuid'];
    }


    public static function bearerToken(
        ?string $authorization
    ): string {
        return self::extractBearerToken(
            $authorization
        );
    }


    private static function extractBearerToken(
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
            throw new AuthenticationException(
                'No se encontró un token de autenticación.'
            );
        }

        $token = trim(
            substr(
                $authorization,
                7
            )
        );

        if ($token === '') {
            throw new AuthenticationException(
                'El token de autenticación está vacío.'
            );
        }

        return $token;
    }


    /**
     * @return array<string, mixed>
     */
    private static function decodeJsonPart(
        string $encodedValue,
        string $partName
    ): array {
        $decoded = self::decodeBase64Url(
            $encodedValue
        );

        $data = json_decode(
            $decoded,
            true
        );

        if (! is_array($data)) {
            throw new AuthenticationException(
                'No fue posible interpretar la '.$partName.' del token.'
            );
        }

        return $data;
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
            throw new AuthenticationException(
                'El token de autenticación contiene una codificación inválida.'
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
