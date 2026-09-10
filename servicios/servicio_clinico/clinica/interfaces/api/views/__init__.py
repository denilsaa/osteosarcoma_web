from .health_view import (
    health_view,
)

from .patient_views import (
    patient_catalogs_view,
    patient_create_view,
    patient_detail_view,
    patient_duplicates_view,
    patient_list_view,
    patient_update_view,
)

from .clinical_case_views import (
    clinical_case_catalogs_view,
    clinical_case_detail_view,
    clinical_case_list_view,
    patient_cases_view,
)


__all__ = [
    "health_view",

    "patient_catalogs_view",
    "patient_create_view",
    "patient_detail_view",
    "patient_duplicates_view",
    "patient_list_view",
    "patient_update_view",

    "patient_cases_view",
    "clinical_case_list_view",
    "clinical_case_detail_view",
    "clinical_case_catalogs_view",
]