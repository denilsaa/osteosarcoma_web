import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinica", "0009_historial_gestion_caso")]
    operations = [
        migrations.CreateModel(
            name="NotificacionClinica",
            fields=[
                ("id_notificacion", models.UUIDField(primary_key=True, serialize=False, default=uuid.uuid4, editable=False)),
                ("destinatario_uuid", models.UUIDField()),
                ("tipo", models.CharField(max_length=24)),
                ("titulo", models.CharField(max_length=100)),
                ("mensaje", models.CharField(max_length=255)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_lectura", models.DateTimeField(null=True, blank=True)),
                ("caso", models.ForeignKey(db_column="id_caso", to="clinica.casoclinico",
                    related_name="notificaciones", on_delete=django.db.models.deletion.CASCADE)),
                ("evento_gestion", models.OneToOneField(db_column="id_gestion",
                    to="clinica.historialgestioncaso", related_name="notificacion",
                    on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={"db_table": "notificaciones_clinicas"},
        ),
        migrations.AddIndex(model_name="notificacionclinica", index=models.Index(
            fields=["destinatario_uuid", "fecha_creacion"], name="idx_notif_dest_fecha")),
        migrations.AddIndex(model_name="notificacionclinica", index=models.Index(
            fields=["destinatario_uuid", "fecha_lectura"], name="idx_notif_dest_lect")),
    ]
