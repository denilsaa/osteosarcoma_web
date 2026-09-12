from django.db import migrations


def cargar_signos_sintomas(
    apps,
    schema_editor,
):

    CatalogoSintoma = apps.get_model(
        "clinica",
        "CatalogoSintoma",
    )

    CatalogoSigno = apps.get_model(
        "clinica",
        "CatalogoSigno",
    )


    # ==========================================================
    # SINTOMAS
    # ==========================================================

    sintomas = [
        {
            "codigo":
                "DOLOR_OSEO",

            "nombre":
                "Dolor óseo",

            "descripcion":
                (
                    "Dolor localizado en una zona ósea, "
                    "persistente o progresivo."
                ),
        },
        {
            "codigo":
                "DOLOR_NOCTURNO",

            "nombre":
                "Dolor nocturno",

            "descripcion":
                (
                    "Dolor que aumenta durante la noche "
                    "o interfiere con el descanso."
                ),
        },
        {
            "codigo":
                "LIMITACION_MOVIMIENTO",

            "nombre":
                "Limitación del movimiento",

            "descripcion":
                (
                    "Dificultad o reducción del rango "
                    "normal de movimiento."
                ),
        },
        {
            "codigo":
                "DEBILIDAD",

            "nombre":
                "Debilidad",

            "descripcion":
                (
                    "Sensación de disminución de fuerza "
                    "en la extremidad afectada."
                ),
        },
        {
            "codigo":
                "FATIGA",

            "nombre":
                "Fatiga",

            "descripcion":
                (
                    "Sensación persistente de cansancio "
                    "o agotamiento."
                ),
        },
        {
            "codigo":
                "PERDIDA_PESO",

            "nombre":
                "Pérdida de peso",

            "descripcion":
                (
                    "Pérdida de peso involuntaria "
                    "referida por el paciente."
                ),
        },
        {
            "codigo":
                "DOLOR_MOVIMIENTO",

            "nombre":
                "Dolor con el movimiento",

            "descripcion":
                (
                    "Dolor que aparece o incrementa "
                    "al movilizar la zona afectada."
                ),
        },
        {
            "codigo":
                "HORMIGUEO",

            "nombre":
                "Hormigueo",

            "descripcion":
                (
                    "Sensación de hormigueo o parestesia "
                    "en la región afectada."
                ),
        },
    ]


    for item in sintomas:

        CatalogoSintoma.objects.update_or_create(
            codigo=
                item[
                    "codigo"
                ],

            defaults={
                "nombre":
                    item[
                        "nombre"
                    ],

                "descripcion":
                    item[
                        "descripcion"
                    ],
            },
        )


    # ==========================================================
    # SIGNOS
    # ==========================================================

    signos = [
        {
            "codigo":
                "MASA_PALPABLE",

            "nombre":
                "Masa palpable",

            "descripcion":
                (
                    "Presencia de una masa detectable "
                    "mediante palpación clínica."
                ),
        },
        {
            "codigo":
                "EDEMA_LOCAL",

            "nombre":
                "Edema local",

            "descripcion":
                (
                    "Aumento de volumen o inflamación "
                    "en la región evaluada."
                ),
        },
        {
            "codigo":
                "ERITEMA",

            "nombre":
                "Eritema",

            "descripcion":
                (
                    "Enrojecimiento visible de la piel "
                    "en la región afectada."
                ),
        },
        {
            "codigo":
                "AUMENTO_VOLUMEN",

            "nombre":
                "Aumento de volumen",

            "descripcion":
                (
                    "Incremento visible o palpable del "
                    "volumen de la zona afectada."
                ),
        },
        {
            "codigo":
                "DOLOR_PALPACION",

            "nombre":
                "Dolor a la palpación",

            "descripcion":
                (
                    "Respuesta dolorosa producida "
                    "durante la exploración física."
                ),
        },
        {
            "codigo":
                "MOVILIDAD_REDUCIDA",

            "nombre":
                "Movilidad reducida",

            "descripcion":
                (
                    "Disminución objetiva del rango "
                    "de movimiento durante la evaluación."
                ),
        },
        {
            "codigo":
                "DEFORMIDAD",

            "nombre":
                "Deformidad visible",

            "descripcion":
                (
                    "Alteración visible de la forma "
                    "anatómica habitual."
                ),
        },
        {
            "codigo":
                "AUMENTO_TEMPERATURA",

            "nombre":
                "Aumento de temperatura local",

            "descripcion":
                (
                    "Incremento de temperatura apreciable "
                    "en la región examinada."
                ),
        },
    ]


    for item in signos:

        CatalogoSigno.objects.update_or_create(
            codigo=
                item[
                    "codigo"
                ],

            defaults={
                "nombre":
                    item[
                        "nombre"
                    ],

                "descripcion":
                    item[
                        "descripcion"
                    ],
            },
        )


def revertir_signos_sintomas(
    apps,
    schema_editor,
):
    """
    No eliminamos los catálogos durante rollback
    porque podrían estar asociados a información
    clínica registrada.
    """

    pass


class Migration(
    migrations.Migration,
):

    dependencies = [
        (
            "clinica",
            "0006_casoobservacion_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(
            cargar_signos_sintomas,
            revertir_signos_sintomas,
        ),
    ]