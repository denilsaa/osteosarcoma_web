import re

from rest_framework import serializers

from identidad.models import (
    PerfilProfesional,
    Rol,
    Usuario,
)


# ==========================================================
# CONSTANTES
# ==========================================================

ESPECIALIDAD_ONCOLOGIA = "Oncología"

AREA_CLINICA_OSTEOSARCOMA = (
    "Tumores óseos / Osteosarcoma"
)

ROLES_ONCOLOGIA_PERMITIDOS = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}


SUBESPECIALIDADES_ONCOLOGIA = [
    "Oncología médica",
    "Oncología pediátrica",
    "Oncología quirúrgica",
    "Oncología radioterápica",
    "Oncología ortopédica",
    "Otra",
]


EXPEDIDOS_BOLIVIA = {
    "LP": "La Paz",
    "CB": "Cochabamba",
    "SC": "Santa Cruz",
    "OR": "Oruro",
    "PT": "Potosí",
    "CH": "Chuquisaca",
    "TJ": "Tarija",
    "BE": "Beni",
    "PD": "Pando",
}


# ==========================================================
# PATRONES
# ==========================================================

PATRON_TELEFONO_PERSONAL = re.compile(
    r"^[67]\d{7}$"
)

PATRON_TELEFONO_INSTITUCIONAL = re.compile(
    r"^\d{8}$"
)

PATRON_MATRICULA = re.compile(
    r"^[A-Z0-9]+(?:[./-][A-Z0-9]+)*$"
)

PATRON_CI = re.compile(
    r"^\d{4,20}$"
)

PATRON_COMPLEMENTO = re.compile(
    r"^[A-Z0-9]{1,10}$"
)


# ==========================================================
# UTILIDADES
# ==========================================================


def normalizar_texto_opcional(valor):
    """
    Convierte cadenas vacías en None.
    """

    if valor in (
        None,
        "",
    ):
        return None

    valor = str(
        valor
    ).strip()

    if not valor:
        return None

    return valor


def validar_telefono_personal(valor):
    """
    Valida teléfono móvil boliviano.

    Se mantiene como opcional.
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:
        return None

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El teléfono personal solo puede contener números."
        )

    if len(valor) != 8:
        raise serializers.ValidationError(
            "El teléfono personal debe tener exactamente 8 dígitos."
        )

    if not PATRON_TELEFONO_PERSONAL.fullmatch(
        valor
    ):
        raise serializers.ValidationError(
            "El teléfono personal debe comenzar con 6 o 7."
        )

    return valor


def validar_telefono_institucional(valor):
    """
    Valida teléfono institucional.

    Por ahora se admite cualquier número de 8 dígitos.
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:
        return None

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El teléfono institucional solo puede contener números."
        )

    if not PATRON_TELEFONO_INSTITUCIONAL.fullmatch(
        valor
    ):
        raise serializers.ValidationError(
            "El teléfono institucional debe tener exactamente 8 dígitos."
        )

    return valor


def normalizar_y_validar_matricula(
    valor,
    obligatoria=False,
):
    """
    Normaliza matrícula profesional.

    Ejemplos válidos:
    MED-5487
    MS-12345
    COL.MED-4456
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:

        if obligatoria:

            raise serializers.ValidationError(
                "La matrícula profesional es obligatoria."
            )

        return None

    valor = (
        valor
        .upper()
        .replace(
            " ",
            "",
        )
    )

    if (
        len(valor) < 4
        or
        len(valor) > 30
    ):

        raise serializers.ValidationError(
            "La matrícula debe tener entre 4 y 30 caracteres."
        )

    if not PATRON_MATRICULA.fullmatch(
        valor
    ):

        raise serializers.ValidationError(
            "Use solo letras, números y separadores válidos: "
            "guion (-), punto (.) o barra (/)."
        )

    return valor


def normalizar_y_validar_ci(
    valor,
):
    """
    CI obligatorio para nuevos oncólogos.
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:

        raise serializers.ValidationError(
            "La cédula de identidad es obligatoria."
        )

    valor = (
        valor
        .replace(
            " ",
            "",
        )
        .replace(
            ".",
            "",
        )
    )

    if not PATRON_CI.fullmatch(
        valor
    ):

        raise serializers.ValidationError(
            "La cédula de identidad debe contener únicamente números."
        )

    return valor


