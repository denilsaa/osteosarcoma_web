from clinica.application.dto import (
    AuditActorDTO,
    AuditChangeDTO,
    AuditEventDTO,
    FieldChangeDTO,
)
from clinica.application.ports import (
    AuditEventPort,
)


class AuditService:
    def __init__(
        self,
        publisher: AuditEventPort,
    ):
        self.publisher = publisher

    def patient_created(
        self,
        *,
        patient,
        actor: AuditActorDTO,
    ) -> bool:

        document = (
            patient.primary_document
        )

        return self.publisher.publish(
            AuditEventDTO(
                service="CLINICO",
                module="PACIENTES",
                action="CREAR",
                result="EXITOSO",

                entity_type=
                    "PACIENTE",

                entity_id=
                    str(
                        patient.id_patient
                    ),

                actor=
                    actor,

                description=
                    (
                        "Se registró un "
                        "nuevo paciente."
                    ),

                detail={
                    "paciente_nombre":
                        patient.full_name,

                    "documento":
                        (
                            document
                            .document_number
                            if document
                            else None
                        ),
                },
            )
        )

    def patient_updated(
        self,
        *,
        patient,
        actor: AuditActorDTO,
        reason: str,
        changes: list[
            FieldChangeDTO
        ],
    ) -> bool:

        audit_changes = [
            AuditChangeDTO(
                field=
                    change.field,

                old_value=
                    change.old_value,

                new_value=
                    change.new_value,
            )
            for change
            in changes
        ]

        return self.publisher.publish(
            AuditEventDTO(
                service="CLINICO",
                module="PACIENTES",
                action="EDITAR",
                result="EXITOSO",

                entity_type=
                    "PACIENTE",

                entity_id=
                    str(
                        patient.id_patient
                    ),

                actor=
                    actor,

                description=
                    (
                        "Se actualizaron "
                        "los datos del "
                        "paciente."
                    ),

                reason=
                    reason,

                changes=
                    audit_changes,

                detail={
                    "paciente_nombre":
                        patient.full_name,

                    "cantidad_cambios":
                        len(
                            audit_changes
                        ),
                },
            )
        )