from django.core.management.base import BaseCommand

from identidad.models import EstadoRecuperacion


class Command(BaseCommand):

    help = (
        "Asegura los estados necesarios "
        "para el flujo de recuperación."
    )

    def handle(
        self,
        *args,
        **options,
    ):

        estados = [

            (
                "PENDIENTE",
                "Pendiente",
                "Solicitud pendiente de revisión por Jefatura.",
            ),

            (
                "APROBADA",
                "Aprobada",
                "Solicitud aprobada por Jefatura.",
            ),

            (
                "RECHAZADA",
                "Rechazada",
                "Solicitud rechazada por Jefatura.",
            ),

            (
                "UTILIZADA",
                "Utilizada",
                "El código ya fue utilizado para cambiar la contraseña.",
            ),

            (
                "EXPIRADA",
                "Expirada",
                "La solicitud o el código superó su tiempo de validez.",
            ),

        ]


        for (
            codigo,
            nombre,
            descripcion,
        ) in estados:

            EstadoRecuperacion.objects.update_or_create(

                codigo=codigo,

                defaults={

                    "nombre":
                        nombre,

                    "descripcion":
                        descripcion,

                },

            )


        self.stdout.write(

            self.style.SUCCESS(

                "Estados de recuperación preparados correctamente."

            )

        )