from abc import ABC, abstractmethod

from clinica.application.dto import (
    AuditEventDTO,
)


class AuditEventPort(ABC):
    """
    Puerto de salida para eventos de Auditoría.

    Application conoce solamente esta abstracción.
    RabbitMQ pertenece exclusivamente a Infrastructure.
    """

    @abstractmethod
    def publish(
        self,
        event: AuditEventDTO,
    ) -> bool:
        raise NotImplementedError