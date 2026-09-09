from clinica.application.dto import (
    CreatePatientDTO,
)

from clinica.domain.exceptions import (
    DuplicatePatientError,
)

from clinica.domain.repositories import (
    PatientRepository,
)

from clinica.domain.services import (
    PatientDomainService,
)


class CreatePatientUseCase:

    def __init__(
        self,
        repository: PatientRepository,
    ):

        self.repository = repository

    # ======================================================
    # NORMALIZAR OPCIONAL
    # ======================================================

    @staticmethod
    def _optional_text(
        value,
    ):

        if value in (
            None,
            "",
        ):
            return None

        value = str(
            value
        ).strip()

        return (
            value
            if value
            else None
        )

    # ======================================================
    # EJECUTAR
    # ======================================================

    def execute(
        self,
        dto: CreatePatientDTO,
    ):

        # ==================================================
        # DATOS PERSONALES
        # ==================================================

        first_names = (
            PatientDomainService
            .validate_name(
                dto.first_names,
                "Los nombres",
            )
        )

        paternal_surname = (
            PatientDomainService
            .validate_name(
                dto.paternal_surname,
                "El apellido paterno",
            )
        )

        maternal_surname = (
            PatientDomainService
            .normalize_text(
                dto.maternal_surname
            )
        )

        PatientDomainService.validate_birth_date(
            dto.birth_date
        )

        # ==================================================
        # DOCUMENTO
        # ==================================================

        document_number = (
            PatientDomainService
            .normalize_document(
                dto.document_number
            )
        )

        exact_duplicate = (
            self.repository
            .find_exact_document(
                document_type_id=(
                    dto.document_type_id
                ),
                document_number=(
                    document_number
                ),
            )
        )

        if exact_duplicate:

            raise DuplicatePatientError()

        complement = (
            PatientDomainService
            .normalize_text(
                dto.complement
            )
        )

        issued_in = (
            PatientDomainService
            .normalize_text(
                dto.issued_in
            )
        )

        if issued_in:

            issued_in = (
                issued_in.upper()
            )

        # ==================================================
        # CONTACTOS DEL PACIENTE
        # ==================================================

        mobile_phone = (
            self._optional_text(
                dto.mobile_phone
            )
        )

        landline_phone = (
            self._optional_text(
                dto.landline_phone
            )
        )

        email = (
            self._optional_text(
                dto.email
            )
        )

        if email:

            email = (
                email.lower()
            )

        # ==================================================
        # CONTACTO DE EMERGENCIA
        # ==================================================

        emergency_contact_name = (
            self._optional_text(
                dto.emergency_contact_name
            )
        )

        emergency_relationship = (
            self._optional_text(
                dto.emergency_relationship
            )
        )

        emergency_phone = (
            self._optional_text(
                dto.emergency_phone
            )
        )

        emergency_email = (
            self._optional_text(
                dto.emergency_email
            )
        )

        if emergency_email:

            emergency_email = (
                emergency_email.lower()
            )

        # ==================================================
        # CREAR
        # ==================================================

        return self.repository.create(
            first_names=(
                first_names
            ),
            paternal_surname=(
                paternal_surname
            ),
            maternal_surname=(
                maternal_surname
            ),
            birth_date=(
                dto.birth_date
            ),
            sex_id=(
                dto.sex_id
            ),
            document_type_id=(
                dto.document_type_id
            ),
            document_number=(
                document_number
            ),
            complement=(
                complement
            ),
            issued_in=(
                issued_in
            ),

            mobile_phone=(
                mobile_phone
            ),
            landline_phone=(
                landline_phone
            ),
            email=(
                email
            ),

            emergency_contact_name=(
                emergency_contact_name
            ),
            emergency_relationship=(
                emergency_relationship
            ),
            emergency_phone=(
                emergency_phone
            ),
            emergency_email=(
                emergency_email
            ),
        )