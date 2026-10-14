from django.db import migrations

CRITERIOS = [
    ("SOSPECHA_CLINICA", "Hallazgos sospechosos", "La valoración médica identifica hallazgos que requieren estudio complementario."),
    ("SIN_SOSPECHA", "Sin sospecha radiográfica", "No se observan hallazgos radiográficos suficientes en esta evaluación."),
    ("NO_CONCLUYENTE", "No concluyente", "Requiere estudios adicionales o una nueva valoración clínica."),
]


def seed(apps, schema_editor):
    model = apps.get_model("clinica", "CriterioValoracion")
    for code, name, description in CRITERIOS:
        model.objects.update_or_create(codigo=code, defaults={"nombre": name, "descripcion": description})


class Migration(migrations.Migration):
    dependencies = [("clinica", "0007_seed_signos_sintomas")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
