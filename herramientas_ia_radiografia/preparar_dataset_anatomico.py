from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path("/datos_radiografias_san_juan_de_dios")

PARTITIONS_DIR = BASE / "03_particiones"
REPORTS_DIR = BASE / "04_reportes"

TRAIN_SOURCE = PARTITIONS_DIR / "train_v1.csv"
VAL_SOURCE = PARTITIONS_DIR / "validation_v1.csv"
TEST_SOURCE = PARTITIONS_DIR / "test_v1.csv"

ANATOMY_DIR = PARTITIONS_DIR / "anatomia_v1"

TRAIN_OUTPUT = ANATOMY_DIR / "train_anatomia_v1.csv"
VAL_OUTPUT = ANATOMY_DIR / "validation_anatomia_v1.csv"
TEST_OUTPUT = ANATOMY_DIR / "test_anatomia_v1.csv"

SUMMARY_OUTPUT = (
    REPORTS_DIR
    / "resumen_dataset_anatomico_v1.json"
)

DETAIL_OUTPUT = (
    REPORTS_DIR
    / "distribucion_anatomica_v1.csv"
)


# ============================================================
# DEFINICIÓN DEL ALCANCE
# ============================================================

# Huesos largos admitidos por el proyecto.
LONG_BONES = {
    "humerus",
    "radius",
    "ulna",
    "femur",
    "tibia",
    "fibula",
}

# Estructuras que NO se consideran directamente
# huesos largos admitidos.
EXCLUDED_STRUCTURES = {
    "hand",
    "foot",
    "hip bone",
    "ankle-joint",
    "knee-joint",
    "hip-joint",
    "wrist-joint",
    "elbow-joint",
    "shoulder-joint",
}


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
            indent=2,
            ensure_ascii=False,
        )


def parse_anatomy(
    value,
) -> set[str]:
    if pd.isna(value):
        return set()

    text = str(value).strip()

    if not text:
        return set()

    return {
        item.strip()
        for item in text.split("|")
        if item.strip()
    }


# ============================================================
# CLASIFICACIÓN
# ============================================================

def classify_anatomy(
    anatomy: set[str],
    body_region: str,
) -> tuple[str, str]:

    """
    Genera dos niveles de información:

    binary_class:
        admitida
        no_admitida
        indeterminada

    anatomical_group:
        upper_long_bone
        lower_long_bone
        excluded_anatomy
        unspecified_upper
        unspecified_lower
        pelvis
        unknown

    IMPORTANTE:
    Una imagen con etiquetas múltiples puede seguir siendo
    válida si contiene un hueso largo admitido.

    Ejemplos:
        tibia|fibula        -> admitida
        ulna|radius         -> admitida
        tibia|knee-joint    -> admitida

    No se usa una etiqueta amplia como
    upper_limb_unspecified o lower_limb_unspecified
    como positiva automática, porque no demuestra que
    corresponda específicamente a un hueso largo.
    """

    long_bones = (
        anatomy
        .intersection(
            LONG_BONES
        )
    )

    if long_bones:
        upper = bool(
            long_bones.intersection(
                {
                    "humerus",
                    "radius",
                    "ulna",
                }
            )
        )

        lower = bool(
            long_bones.intersection(
                {
                    "femur",
                    "tibia",
                    "fibula",
                }
            )
        )

        if upper and not lower:
            return (
                "admitida",
                "upper_long_bone",
            )

        if lower and not upper:
            return (
                "admitida",
                "lower_long_bone",
            )

        return (
            "admitida",
            "mixed_long_bone",
        )

    # --------------------------------------------------------
    # SIN HUESO LARGO ESPECÍFICO
    # --------------------------------------------------------

    if anatomy.intersection(
        EXCLUDED_STRUCTURES
    ):
        return (
            "no_admitida",
            "excluded_anatomy",
        )

    if (
        "pelvis_unspecified"
        in anatomy
        or body_region == "pelvis"
    ):
        return (
            "no_admitida",
            "pelvis",
        )

    if (
        "upper_limb_unspecified"
        in anatomy
    ):
        return (
            "indeterminada",
            "unspecified_upper",
        )

    if (
        "lower_limb_unspecified"
        in anatomy
    ):
        return (
            "indeterminada",
            "unspecified_lower",
        )

    return (
        "indeterminada",
        "unknown",
    )


# ============================================================
# PREPARAR PARTICIÓN
# ============================================================

