import secrets
import string
import unicodedata

from django.db import transaction

from identidad.application.services.oncologo_email_service import (
    OncologoEmailService,
)

from identidad.infrastructure.repositories.usuario_repository import (
    UsuarioRepository,
)

from identidad.infrastructure.repositories.credencial_repository import (
    CredencialRepository,
)

from identidad.infrastructure.repositories.perfil_repository import (
    PerfilRepository,
)

from identidad.infrastructure.repositories.rol_repository import (
    RolRepository,
)

from identidad.infrastructure.security.password_hasher import (
    PasswordHasher,
)

from identidad.models import (
    EstadoUsuario,
    PerfilProfesional,
    Usuario,
)


# ==========================================================
# CONSTANTES
# ==========================================================

ESPECIALIDAD_ONCOLOGIA = "Oncología"

AREA_CLINICA_OSTEOSARCOMA = (
    "Tumores óseos / Osteosarcoma"
)

ROLES_PERMITIDOS = {
    "ONCOLOGO",
    "JEFE_ONCOLOGIA",
}


# ==========================================================
# CASO DE USO
# ==========================================================


class CrearOncologoUseCase:
    """
    Registra una nueva cuenta profesional.

    El sistema:

    1. Valida correo, CI y matrícula.
    2. Genera automáticamente el nombre de usuario.
    3. Genera una contraseña temporal segura.
    4. Guarda únicamente el hash de la contraseña.
    5. Crea el perfil profesional.
    6. Asigna ONCOLOGO o JEFE_ONCOLOGIA.
    7. Envía las credenciales al correo institucional.

    Si falla alguna operación de persistencia,
    la transacción se revierte.
    """

    # ======================================================
    # INICIALIZACIÓN
    # ======================================================

    def __init__(
        self
    ):

        self.usuario_repository = (
            UsuarioRepository()
        )

        self.credencial_repository = (
            CredencialRepository()
        )

        self.perfil_repository = (
            PerfilRepository()
        )

        self.rol_repository = (
            RolRepository()
        )

        self.password_hasher = (
            PasswordHasher()
        )

        self.email_service = (
            OncologoEmailService()
        )

    # ======================================================
    # EJECUTAR
    # ======================================================

    @transaction.atomic
    def ejecutar(
        self,
        datos,
        usuario_creador=None,
    ):

        # ==================================================
        # DATOS PERSONALES
        # ==================================================

        nombres = (
            str(
                datos["nombres"]
            )
            .strip()
        )

        apellido_paterno = (
            str(
                datos["apellido_paterno"]
            )
            .strip()
        )

        apellido_materno = (
            self._normalizar_opcional(
                datos.get(
                    "apellido_materno"
                )
            )
        )

        telefono = (
            self._normalizar_opcional(
                datos.get(
                    "telefono"
                )
            )
        )

        # ==================================================
        # CORREO
        # ==================================================

        correo = (
            str(
                datos["correo"]
            )
            .strip()
            .lower()
        )

        # ==================================================
        # CI
        # ==================================================

        ci_numero = (
            str(
                datos["ci_numero"]
            )
            .strip()
        )

        ci_complemento = (
            self._normalizar_opcional(
                datos.get(
                    "ci_complemento"
                )
            )
        )

        if ci_complemento:

            ci_complemento = (
                ci_complemento
                .upper()
            )

        ci_expedido = (
            str(
                datos["ci_expedido"]
            )
            .strip()
            .upper()
        )

        # ==================================================
        # DATOS PROFESIONALES
        # ==================================================

        matricula_profesional = (
            str(
                datos["matricula_profesional"]
            )
            .strip()
            .upper()
        )

        subespecialidad = (
            str(
                datos["subespecialidad"]
            )
            .strip()
        )

        telefono_institucional = (
            self._normalizar_opcional(
                datos.get(
                    "telefono_institucional"
                )
            )
        )

        # ==================================================
        # ROL
        # ==================================================

        rol_codigo = (
            str(
                datos["rol_codigo"]
            )
            .strip()
            .upper()
        )

        # ==================================================
        # VALIDAR ROL
        # ==================================================

        if (
            rol_codigo
            not in
            ROLES_PERMITIDOS
        ):

            raise Exception(
                "El rol seleccionado no es válido."
            )

        # ==================================================
        # VALIDAR CORREO
        # ==================================================

        usuario_existente = (
            self.usuario_repository
            .obtener_por_correo(
                correo
            )
        )

        if usuario_existente:

            raise Exception(
                "El correo ya está registrado."
            )

        # ==================================================
        # VALIDAR CI
        # ==================================================

        ci_existente = (
            Usuario.objects
            .filter(
                ci_numero=ci_numero,
                ci_complemento=ci_complemento,
            )
            .exists()
        )

        if ci_existente:

            raise Exception(
                "Ya existe un usuario registrado "
                "con esta cédula de identidad."
            )

        # ==================================================
        # VALIDAR MATRÍCULA
        # ==================================================

        matricula_existente = (
            PerfilProfesional.objects
            .filter(
                matricula_profesional__iexact=(
                    matricula_profesional
                )
            )
            .exists()
        )

        if matricula_existente:

            raise Exception(
                "La matrícula profesional "
                "ya se encuentra registrada."
            )

        # ==================================================
        # ESTADO ACTIVO
        # ==================================================

        estado_activo = (
            self.obtener_estado_activo()
        )

        if not estado_activo:

            raise Exception(
                "No existe el estado ACTIVO "
                "en la base de datos."
            )

        # ==================================================
        # OBTENER ROL
        # ==================================================

        rol = (
            self.rol_repository
            .obtener_por_codigo(
                rol_codigo
            )
        )

        if not rol:

            raise Exception(
                f"No existe el rol {rol_codigo}."
            )

        if not rol.activo:

            raise Exception(
                f"El rol {rol_codigo} "
                "se encuentra inactivo."
            )

        # ==================================================
        # GENERAR NOMBRE DE USUARIO
        # ==================================================

        nombre_usuario = (
            self.generar_nombre_usuario(
                nombres=nombres,
                apellido_paterno=(
                    apellido_paterno
                ),
                apellido_materno=(
                    apellido_materno
                ),
                ci_numero=(
                    ci_numero
                ),
            )
        )

        # ==================================================
        # GENERAR CONTRASEÑA TEMPORAL
        # ==================================================

        password_temporal = (
            self.generar_password_temporal()
        )

        # ==================================================
        # CREAR USUARIO
        # ==================================================

        usuario = (
            self.usuario_repository
            .crear(
                {
                    "estado_usuario":
                        estado_activo,

                    "nombres":
                        nombres,

                    "apellido_paterno":
                        apellido_paterno,

                    "apellido_materno":
                        apellido_materno,

                    "correo":
                        correo,

                    "nombre_usuario":
                        nombre_usuario,

                    "telefono":
                        telefono,

                    "ci_numero":
                        ci_numero,

                    "ci_complemento":
                        ci_complemento,

                    "ci_expedido":
                        ci_expedido,
                }
            )
        )

        # ==================================================
        # CREAR CREDENCIAL
        # ==================================================

        password_hash = (
            self.password_hasher
            .generar_hash(
                password_temporal
            )
        )

        self.credencial_repository.crear(
            {
                "usuario":
                    usuario,

                "password_hash":
                    password_hash,

                "debe_cambiar_password":
                    True,
            }
        )

        # ==================================================
        # CARGO
        # ==================================================

        if (
            rol_codigo
            ==
            "JEFE_ONCOLOGIA"
        ):

            cargo = (
                "Jefe de Oncología"
            )

        else:

            cargo = (
                "Oncólogo"
            )

        # ==================================================
        # PERFIL PROFESIONAL
        # ==================================================

        self.perfil_repository.crear(
            {
                "usuario":
                    usuario,

                "matricula_profesional":
                    matricula_profesional,

                "especialidad":
                    ESPECIALIDAD_ONCOLOGIA,

                "subespecialidad":
                    subespecialidad,

                "area_clinica":
                    AREA_CLINICA_OSTEOSARCOMA,

                "cargo":
                    cargo,

                "telefono_institucional":
                    telefono_institucional,
            }
        )

        # ==================================================
        # ASIGNAR ROL
        # ==================================================

        self.rol_repository.asignar_rol(
            usuario,
            rol,
            usuario_creador,
        )

        # ==================================================
        # ENVIAR CREDENCIALES
        # ==================================================
        #
        # La contraseña temporal existe en texto plano
        # únicamente en memoria durante este proceso.
        #
        # Después del envío no se persiste.
        # ==================================================

        self.email_service.enviar_credenciales_temporales(
            usuario=usuario,
            password_temporal=(
                password_temporal
            ),
            rol_codigo=rol_codigo,
        )

        # ==================================================
        # INFORMACIÓN TRANSITORIA PARA RESPUESTA/AUDITORÍA
        # ==================================================
        #
        # Nunca incluimos password_temporal en la respuesta.
        # ==================================================

        usuario.rol_codigo_creado = (
            rol_codigo
        )

        usuario.correo_credenciales_enviado = (
            True
        )

        return usuario

    # ======================================================
    # ESTADO ACTIVO
    # ======================================================

    def obtener_estado_activo(
        self
    ):

        return (
            EstadoUsuario.objects
            .filter(
                codigo="ACTIVO"
            )
            .first()
        )

    # ======================================================
    # GENERAR NOMBRE DE USUARIO
    # ======================================================

    def generar_nombre_usuario(
        self,
        *,
        nombres,
        apellido_paterno,
        apellido_materno,
        ci_numero,
    ):
        """
        Formato:

        inicial del primer nombre
        +
        apellido paterno
        +
        últimos 3 dígitos del CI

        Ejemplo:

        Andrea López
        CI 8459217

        alopez217
        """

        primer_nombre = (
            nombres
            .split()[0]
            if nombres
            else "u"
        )

        primer_nombre = (
            self._normalizar_para_usuario(
                primer_nombre
            )
        )

        apellido = (
            self._normalizar_para_usuario(
                apellido_paterno
            )
        )

        if not apellido:

            apellido = (
                self._normalizar_para_usuario(
                    apellido_materno
                    or
                    "usuario"
                )
            )

        digitos_ci = "".join(
            caracter
            for caracter
            in str(
                ci_numero
            )
            if caracter.isdigit()
        )

        ultimos_ci = (
            digitos_ci[-3:]
            if len(
                digitos_ci
            ) >= 3
            else
            digitos_ci
        )

        if not ultimos_ci:

            ultimos_ci = "000"

        inicial = (
            primer_nombre[0]
            if primer_nombre
            else "u"
        )

        base = (
            f"{inicial}"
            f"{apellido}"
            f"{ultimos_ci}"
        )

        base = (
            base[:70]
            .lower()
        )

        # --------------------------------------------------
        # DISPONIBLE
        # --------------------------------------------------

        if not (
            self.usuario_repository
            .obtener_por_nombre_usuario(
                base
            )
        ):

            return base

        # --------------------------------------------------
        # COLISIÓN
        # --------------------------------------------------

        contador = 2

        while True:

            sufijo = str(
                contador
            )

            longitud_base = (
                80
                -
                len(
                    sufijo
                )
            )

            candidato = (
                f"{base[:longitud_base]}"
                f"{sufijo}"
            )

            existe = (
                self.usuario_repository
                .obtener_por_nombre_usuario(
                    candidato
                )
            )

            if not existe:

                return candidato

            contador += 1

            if contador > 9999:

                raise Exception(
                    "No fue posible generar "
                    "un nombre de usuario único."
                )

    # ======================================================
    # GENERAR CONTRASEÑA
    # ======================================================

    def generar_password_temporal(
        self,
        longitud=12,
    ):
        """
        Genera una contraseña segura utilizando secrets.

        Garantiza:

        - mayúscula
        - minúscula
        - número
        - símbolo
        """

        if longitud < 10:

            longitud = 10

        mayusculas = (
            string.ascii_uppercase
        )

        minusculas = (
            string.ascii_lowercase
        )

        numeros = (
            string.digits
        )

        simbolos = (
            "@#$%&*!?"
        )

        todos = (
            mayusculas
            +
            minusculas
            +
            numeros
            +
            simbolos
        )

        password = [

            secrets.choice(
                mayusculas
            ),

            secrets.choice(
                minusculas
            ),

            secrets.choice(
                numeros
            ),

            secrets.choice(
                simbolos
            ),

        ]

        for _ in range(
            longitud
            -
            len(
                password
            )
        ):

            password.append(
                secrets.choice(
                    todos
                )
            )

        # --------------------------------------------------
        # MEZCLA SEGURA
        # --------------------------------------------------

        for indice in range(
            len(
                password
            )
            -
            1,
            0,
            -1,
        ):

            posicion = (
                secrets.randbelow(
                    indice
                    +
                    1
                )
            )

            password[
                indice
            ], password[
                posicion
            ] = (
                password[
                    posicion
                ],
                password[
                    indice
                ],
            )

        return "".join(
            password
        )

    # ======================================================
    # NORMALIZAR USUARIO
    # ======================================================

    def _normalizar_para_usuario(
        self,
        valor,
    ):

        if not valor:

            return ""

        valor = str(
            valor
        ).strip()

        valor = unicodedata.normalize(
            "NFKD",
            valor,
        )

        valor = "".join(
            caracter
            for caracter
            in valor
            if not unicodedata.combining(
                caracter
            )
        )

        valor = valor.lower()

        return "".join(
            caracter
            for caracter
            in valor
            if caracter.isalnum()
        )

    # ======================================================
    # NORMALIZAR OPCIONAL
    # ======================================================

    def _normalizar_opcional(
        self,
        valor,
    ):

        if valor is None:

            return None

        valor = str(
            valor
        ).strip()

        if not valor:

            return None

        return valor