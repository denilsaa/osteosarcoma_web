from uuid import (
    UUID,
)

from clinica.application.services import (
    PatientPhotoService,
)

from clinica.infrastructure.persistence.models import (
    Paciente,
)


# ==========================================================
# SUBIR / CAMBIAR FOTO
# ==========================================================


class UpdatePatientPhotoUseCase:

    def execute(
        self,
        *,
        patient_id:
            UUID,

        uploaded_file,
    ) -> Paciente:

        # ==================================================
        # BUSCAR PACIENTE
        # ==================================================

        patient = (
            Paciente
            .objects
            .filter(
                id_paciente=
                    patient_id,
            )
            .first()
        )


        if patient is None:

            raise ValueError(
                "El paciente no existe."
            )


        # ==================================================
        # VALIDAR ARCHIVO
        # ==================================================

        filename, content = (
            PatientPhotoService
            .validate_and_prepare(
                uploaded_file
            )
        )


        # ==================================================
        # FOTO ANTERIOR
        # ==================================================

        old_storage = None

        old_name = None


        if (
            patient.foto
            and
            patient.foto.name
        ):

            old_storage = (
                patient
                .foto
                .storage
            )


            old_name = (
                patient
                .foto
                .name
            )


        # ==================================================
        # GUARDAR NUEVA
        # ==================================================

        patient.foto.save(
            filename,
            content,
            save=True,
        )


        # ==================================================
        # ELIMINAR FOTO ANTERIOR
        # SOLO DESPUÉS DE GUARDAR LA NUEVA
        # ==================================================

        if (
            old_storage
            and
            old_name
            and
            old_name
            !=
            patient.foto.name
        ):

            try:

                if (
                    old_storage
                    .exists(
                        old_name
                    )
                ):

                    old_storage.delete(
                        old_name
                    )


            except Exception:

                # No invalidamos la operación si solo
                # falló la limpieza del archivo anterior.
                pass


        return patient


# ==========================================================
# ELIMINAR FOTO
# ==========================================================


class DeletePatientPhotoUseCase:

    def execute(
        self,
        *,
        patient_id:
            UUID,
    ) -> Paciente:

        patient = (
            Paciente
            .objects
            .filter(
                id_paciente=
                    patient_id,
            )
            .first()
        )


        if patient is None:

            raise ValueError(
                "El paciente no existe."
            )


        if (
            not patient.foto
            or
            not patient.foto.name
        ):

            return patient


        storage = (
            patient
            .foto
            .storage
        )


        filename = (
            patient
            .foto
            .name
        )


        # ==================================================
        # LIMPIAR BD
        # ==================================================

        patient.foto = None


        patient.save(
            update_fields=[
                "foto",
            ]
        )


        # ==================================================
        # ELIMINAR ARCHIVO
        # ==================================================

        try:

            if storage.exists(
                filename
            ):

                storage.delete(
                    filename
                )


        except Exception:

            pass


        return patient