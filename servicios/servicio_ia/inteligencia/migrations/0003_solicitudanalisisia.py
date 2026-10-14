from django.db import migrations, models
from django.db.models import Q
import django.db.models.deletion
import uuid

class Migration(migrations.Migration):
    dependencies = [('inteligencia', '0002_analisisradiografiaia')]
    operations = [
        migrations.AddField(
            model_name='analisisradiografiaia',
            name='solicitud_uuid',
            field=models.UUIDField(null=True, blank=True, unique=True),
        ),
        migrations.CreateModel(
            name='SolicitudAnalisisIA',
            fields=[
                ('id_solicitud', models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, serialize=False)),
                ('caso_uuid', models.UUIDField(db_index=True)),
                ('radiografia_uuid', models.UUIDField(db_index=True)),
                ('solicitado_por_uuid', models.UUIDField()),
                ('estado', models.CharField(max_length=20, default='PENDIENTE', db_index=True)),
                ('intentos', models.PositiveSmallIntegerField(default=0)),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True)),
                ('fecha_inicio', models.DateTimeField(null=True, blank=True)),
                ('fecha_fin', models.DateTimeField(null=True, blank=True)),
                ('duracion_segundos', models.FloatField(null=True, blank=True)),
                ('version_modelo', models.CharField(max_length=120)),
                ('archivo', models.FileField(upload_to='solicitudes_ia/')),
                ('analisis_id', models.UUIDField(null=True, blank=True)),
                ('error_codigo', models.CharField(max_length=60, null=True, blank=True)),
                ('motivo_reproceso', models.TextField(blank=True, default='')),
                ('historial', models.JSONField(default=list)),
            ],
            options={'db_table': 'solicitudes_analisis_ia'},
        ),
        migrations.AddIndex(
            model_name='solicitudanalisisia',
            index=models.Index(fields=['caso_uuid', 'fecha_solicitud'], name='idx_sol_ia_caso_fecha'),
        ),
        migrations.AddConstraint(
            model_name='solicitudanalisisia',
            constraint=models.UniqueConstraint(fields=('caso_uuid', 'radiografia_uuid'), condition=Q(estado__in=['PENDIENTE', 'PROCESANDO']), name='uq_sol_ia_activa_radiografia'),
        ),
    ]