def normalizar_complemento(
    valor,
):
    """
    Complemento opcional del CI.
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:
        return None

    valor = (
        valor
        .upper()
        .replace(
            " ",
            "",
        )
    )

    if not PATRON_COMPLEMENTO.fullmatch(
        valor
    ):

        raise serializers.ValidationError(
            "El complemento del CI solo puede contener letras y números."
        )

    return valor


def normalizar_expedido(
    valor,
):
    """
    Valida departamento de expedición.
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:

        raise serializers.ValidationError(
            "Seleccione el departamento de expedición."
        )

    valor = valor.upper()

    if valor not in EXPEDIDOS_BOLIVIA:

        raise serializers.ValidationError(
            "El departamento de expedición seleccionado no es válido."
        )

    return valor


def validar_rol_oncologia(
    valor,
):
    """
    Solo permite crear:

    ONCOLOGO
    JEFE_ONCOLOGIA
    """

    valor = normalizar_texto_opcional(
        valor
    )

    if valor is None:

        raise serializers.ValidationError(
            "Seleccione el rol del usuario."
        )

    valor = valor.upper()

    if valor not in ROLES_ONCOLOGIA_PERMITIDOS:

        raise serializers.ValidationError(
            "El rol seleccionado no es válido."
        )

    rol = (
        Rol.objects
        .filter(
            codigo=valor,
            activo=True,
        )
        .first()
    )

    if not rol:

        raise serializers.ValidationError(
            "El rol seleccionado no se encuentra disponible."
        )

    return valor


# ==========================================================
# SERIALIZER CREAR ONCÓLOGO
# ==========================================================


class CrearOncologoSerializer(
    serializers.Serializer
):

    # ======================================================
    # DATOS PERSONALES
    # ======================================================

    nombres = serializers.CharField(
        max_length=100,
    )

    apellido_paterno = serializers.CharField(
        max_length=80,
    )

    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    # ======================================================
    # DOCUMENTO
    # ======================================================

    ci_numero = serializers.CharField(
        required=True,
        allow_blank=False,
        max_length=20,
    )

    ci_complemento = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=10,
    )

    ci_expedido = serializers.ChoiceField(
        choices=[
            (
                codigo,
                nombre,
            )
            for codigo, nombre
            in EXPEDIDOS_BOLIVIA.items()
        ],
        required=True,
    )

    # ======================================================
    # CORREO
    # ======================================================

    correo = serializers.EmailField(
        max_length=150,
    )

    # ======================================================
    # DATOS PROFESIONALES
    # ======================================================

    matricula_profesional = (
        serializers.CharField(
            required=True,
            allow_blank=False,
            allow_null=False,
            max_length=30,
        )
    )

    subespecialidad = serializers.ChoiceField(
        choices=[
            (
                valor,
                valor,
            )
            for valor
            in SUBESPECIALIDADES_ONCOLOGIA
        ],
        required=True,
    )

    telefono_institucional = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=8,
        )
    )

    # ======================================================
    # ROL
    # ======================================================

    rol_codigo = serializers.ChoiceField(
        choices=[
            (
                "ONCOLOGO",
                "Oncólogo",
            ),
            (
                "JEFE_ONCOLOGIA",
                "Jefe de Oncología",
            ),
        ],
        required=True,
    )

    # ======================================================
    # VALIDACIÓN NOMBRES
    # ======================================================

    def validate_nombres(
        self,
        valor,
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )

        return valor

    # ======================================================
    # APELLIDO PATERNO
    # ======================================================

    def validate_apellido_paterno(
        self,
        valor,
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )

        return valor

    # ======================================================
    # APELLIDO MATERNO
    # ======================================================

    def validate_apellido_materno(
        self,
        valor,
    ):

        return normalizar_texto_opcional(
            valor
        )

    # ======================================================
    # CORREO
    # ======================================================

    def validate_correo(
        self,
        valor,
    ):

        valor = (
            valor
            .strip()
            .lower()
        )

        if " " in valor:

            raise serializers.ValidationError(
                "El correo no puede contener espacios."
            )

        if ".." in valor:

            raise serializers.ValidationError(
                "El correo no puede contener dos puntos consecutivos."
            )

        if (
            Usuario.objects
            .filter(
                correo__iexact=valor
            )
            .exists()
        ):

            raise serializers.ValidationError(
                "Este correo ya se encuentra registrado."
            )

        return valor

    # ======================================================
    # CI
    # ======================================================

    def validate_ci_numero(
        self,
        valor,
    ):

        return normalizar_y_validar_ci(
            valor
        )

    # ======================================================
    # COMPLEMENTO
    # ======================================================

    def validate_ci_complemento(
        self,
        valor,
    ):

        return normalizar_complemento(
            valor
        )

    # ======================================================
    # EXPEDIDO
    # ======================================================

    def validate_ci_expedido(
        self,
        valor,
    ):

        return normalizar_expedido(
            valor
        )

    # ======================================================
    # TELÉFONO PERSONAL
    # ======================================================

    def validate_telefono(
        self,
        valor,
    ):

        return validar_telefono_personal(
            valor
        )

    # ======================================================
    # TELÉFONO INSTITUCIONAL
    # ======================================================

    def validate_telefono_institucional(
        self,
        valor,
    ):

        return validar_telefono_institucional(
            valor
        )

    # ======================================================
    # MATRÍCULA
    # ======================================================

    def validate_matricula_profesional(
        self,
        valor,
    ):

        valor = normalizar_y_validar_matricula(
            valor,
            obligatoria=True,
        )

        if (
            PerfilProfesional.objects
            .filter(
                matricula_profesional__iexact=valor
            )
            .exists()
        ):

            raise serializers.ValidationError(
                "Esta matrícula profesional ya se encuentra registrada."
            )

        return valor

    # ======================================================
    # SUBESPECIALIDAD
    # ======================================================

    def validate_subespecialidad(
        self,
        valor,
    ):

        valor = valor.strip()

        if (
            valor
            not in
            SUBESPECIALIDADES_ONCOLOGIA
        ):

            raise serializers.ValidationError(
                "La subespecialidad seleccionada no es válida."
            )

        return valor

    # ======================================================
    # ROL
    # ======================================================

    def validate_rol_codigo(
        self,
        valor,
    ):

        return validar_rol_oncologia(
            valor
        )

    # ======================================================
    # VALIDACIÓN GENERAL
    # ======================================================

    def validate(
        self,
        attrs,
    ):

        ci_numero = attrs.get(
            "ci_numero"
        )

        ci_complemento = attrs.get(
            "ci_complemento"
        )

        # --------------------------------------------------
        # VERIFICAR CI DUPLICADO
        # --------------------------------------------------

        if (
            Usuario.objects
            .filter(
                ci_numero=ci_numero,
                ci_complemento=ci_complemento,
            )
            .exists()
        ):

            raise serializers.ValidationError(
                {
                    "ci_numero": (
                        "Ya existe un usuario registrado "
                        "con esta cédula de identidad."
                    )
                }
            )

        # --------------------------------------------------
        # NORMALIZAR OPCIONALES
        # --------------------------------------------------

        campos_opcionales = [
            "apellido_materno",
            "telefono",
            "ci_complemento",
            "telefono_institucional",
        ]

        for campo in campos_opcionales:

            if (
                campo in attrs
                and
                attrs[campo] == ""
            ):

                attrs[campo] = None

        # --------------------------------------------------
        # VALORES CONTROLADOS POR BACKEND
        # --------------------------------------------------

        attrs[
            "especialidad"
        ] = ESPECIALIDAD_ONCOLOGIA

        attrs[
            "area_clinica"
        ] = AREA_CLINICA_OSTEOSARCOMA

        return attrs


