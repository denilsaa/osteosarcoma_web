
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("clinica", "0008_seed_criterios_valoracion")]

    operations = [
        migrations.CreateModel(
            name="HistorialGestionCaso",
            fields=[
                ("id_gestion", models.BigAutoField(primary_key=True, serialize=False)),
                ("tipo_cambio", models.CharField(max_length=20)),
                ("valor_anterior", models.CharField(blank=True, max_length=80, null=True)),
                ("valor_nuevo", models.CharField(max_length=80)),
                ("actor_uuid", models.UUIDField()),
                ("motivo", models.TextField()),
                ("fecha_cambio", models.DateTimeField(auto_now_add=True)),
                ("caso", models.ForeignKey(
                    db_column="id_caso", on_delete=django.db.models.deletion.CASCADE,
                    related_name="historial_gestion", to="clinica.casoclinico",
                )),
            ],
            options={"db_table": "historial_gestion_caso"},
        ),
        migrations.AddIndex(
            model_name="historialgestioncaso",
            index=models.Index(fields=["caso", "fecha_cambio"], name="idx_gestion_caso_fecha"),
        ),
    ]
