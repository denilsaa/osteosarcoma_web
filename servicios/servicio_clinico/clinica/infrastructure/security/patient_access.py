"""Acceso mínimo por responsabilidad asistencial, verificado desde Django."""
from django.db.models import Q
from clinica.infrastructure.security.clinical_case_access import (
    ClinicalCaseAccess, ClinicalAuthorizationError,
)


class PatientAccess:
    @staticmethod
    def actor(request):
        return ClinicalCaseAccess.get_actor(request)

    @staticmethod
    def scope(queryset, actor):
        if ClinicalCaseAccess.is_head(actor):
            return queryset
        return queryset.filter(
            Q(asignaciones_clinicas__oncologo_uuid=actor.usuario_uuid,
              asignaciones_clinicas__activa=True)
            | Q(casos_clinicos__oncologo_responsable_uuid=actor.usuario_uuid)
        ).distinct()

    @classmethod
    def can_access(cls, actor, patient_id):
        from clinica.infrastructure.persistence.models import Paciente
        return cls.scope(Paciente.objects.filter(id_paciente=patient_id), actor).exists()

    @classmethod
    def require(cls, actor, patient_id):
        if not cls.can_access(actor, patient_id):
            # No se revela si el paciente existe o pertenece a otro profesional.
            raise ClinicalAuthorizationError("No tiene autorización para acceder a este paciente.")

    @classmethod
    def require_head(cls, actor):
        if not ClinicalCaseAccess.is_head(actor):
            raise ClinicalAuthorizationError("Esta gestión requiere jefatura de oncología.")
