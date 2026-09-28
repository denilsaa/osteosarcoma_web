from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from PIL import Image


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path("/datos_radiografias_san_juan_de_dios")

PARTITIONS_DIR = BASE / "03_particiones"
REPORTS_DIR = BASE / "04_reportes"

TRAIN_PATH = PARTITIONS_DIR / "train_v1.csv"
VAL_PATH = PARTITIONS_DIR / "validation_v1.csv"
TEST_PATH = PARTITIONS_DIR / "test_v1.csv"

PREPROCESSING_PATH = (
    REPORTS_DIR
    / "configuracion_preprocesamiento_v1.json"
)

VERSION_PATH = (
    REPORTS_DIR
    / "version_dataset_preparado_v1.json"
)

REPORT_PATH = (
    REPORTS_DIR
    / "verificacion_preprocesamiento_v1.json"
)

IMAGE_SIZE = 224

CHANNELS = 3

# Normalización estándar utilizada por modelos
# EfficientNet con pesos ImageNet.
IMAGENET_MEAN = [
    0.485,
    0.456,
    0.406,
]

IMAGENET_STD = [
    0.229,
    0.224,
    0.225,
]

SEED = 42


# ============================================================
# UTILIDADES
# ============================================================

def utc_now() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def section(
    title: str,
) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


def save_json(
    path: Path,
    data: dict,
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
        )


