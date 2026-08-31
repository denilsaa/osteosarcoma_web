import re

from rest_framework import serializers

from identidad.models import PerfilProfesional, Usuario


PATRON_TELEFONO_PERSONAL = re.compile(r"^[67]\d{7}$")
PATRON_TELEFONO_INSTITUCIONAL = re.compile(r"^\d{8}$")
PATRON_MATRICULA = re.compile(r"^[A-Z0-9]+(?:[./-][A-Z0-9]+)*$")
PATRON_USUARIO = re.compile(r"^[A-Za-z][A-Za-z0-9._-]{2,29}$")
PATRON_MAYUSCULA = re.compile(r"[A-Z]")
PATRON_MINUSCULA = re.compile(r"[a-z]")
PATRON_NUMERO = re.compile(r"\d")
PATRON_ESPECIAL = re.compile(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?`~]")

CONTRASENAS_COMUNES = {
    "12345678",
    "123456789",
    "password",
    "password123",
    "qwerty123",
    "admin123",
    "oncologo123",
}


def validar_telefono_personal(valor):
    if valor in (None, ""):
        return None

    valor = valor.strip()

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El teléfono personal solo puede contener números."
        )

    if len(valor) != 8:
        raise serializers.ValidationError(
            "El teléfono personal debe tener exactamente 8 dígitos."
        )

    if not PATRON_TELEFONO_PERSONAL.fullmatch(valor):
        raise serializers.ValidationError(
            "El teléfono personal debe comenzar con 6 o 7."
        )

    return valor


def validar_telefono_institucional(valor):
    if valor in (None, ""):
        return None

    valor = valor.strip()

    if not valor.isdigit():
        raise serializers.ValidationError(
            "El teléfono institucional solo puede contener números."
        )

    if not PATRON_TELEFONO_INSTITUCIONAL.fullmatch(valor):
        raise serializers.ValidationError(
            "El teléfono institucional debe tener exactamente 8 dígitos."
        )

    return valor


def normalizar_y_validar_matricula(valor, obligatoria=False):
    if valor in (None, ""):
        if obligatoria:
            raise serializers.ValidationError(
                "La matrícula profesional es obligatoria."
            )
        return None

    valor = valor.strip().upper().replace(" ", "")

    if len(valor) < 4 or len(valor) > 30:
        raise serializers.ValidationError(
            "La matrícula debe tener entre 4 y 30 caracteres."
        )

    if not PATRON_MATRICULA.fullmatch(valor):
        raise serializers.ValidationError(
            "Use solo letras, números y separadores válidos: guion (-), punto (.) o barra (/)."
        )

    return valor


def validar_formato_usuario(valor):
    valor = valor.strip().lower()

    if len(valor) < 3 or len(valor) > 30:
        raise serializers.ValidationError(
            "El nombre de usuario debe tener entre 3 y 30 caracteres."
        )

    if " " in valor:
        raise serializers.ValidationError(
            "El nombre de usuario no puede contener espacios."
        )

    if not PATRON_USUARIO.fullmatch(valor):
        raise serializers.ValidationError(
            "El nombre de usuario debe comenzar con una letra y solo puede contener letras, números, punto, guion o guion bajo."
        )

    return valor


def validar_password_segura(password, nombre_usuario=""):
    errores = []

    if len(password) < 8 or len(password) > 64:
        errores.append("Debe tener entre 8 y 64 caracteres.")

    if not PATRON_MAYUSCULA.search(password):
        errores.append("Debe incluir al menos una letra mayúscula.")

    if not PATRON_MINUSCULA.search(password):
        errores.append("Debe incluir al menos una letra minúscula.")

    if not PATRON_NUMERO.search(password):
        errores.append("Debe incluir al menos un número.")

    if not PATRON_ESPECIAL.search(password):
        errores.append("Debe incluir al menos un carácter especial.")

    if re.search(r"\s", password):
        errores.append("No puede contener espacios.")

    usuario = (nombre_usuario or "").strip().lower()
    if len(usuario) >= 3 and usuario in password.lower():
        errores.append("No puede contener el nombre de usuario.")

    if password.lower() in CONTRASENAS_COMUNES:
        errores.append("No puede utilizar una contraseña común o predecible.")

    if errores:
        raise serializers.ValidationError(" ".join(errores))

    return password


class CrearOncologoSerializer(serializers.Serializer):
    nombres = serializers.CharField(max_length=100)
    apellido_paterno = serializers.CharField(max_length=80)
    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )
    correo = serializers.EmailField(max_length=150)
    nombre_usuario = serializers.CharField(max_length=30)
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        max_length=64,
        trim_whitespace=False,
    )
    matricula_profesional = serializers.CharField(
        required=True,
        allow_blank=False,
        allow_null=False,
        max_length=30,
    )
    especialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )
    subespecialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )
    telefono_institucional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    def validate_nombres(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )
        return valor

    def validate_apellido_paterno(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )
        return valor

    def validate_correo(self, valor):
        valor = valor.strip().lower()

        if " " in valor:
            raise serializers.ValidationError(
                "El correo no puede contener espacios."
            )

        if ".." in valor:
            raise serializers.ValidationError(
                "El correo no puede contener dos puntos (.) consecutivos."
            )

        if Usuario.objects.filter(correo__iexact=valor).exists():
            raise serializers.ValidationError(
                "Este correo ya se encuentra registrado."
            )

        return valor

    def validate_nombre_usuario(self, valor):
        valor = validar_formato_usuario(valor)

        if Usuario.objects.filter(nombre_usuario__iexact=valor).exists():
            raise serializers.ValidationError(
                "Este nombre de usuario ya se encuentra registrado."
            )

        return valor

    def validate_telefono(self, valor):
        return validar_telefono_personal(valor)

    def validate_telefono_institucional(self, valor):
        return validar_telefono_institucional(valor)

    def validate_matricula_profesional(self, valor):
        valor = normalizar_y_validar_matricula(
            valor,
            obligatoria=True,
        )

        if PerfilProfesional.objects.filter(
            matricula_profesional__iexact=valor
        ).exists():
            raise serializers.ValidationError(
                "Esta matrícula profesional ya se encuentra registrada."
            )

        return valor

    def validate(self, attrs):
        password = attrs.get("password", "")
        nombre_usuario = attrs.get("nombre_usuario", "")

        attrs["password"] = validar_password_segura(
            password,
            nombre_usuario,
        )

        campos_opcionales = [
            "apellido_materno",
            "telefono",
            "especialidad",
            "subespecialidad",
            "telefono_institucional",
        ]

        for campo in campos_opcionales:
            if campo in attrs and attrs[campo] == "":
                attrs[campo] = None

        return attrs


class EditarOncologoSerializer(serializers.Serializer):
    nombres = serializers.CharField(required=False, max_length=100)
    apellido_paterno = serializers.CharField(required=False, max_length=80)
    apellido_materno = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=80,
    )
    correo = serializers.EmailField(required=False, max_length=150)
    nombre_usuario = serializers.CharField(required=False, max_length=30)
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )
    matricula_profesional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=30,
    )
    especialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )
    subespecialidad = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=120,
    )
    telefono_institucional = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        max_length=8,
    )

    def obtener_usuario_id(self):
        return self.context.get("usuario_id")

    def validate_nombres(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese los nombres del oncólogo."
            )
        return valor

    def validate_apellido_paterno(self, valor):
        valor = valor.strip()
        if len(valor) < 2:
            raise serializers.ValidationError(
                "Ingrese el apellido paterno."
            )
        return valor

    def validate_correo(self, valor):
        valor = valor.strip().lower()

        if " " in valor:
            raise serializers.ValidationError(
                "El correo no puede contener espacios."
            )

        if ".." in valor:
            raise serializers.ValidationError(
                "El correo no puede contener dos puntos (.) consecutivos."
            )

        consulta = Usuario.objects.filter(correo__iexact=valor)
        usuario_id = self.obtener_usuario_id()

        if usuario_id:
            consulta = consulta.exclude(id_usuario=usuario_id)

        if consulta.exists():
            raise serializers.ValidationError(
                "Este correo ya pertenece a otra cuenta."
            )

        return valor

    def validate_nombre_usuario(self, valor):
        valor = validar_formato_usuario(valor)

        consulta = Usuario.objects.filter(nombre_usuario__iexact=valor)
        usuario_id = self.obtener_usuario_id()

        if usuario_id:
            consulta = consulta.exclude(id_usuario=usuario_id)

        if consulta.exists():
            raise serializers.ValidationError(
                "Este nombre de usuario pertenece a otra cuenta."
            )

        return valor

    def validate_telefono(self, valor):
        return validar_telefono_personal(valor)

    def validate_telefono_institucional(self, valor):
        return validar_telefono_institucional(valor)

    def validate_matricula_profesional(self, valor):
        valor = normalizar_y_validar_matricula(
            valor,
            obligatoria=False,
        )

        if valor is None:
            return None

        consulta = PerfilProfesional.objects.filter(
            matricula_profesional__iexact=valor
        )
        usuario_id = self.obtener_usuario_id()

        if usuario_id:
            consulta = consulta.exclude(usuario_id=usuario_id)

        if consulta.exists():
            raise serializers.ValidationError(
                "Esta matrícula profesional pertenece a otro oncólogo."
            )

        return valor

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "No se enviaron datos para actualizar."
            )

        campos_opcionales = [
            "apellido_materno",
            "telefono",
            "matricula_profesional",
            "especialidad",
            "subespecialidad",
            "telefono_institucional",
        ]

        for campo in campos_opcionales:
            if campo in attrs and attrs[campo] == "":
                attrs[campo] = None

        return attrs
