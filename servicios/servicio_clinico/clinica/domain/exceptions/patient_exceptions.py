class PatientDomainError(
    Exception
):
    """
    Excepción base para errores
    relacionados con pacientes.
    """


class PatientNotFoundError(
    PatientDomainError
):
    def __init__(
        self,
        patient_id,
    ):
        self.patient_id = patient_id

        super().__init__(
            "El paciente solicitado "
            "no existe."
        )


class DuplicatePatientError(
    PatientDomainError
):
    def __init__(
        self,
        message=(
            "Ya existe un paciente "
            "registrado con el mismo "
            "documento."
        ),
    ):
        super().__init__(
            message
        )


class InvalidPatientDataError(
    PatientDomainError
):
    pass


class PatientWithoutChangesError(
    PatientDomainError
):
    def __init__(
        self,
    ):
        super().__init__(
            "No existen cambios "
            "para guardar."
        )


class EditReasonRequiredError(
    PatientDomainError
):
    def __init__(
        self,
    ):
        super().__init__(
            "Debe indicar el motivo "
            "de la modificación."
        )