def prepare_partition(
    source_path: Path,
    output_path: Path,
    expected_partition: str,
) -> pd.DataFrame:

    df = pd.read_csv(
        source_path
    )

    required_columns = {
        "image_id",
        "image_path",
        "sha256",
        "anatomy",
        "body_region",
        "partition",
    }

    missing = (
        required_columns
        - set(df.columns)
    )

    if missing:
        raise RuntimeError(
            "Faltan columnas requeridas: "
            + ", ".join(
                sorted(missing)
            )
        )

    records = []

    for _, row in df.iterrows():

        anatomy = parse_anatomy(
            row["anatomy"]
        )

        body_region = (
            str(
                row["body_region"]
            ).strip()
            if not pd.isna(
                row["body_region"]
            )
            else ""
        )

        (
            binary_class,
            anatomical_group,
        ) = classify_anatomy(
            anatomy,
            body_region,
        )

        record = row.to_dict()

        record[
            "anatomy_labels"
        ] = "|".join(
            sorted(anatomy)
        )

        record[
            "anatomy_class"
        ] = binary_class

        record[
            "anatomical_group"
        ] = anatomical_group

        record[
            "usable_for_anatomy_training"
        ] = int(
            binary_class
            in {
                "admitida",
                "no_admitida",
            }
        )

        records.append(
            record
        )

    result = pd.DataFrame(
        records
    )

    if not (
        result["partition"]
        == expected_partition
    ).all():
        raise RuntimeError(
            f"La partición {source_path} "
            "contiene valores inesperados."
        )

    result.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",
    )

    return result


# ============================================================
# RESUMEN
# ============================================================

