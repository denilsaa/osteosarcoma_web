from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID


@dataclass(frozen=True)
class AuditActorDTO:
    usuario_uuid: Optional[UUID] = None
    nombre: Optional[str] = None
    rol: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass(frozen=True)
class AuditChangeDTO:
    field: str
    old_value: Optional[str]
    new_value: Optional[str]


@dataclass(frozen=True)
class AuditEventDTO:
    service: str
    module: str
    action: str
    result: str

    entity_type: Optional[str]
    entity_id: Optional[str]

    actor: AuditActorDTO

    description: Optional[str] = None
    reason: Optional[str] = None

    correlation_id: Optional[str] = None

    changes: list[
        AuditChangeDTO
    ] = field(
        default_factory=list
    )

    detail: dict[
        str,
        Any
    ] = field(
        default_factory=dict
    )