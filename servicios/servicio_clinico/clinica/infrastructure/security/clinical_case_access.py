from clinica.application.dto import (
    AuditActorDTO,
)
from clinica.infrastructure.security.request_actor import (
    RequestActorExtractor,
)


class ClinicalAuthenticationError(Exception):
    """La petición no posee una autenticación clínica válida."""


class ClinicalAuthorizationError(Exception):
    """El actor autenticado no tiene permiso para la operación."""


class ClinicalCaseAccess:
    """
    Reglas de autorización del módulo de Casos clínicos.

    JEFE_ONCOLOGIA:
        - puede consultar todos los casos;
        - puede filtrar por cualquier oncólogo;
        - puede asignar un caso a otro oncólogo.

    ONCOLOGO:
        - solo puede consultar casos donde es responsable;
        - no puede forzar filtros hacia otro oncólogo;
        - solo puede crear casos asignados a sí mismo.
    """

    ROLE_HEAD = "JEFE_ONCOLOGIA"
    ROLE_ONCOLOGIST = "ONCOLOGO"

    ALLOWED_ROLES = {
        ROLE_HEAD,
        ROLE_ONCOLOGIST,
    }

    @classmethod
    def get_actor(
        cls,
        request,
    ) -> AuditActorDTO:

        try:
            actor = (
                RequestActorExtractor
                .extract_authenticated(
                    request
                )
            )

        except ValueError as error:
            raise ClinicalAuthenticationError(
                str(error)
            ) from error

        role = (
            str(actor.rol or "")
            .strip()
            .upper()
        )

        if role not in cls.ALLOWED_ROLES:
            raise ClinicalAuthorizationError(
                "El usuario autenticado no posee un rol "
                "habilitado para gestionar casos clínicos."
            )

        return actor

    @classmethod
    def is_head(
        cls,
        actor: AuditActorDTO,
    ) -> bool:
        return (
            str(actor.rol or "")
            .strip()
            .upper()
            == cls.ROLE_HEAD
        )

    @classmethod
    def can_access_case(
        cls,
        actor: AuditActorDTO,
        case,
    ) -> bool:

        if cls.is_head(actor):
            return True

        return (
            case.responsible_oncologist_uuid
            == actor.usuario_uuid
        )

    @classmethod
    def assert_case_access(
        cls,
        actor: AuditActorDTO,
        case,
    ) -> None:

        if cls.can_access_case(
            actor,
            case,
        ):
            return

        raise ClinicalAuthorizationError(
            "No tiene permiso para acceder a este caso clínico."
        )

    @classmethod
    def filter_cases_for_actor(
        cls,
        actor: AuditActorDTO,
        cases,
    ):

        if cls.is_head(actor):
            return list(cases)

        return [
            case
            for case in cases
            if (
                case.responsible_oncologist_uuid
                == actor.usuario_uuid
            )
        ]

    @classmethod
    def resolve_list_oncologist_filter(
        cls,
        actor: AuditActorDTO,
        requested_oncologist_uuid,
    ):

        if cls.is_head(actor):
            return requested_oncologist_uuid

        if (
            requested_oncologist_uuid is not None
            and requested_oncologist_uuid
            != actor.usuario_uuid
        ):
            raise ClinicalAuthorizationError(
                "No tiene permiso para consultar casos "
                "asignados a otro médico."
            )

        return actor.usuario_uuid

    @classmethod
    def resolve_responsible_for_create(
        cls,
        actor: AuditActorDTO,
        requested_oncologist_uuid,
    ):

        if cls.is_head(actor):
            return (
                requested_oncologist_uuid
                or actor.usuario_uuid
            )

        if (
            requested_oncologist_uuid is not None
            and requested_oncologist_uuid
            != actor.usuario_uuid
        ):
            raise ClinicalAuthorizationError(
                "Un oncólogo no puede registrar un caso "
                "asignándolo a otro médico."
            )

        return actor.usuario_uuid
