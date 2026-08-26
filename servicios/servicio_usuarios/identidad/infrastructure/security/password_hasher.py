from django.contrib.auth.hashers import (
    make_password,
    check_password,
)


class PasswordHasher:
    """
    Servicio encargado de generar
    y validar contraseñas utilizando
    el algoritmo configurado por Django.
    """

    def generar_hash(
        self,
        password: str
    ) -> str:

        return make_password(
            password
        )


    def verificar_password(
        self,
        password_plano: str,
        password_hash: str
    ) -> bool:

        return check_password(
            password_plano,
            password_hash
        )