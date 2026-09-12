from django.urls import (
    path,
)

from .views import (
    clinical_case_antecedents_view,
    clinical_case_catalogs_view,
    clinical_case_detail_view,
    clinical_case_list_view,
    clinical_case_observations_view,
    clinical_case_signs_view,
    clinical_case_symptoms_view,
    patient_cases_view,
    patient_catalogs_view,
    patient_create_view,
    patient_detail_view,
    patient_duplicates_view,
    patient_list_view,
    patient_photo_view,
    patient_update_view,
)


urlpatterns = [

    # ======================================================
    # PACIENTES
    # ======================================================

    path(
        "pacientes/catalogos/",
        patient_catalogs_view,
        name="patient-catalogs",
    ),

    path(
        "pacientes/posibles-duplicados/",
        patient_duplicates_view,
        name="patient-duplicates",
    ),

    path(
        "pacientes/",
        patient_list_view,
        name="patient-list",
    ),

    path(
        "pacientes/registrar/",
        patient_create_view,
        name="patient-create",
    ),

    path(
        "pacientes/<uuid:patient_id>/",
        patient_detail_view,
        name="patient-detail",
    ),

    path(
        "pacientes/<uuid:patient_id>/editar/",
        patient_update_view,
        name="patient-update",
    ),


    # ======================================================
    # FOTO DEL PACIENTE
    # ======================================================

    path(
        "pacientes/<uuid:patient_id>/foto/",
        patient_photo_view,
        name="patient-photo",
    ),


    # ======================================================
    # CASOS DEL PACIENTE
    # ======================================================

    path(
        "pacientes/<uuid:patient_id>/casos/",
        patient_cases_view,
        name="patient-cases",
    ),


    # ======================================================
    # CASOS CLINICOS
    # ======================================================

    path(
        "casos/catalogos/",
        clinical_case_catalogs_view,
        name="clinical-case-catalogs",
    ),

    path(
        "casos/",
        clinical_case_list_view,
        name="clinical-case-list",
    ),

    path(
        "casos/<uuid:case_id>/",
        clinical_case_detail_view,
        name="clinical-case-detail",
    ),


    # ======================================================
    # INFORMACION CLINICA DEL CASO
    # ======================================================

    path(
        "casos/<uuid:case_id>/antecedentes/",
        clinical_case_antecedents_view,
        name="clinical-case-antecedents",
    ),

    path(
        "casos/<uuid:case_id>/sintomas/",
        clinical_case_symptoms_view,
        name="clinical-case-symptoms",
    ),

    path(
        "casos/<uuid:case_id>/signos/",
        clinical_case_signs_view,
        name="clinical-case-signs",
    ),

    path(
        "casos/<uuid:case_id>/observaciones/",
        clinical_case_observations_view,
        name="clinical-case-observations",
    ),
]