import uuid

from dataclasses import (
    asdict,
    dataclass,
    field,
)

from datetime import (
    datetime,
    timezone,
)

from typing import (
    Any,
)


# ==========================================================
# EVENTO DE AUDITORÍA
# ==========================================================

@dataclass(
    frozen=True
)
class AuditEvent:
    """
    Contrato estándar de eventos de auditoría.

    Este objeto pertenece al dominio del microservicio
    productor.

    NO conoce:
    - PostgreSQL Auditoría
    - Laravel
    - HTTP
    - tablas externas

    Solamente describe un hecho ocurrido.
    """

    event_id: str

    event_version: int

    occurred_at: str

    service: str

    module: str

    action: str

    result: str

    actor: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    entity: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    correlation_id: (
        str
        | None
    ) = None

    context: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    description: (
        str
        | None
    ) = None

    reason: (
        str
        | None
    ) = None

    detail: dict[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    changes: list[
        dict[
            str,
            Any,
        ]
    ] = field(
        default_factory=list
    )


    # ======================================================
    # CREAR EVENTO
    # ======================================================

    @classmethod
    def create(
        cls,
        *,
        service,
        module,
        action,
        result,

        actor_user_id=None,
        actor_name=None,
        actor_role=None,

        entity_type=None,
        entity_id=None,

        correlation_id=None,

        ip_address=None,
        user_agent=None,

        description=None,
        reason=None,

        detail=None,
        changes=None,
    ):

        return cls(

            event_id=
                str(
                    uuid.uuid4()
                ),

            event_version=
                1,

            occurred_at=
                datetime.now(
                    timezone.utc
                )
                .isoformat(),

            service=
                cls._required_upper(
                    service,
                    "service",
                ),

            module=
                cls._required_upper(
                    module,
                    "module",
                ),

            action=
                cls._required_upper(
                    action,
                    "action",
                ),

            result=
                cls._required_upper(
                    result,
                    "result",
                ),

            actor={
                "user_id":
                    cls._optional_text(
                        actor_user_id
                    ),

                "name":
                    cls._optional_text(
                        actor_name
                    ),

                "role":
                    cls._optional_text(
                        actor_role
                    ),
            },

            entity={
                "type":
                    cls._optional_upper(
                        entity_type
                    ),

                "id":
                    cls._optional_text(
                        entity_id
                    ),
            },

            correlation_id=
                cls._optional_text(
                    correlation_id
                ),

            context={
                "ip_address":
                    cls._optional_text(
                        ip_address
                    ),

                "user_agent":
                    cls._optional_text(
                        user_agent
                    ),
            },

            description=
                cls._optional_text(
                    description
                ),

            reason=
                cls._optional_text(
                    reason
                ),

            detail=(
                dict(
                    detail
                )
                if isinstance(
                    detail,
                    dict,
                )
                else {}
            ),

            changes=(
                list(
                    changes
                )
                if isinstance(
                    changes,
                    list,
                )
                else []
            ),

        )


    # ======================================================
    # ROUTING KEY
    # ======================================================

    @property
    def routing_key(
        self,
    ):

        return (
            f"{self.service.lower()}"
            ".audit.v1"
        )


    # ======================================================
    # SERIALIZACIÓN
    # ======================================================

    def to_dict(
        self,
    ):

        return asdict(
            self
        )


    # ======================================================
    # UTILIDADES
    # ======================================================

    @staticmethod
    def _required_upper(
        value,
        field_name,
    ):

        value = str(
            value or ""
        ).strip()

        if not value:

            raise ValueError(
                (
                    "El campo "
                    f"{field_name} "
                    "es obligatorio."
                )
            )

        return value.upper()


    @staticmethod
    def _optional_upper(
        value,
    ):

        if value is None:

            return None

        value = str(
            value
        ).strip()

        return (
            value.upper()
            if value
            else None
        )


    @staticmethod
    def _optional_text(
        value,
    ):

        if value is None:

            return None

        value = str(
            value
        ).strip()

        return (
            value
            if value
            else None
        )