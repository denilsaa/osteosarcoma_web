from django.urls import (
    path,
)

from .views import (
    clinical_case_advance_status_view,
    clinical_case_antecedents_view,
    clinical_case_catalogs_view,
    clinical_case_detail_view,
    clinical_case_list_view,
    clinical_case_observations_view,
    clinical_case_signs_view,
    clinical_case_status_history_view,
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


from .views.clinical_case_review_views import (
    clinical_case_valuation_catalog_view,
    clinical_case_valuations_view,
)


from .views.clinical_case_management_views import (
    clinical_case_management_view,
    clinical_case_supervision_view,
)


from .views.clinical_notifications_views import (
    clinical_notifications_view,
    clinical_notification_read_view,
)


from .views.patient_assignments_views import (
    patient_assignments_view, patient_assignment_revoke_view,
)


urlpatterns = [
    path("pacientes/<uuid:patient_id>/asignaciones/", patient_assignments_view, name="patient-assignments"),
    path("pacientes/<uuid:patient_id>/asignaciones/<uuid:oncologist_id>/revocar/", patient_assignment_revoke_view, name="patient-assignment-revoke"),
    path("notificaciones/", clinical_notifications_view, name="clinical-notifications"),
    path("notificaciones/<uuid:notification_id>/leer/", clinical_notification_read_view, name="clinical-notification-read"),
    path("casos/supervision/resumen/", clinical_case_supervision_view, name="case-supervision"),
    path("casos/<uuid:case_id>/gestion/", clinical_case_management_view, name="case-management"),

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


    path(
        "casos/valoraciones/criterios/",
        clinical_case_valuation_catalog_view,
        name="case-valuation-catalog",
    ),

    path(
        "casos/<uuid:case_id>/valoraciones/",
        clinical_case_valuations_view,
        name="case-valuations",
    ),


    # ======================================================
    # FLUJO DE ESTADOS
    # ======================================================

    path(
        "casos/<uuid:case_id>/historial-estados/",
        clinical_case_status_history_view,
        name="clinical-case-status-history",
    ),

    path(
        "casos/<uuid:case_id>/estado/",
        clinical_case_advance_status_view,
        name="clinical-case-advance-status",
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