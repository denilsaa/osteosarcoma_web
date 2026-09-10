from django.db import migrations


ESTADOS_NUEVOS = [
    {
        "id": 1,
        "codigo": "REGISTRADO",
        "nombre": "Registrado",
        "descripcion": (
            "Caso clínico registrado inicialmente "
            "en el sistema."
        ),
    },
    {
        "id": 2,
        "codigo": "PENDIENTE",
        "nombre": "Pendiente",
        "descripcion": (
            "Caso pendiente de evaluación "
            "o revisión clínica."
        ),
    },
    {
        "id": 3,
        "codigo": "EN_ANALISIS",
        "nombre": "En análisis",
        "descripcion": (
            "Caso clínico actualmente "
            "en proceso de análisis."
        ),
    },
    {
        "id": 4,
        "codigo": "REVISADO",
        "nombre": "Revisado",
        "descripcion": (
            "Caso revisado por el "
            "especialista responsable."
        ),
    },
    {
        "id": 5,
        "codigo": "CERRADO",
        "nombre": "Cerrado",
        "descripcion": (
            "Caso clínico finalizado."
        ),
    },
]


ESTADOS_ANTERIORES = [
    {
        "id": 1,
        "codigo": "ABIERTO",
        "nombre": "Abierto",
        "descripcion": (
            "Caso clínico registrado y activo."
        ),
    },
    {
        "id": 2,
        "codigo": "EN_EVALUACION",
        "nombre": "En evaluación",
        "descripcion": (
            "Caso en proceso de evaluación clínica."
        ),
    },
    {
        "id": 3,
        "codigo": "EN_ANALISIS",
        "nombre": "En análisis",
        "descripcion": (
            "Caso con estudios en análisis."
        ),
    },
    {
        "id": 4,
        "codigo": "VALIDADO",
        "nombre": "Validado",
        "descripcion": (
            "Caso revisado y validado "
            "por especialista."
        ),
    },
    {
        "id": 5,
        "codigo": "CERRADO",
        "nombre": "Cerrado",
        "descripcion": (
            "Caso clínico finalizado."
        ),
    },
]


def actualizar_estados(
    apps,
    schema_editor,
):
    EstadoCaso = apps.get_model(
        "clinica",
        "EstadoCaso",
    )

    for item in ESTADOS_NUEVOS:
        EstadoCaso.objects.filter(
            id_estado_caso=item["id"],
        ).update(
            codigo=item["codigo"],
            nombre=item["nombre"],
            descripcion=item["descripcion"],
        )


def revertir_estados(
    apps,
    schema_editor,
):
    EstadoCaso = apps.get_model(
        "clinica",
        "EstadoCaso",
    )

    for item in ESTADOS_ANTERIORES:
        EstadoCaso.objects.filter(
            id_estado_caso=item["id"],
        ).update(
            codigo=item["codigo"],
            nombre=item["nombre"],
            descripcion=item["descripcion"],
        )


class Migration(
    migrations.Migration,
):

    dependencies = [
        (
            "clinica",
            "0003_contactoemergenciapaciente",
        ),
    ]

    operations = [
        migrations.RunPython(
            actualizar_estados,
            revertir_estados,
        ),
    ]