# ==========================================================
# SERIALIZER EDITAR ONCÓLOGO
# ==========================================================


class EditarOncologoSerializer(
    serializers.Serializer
):

    # ======================================================
    # DATOS PERSONALES
    # ======================================================

    nombres = serializers.CharField(
        required=False,
        max_length=100,
    )

    apellido_paterno = serializers.CharField(
        required=False,
        max_length=80,
    )

    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )

    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    # ======================================================
    # DOCUMENTO
    # ======================================================

    ci_numero = serializers.CharField(
        required=False,
        allow_blank=False,
        max_length=20,
    )

    ci_complemento = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=10,
    )

    ci_expedido = serializers.ChoiceField(
        choices=[
            (
                codigo,
                nombre,
            )
            for codigo, nombre
            in EXPEDIDOS_BOLIVIA.items()
        ],
        required=False,
    )

    # ======================================================
    # CORREO
    # ======================================================

    correo = serializers.EmailField(
        required=False,
        max_length=150,
    )

    # ======================================================
    # PROFESIONAL
    # ======================================================

    matricula_profesional = (
        serializers.CharField(
            required=False,
            allow_blank=False,
            allow_null=False,
            max_length=30,
        )
    )

    subespecialidad = serializers.ChoiceField(
        choices=[
            (
                valor,
                valor,
            )
            for valor
            in SUBESPECIALIDADES_ONCOLOGIA
        ],
        required=False,
    )

    telefono_institucional = (
        serializers.CharField(
            required=False,
            allow_blank=True,
            allow_null=True,
            max_length=8,
        )
    )

    # ======================================================
    # ROL
    # ======================================================

    rol_codigo = serializers.ChoiceField(
        choices=[
            (
                "ONCOLOGO",
                "Oncólogo",
            ),
            (
                "JEFE_ONCOLOGIA",
                "Jefe de Oncología",
            ),
        ],
        required=False,
    )

    # ======================================================
    # USUARIO ID
    # ======================================================

    def obtener_usuario_id(
        self,
    ):

        return self.context.get(
            "usuario_id"
        )

    # ======================================================
    # NOMBRES
    # ======================================================

    def validate_nombres(
        self,
        valor,
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )

        return valor

    # ======================================================
    # APELLIDO PATERNO
    # ======================================================

    def validate_apellido_paterno(
        self,
        valor,
    ):

        valor = valor.strip()

        if len(valor) < 2:

            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )

        return valor

    # ======================================================
    # APELLIDO MATERNO
    # ======================================================

    def validate_apellido_materno(
        self,
        valor,
    ):

        return normalizar_texto_opcional(
            valor
        )

    # ======================================================
    # CORREO
    # ======================================================

    def validate_correo(
        self,
        valor,
    ):

        valor = (
            valor
            .strip()
            .lower()
        )

        usuario_id = self.obtener_usuario_id()

        consulta = (
            Usuario.objects
            .filter(
                correo__iexact=valor
            )
        )

        if usuario_id:

            consulta = consulta.exclude(
                id_usuario=usuario_id
            )

        if consulta.exists():

            raise serializers.ValidationError(
                "Este correo ya se encuentra registrado."
            )

        return valor

    # ======================================================
    # CI
    # ======================================================

    def validate_ci_numero(
        self,
        valor,
    ):

        return normalizar_y_validar_ci(
            valor
        )

    # ======================================================
    # COMPLEMENTO
    # ======================================================

    def validate_ci_complemento(
        self,
        valor,
    ):

        return normalizar_complemento(
            valor
        )

    # ======================================================
    # EXPEDIDO
    # ======================================================

    def validate_ci_expedido(
        self,
        valor,
    ):

        return normalizar_expedido(
            valor
        )

    # ======================================================
    # TELÉFONO PERSONAL
    # ======================================================

    def validate_telefono(
        self,
        valor,
    ):

        return validar_telefono_personal(
            valor
        )

    # ======================================================
    # TELÉFONO INSTITUCIONAL
    # ======================================================

    def validate_telefono_institucional(
        self,
        valor,
    ):

        return validar_telefono_institucional(
            valor
        )

    # ======================================================
    # MATRÍCULA
    # ======================================================

    def validate_matricula_profesional(
        self,
        valor,
    ):

        valor = normalizar_y_validar_matricula(
            valor,
            obligatoria=True,
        )

        usuario_id = self.obtener_usuario_id()

        consulta = (
            PerfilProfesional.objects
            .filter(
                matricula_profesional__iexact=valor
            )
        )

        if usuario_id:

            consulta = consulta.exclude(
                usuario__id_usuario=usuario_id
            )

        if consulta.exists():

            raise serializers.ValidationError(
                "Esta matrícula profesional ya se encuentra registrada."
            )

        return valor

    # ======================================================
    # ROL
    # ======================================================

    def validate_rol_codigo(
        self,
        valor,
    ):

        return validar_rol_oncologia(
            valor
        )

    # ======================================================
    # VALIDACIÓN GENERAL
    # ======================================================

    def validate(
        self,
        attrs,
    ):

        usuario_id = self.obtener_usuario_id()

        # --------------------------------------------------
        # VERIFICACIÓN DE CI EN EDICIÓN
        # --------------------------------------------------

        if usuario_id:

            usuario_actual = (
                Usuario.objects
                .filter(
                    id_usuario=usuario_id
                )
                .first()
            )

            if usuario_actual:

                ci_numero = attrs.get(
                    "ci_numero",
                    usuario_actual.ci_numero,
                )

                ci_complemento = attrs.get(
                    "ci_complemento",
                    usuario_actual.ci_complemento,
                )

                if ci_numero:

                    consulta = (
                        Usuario.objects
                        .filter(
                            ci_numero=ci_numero,
                            ci_complemento=ci_complemento,
                        )
                        .exclude(
                            id_usuario=usuario_id
                        )
                    )

                    if consulta.exists():

                        raise serializers.ValidationError(
                            {
                                "ci_numero": (
                                    "Ya existe otro usuario "
                                    "registrado con esta "
                                    "cédula de identidad."
                                )
                            }
                        )

        # --------------------------------------------------
        # NORMALIZAR OPCIONALES
        # --------------------------------------------------

        campos_opcionales = [
            "apellido_materno",
            "telefono",
            "ci_complemento",
            "telefono_institucional",
        ]

        for campo in campos_opcionales:

            if (
                campo in attrs
                and
                attrs[campo] == ""
            ):

                attrs[campo] = None

        return attrs