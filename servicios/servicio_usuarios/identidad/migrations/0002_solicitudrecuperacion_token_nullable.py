from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("identidad", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="solicitudrecuperacion",
            name="token_recuperacion",
            field=models.CharField(
                blank=True,
                max_length=255,
                null=True,
                unique=True,
            ),
        ),
    ]
