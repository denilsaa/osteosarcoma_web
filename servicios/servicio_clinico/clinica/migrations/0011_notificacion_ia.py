import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinica", "0010_notificaciones_clinicas")]
    operations = [
        migrations.AlterField(
            model_name="notificacionclinica", name="evento_gestion",
            field=models.OneToOneField(
                to="clinica.historialgestioncaso", db_column="id_gestion",
                related_name="notificacion", null=True, blank=True,
                on_delete=django.db.models.deletion.CASCADE,
            ),
        ),
        migrations.AddField(
            model_name="notificacionclinica", name="evento_ia_uuid",
            field=models.UUIDField(null=True, blank=True, unique=True),
        ),
    ]
