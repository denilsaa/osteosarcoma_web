import base64
import json
from uuid import UUID

from clinica.application.dto import (
    AuditActorDTO,
)


class RequestActorExtractor:
    """
    Extrae el contexto del actor desde el request HTTP.

    El servicio Clínico NO consulta la base de datos
    de servicio_usuarios.

    El JWT es emitido por servicio_usuarios y contiene:
        - usuario_id
        - correo
        - sid
        - type
        - iat
        - exp
    """

    # ======================================================
    # DECODIFICAR PAYLOAD JWT
    # ======================================================

    @staticmethod
    def _decode_payload(
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
    # EXTRAER ACTOR
    # ======================================================

    @classmethod
    def extract(
        cls,
        request,
    ) -> AuditActorDTO:

        authorization = (
            request.headers.get(
                "Authorization",
                "",
            )
        )

        payload = {}

        if (
            authorization
            .lower()
            .startswith(
                "bearer "
            )
        ):
            token = (
                authorization[
                    7:
                ]
                .strip()
            )

            payload = (
                cls._decode_payload(
                    token
                )
            )

        # ==================================================
        # UUID
        #
        # El JWT real de servicio_usuarios utiliza
        # "usuario_id".
        # ==================================================

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

        # ==================================================
        # NOMBRE
        #
        # El JWT actual no contiene nombre completo.
        # Como identificador legible utilizamos correo.
        # ==================================================

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

        # ==================================================
        # ROL
        #
        # El JWT actual no contiene rol.
        # Se conserva compatibilidad por si en el futuro
        # servicio_usuarios lo incorpora.
        # ==================================================

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
                        "nombre"
                    )
                    or first_role.get(
                        "codigo"
                    )
                )

            else:
                rol = str(
                    first_role
                )

        # ==================================================
        # CONTEXTO HTTP
        # ==================================================

        ip = (
            cls._extract_ip(
                request
            )
        )

        user_agent = (
            request.headers.get(
                "User-Agent"
            )
        )

        return AuditActorDTO(
            usuario_uuid=
                usuario_uuid,

            nombre=
                nombre,

            rol=
                rol,

            ip=
                ip,

            user_agent=
                user_agent,
        )