import base64
import json
import os
from uuid import UUID

import jwt

from clinica.application.dto import (
    AuditActorDTO,
)


class RequestActorExtractor:
    """
    Extrae el contexto del actor desde el request HTTP.

    El servicio Clínico NO consulta la base de datos
    de servicio_usuarios.

    Para operaciones de auditoría se conserva `extract`,
    que tolera requests sin autenticación.

    Para operaciones clínicas protegidas debe utilizarse
    `extract_authenticated`, que valida criptográficamente
    el JWT emitido por servicio_usuarios.
    """

    ALGORITHM = "HS256"

    # ======================================================
    # OBTENER TOKEN BEARER
    # ======================================================

    @staticmethod
    def _extract_bearer_token(
        request,
    ) -> str | None:

        authorization = (
            request.headers.get(
                "Authorization",
                "",
            )
        )

        if not (
            authorization
            .lower()
            .startswith(
                "bearer "
            )
        ):
            return None

        token = (
            authorization[7:]
            .strip()
        )

        return token or None

    # ======================================================
    # DECODIFICAR PAYLOAD SIN VERIFICAR
    # SOLO COMPATIBILIDAD PARA AUDITORÍA
    # ======================================================

    @staticmethod
    def _decode_payload_unverified(
        token: str,
    ) -> dict:

        try:
            parts = token.split(".")

            if len(parts) != 3:
                return {}

            payload = parts[1]

            padding = (
                "="
                * (
                    -len(payload)
                    % 4
                )
            )

            decoded = (
                base64
                .urlsafe_b64decode(
                    payload
                    + padding
                )
            )

            return json.loads(
                decoded.decode(
                    "utf-8"
                )
            )

        except (
            ValueError,
            json.JSONDecodeError,
            UnicodeDecodeError,
        ):
            return {}

    # ======================================================
    # VALIDAR JWT FIRMADO
    # ======================================================

    @classmethod
    def _decode_payload_verified(
        cls,
        token: str,
    ) -> dict:

        signing_key = (
            os.environ.get(
                "JWT_SIGNING_KEY"
            )
        )

        if not signing_key:
            raise ValueError(
                "El servicio clínico no tiene configurada "
                "la clave de validación JWT."
            )

        try:
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=[
                    cls.ALGORITHM
                ],
                options={
                    "require": [
                        "exp",
                        "iat",
                        "type",
                        "usuario_id",
                        "sid",
                    ]
                },
            )

        except jwt.ExpiredSignatureError as error:
            raise ValueError(
                "La sesión expiró. Inicie sesión nuevamente."
            ) from error

        except jwt.InvalidSignatureError as error:
            raise ValueError(
                "La firma del token de acceso no es válida."
            ) from error

        except jwt.MissingRequiredClaimError as error:
            raise ValueError(
                "El token de acceso está incompleto."
            ) from error

        except jwt.InvalidTokenError as error:
            raise ValueError(
                "El token de acceso no es válido."
            ) from error

        if (
            payload.get("type")
            != "access"
        ):
            raise ValueError(
                "Se requiere un access token válido."
            )

        return payload

    # ======================================================
    # NORMALIZAR UUID
    # ======================================================

    @staticmethod
    def _parse_uuid(
        value,
    ):
        if not value:
            return None

        try:
            return UUID(
                str(value)
            )

        except (
            ValueError,
            TypeError,
            AttributeError,
        ):
            return None

    # ======================================================
    # OBTENER IP
    # ======================================================

    @staticmethod
    def _extract_ip(
        request,
    ):
        forwarded_for = (
            request.META.get(
                "HTTP_X_FORWARDED_FOR"
            )
        )

        if forwarded_for:
            return (
                forwarded_for
                .split(",")[0]
                .strip()
            )

        return (
            request.META.get(
                "REMOTE_ADDR"
            )
        )

    # ======================================================
    # CONSTRUIR ACTOR
    # ======================================================

    @classmethod
    def _build_actor(
        cls,
        request,
        payload: dict,
    ) -> AuditActorDTO:

        raw_uuid = (
            payload.get(
                "usuario_id"
            )
            or payload.get(
                "id_usuario"
            )
            or payload.get(
                "usuario_uuid"
            )
            or payload.get(
                "user_id"
            )
            or payload.get(
                "sub"
            )
        )

        usuario_uuid = (
            cls._parse_uuid(
                raw_uuid
            )
        )

        nombre = (
            payload.get(
                "nombre_completo"
            )
            or payload.get(
                "nombre"
            )
            or payload.get(
                "username"
            )
            or payload.get(
                "correo"
            )
        )

        rol = (
            payload.get(
                "rol"
            )
            or payload.get(
                "role"
            )
        )

        roles = (
            payload.get(
                "roles"
            )
        )

        if (
            rol is None
            and isinstance(
                roles,
                list,
            )
            and roles
        ):
            first_role = (
                roles[0]
            )

            if isinstance(
                first_role,
                dict,
            ):
                rol = (
                    first_role.get(
                        "codigo"
                    )
                    or first_role.get(
                        "nombre"
                    )
                )

            else:
                rol = str(
                    first_role
                )

        if rol is not None:
            rol = (
                str(rol)
                .strip()
                .upper()
            )

        return AuditActorDTO(
            usuario_uuid=
                usuario_uuid,

            nombre=
                nombre,

            rol=
                rol,

            ip=
                cls._extract_ip(
                    request
                ),

            user_agent=
                request.headers.get(
                    "User-Agent"
                ),
        )

    # ======================================================
    # EXTRAER ACTOR PARA AUDITORÍA
    # ======================================================

    @classmethod
    def extract(
        cls,
        request,
    ) -> AuditActorDTO:

        token = (
            cls._extract_bearer_token(
                request
            )
        )

        payload = {}

        if token:
            payload = (
                cls
                ._decode_payload_unverified(
                    token
                )
            )

        return cls._build_actor(
            request,
            payload,
        )

    # ======================================================
    # EXTRAER ACTOR AUTENTICADO
    # ======================================================

    @classmethod
    def extract_authenticated(
        cls,
        request,
    ) -> AuditActorDTO:

        token = (
            cls._extract_bearer_token(
                request
            )
        )

        if not token:
            raise ValueError(
                "Debe iniciar sesión para realizar esta operación."
            )

        payload = (
            cls
            ._decode_payload_verified(
                token
            )
        )

        actor = cls._build_actor(
            request,
            payload,
        )

        if actor.usuario_uuid is None:
            raise ValueError(
                "No fue posible identificar al usuario autenticado."
            )

        if not actor.rol:
            raise ValueError(
                "El token no contiene un rol activo. "
                "Cierre sesión e inicie sesión nuevamente."
            )

        return actor
