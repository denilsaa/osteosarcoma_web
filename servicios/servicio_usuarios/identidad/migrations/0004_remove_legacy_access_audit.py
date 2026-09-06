from django.db import migrations


class Migration(
    migrations.Migration
):

    dependencies = [

        (
            "identidad",
            "0003_desafio_segundo_factor",
        ),

    ]


    operations = [

        # ==================================================
        # ELIMINAR AUDITORÍA LEGADA DE SERVICIO_USUARIOS
        # ==================================================
        #
        # El historial de auditoría pertenece exclusivamente
        # al microservicio servicio_auditoria.
        #
        # Estas tablas se encuentran vacías y ya no son
        # utilizadas por la aplicación.
        # ==================================================

        migrations.DeleteModel(
            name="EventoAcceso",
        ),

        migrations.DeleteModel(
            name="TipoEventoAcceso",
        ),

    ]