import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identidad", "0002_solicitudrecuperacion_token_nullable"),
    ]

    operations = [
        migrations.CreateModel(
            name="DesafioSegundoFactor",
            fields=[
                (
                    "id_desafio",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("codigo_hash", models.CharField(max_length=64)),
                ("fecha_creacion", models.DateTimeField(auto_now_add=True)),
                ("fecha_expiracion", models.DateTimeField()),
                ("fecha_ultimo_envio", models.DateTimeField()),
                ("intentos_fallidos", models.PositiveSmallIntegerField(default=0)),
                ("reenvios", models.PositiveSmallIntegerField(default=0)),
                ("utilizado", models.BooleanField(default=False)),
                ("fecha_utilizacion", models.DateTimeField(blank=True, null=True)),
                ("ip_origen", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                (
                    "usuario",
                    models.ForeignKey(
                        db_column="id_usuario",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="desafios_segundo_factor",
                        to="identidad.usuario",
                    ),
                ),
            ],
            options={
                "db_table": "desafios_segundo_factor",
            },
        ),
        migrations.AddIndex(
            model_name="desafiosegundofactor",
            index=models.Index(
                fields=["usuario", "utilizado"],
                name="idx_2fa_usuario",
            ),
        ),
        migrations.AddIndex(
            model_name="desafiosegundofactor",
            index=models.Index(
                fields=["utilizado", "fecha_expiracion"],
                name="idx_2fa_estado",
            ),
        ),
    ]
