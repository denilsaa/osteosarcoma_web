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
        repository:
            PatientRepository,
    ):

        self.repository = (
            repository
        )


    # ======================================================
    # OPCIONAL
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
        dto:
            CreatePatientDTO,
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
        # SEXO
        # SOLO MASCULINO / FEMENINO
        # ==================================================

        if dto.sex_id not in (
            1,
            2,
        ):

            raise ValueError(
                "Seleccione Masculino o Femenino."
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
                document_type_id=
                    dto.document_type_id,

                document_number=
                    document_number,
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

        contacts: list[
            dict
        ] = []


        principal_count = 0


        for contact in dto.contacts:

            value = (
                self._optional_text(
                    contact.value
                )
            )


            if not value:

                continue


            if contact.primary:

                principal_count += 1


            contacts.append(
                {
                    "contact_type_id":
                        contact.contact_type_id,

                    "value":
                        value,

                    "primary":
                        contact.primary,
                }
            )


        if principal_count > 1:

            raise ValueError(
                "Solo un contacto del paciente "
                "puede ser principal."
            )


        if (
            contacts
            and
            principal_count == 0
        ):

            contacts[0][
                "primary"
            ] = True


        # ==================================================
        # CONTACTOS DE EMERGENCIA
        # ==================================================

        emergency_contacts: list[
            dict
        ] = []


        emergency_principal_count = 0


        for emergency in (
            dto.emergency_contacts
        ):

            full_name = (
                self._optional_text(
                    emergency.full_name
                )
            )


            relationship = (
                self._optional_text(
                    emergency.relationship
                )
            )


            phone = (
                self._optional_text(
                    emergency.phone
                )
            )


            email = (
                self._optional_text(
                    emergency.email
                )
            )


            if email:

                email = (
                    email.lower()
                )


            if (
                not full_name
                or
                not relationship
                or
                not phone
            ):

                raise ValueError(
                    "Cada contacto de emergencia "
                    "debe incluir nombre, parentesco "
                    "y teléfono."
                )


            if emergency.primary:

                emergency_principal_count += 1


            emergency_contacts.append(
                {
                    "full_name":
                        full_name,

                    "relationship":
                        relationship,

                    "phone":
                        phone,

                    "email":
                        email,

                    "primary":
                        emergency.primary,
                }
            )


        if emergency_principal_count > 1:

            raise ValueError(
                "Solo un contacto de emergencia "
                "puede ser principal."
            )


        if (
            emergency_contacts
            and
            emergency_principal_count == 0
        ):

            emergency_contacts[0][
                "primary"
            ] = True


        # ==================================================
        # CREAR
        # ==================================================

        return (
            self.repository
            .create(
                first_names=
                    first_names,

                paternal_surname=
                    paternal_surname,

                maternal_surname=
                    maternal_surname,

                birth_date=
                    dto.birth_date,

                sex_id=
                    dto.sex_id,

                document_type_id=
                    dto.document_type_id,

                document_number=
                    document_number,

                complement=
                    complement,

                issued_in=
                    issued_in,

                contacts=
                    contacts,

                emergency_contacts=
                    emergency_contacts,
            )
        )