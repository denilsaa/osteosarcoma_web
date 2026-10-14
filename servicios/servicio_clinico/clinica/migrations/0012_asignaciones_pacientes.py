from django.db import migrations, models
from django.db.models import Q
from django.utils import timezone
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [("clinica", "0011_notificacion_ia")]
    operations = [
        migrations.CreateModel(
            name="AsignacionPaciente",
            fields=[
                ("id_asignacion", models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ("oncologo_uuid", models.UUIDField()),
                ("asignado_por_uuid", models.UUIDField()),
                ("motivo", models.CharField(max_length=500)),
                ("fecha_asignacion", models.DateTimeField(default=timezone.now)),
                ("activa", models.BooleanField(default=True)),
                ("fecha_revocacion", models.DateTimeField(null=True, blank=True)),
                ("revocado_por_uuid", models.UUIDField(null=True, blank=True)),
                ("motivo_revocacion", models.CharField(max_length=500, blank=True, default="")),
                ("paciente", models.ForeignKey(to="clinica.paciente", db_column="id_paciente", on_delete=django.db.models.deletion.PROTECT, related_name="asignaciones_clinicas")),
            ],
            options={"db_table": "asignaciones_pacientes"},
        ),
        migrations.AddConstraint(
            model_name="asignacionpaciente",
            constraint=models.UniqueConstraint(fields=("paciente", "oncologo_uuid"), condition=Q(activa=True), name="uq_paciente_onco_activo"),
        ),
        migrations.AddIndex(model_name="asignacionpaciente", index=models.Index(fields=["oncologo_uuid", "activa"], name="idx_asig_onco_activa")),
        migrations.AddIndex(model_name="asignacionpaciente", index=models.Index(fields=["paciente", "activa"], name="idx_asig_paciente_act")),
    ]