def partition_summary(
    df: pd.DataFrame,
) -> dict:

    usable = df[
        df[
            "usable_for_anatomy_training"
        ] == 1
    ]

    return {
        "total": int(
            len(df)
        ),
        "usable_for_training": int(
            len(usable)
        ),
        "excluded_indeterminate": int(
            len(df)
            - len(usable)
        ),
        "classes_all": {
            str(key): int(value)
            for key, value
            in (
                df[
                    "anatomy_class"
                ]
                .value_counts()
                .to_dict()
                .items()
            )
        },
        "classes_training": {
            str(key): int(value)
            for key, value
            in (
                usable[
                    "anatomy_class"
                ]
                .value_counts()
                .to_dict()
                .items()
            )
        },
        "groups": {
            str(key): int(value)
            for key, value
            in (
                df[
                    "anatomical_group"
                ]
                .value_counts()
                .to_dict()
                .items()
            )
        },
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    section(
        "PREPARACIÓN DATASET ANATÓMICO V1"
    )

    required = [
        TRAIN_SOURCE,
        VAL_SOURCE,
        TEST_SOURCE,
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(
                f"No existe: {path}"
            )

    ANATOMY_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # PREPARAR
    # ========================================================

    section(
        "1. CLASIFICANDO ANATOMÍA"
    )

    train = prepare_partition(
        TRAIN_SOURCE,
        TRAIN_OUTPUT,
        "train",
    )

    validation = prepare_partition(
        VAL_SOURCE,
        VAL_OUTPUT,
        "validation",
    )

    test = prepare_partition(
        TEST_SOURCE,
        TEST_OUTPUT,
        "test",
    )

    # ========================================================
    # DISTRIBUCIÓN GLOBAL
    # ========================================================

    all_data = pd.concat(
        [
            train,
            validation,
            test,
        ],
        ignore_index=True,
    )

    usable = all_data[
        all_data[
            "usable_for_anatomy_training"
        ] == 1
    ].copy()

    indeterminate = all_data[
        all_data[
            "usable_for_anatomy_training"
        ] == 0
    ].copy()

    section(
        "2. DISTRIBUCIÓN"
    )

    print(
        "Total:",
        len(all_data),
    )

    print(
        "Utilizables:",
        len(usable),
    )

    print(
        "Indeterminadas:",
        len(indeterminate),
    )

    print()

    print(
        "CLASES:"
    )

    for (
        label,
        count,
    ) in (
        all_data[
            "anatomy_class"
        ]
        .value_counts()
        .items()
    ):
        print(
            f" - {label}: {count}"
        )

    print()

    print(
        "GRUPOS:"
    )

    for (
        label,
        count,
    ) in (
        all_data[
            "anatomical_group"
        ]
        .value_counts()
        .items()
    ):
        print(
            f" - {label}: {count}"
        )

    # ========================================================
    # DISTRIBUCIÓN DETALLADA
    # ========================================================

    detail = (
        all_data
        .groupby(
            [
                "partition",
                "anatomy_class",
                "anatomical_group",
            ],
            dropna=False,
        )
        .size()
        .reset_index(
            name="cantidad"
        )
    )

    detail.to_csv(
        DETAIL_OUTPUT,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # SEGURIDAD CONTRA FUGAS
    # ========================================================

    train_hash = set(
        train["sha256"]
    )

    val_hash = set(
        validation["sha256"]
    )

    test_hash = set(
        test["sha256"]
    )

    train_val_overlap = len(
        train_hash
        .intersection(
            val_hash
        )
    )

    train_test_overlap = len(
        train_hash
        .intersection(
            test_hash
        )
    )

    val_test_overlap = len(
        val_hash
        .intersection(
            test_hash
        )
    )

    if any(
        [
            train_val_overlap,
            train_test_overlap,
            val_test_overlap,
        ]
    ):
        raise RuntimeError(
            "Se detectó fuga SHA-256 "
            "entre particiones."
        )

    # ========================================================
    # RESUMEN
    # ========================================================

    summary = {
        "dataset": (
            "dataset_anatomico_v1"
        ),
        "generated_at_utc": (
            utc_now()
        ),
        "objective": (
            "Determinar si una radiografía "
            "corresponde a una estructura "
            "anatómica admitida para el "
            "análisis posterior."
        ),
        "accepted_long_bones": sorted(
            LONG_BONES
        ),
        "classes": {
            "positive": "admitida",
            "negative": "no_admitida",
            "excluded_from_training": (
                "indeterminada"
            ),
        },
        "global": {
            "total": int(
                len(all_data)
            ),
            "usable_for_training": int(
                len(usable)
            ),
            "indeterminate": int(
                len(indeterminate)
            ),
            "class_distribution": {
                str(key): int(value)
                for key, value
                in (
                    all_data[
                        "anatomy_class"
                    ]
                    .value_counts()
                    .to_dict()
                    .items()
                )
            },
        },
        "partitions": {
            "train": (
                partition_summary(
                    train
                )
            ),
            "validation": (
                partition_summary(
                    validation
                )
            ),
            "test": (
                partition_summary(
                    test
                )
            ),
        },
        "leakage": {
            "train_validation_sha256": (
                train_val_overlap
            ),
            "train_test_sha256": (
                train_test_overlap
            ),
            "validation_test_sha256": (
                val_test_overlap
            ),
            "passed": True,
        },
        "limitations": [
            (
                "Las etiquetas amplias "
                "upper_limb_unspecified y "
                "lower_limb_unspecified no se "
                "utilizan automáticamente como "
                "positivas porque no identifican "
                "un hueso largo específico."
            ),
            (
                "No existe identificador explícito "
                "de paciente en los metadatos "
                "tabulares utilizados."
            ),
            (
                "Este conjunto utiliza únicamente "
                "radiografías BTXRD y no sustituye "
                "una validación externa posterior."
            ),
        ],
    }

    save_json(
        SUMMARY_OUTPUT,
        summary,
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    section(
        "RESULTADO"
    )

    print(
        "TOTAL              :",
        len(all_data),
    )

    print(
        "ADMITIDAS          :",
        int(
            (
                all_data[
                    "anatomy_class"
                ]
                == "admitida"
            ).sum()
        ),
    )

    print(
        "NO ADMITIDAS       :",
        int(
            (
                all_data[
                    "anatomy_class"
                ]
                == "no_admitida"
            ).sum()
        ),
    )

    print(
        "INDETERMINADAS     :",
        int(
            (
                all_data[
                    "anatomy_class"
                ]
                == "indeterminada"
            ).sum()
        ),
    )

    print()

    for name, df in [
        (
            "TRAIN",
            train,
        ),
        (
            "VALIDATION",
            validation,
        ),
        (
            "TEST",
            test,
        ),
    ]:

        usable_df = df[
            df[
                "usable_for_anatomy_training"
            ] == 1
        ]

        positive = int(
            (
                usable_df[
                    "anatomy_class"
                ]
                == "admitida"
            ).sum()
        )

        negative = int(
            (
                usable_df[
                    "anatomy_class"
                ]
                == "no_admitida"
            ).sum()
        )

        print(
            f"{name:<10}: "
            f"{len(usable_df)} "
            f"(admitida={positive}, "
            f"no_admitida={negative})"
        )

    print()

    print(
        "Fuga SHA TRAIN/VAL :",
        train_val_overlap,
    )

    print(
        "Fuga SHA TRAIN/TEST:",
        train_test_overlap,
    )

    print(
        "Fuga SHA VAL/TEST  :",
        val_test_overlap,
    )

    print()

    print(
        "Archivos:"
    )

    print(
        " -",
        TRAIN_OUTPUT,
    )

    print(
        " -",
        VAL_OUTPUT,
    )

    print(
        " -",
        TEST_OUTPUT,
    )

    print(
        " -",
        SUMMARY_OUTPUT,
    )

    print(
        " -",
        DETAIL_OUTPUT,
    )

    print()

    print(
        "DATASET ANATÓMICO V1 PREPARADO."
    )


if __name__ == "__main__":
    main()
