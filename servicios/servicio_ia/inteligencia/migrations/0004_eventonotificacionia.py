import uuid
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("inteligencia", "0003_solicitudanalisisia")]
    operations = [
        migrations.CreateModel(
            name="EventoNotificacionIA",
            fields=[
                ("id_evento", models.UUIDField(primary_key=True, serialize=False, editable=False, default=uuid.uuid4)),
                ("caso_uuid", models.UUIDField()),
                ("estado", models.CharField(max_length=20)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("publicado_en", models.DateTimeField(null=True, blank=True)),
                ("intentos_publicacion", models.PositiveIntegerField(default=0)),
                ("solicitud", models.OneToOneField(to="inteligencia.solicitudanalisisia",
                    related_name="evento_notificacion", db_column="id_solicitud",
                    on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={"db_table": "eventos_notificacion_ia"},
        ),
        migrations.AddIndex(
            model_name="eventonotificacionia",
            index=models.Index(fields=["publicado_en", "fecha_creacion"], name="idx_ia_evt_pendiente"),
        ),
    ]
