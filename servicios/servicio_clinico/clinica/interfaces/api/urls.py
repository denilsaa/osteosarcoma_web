from django.urls import (
    path,
)

from .views import (
    patient_cases_view,
    patient_catalogs_view,
    patient_create_view,
    patient_detail_view,
    patient_duplicates_view,
    patient_list_view,
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
    # CASOS CLÍNICOS DEL PACIENTE
    # ======================================================

    path(
        "pacientes/<uuid:patient_id>/casos/",
        patient_cases_view,
        name="patient-cases",
    ),

]