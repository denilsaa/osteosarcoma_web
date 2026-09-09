from clinica.domain.entities import (
    Patient,
)


class PatientPresenter:

    # ======================================================
    # DOCUMENTO
    # ======================================================

    @staticmethod
    def document(
        document,
    ):

        if document is None:

            return None

        return {
            "id_document":
                (
                    str(
                        document.id_document
                    )
                    if document.id_document
                    else None
                ),

            "document_type_id":
                document.document_type_id,

            "document_type_code":
                document.document_type_code,

            "document_type_name":
                document.document_type_name,

            "document_number":
                document.document_number,

            "complement":
                document.complement,

            "issued_in":
                document.issued_in,
        }

    # ======================================================
    # CONTACTO
    # ======================================================

    @staticmethod
    def contact(
        contact,
    ):

        if contact is None:

            return None

        return {
            "id_contact":
                (
                    str(
                        contact.id_contact
                    )
                    if contact.id_contact
                    else None
                ),

            "contact_type_id":
                contact.contact_type_id,

            "contact_type_code":
                contact.contact_type_code,

            "contact_type_name":
                contact.contact_type_name,

            "value":
                contact.value,

            "primary":
                contact.primary,
        }

    # ======================================================
    # CONTACTO EMERGENCIA
    # ======================================================

    @staticmethod
    def emergency_contact(
        contact,
    ):

        if contact is None:

            return None

        return {
            "id_emergency_contact":
                (
                    str(
                        contact
                        .id_emergency_contact
                    )
                    if (
                        contact
                        .id_emergency_contact
                    )
                    else None
                ),

            "full_name":
                contact.full_name,

            "relationship":
                contact.relationship,

            "phone":
                contact.phone,

            "email":
                contact.email,

            "primary":
                contact.primary,

            "registration_date":
                (
                    contact
                    .registration_date
                    .isoformat()
                    if (
                        contact
                        .registration_date
                    )
                    else None
                ),
        }

    # ======================================================
    # DETALLE
    # ======================================================

    @classmethod
    def detail(
        cls,
        patient: Patient,
    ) -> dict:

        return {
            "id_patient":
                (
                    str(
                        patient.id_patient
                    )
                    if patient.id_patient
                    else None
                ),

            "first_names":
                patient.first_names,

            "paternal_surname":
                patient.paternal_surname,

            "maternal_surname":
                patient.maternal_surname,

            "full_name":
                patient.full_name,

            "birth_date":
                patient
                .birth_date
                .isoformat(),

            "sex": {
                "id":
                    patient.sex_id,

                "code":
                    patient.sex_code,

                "name":
                    patient.sex_name,
            },

            "active":
                patient.active,

            "registration_date":
                (
                    patient
                    .registration_date
                    .isoformat()
                    if patient.registration_date
                    else None
                ),

            "documents": [
                cls.document(
                    document
                )
                for document
                in patient.documents
            ],

            "contacts": [
                cls.contact(
                    contact
                )
                for contact
                in patient.contacts
            ],

            "emergency_contacts": [
                cls.emergency_contact(
                    contact
                )
                for contact
                in patient.emergency_contacts
            ],

            "primary_emergency_contact":
                cls.emergency_contact(
                    patient
                    .primary_emergency_contact
                ),

            "clinical_cases_count":
                patient
                .clinical_cases_count,
        }

    # ======================================================
    # RESUMEN
    # ======================================================

    @classmethod
    def summary(
        cls,
        patient: Patient,
    ) -> dict:

        return {
            "id_patient":
                str(
                    patient.id_patient
                ),

            "full_name":
                patient.full_name,

            "birth_date":
                patient
                .birth_date
                .isoformat(),

            "sex": {
                "code":
                    patient.sex_code,

                "name":
                    patient.sex_name,
            },

            "active":
                patient.active,

            "primary_document":
                cls.document(
                    patient
                    .primary_document
                ),

            "primary_contact":
                cls.contact(
                    patient
                    .primary_contact
                ),

            "clinical_cases_count":
                patient
                .clinical_cases_count,

            "registration_date":
                (
                    patient
                    .registration_date
                    .isoformat()
                    if patient.registration_date
                    else None
                ),
        }