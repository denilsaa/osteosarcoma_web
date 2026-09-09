from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

from django.db import transaction

from django.db.models import (
    Count,
    Q,
)

from clinica.domain.entities import (
    Patient,
    PatientContact,
    PatientDocument,
)

from clinica.domain.entities.patient import (
    PatientEmergencyContact,
)

from clinica.domain.repositories import (
    PatientRepository,
)

from clinica.infrastructure.persistence.models import (
    ContactoPaciente,
    DocumentoPaciente,
    Paciente,
    Sexo,
    TipoContacto,
    TipoDocumento,
)

from clinica.infrastructure.persistence.models.patient_models import (
    ContactoEmergenciaPaciente,
)


class DjangoPatientRepository(
    PatientRepository
):

    # ======================================================
    # QUERY BASE
    # ======================================================

    @staticmethod
    def _base_queryset():

        return (
            Paciente.objects
            .select_related(
                "sexo",
            )
            .prefetch_related(
                "documentos__tipo_documento",
                "contactos__tipo_contacto",
                "contactos_emergencia",
            )
        )

    # ======================================================
    # ORM -> DOMAIN
    # ======================================================

    @staticmethod
    def _to_domain(
        model: Paciente,
    ) -> Patient:

        # ==================================================
        # DOCUMENTOS
        # ==================================================

        documents: list[
            PatientDocument
        ] = []

        for document in (
            model.documentos.all()
        ):

            documents.append(
                PatientDocument(
                    id_document=(
                        document.id_documento
                    ),
                    document_type_id=(
                        document
                        .tipo_documento
                        .id_tipo_documento
                    ),
                    document_type_code=(
                        document
                        .tipo_documento
                        .codigo
                    ),
                    document_type_name=(
                        document
                        .tipo_documento
                        .nombre
                    ),
                    document_number=(
                        document
                        .numero_documento
                    ),
                    complement=(
                        document.complemento
                    ),
                    issued_in=(
                        document.expedido_en
                    ),
                )
            )

        # ==================================================
        # CONTACTOS
        # ==================================================

        contacts: list[
            PatientContact
        ] = []

        for contact in (
            model.contactos.all()
        ):

            contacts.append(
                PatientContact(
                    id_contact=(
                        contact.id_contacto
                    ),
                    contact_type_id=(
                        contact
                        .tipo_contacto
                        .id_tipo_contacto
                    ),
                    contact_type_code=(
                        contact
                        .tipo_contacto
                        .codigo
                    ),
                    contact_type_name=(
                        contact
                        .tipo_contacto
                        .nombre
                    ),
                    value=(
                        contact.valor
                    ),
                    primary=(
                        contact.principal
                    ),
                )
            )

        # ==================================================
        # CONTACTOS DE EMERGENCIA
        # ==================================================

        emergency_contacts: list[
            PatientEmergencyContact
        ] = []

        for emergency in (
            model
            .contactos_emergencia
            .all()
        ):

            emergency_contacts.append(
                PatientEmergencyContact(
                    id_emergency_contact=(
                        emergency
                        .id_contacto_emergencia
                    ),
                    full_name=(
                        emergency
                        .nombre_completo
                    ),
                    relationship=(
                        emergency.parentesco
                    ),
                    phone=(
                        emergency.telefono
                    ),
                    email=(
                        emergency.correo
                    ),
                    primary=(
                        emergency.principal
                    ),
                    registration_date=(
                        emergency.fecha_registro
                    ),
                )
            )

        # ==================================================
        # CASOS
        # ==================================================

        clinical_cases_count = int(
            getattr(
                model,
                "cantidad_casos",
                0,
            )
            or
            0
        )

        # ==================================================
        # PACIENTE
        # ==================================================

        return Patient(
            id_patient=(
                model.id_paciente
            ),
            first_names=(
                model.nombres
            ),
            paternal_surname=(
                model.apellido_paterno
            ),
            maternal_surname=(
                model.apellido_materno
            ),
            birth_date=(
                model.fecha_nacimiento
            ),
            sex_id=(
                model.sexo.id_sexo
            ),
            sex_code=(
                model.sexo.codigo
            ),
            sex_name=(
                model.sexo.nombre
            ),
            active=(
                model.activo
            ),
            registration_date=(
                model.fecha_registro
            ),
            documents=(
                documents
            ),
            contacts=(
                contacts
            ),
            emergency_contacts=(
                emergency_contacts
            ),
            clinical_cases_count=(
                clinical_cases_count
            ),
        )

    # ======================================================
    # CREAR
    # ======================================================

    @transaction.atomic
    def create(
        self,
        *,
        first_names: str,
        paternal_surname: str,
        maternal_surname: str | None,
        birth_date: date,
        sex_id: int,
        document_type_id: int,
        document_number: str,
        complement: str | None,
        issued_in: str | None,

        mobile_phone: str | None,
        landline_phone: str | None,
        email: str | None,

        emergency_contact_name: str | None,
        emergency_relationship: str | None,
        emergency_phone: str | None,
        emergency_email: str | None,
    ) -> Patient:

        # ==================================================
        # CATÁLOGOS
        # ==================================================

        sex = (
            Sexo.objects.get(
                id_sexo=(
                    sex_id
                )
            )
        )

        document_type = (
            TipoDocumento.objects.get(
                id_tipo_documento=(
                    document_type_id
                )
            )
        )

        # ==================================================
        # PACIENTE
        # ==================================================

        patient = (
            Paciente.objects.create(
                sexo=(
                    sex
                ),
                nombres=(
                    first_names
                ),
                apellido_paterno=(
                    paternal_surname
                ),
                apellido_materno=(
                    maternal_surname
                ),
                fecha_nacimiento=(
                    birth_date
                ),
                activo=True,
            )
        )

        # ==================================================
        # DOCUMENTO
        # ==================================================

        DocumentoPaciente.objects.create(
            paciente=(
                patient
            ),
            tipo_documento=(
                document_type
            ),
            numero_documento=(
                document_number
            ),
            complemento=(
                complement
            ),
            expedido_en=(
                issued_in
            ),
        )

        # ==================================================
        # CONTACTOS DEL PACIENTE
        # ==================================================

        contactos_a_crear = [
            (
                "CELULAR",
                mobile_phone,
            ),
            (
                "TELEFONO",
                landline_phone,
            ),
            (
                "CORREO",
                email,
            ),
        ]

        principal_asignado = False

        for (
            codigo,
            valor,
        ) in contactos_a_crear:

            if not valor:
                continue

            tipo_contacto = (
                TipoContacto.objects.get(
                    codigo=(
                        codigo
                    )
                )
            )

            ContactoPaciente.objects.create(
                paciente=(
                    patient
                ),
                tipo_contacto=(
                    tipo_contacto
                ),
                valor=(
                    valor
                ),
                principal=(
                    not principal_asignado
                ),
            )

            principal_asignado = True

        # ==================================================
        # CONTACTO DE EMERGENCIA
        # ==================================================

        if (
            emergency_contact_name
            and
            emergency_relationship
            and
            emergency_phone
        ):

            ContactoEmergenciaPaciente.objects.create(
                paciente=(
                    patient
                ),
                nombre_completo=(
                    emergency_contact_name
                ),
                parentesco=(
                    emergency_relationship
                ),
                telefono=(
                    emergency_phone
                ),
                correo=(
                    emergency_email
                ),
                principal=True,
            )

        # ==================================================
        # RECARGAR AGREGADO
        # ==================================================

        stored_patient = (
            self._base_queryset()
            .annotate(
                cantidad_casos=Count(
                    "casos_clinicos",
                    distinct=True,
                )
            )
            .get(
                id_paciente=(
                    patient.id_paciente
                )
            )
        )

        return self._to_domain(
            stored_patient
        )

    # ======================================================
    # OBTENER
    # ======================================================

    def get_by_id(
        self,
        patient_id: UUID,
    ) -> Optional[Patient]:

        try:

            patient = (
                self._base_queryset()
                .annotate(
                    cantidad_casos=Count(
                        "casos_clinicos",
                        distinct=True,
                    )
                )
                .get(
                    id_paciente=(
                        patient_id
                    )
                )
            )

            return self._to_domain(
                patient
            )

        except Paciente.DoesNotExist:

            return None

    # ======================================================
    # LISTAR
    # ======================================================

    def list_patients(
        self,
        *,
        search: str | None,
        sex_code: str | None,
        active: bool | None,
        document_type_code: str | None,
        page: int,
        page_size: int,
    ) -> tuple[
        list[Patient],
        int,
    ]:

        queryset = (
            self._base_queryset()
        )

        # ==================================================
        # BÚSQUEDA
        # ==================================================

        if search:

            search = (
                search.strip()
            )

            queryset = (
                queryset.filter(
                    Q(
                        nombres__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        apellido_paterno__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        apellido_materno__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        documentos__numero_documento__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        contactos__valor__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        contactos_emergencia__nombre_completo__icontains=(
                            search
                        )
                    )
                    |
                    Q(
                        contactos_emergencia__telefono__icontains=(
                            search
                        )
                    )
                )
            )

        # ==================================================
        # SEXO
        # ==================================================

        if sex_code:

            queryset = (
                queryset.filter(
                    sexo__codigo=(
                        sex_code
                    )
                )
            )

        # ==================================================
        # ACTIVO
        # ==================================================

        if active is not None:

            queryset = (
                queryset.filter(
                    activo=(
                        active
                    )
                )
            )

        # ==================================================
        # DOCUMENTO
        # ==================================================

        if document_type_code:

            queryset = (
                queryset.filter(
                    documentos__tipo_documento__codigo=(
                        document_type_code
                    )
                )
            )

        # ==================================================
        # DISTINCT + CASOS
        # ==================================================

        queryset = (
            queryset
            .distinct()
            .annotate(
                cantidad_casos=Count(
                    "casos_clinicos",
                    distinct=True,
                )
            )
            .order_by(
                "-fecha_registro"
            )
        )

        total = (
            queryset.count()
        )

        start = (
            (page - 1)
            *
            page_size
        )

        end = (
            start
            +
            page_size
        )

        page_items = (
            queryset[
                start:end
            ]
        )

        patients = [
            self._to_domain(
                patient
            )
            for patient
            in page_items
        ]

        return (
            patients,
            total,
        )

    # ======================================================
    # DOCUMENTO EXACTO
    # ======================================================

    def find_exact_document(
        self,
        *,
        document_type_id: int,
        document_number: str,
    ) -> Optional[Patient]:

        try:

            patient = (
                self._base_queryset()
                .annotate(
                    cantidad_casos=Count(
                        "casos_clinicos",
                        distinct=True,
                    )
                )
                .get(
                    documentos__tipo_documento__id_tipo_documento=(
                        document_type_id
                    ),
                    documentos__numero_documento__iexact=(
                        document_number
                    ),
                )
            )

            return self._to_domain(
                patient
            )

        except Paciente.DoesNotExist:

            return None

    # ======================================================
    # DUPLICADOS
    # ======================================================

    def find_possible_duplicates(
        self,
        *,
        document_type_id: int | None,
        document_number: str | None,
        first_names: str | None,
        paternal_surname: str | None,
        maternal_surname: str | None,
        birth_date: date | None,
        limit: int = 10,
    ) -> list[Patient]:

        queryset = (
            self._base_queryset()
        )

        conditions = Q()

        has_conditions = False

        # ==================================================
        # DOCUMENTO EXACTO
        # ==================================================

        if (
            document_type_id
            is not None
            and
            document_number
        ):

            conditions |= Q(
                documentos__tipo_documento__id_tipo_documento=(
                    document_type_id
                ),
                documentos__numero_documento__iexact=(
                    document_number
                ),
            )

            has_conditions = True

        # ==================================================
        # IDENTIDAD
        # ==================================================

        if (
            first_names
            and
            paternal_surname
        ):

            identity_condition = (
                Q(
                    nombres__iexact=(
                        first_names
                    )
                )
                &
                Q(
                    apellido_paterno__iexact=(
                        paternal_surname
                    )
                )
            )

            if maternal_surname:

                identity_condition &= Q(
                    apellido_materno__iexact=(
                        maternal_surname
                    )
                )

            if birth_date:

                identity_condition &= Q(
                    fecha_nacimiento=(
                        birth_date
                    )
                )

            conditions |= (
                identity_condition
            )

            has_conditions = True

        if not has_conditions:

            return []

        queryset = (
            queryset
            .filter(
                conditions
            )
            .distinct()
            .annotate(
                cantidad_casos=Count(
                    "casos_clinicos",
                    distinct=True,
                )
            )
            .order_by(
                "-fecha_registro"
            )[:limit]
        )

        return [
            self._to_domain(
                patient
            )
            for patient
            in queryset
        ]

    # ======================================================
    # ACTUALIZAR
    # ======================================================

    @transaction.atomic
    def update(
        self,
        *,
        patient_id: UUID,
        changes: dict,
    ) -> Patient:

        patient = (
            Paciente.objects
            .select_for_update()
            .select_related(
                "sexo"
            )
            .get(
                id_paciente=(
                    patient_id
                )
            )
        )

        field_mapping = {
            "first_names":
                "nombres",

            "paternal_surname":
                "apellido_paterno",

            "maternal_surname":
                "apellido_materno",

            "birth_date":
                "fecha_nacimiento",

            "active":
                "activo",
        }

        updated_fields: list[
            str
        ] = []

        for (
            domain_field,
            model_field,
        ) in field_mapping.items():

            if (
                domain_field
                not in changes
            ):
                continue

            setattr(
                patient,
                model_field,
                changes[
                    domain_field
                ],
            )

            updated_fields.append(
                model_field
            )

        if (
            "sex_id"
            in changes
        ):

            patient.sexo = (
                Sexo.objects.get(
                    id_sexo=(
                        changes[
                            "sex_id"
                        ]
                    )
                )
            )

            updated_fields.append(
                "sexo"
            )

        if updated_fields:

            patient.save(
                update_fields=(
                    updated_fields
                )
            )

        updated_patient = (
            self._base_queryset()
            .annotate(
                cantidad_casos=Count(
                    "casos_clinicos",
                    distinct=True,
                )
            )
            .get(
                id_paciente=(
                    patient_id
                )
            )
        )

        return self._to_domain(
            updated_patient
        )