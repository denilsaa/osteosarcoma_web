from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path("/datos_radiografias_san_juan_de_dios")

MANIFEST_PATH = (
    BASE
    / "02_limpio"
    / "manifest_dataset_v1.csv"
)

PARTITIONS_DIR = BASE / "03_particiones"
REPORTS_DIR = BASE / "04_reportes"

PARTITIONS_PATH = (
    PARTITIONS_DIR
    / "particiones_v1.csv"
)

TRAIN_PATH = (
    PARTITIONS_DIR
    / "train_v1.csv"
)

VAL_PATH = (
    PARTITIONS_DIR
    / "validation_v1.csv"
)

TEST_PATH = (
    PARTITIONS_DIR
    / "test_v1.csv"
)

SUMMARY_PATH = (
    REPORTS_DIR
    / "resumen_particiones_v1.json"
)

LEAKAGE_PATH = (
    REPORTS_DIR
    / "verificacion_fugas_v1.json"
)

EXCLUDED_PATH = (
    REPORTS_DIR
    / "excluidos_particiones_v1.csv"
)

SEED = 42

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# UTILIDADES
# ============================================================

def now_utc() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def print_section(
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


def value_counts_dict(
    series: pd.Series,
) -> dict:
    counts = (
        series
        .value_counts(
            dropna=False
        )
        .to_dict()
    )

    return {
        str(key): int(value)
        for key, value
        in counts.items()
    }


# ============================================================
# ETIQUETA DE ESTRATIFICACIÓN
# ============================================================

def build_stratification_label(
    row: pd.Series,
) -> str:
    """
    Estratificación principal para conservar la distribución
    clínica relevante.

    Clases:
    - normal
    - benign
    - osteosarcoma
    - other_malignant
    """

    if int(
        row["tumor"]
    ) == 0:
        return "normal"

    if int(
        row["benign"]
    ) == 1:
        return "benign"

    if int(
        row["osteosarcoma"]
    ) == 1:
        return "osteosarcoma"

    if int(
        row["malignant"]
    ) == 1:
        return "other_malignant"

    return "unknown"


# ============================================================
# DUPLICADOS
# ============================================================

def choose_duplicate_representatives(
    df: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Para cada SHA-256 se conserva una única imagen.

    Esto evita que una copia exacta aparezca en otra
    partición y produzca fuga de información.

    No se elimina ningún archivo físico.
    Solo se excluyen copias del manifest utilizado para
    entrenamiento.
    """

    working = df.copy()

    working[
        "duplicate_group_size"
    ] = (
        working
        .groupby("sha256")[
            "image_id"
        ]
        .transform("size")
    )

    working[
        "duplicate_rank"
    ] = (
        working
        .groupby("sha256")
        .cumcount()
    )

    keep = working[
        working[
            "duplicate_rank"
        ] == 0
    ].copy()

    removed = working[
        working[
            "duplicate_rank"
        ] > 0
    ].copy()

    removed[
        "exclusion_reason"
    ] = (
        "duplicate_sha256"
    )

    return (
        keep,
        removed,
    )


# ============================================================
# PARTICIÓN ESTRATIFICADA
# ============================================================

def generate_split(
    df: pd.DataFrame,
) -> pd.DataFrame:

    # --------------------------------------------------------
    # TRAIN vs TEMP
    # --------------------------------------------------------

    train_df, temp_df = (
        train_test_split(
            df,
            test_size=(
                VAL_RATIO
                + TEST_RATIO
            ),
            random_state=SEED,
            stratify=df[
                "stratification_label"
            ],
        )
    )

    # --------------------------------------------------------
    # VALIDATION vs TEST
    # --------------------------------------------------------

    relative_test_ratio = (
        TEST_RATIO
        / (
            VAL_RATIO
            + TEST_RATIO
        )
    )

    val_df, test_df = (
        train_test_split(
            temp_df,
            test_size=(
                relative_test_ratio
            ),
            random_state=SEED,
            stratify=temp_df[
                "stratification_label"
            ],
        )
    )

    train_df = train_df.copy()
    val_df = val_df.copy()
    test_df = test_df.copy()

    train_df[
        "partition"
    ] = "train"

    val_df[
        "partition"
    ] = "validation"

    test_df[
        "partition"
    ] = "test"

    result = pd.concat(
        [
            train_df,
            val_df,
            test_df,
        ],
        ignore_index=True,
    )

    return result


# ============================================================
# VERIFICACIÓN DE FUGAS
# ============================================================

def intersections(
    a: set,
    b: set,
) -> list:
    return sorted(
        list(
            a.intersection(b)
        )
    )


def verify_leakage(
    df: pd.DataFrame,
) -> dict:

    train = df[
        df["partition"]
        == "train"
    ]

    val = df[
        df["partition"]
        == "validation"
    ]

    test = df[
        df["partition"]
        == "test"
    ]

    train_ids = set(
        train["image_id"]
    )

    val_ids = set(
        val["image_id"]
    )

    test_ids = set(
        test["image_id"]
    )

    train_hashes = set(
        train["sha256"]
    )

    val_hashes = set(
        val["sha256"]
    )

    test_hashes = set(
        test["sha256"]
    )

    id_train_val = intersections(
        train_ids,
        val_ids,
    )

    id_train_test = intersections(
        train_ids,
        test_ids,
    )

    id_val_test = intersections(
        val_ids,
        test_ids,
    )

    hash_train_val = intersections(
        train_hashes,
        val_hashes,
    )

    hash_train_test = intersections(
        train_hashes,
        test_hashes,
    )

    hash_val_test = intersections(
        val_hashes,
        test_hashes,
    )

    no_image_id_leakage = (
        len(id_train_val) == 0
        and len(id_train_test) == 0
        and len(id_val_test) == 0
    )

    no_hash_leakage = (
        len(hash_train_val) == 0
        and len(hash_train_test) == 0
        and len(hash_val_test) == 0
    )

    return {
        "verified_at_utc": (
            now_utc()
        ),
        "patient_level_verified": False,
        "patient_level_note": (
            "El dataset tabular utilizado no proporciona "
            "un identificador explícito de paciente. "
            "Por ello no se afirma separación por paciente."
        ),
        "image_id": {
            "train_validation_overlap": (
                len(id_train_val)
            ),
            "train_test_overlap": (
                len(id_train_test)
            ),
            "validation_test_overlap": (
                len(id_val_test)
            ),
        },
        "sha256": {
            "train_validation_overlap": (
                len(hash_train_val)
            ),
            "train_test_overlap": (
                len(hash_train_test)
            ),
            "validation_test_overlap": (
                len(hash_val_test)
            ),
        },
        "no_image_id_leakage": (
            no_image_id_leakage
        ),
        "no_exact_duplicate_leakage": (
            no_hash_leakage
        ),
        "passed": (
            no_image_id_leakage
            and no_hash_leakage
        ),
    }


# ============================================================
# RESUMEN
# ============================================================

def partition_summary(
    df: pd.DataFrame,
    partition: str,
) -> dict:

    subset = df[
        df["partition"]
        == partition
    ]

    return {
        "total": int(
            len(subset)
        ),
        "percentage": round(
            (
                len(subset)
                / len(df)
            )
            * 100,
            2,
        ),
        "stratification_classes": (
            value_counts_dict(
                subset[
                    "stratification_label"
                ]
            )
        ),
        "clinical_class": (
            value_counts_dict(
                subset[
                    "clinical_class"
                ]
            )
        ),
        "osteosarcoma": {
            "positive": int(
                subset[
                    "osteosarcoma"
                ].sum()
            ),
            "negative": int(
                len(subset)
                - subset[
                    "osteosarcoma"
                ].sum()
            ),
        },
        "body_region": (
            value_counts_dict(
                subset[
                    "body_region"
                ]
            )
        ),
        "projection": (
            value_counts_dict(
                subset[
                    "projection"
                ]
            )
        ),
        "center": (
            value_counts_dict(
                subset[
                    "center"
                ]
            )
        ),
    }


# ============================================================
# MAIN
# ============================================================

def main() -> None:

    print_section(
        "GENERACIÓN DE PARTICIONES - DATASET TUMORES V1"
    )

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(
            f"No existe: {MANIFEST_PATH}"
        )

    PARTITIONS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTS_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # --------------------------------------------------------
    # CARGAR
    # --------------------------------------------------------

    df = pd.read_csv(
        MANIFEST_PATH
    )

    print(
        "Manifest original:",
        len(df),
    )

    # --------------------------------------------------------
    # SOLO REGISTROS AUDITADOS UTILIZABLES
    # --------------------------------------------------------

    usable = df[
        df["dataset_status"]
        == "usable"
    ].copy()

    quality_excluded = df[
        df["dataset_status"]
        != "usable"
    ].copy()

    quality_excluded[
        "exclusion_reason"
    ] = "quality_control"

    print(
        "Utilizables tras auditoría:",
        len(usable),
    )

    print(
        "Excluidos por calidad:",
        len(
            quality_excluded
        ),
    )

    # --------------------------------------------------------
    # VERIFICAR SHA-256
    # --------------------------------------------------------

    missing_hash = (
        usable["sha256"]
        .isna()
        | (
            usable["sha256"]
            .astype(str)
            .str.strip()
            == ""
        )
    )

    if missing_hash.any():
        raise RuntimeError(
            "Existen imágenes utilizables sin SHA-256."
        )

    # --------------------------------------------------------
    # QUITAR COPIAS EXACTAS
    # --------------------------------------------------------

    unique_df, duplicate_excluded = (
        choose_duplicate_representatives(
            usable
        )
    )

    print(
        "Copias exactas excluidas:",
        len(
            duplicate_excluded
        ),
    )

    print(
        "Imágenes únicas disponibles:",
        len(
            unique_df
        ),
    )

    # --------------------------------------------------------
    # ETIQUETA ESTRATIFICACIÓN
    # --------------------------------------------------------

    unique_df[
        "stratification_label"
    ] = unique_df.apply(
        build_stratification_label,
        axis=1,
    )

    print()
    print(
        "Distribución para estratificación:"
    )

    for (
        label,
        count,
    ) in (
        unique_df[
            "stratification_label"
        ]
        .value_counts()
        .items()
    ):
        print(
            f" - {label}: {count}"
        )

    if (
        unique_df[
            "stratification_label"
        ]
        == "unknown"
    ).any():
        raise RuntimeError(
            "Hay registros con clase de "
            "estratificación desconocida."
        )

    # --------------------------------------------------------
    # GENERAR PARTICIONES
    # --------------------------------------------------------

    print_section(
        "GENERANDO TRAIN / VALIDATION / TEST"
    )

    partitioned = generate_split(
        unique_df
    )

    # Orden reproducible para archivos
    partition_order = {
        "train": 0,
        "validation": 1,
        "test": 2,
    }

    partitioned[
        "_partition_order"
    ] = (
        partitioned[
            "partition"
        ]
        .map(
            partition_order
        )
    )

    partitioned = (
        partitioned
        .sort_values(
            [
                "_partition_order",
                "image_id",
            ]
        )
        .drop(
            columns=[
                "_partition_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    # --------------------------------------------------------
    # VERIFICAR FUGAS
    # --------------------------------------------------------

    leakage = verify_leakage(
        partitioned
    )

    print(
        "Fuga image_id:",
        not leakage[
            "no_image_id_leakage"
        ],
    )

    print(
        "Fuga SHA-256:",
        not leakage[
            "no_exact_duplicate_leakage"
        ],
    )

    if not leakage[
        "passed"
    ]:
        raise RuntimeError(
            "La verificación de fugas "
            "no fue superada."
        )

    # --------------------------------------------------------
    # GUARDAR PARTICIONES
    # --------------------------------------------------------

    partitioned.to_csv(
        PARTITIONS_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    train_df = partitioned[
        partitioned["partition"]
        == "train"
    ].copy()

    val_df = partitioned[
        partitioned["partition"]
        == "validation"
    ].copy()

    test_df = partitioned[
        partitioned["partition"]
        == "test"
    ].copy()

    train_df.to_csv(
        TRAIN_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    val_df.to_csv(
        VAL_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    test_df.to_csv(
        TEST_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # EXCLUIDOS
    # --------------------------------------------------------

    excluded = pd.concat(
        [
            quality_excluded,
            duplicate_excluded,
        ],
        ignore_index=True,
        sort=False,
    )

    excluded.to_csv(
        EXCLUDED_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    summary = {
        "dataset_version": "1.0.0",
        "generated_at_utc": (
            now_utc()
        ),
        "random_seed": SEED,
        "strategy": (
            "estratificación clínica con "
            "eliminación lógica de duplicados "
            "exactos por SHA-256"
        ),
        "requested_ratios": {
            "train": TRAIN_RATIO,
            "validation": VAL_RATIO,
            "test": TEST_RATIO,
        },
        "source_counts": {
            "manifest_total": int(
                len(df)
            ),
            "quality_usable": int(
                len(usable)
            ),
            "quality_excluded": int(
                len(
                    quality_excluded
                )
            ),
            "exact_duplicate_copies_excluded": int(
                len(
                    duplicate_excluded
                )
            ),
            "unique_images_partitioned": int(
                len(
                    partitioned
                )
            ),
        },
        "partitions": {
            "train": (
                partition_summary(
                    partitioned,
                    "train",
                )
            ),
            "validation": (
                partition_summary(
                    partitioned,
                    "validation",
                )
            ),
            "test": (
                partition_summary(
                    partitioned,
                    "test",
                )
            ),
        },
        "leakage_verification": {
            "image_id_passed": (
                leakage[
                    "no_image_id_leakage"
                ]
            ),
            "sha256_passed": (
                leakage[
                    "no_exact_duplicate_leakage"
                ]
            ),
            "patient_level_verified": False,
        },
        "limitations": [
            (
                "El archivo tabular disponible de "
                "BTXRD no contiene un identificador "
                "explícito de paciente."
            ),
            (
                "Por esta razón no se afirma que la "
                "partición sea independiente a nivel "
                "de paciente."
            ),
            (
                "Se garantiza que una imagen y sus "
                "duplicados exactos SHA-256 no se "
                "distribuyan entre particiones."
            ),
            (
                "Las técnicas de balanceo y "
                "aumentación se aplicarán únicamente "
                "sobre TRAIN."
            ),
        ],
    }

    save_json(
        SUMMARY_PATH,
        summary,
    )

    save_json(
        LEAKAGE_PATH,
        leakage,
    )

    # --------------------------------------------------------
    # RESULTADO
    # --------------------------------------------------------

    print_section(
        "RESULTADO"
    )

    print(
        "Imágenes particionadas:",
        len(
            partitioned
        ),
    )

    print(
        "TRAIN      :",
        len(train_df),
        f"({len(train_df) / len(partitioned) * 100:.2f}%)",
    )

    print(
        "VALIDATION :",
        len(val_df),
        f"({len(val_df) / len(partitioned) * 100:.2f}%)",
    )

    print(
        "TEST       :",
        len(test_df),
        f"({len(test_df) / len(partitioned) * 100:.2f}%)",
    )

    print()
    print(
        "OSTEOSARCOMA:"
    )

    print(
        " TRAIN      :",
        int(
            train_df[
                "osteosarcoma"
            ].sum()
        ),
    )

    print(
        " VALIDATION :",
        int(
            val_df[
                "osteosarcoma"
            ].sum()
        ),
    )

    print(
        " TEST       :",
        int(
            test_df[
                "osteosarcoma"
            ].sum()
        ),
    )

    print()
    print(
        "Fuga por image_id :",
        "NO"
        if leakage[
            "no_image_id_leakage"
        ]
        else "SÍ",
    )

    print(
        "Fuga por SHA-256  :",
        "NO"
        if leakage[
            "no_exact_duplicate_leakage"
        ]
        else "SÍ",
    )

    print(
        "Separación paciente:",
        "NO VERIFICABLE CON METADATOS DISPONIBLES",
    )

    print()
    print(
        "Archivos generados:"
    )

    for path in [
        PARTITIONS_PATH,
        TRAIN_PATH,
        VAL_PATH,
        TEST_PATH,
        SUMMARY_PATH,
        LEAKAGE_PATH,
        EXCLUDED_PATH,
    ]:
        print(
            " -",
            path,
        )

    print()
    print(
        "PARTICIONES V1 GENERADAS CORRECTAMENTE."
    )


if __name__ == "__main__":
    main()