def validate_image(
    image_path: str,
) -> dict:

    path = Path(
        image_path
    )

    result = {
        "exists": False,
        "readable": False,
        "width": None,
        "height": None,
        "mode": None,
        "error": None,
    }

    if not path.exists():
        result["error"] = (
            "Archivo no encontrado."
        )
        return result

    result["exists"] = True

    try:
        with Image.open(
            path
        ) as image:

            result[
                "width"
            ] = image.width

            result[
                "height"
            ] = image.height

            result[
                "mode"
            ] = image.mode

            image.convert(
                "RGB"
            )

            result[
                "readable"
            ] = True

    except Exception as exc:
        result["error"] = str(
            exc
        )

    return result


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    section(
        "PREPARACIÓN DEL PREPROCESAMIENTO - DATASET V1"
    )

    # --------------------------------------------------------
    # VERIFICAR PARTICIONES
    # --------------------------------------------------------

    required = [
        TRAIN_PATH,
        VAL_PATH,
        TEST_PATH,
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    if missing:
        raise FileNotFoundError(
            "Faltan particiones:\n"
            + "\n".join(
                missing
            )
        )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # CARGAR
    # --------------------------------------------------------

    train = pd.read_csv(
        TRAIN_PATH
    )

    validation = pd.read_csv(
        VAL_PATH
    )

    test = pd.read_csv(
        TEST_PATH
    )

    section(
        "1. PARTICIONES"
    )

    print(
        "TRAIN      :",
        len(train),
    )

    print(
        "VALIDATION :",
        len(validation),
    )

    print(
        "TEST       :",
        len(test),
    )

    total = (
        len(train)
        + len(validation)
        + len(test)
    )

    print(
        "TOTAL      :",
        total,
    )

    # --------------------------------------------------------
    # COMPROBAR IMÁGENES
    # --------------------------------------------------------

    section(
        "2. VERIFICANDO IMÁGENES"
    )

    verification = {
        "train": {
            "total": 0,
            "readable": 0,
            "errors": [],
        },
        "validation": {
            "total": 0,
            "readable": 0,
            "errors": [],
        },
        "test": {
            "total": 0,
            "readable": 0,
            "errors": [],
        },
    }

    datasets = {
        "train": train,
        "validation": validation,
        "test": test,
    }

    for (
        partition_name,
        dataframe,
    ) in datasets.items():

        verification[
            partition_name
        ]["total"] = len(
            dataframe
        )

        for index, row in (
            dataframe.iterrows()
        ):

            result = validate_image(
                row[
                    "image_path"
                ]
            )

            if result[
                "readable"
            ]:
                verification[
                    partition_name
                ][
                    "readable"
                ] += 1

            else:
                verification[
                    partition_name
                ][
                    "errors"
                ].append(
                    {
                        "image_id": (
                            row[
                                "image_id"
                            ]
                        ),
                        "error": (
                            result[
                                "error"
                            ]
                        ),
                    }
                )

        print(
            partition_name.upper(),
            ":",
            verification[
                partition_name
            ][
                "readable"
            ],
            "/",
            verification[
                partition_name
            ][
                "total"
            ],
            "legibles",
        )

    # --------------------------------------------------------
    # CONFIGURACIÓN DE PREPROCESAMIENTO
    # --------------------------------------------------------

    section(
        "3. CONFIGURACIÓN"
    )

    preprocessing = {
        "version": "1.0.0",
        "generated_at_utc": (
            utc_now()
        ),
        "target_architecture": (
            "EfficientNetB0"
        ),
        "input": {
            "width": IMAGE_SIZE,
            "height": IMAGE_SIZE,
            "channels": CHANNELS,
            "color_mode": "RGB",
        },
        "base_processing": {
            "decode": (
                "PIL"
            ),
            "convert_to_rgb": True,
            "resize": {
                "enabled": True,
                "width": IMAGE_SIZE,
                "height": IMAGE_SIZE,
                "interpolation": (
                    "bilinear"
                ),
            },
            "tensor_conversion": True,
            "normalization": {
                "type": (
                    "ImageNet"
                ),
                "mean": (
                    IMAGENET_MEAN
                ),
                "std": (
                    IMAGENET_STD
                ),
            },
        },
        "train_augmentation": {
            "enabled": True,

            # HorizontalFlip NO se habilita en esta V1.
            # En radiografías clínicas la lateralidad puede
            # tener significado y no queremos introducir una
            # transformación innecesaria.
            "horizontal_flip": False,

            "vertical_flip": False,

            # Rotaciones pequeñas para simular variaciones
            # razonables de posicionamiento.
            "random_rotation_degrees": 7,

            # Variación geométrica leve.
            "random_affine": {
                "enabled": True,
                "translate": 0.03,
                "scale_min": 0.97,
                "scale_max": 1.03,
            },

            # Variación leve de brillo/contraste.
            "brightness": 0.08,
            "contrast": 0.08,

            # No se usan transformaciones agresivas.
            "grayscale_probability": 0.0,
            "random_crop": False,
            "perspective": False,
            "elastic_transform": False,
        },
        "validation_augmentation": {
            "enabled": False,
        },
        "test_augmentation": {
            "enabled": False,
        },
        "balancing": {
            "apply_only_to_train": True,
            "technique": (
                "none_baseline"
            ),
            "note": (
                "La primera ejecución se conserva "
                "como baseline sin balanceo. "
                "Las técnicas de balanceo serán "
                "comparadas posteriormente."
            ),
        },
        "reproducibility": {
            "seed": SEED,
        },
    }

    save_json(
        PREPROCESSING_PATH,
        preprocessing,
    )

    # --------------------------------------------------------
    # VERIFICACIÓN
    # --------------------------------------------------------

    all_readable = all(
        verification[
            partition
        ][
            "readable"
        ]
        ==
        verification[
            partition
        ][
            "total"
        ]
        for partition
        in verification
    )

    report = {
        "generated_at_utc": (
            utc_now()
        ),
        "all_images_readable": (
            all_readable
        ),
        "partitions": (
            verification
        ),
        "preprocessing": {
            "image_size": (
                f"{IMAGE_SIZE}x"
                f"{IMAGE_SIZE}"
            ),
            "channels": (
                CHANNELS
            ),
            "normalization": (
                "ImageNet"
            ),
            "augmentation_train_only": (
                True
            ),
            "validation_augmentation": (
                False
            ),
            "test_augmentation": (
                False
            ),
        },
    }

    save_json(
        REPORT_PATH,
        report,
    )

    if not all_readable:
        raise RuntimeError(
            "Se encontraron imágenes "
            "no legibles."
        )

    # --------------------------------------------------------
    # VERSIONADO
    # --------------------------------------------------------

    section(
        "4. VERSIONADO DATASET"
    )

    version = {
        "dataset_name": (
            "dataset_radiografias_"
            "tumores_v1"
        ),
        "dataset_version": (
            "1.0.0"
        ),
        "generated_at_utc": (
            utc_now()
        ),
        "state": (
            "READY_FOR_BASELINE_TRAINING"
        ),
        "source": {
            "name": "BTXRD",
            "doi": (
                "10.6084/m9."
                "figshare."
                "27865398.v1"
            ),
            "figshare_article_id": (
                "27865398"
            ),
            "figshare_file_id": (
                "50653575"
            ),
        },
        "quality_control": {
            "original_records": (
                3746
            ),
            "usable_after_audit": (
                3745
            ),
            "quality_excluded": (
                1
            ),
            "exact_duplicate_copies_removed": (
                21
            ),
            "partitioned_unique_images": (
                total
            ),
        },
        "partitions": {
            "train": (
                len(train)
            ),
            "validation": (
                len(validation)
            ),
            "test": (
                len(test)
            ),
        },
        "preprocessing": {
            "configuration_file": (
                str(
                    PREPROCESSING_PATH
                )
            ),
            "input_size": [
                IMAGE_SIZE,
                IMAGE_SIZE,
            ],
            "channels": (
                CHANNELS
            ),
            "normalization": (
                "ImageNet"
            ),
            "augmentation_train_only": (
                True
            ),
        },
        "leakage_control": {
            "image_id_overlap": 0,
            "sha256_overlap": 0,
            "patient_level_verified": (
                False
            ),
            "patient_level_note": (
                "BTXRD no proporciona un "
                "identificador explícito de "
                "paciente en el archivo tabular "
                "utilizado."
            ),
        },
        "training_policy": {
            "validation_used_for": [
                "model_selection",
                "threshold_selection",
                "hyperparameter_selection",
            ],
            "test_used_for": [
                "final_evaluation_only"
            ],
            "test_must_not_be_used_for": [
                "training",
                "augmentation_selection",
                "hyperparameter_selection",
                "threshold_selection",
            ],
        },
        "next_stage": (
            "EfficientNetB0 baseline"
        ),
    }

    save_json(
        VERSION_PATH,
        version,
    )

    print(
        "Estado:",
        version[
            "state"
        ],
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    section(
        "RESULTADO"
    )

    print(
        "Dataset total       :",
        total,
    )

    print(
        "TRAIN               :",
        len(train),
    )

    print(
        "VALIDATION          :",
        len(validation),
    )

    print(
        "TEST                :",
        len(test),
    )

    print(
        "Entrada EfficientNet:",
        f"{IMAGE_SIZE}x"
        f"{IMAGE_SIZE} RGB",
    )

    print(
        "Normalización       :",
        "ImageNet",
    )

    print(
        "Augmentation TRAIN  :",
        "SÍ",
    )

    print(
        "Augmentation VAL    :",
        "NO",
    )

    print(
        "Augmentation TEST   :",
        "NO",
    )

    print(
        "Imágenes legibles   :",
        "SÍ"
        if all_readable
        else "NO",
    )

    print(
        "Estado dataset      :",
        (
            "READY_FOR_"
            "BASELINE_TRAINING"
        ),
    )

    print()
    print(
        "Archivos generados:"
    )

    print(
        " -",
        PREPROCESSING_PATH,
    )

    print(
        " -",
        REPORT_PATH,
    )

    print(
        " -",
        VERSION_PATH,
    )

    print()
    print(
        "TAREAS 3 Y 4 COMPLETADAS."
    )


if __name__ == "__main__":
    main()
