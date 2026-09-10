from .create_clinical_case import (
    CreateClinicalCaseUseCase,
)

from .create_patient import (
    CreatePatientUseCase,
)

from .find_patient_duplicates import (
    FindPatientDuplicatesUseCase,
)

from .get_clinical_case import (
    GetClinicalCaseUseCase,
)

from .get_clinical_case_catalogs import (
    GetClinicalCaseCatalogsUseCase,
)

from .get_patient import (
    GetPatientUseCase,
)

from .get_patient_catalogs import (
    GetPatientCatalogsUseCase,
)

from .list_clinical_cases import (
    ListClinicalCasesUseCase,
)

from .list_patient_cases import (
    ListPatientCasesUseCase,
)

from .list_patients import (
    ListPatientsUseCase,
)

from .patient_photo import (
    DeletePatientPhotoUseCase,
    UpdatePatientPhotoUseCase,
)

from .update_patient import (
    UpdatePatientUseCase,
)


__all__ = [

    # ======================================================
    # PACIENTES
    # ======================================================

    "CreatePatientUseCase",

    "GetPatientUseCase",

    "GetPatientCatalogsUseCase",

    "ListPatientsUseCase",

    "FindPatientDuplicatesUseCase",

    "UpdatePatientUseCase",

    "UpdatePatientPhotoUseCase",

    "DeletePatientPhotoUseCase",


    # ======================================================
    # CASOS CLÍNICOS
    # ======================================================

    "ListPatientCasesUseCase",

    "CreateClinicalCaseUseCase",

    "ListClinicalCasesUseCase",

    "GetClinicalCaseUseCase",

    "GetClinicalCaseCatalogsUseCase",

]