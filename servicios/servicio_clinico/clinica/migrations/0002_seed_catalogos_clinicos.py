from django.db import migrations


def cargar_catalogos(
    apps,
    schema_editor,
):
    Sexo = apps.get_model(
        "clinica",
        "Sexo",
    )

    TipoDocumento = apps.get_model(
        "clinica",
        "TipoDocumento",
    )

    TipoContacto = apps.get_model(
        "clinica",
        "TipoContacto",
    )

    EstadoCaso = apps.get_model(
        "clinica",
        "EstadoCaso",
    )

    PrioridadCaso = apps.get_model(
        "clinica",
        "PrioridadCaso",
    )

    TipoAntecedente = apps.get_model(
        "clinica",
        "TipoAntecedente",
    )

    NivelIntensidad = apps.get_model(
        "clinica",
        "NivelIntensidad",
    )

    # ==========================================================
    # SEXOS
    # ==========================================================

    sexos = [
        {
            "codigo": "M",
            "nombre": "Masculino",
        },
        {
            "codigo": "F",
            "nombre": "Femenino",
        },
        {
            "codigo": "NO_ESPECIFICADO",
            "nombre": "No especificado",
        },
    ]

    for item in sexos:
        Sexo.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],
            },
        )

    # ==========================================================
    # TIPOS DE DOCUMENTO
    # ==========================================================

    documentos = [
        {
            "codigo": "CI",
            "nombre":
                "Cédula de identidad",
        },
        {
            "codigo": "PASAPORTE",
            "nombre":
                "Pasaporte",
        },
        {
            "codigo": "OTRO",
            "nombre":
                "Otro documento",
        },
    ]

    for item in documentos:
        TipoDocumento.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],
            },
        )

    # ==========================================================
    # TIPOS DE CONTACTO
    # ==========================================================

    contactos = [
        {
            "codigo": "CELULAR",
            "nombre":
                "Teléfono celular",
        },
        {
            "codigo": "TELEFONO",
            "nombre":
                "Teléfono fijo",
        },
        {
            "codigo": "CORREO",
            "nombre":
                "Correo electrónico",
        },
    ]

    for item in contactos:
        TipoContacto.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],
            },
        )

    # ==========================================================
    # ESTADOS DE CASO CLÍNICO
    # ==========================================================

    estados = [
        {
            "codigo": "ABIERTO",
            "nombre": "Abierto",
            "descripcion":
                "Caso clínico registrado y activo.",
        },
        {
            "codigo": "EN_EVALUACION",
            "nombre": "En evaluación",
            "descripcion":
                "Caso en proceso de evaluación clínica.",
        },
        {
            "codigo": "EN_ANALISIS",
            "nombre": "En análisis",
            "descripcion":
                "Caso con estudios en análisis.",
        },
        {
            "codigo": "VALIDADO",
            "nombre": "Validado",
            "descripcion":
                "Caso revisado y validado por especialista.",
        },
        {
            "codigo": "CERRADO",
            "nombre": "Cerrado",
            "descripcion":
                "Caso clínico finalizado.",
        },
    ]

    for item in estados:
        EstadoCaso.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],

                "descripcion":
                    item["descripcion"],
            },
        )

    # ==========================================================
    # PRIORIDADES
    # ==========================================================

    prioridades = [
        {
            "codigo": "BAJA",
            "nombre": "Baja",
            "nivel": 1,
        },
        {
            "codigo": "MEDIA",
            "nombre": "Media",
            "nivel": 2,
        },
        {
            "codigo": "ALTA",
            "nombre": "Alta",
            "nivel": 3,
        },
        {
            "codigo": "URGENTE",
            "nombre": "Urgente",
            "nivel": 4,
        },
    ]

    for item in prioridades:
        PrioridadCaso.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],

                "nivel":
                    item["nivel"],
            },
        )

    # ==========================================================
    # TIPOS DE ANTECEDENTE
    # ==========================================================

    antecedentes = [
        {
            "codigo": "PERSONAL",
            "nombre":
                "Antecedente personal",
        },
        {
            "codigo": "FAMILIAR",
            "nombre":
                "Antecedente familiar",
        },
        {
            "codigo": "QUIRURGICO",
            "nombre":
                "Antecedente quirúrgico",
        },
        {
            "codigo": "ALERGICO",
            "nombre":
                "Antecedente alérgico",
        },
        {
            "codigo": "ONCOLOGICO",
            "nombre":
                "Antecedente oncológico",
        },
    ]

    for item in antecedentes:
        TipoAntecedente.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],
            },
        )

    # ==========================================================
    # NIVELES DE INTENSIDAD
    # ==========================================================

    intensidades = [
        {
            "codigo": "LEVE",
            "nombre": "Leve",
            "nivel": 1,
        },
        {
            "codigo": "MODERADO",
            "nombre": "Moderado",
            "nivel": 2,
        },
        {
            "codigo": "SEVERO",
            "nombre": "Severo",
            "nivel": 3,
        },
    ]

    for item in intensidades:
        NivelIntensidad.objects.update_or_create(
            codigo=item["codigo"],
            defaults={
                "nombre":
                    item["nombre"],

                "nivel":
                    item["nivel"],
            },
        )


def revertir_catalogos(
    apps,
    schema_editor,
):
    """
    No eliminamos catálogos durante rollback porque podrían
    estar referenciados por información clínica real.
    """
    pass


class Migration(migrations.Migration):

    dependencies = [
        (
            "clinica",
            "0001_initial",
        ),
    ]

    operations = [
        migrations.RunPython(
            cargar_catalogos,
            revertir_catalogos,
        ),
    ]