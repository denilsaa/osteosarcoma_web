import uuid
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("clinica", "0013_altapacienteoffline")]
    operations = [
        migrations.CreateModel(
            name="AltaCasoOffline",
            fields=[
                ("operacion_uuid", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("actor_uuid", models.UUIDField()),
                ("payload_sha256", models.CharField(max_length=64)),
                ("creado_en", models.DateTimeField(auto_now_add=True)),
                ("caso", models.ForeignKey(to="clinica.casoclinico", db_column="id_caso", on_delete=django.db.models.deletion.PROTECT)),
            ],
            options={"db_table": "altas_casos_offline"},
        ),
    ]
