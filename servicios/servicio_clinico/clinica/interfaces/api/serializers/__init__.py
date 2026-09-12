from .clinical_case_serializers import (
    AdvanceClinicalCaseStatusSerializer,
    CreateClinicalAntecedentSerializer,
    CreateClinicalCaseSerializer,
    CreateClinicalObservationSerializer,
    CreateClinicalSignSerializer,
    CreateClinicalSymptomSerializer,
)

from .patient_serializers import (
    CreatePatientRequestSerializer,
    PatientListQuerySerializer,
    PossibleDuplicateQuerySerializer,
    UpdatePatientRequestSerializer,
)


__all__ = [

    # ======================================================
    # PACIENTES
    # ======================================================

    "CreatePatientRequestSerializer",
    "UpdatePatientRequestSerializer",
    "PatientListQuerySerializer",
    "PossibleDuplicateQuerySerializer",


    # ======================================================
    # CASOS CLINICOS
    # ======================================================

    "CreateClinicalCaseSerializer",
    "AdvanceClinicalCaseStatusSerializer",
    "CreateClinicalAntecedentSerializer",
    "CreateClinicalSymptomSerializer",
    "CreateClinicalSignSerializer",
    "CreateClinicalObservationSerializer",
]