from django.core.management.base import BaseCommand

from identidad.models import (
    EstadoUsuario,
    Rol,
    Permiso,
)


class Command(BaseCommand):

    help = "Carga datos iniciales del servicio identidad"


    def handle(self, *args, **kwargs):

        self.crear_estados_usuario()

        self.crear_roles()

        self.crear_permisos()

        self.stdout.write(
            self.style.SUCCESS(
                "Datos iniciales cargados correctamente"
            )
        )


    def crear_estados_usuario(self):

        estados = [

            {
                "codigo": "ACTIVO",
                "nombre": "Activo",
                "descripcion": "Usuario habilitado",
                "es_operativo": True,
            },

            {
                "codigo": "INACTIVO",
                "nombre": "Inactivo",
                "descripcion": "Usuario deshabilitado",
                "es_operativo": False,
            },

            {
                "codigo": "BLOQUEADO",
                "nombre": "Bloqueado",
                "descripcion": "Usuario bloqueado",
                "es_operativo": False,
            },

            {
                "codigo": "PENDIENTE",
                "nombre": "Pendiente",
                "descripcion": "Usuario pendiente de aprobación",
                "es_operativo": False,
            },

        ]


        for estado in estados:

            EstadoUsuario.objects.get_or_create(
                codigo=estado["codigo"],
                defaults=estado,
            )


    def crear_roles(self):

        roles = [

            {
                "codigo": "JEFE_ONCOLOGIA",
                "nombre": "Jefe de Oncología",
                "descripcion": "Administrador del módulo oncológico",
                "activo": True,
            },


            {
                "codigo": "ONCOLOGO",
                "nombre": "Oncólogo",
                "descripcion": "Médico especialista",
                "activo": True,
            },

        ]


        for rol in roles:

            Rol.objects.get_or_create(
                codigo=rol["codigo"],
                defaults=rol,
            )


    def crear_permisos(self):

        permisos = [

            {
                "codigo": "ONCOLOGO_CREAR",
                "nombre": "Crear oncólogos",
                "modulo": "IDENTIDAD",
                "descripcion": "Registrar cuentas",
            },

            {
                "codigo": "ONCOLOGO_EDITAR",
                "nombre": "Editar oncólogos",
                "modulo": "IDENTIDAD",
                "descripcion": "Modificar cuentas",
            },

            {
                "codigo": "ONCOLOGO_LISTAR",
                "nombre": "Listar oncólogos",
                "modulo": "IDENTIDAD",
                "descripcion": "Consultar cuentas",
            },

            {
                "codigo": "RECUPERACION_APROBAR",
                "nombre": "Aprobar recuperación",
                "modulo": "SEGURIDAD",
                "descripcion": "Aprobar cambios de contraseña",
            },

            {
                "codigo": "USUARIO_ACTIVAR",
                "nombre": "Activar usuario",
                "modulo": "IDENTIDAD",
                "descripcion": "Activar cuentas",
            },

            {
                "codigo": "USUARIO_DESACTIVAR",
                "nombre": "Desactivar usuario",
                "modulo": "IDENTIDAD",
                "descripcion": "Desactivar cuentas",
            },

            {
                "codigo": "PERFIL_EDITAR",
                "nombre": "Editar perfil",
                "modulo": "PERFIL",
                "descripcion": "Editar datos personales",
            },

        ]


        for permiso in permisos:

            Permiso.objects.get_or_create(
                codigo=permiso["codigo"],
                defaults=permiso,
            )