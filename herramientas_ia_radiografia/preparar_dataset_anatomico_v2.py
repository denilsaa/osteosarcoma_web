from __future__ import annotations

import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd
from datasets import Dataset
from PIL import Image


# ============================================================
# RUTAS
# ============================================================

ROOT_DATOS = Path(
    "/datos_radiografias_san_juan_de_dios"
)

ANATOMIA_V1_DIR = (
    ROOT_DATOS
    / "03_particiones"
    / "anatomia_v1"
)

ANATOMIA_V2_DIR = (
    ROOT_DATOS
    / "03_particiones"
    / "anatomia_v2"
)

REPORTES_DIR = (
    ROOT_DATOS
    / "04_reportes"
)

MURA_ARROW = Path(
    "/workspace/.cache/huggingface/datasets/"
    "MEDIFICS___muradatasetsu/default/0.0.0/"
    "3597fd2ff116230e8ee341656c32b1004cc6ad0b/"
    "muradatasetsu-train.arrow"
)

MURA_IMAGES_DIR = (
    ROOT_DATOS
    / "02_limpio"
    / "mura_anatomia_v2"
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

VERSION = "anatomia_v2"

MURA_CATEGORIES = [
    "SHOULDER",
    "HUMERUS",
    "ELBOW",
    "FOREARM",
    "WRIST",
    "HAND",
    "FINGER",
]

# ------------------------------------------------------------
# Categorías MURA que sí corresponden al alcance
# anatómico admitido.
# ------------------------------------------------------------

MURA_ADMITTED = {
    "HUMERUS",
    "FOREARM",
}

# ------------------------------------------------------------
# Categorías MURA que se consideran fuera del alcance.
# ------------------------------------------------------------

MURA_NOT_ADMITTED = {
    "WRIST",
    "HAND",
    "FINGER",
}

# ------------------------------------------------------------
# Hombro y codo se excluyen deliberadamente.
#
# Motivo:
# pueden contener parcialmente huesos largos admitidos,
# por lo que utilizarlos como negativos introduciría
# etiquetas anatómicas ambiguas.
# ------------------------------------------------------------

MURA_EXCLUDED = {
    "SHOULDER",
    "ELBOW",
}


# ============================================================
# UTILIDADES
# ============================================================

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(
        data
    ).hexdigest().upper()


def image_to_jpeg_bytes(
    image: Image.Image,
) -> bytes:

    image = image.convert("RGB")

    buffer = io.BytesIO()

    image.save(
        buffer,
        format="JPEG",
        quality=95,
        optimize=False,
    )

    return buffer.getvalue()


def conversation_to_text(
    record: dict,
) -> str:

    conversation = (
        record.get("conversation")
        or {}
    )

    data = (
        conversation.get("data")
        or []
    )

    fragments = []

    for qa in data:

        if not isinstance(
            qa,
            dict,
        ):
            continue

        for value in qa.values():

            if value is not None:
                fragments.append(
                    str(value)
                )

    return " ".join(
        fragments
    ).upper()


def detect_mura_category(
    record: dict,
) -> str | None:

    text = conversation_to_text(
        record
    )

    # ========================================================
    # PRIMER INTENTO:
    # Buscar identificadores explícitos XR_*
    # ========================================================

    explicit_patterns = {
        "SHOULDER": (
            r"\bXR[_\s-]*SHOULDER\b"
        ),
        "HUMERUS": (
            r"\bXR[_\s-]*HUMERUS\b"
        ),
        "ELBOW": (
            r"\bXR[_\s-]*ELBOW\b"
        ),
        "FOREARM": (
            r"\bXR[_\s-]*FOREARM\b"
        ),
        "WRIST": (
            r"\bXR[_\s-]*WRIST\b"
        ),
        "HAND": (
            r"\bXR[_\s-]*HAND\b"
        ),
        "FINGER": (
            r"\bXR[_\s-]*FINGER\b"
        ),
    }

    explicit_found = []

    for (
        category,
        pattern,
    ) in explicit_patterns.items():

        if re.search(
            pattern,
            text,
        ):
            explicit_found.append(
                category
            )

    if len(
        explicit_found
    ) == 1:
        return explicit_found[0]

    # ========================================================
    # SEGUNDO INTENTO:
    # Buscar mención anatómica directa.
    # ========================================================

    found = []

    for category in MURA_CATEGORIES:

        if re.search(
            rf"\b{re.escape(category)}\b",
            text,
        ):
            found.append(
                category
            )

    if len(found) == 1:
        return found[0]

    return None


def get_image_from_record(
    record: dict,
) -> Image.Image:

    image = record["image"]

    if isinstance(
        image,
        Image.Image,
    ):
        return image.copy()

    if isinstance(
        image,
        dict,
    ):

        if (
            image.get("bytes")
            is not None
        ):
            return Image.open(
                io.BytesIO(
                    image["bytes"]
                )
            ).copy()

        if image.get("path"):

            return Image.open(
                image["path"]
            ).copy()

    raise RuntimeError(
        "No fue posible obtener "
        "la imagen del registro MURA."
    )


def empty_like_v1(
    columns: list[str],
) -> dict:

    return {
        column: None
        for column in columns
    }


# ============================================================
# CARGAR ANATOMÍA V1
# ============================================================

def load_v1():

    files = {
        "train": (
            ANATOMIA_V1_DIR
            / "train_anatomia_v1.csv"
        ),
        "validation": (
            ANATOMIA_V1_DIR
            / "validation_anatomia_v1.csv"
        ),
        "test": (
            ANATOMIA_V1_DIR
            / "test_anatomia_v1.csv"
        ),
    }

    frames = {}

    for (
        partition,
        path,
    ) in files.items():

        if not path.exists():

            raise FileNotFoundError(
                f"No existe: {path}"
            )

        df = pd.read_csv(
            path
        )

        df["partition"] = (
            partition
        )

        # ====================================================
        # CORRECCIÓN IMPORTANTE V2
        #
        # Anatomía V1 conserva también registros
        # "indeterminados" dentro de los CSV.
        #
        # Estos registros NO pueden participar
        # en el entrenamiento binario.
        # ====================================================

        if (
            "usable_for_anatomy_training"
            not in df.columns
        ):
            raise RuntimeError(
                "El archivo de Anatomía V1 "
                "no contiene la columna "
                "'usable_for_anatomy_training'."
            )

        if (
            "anatomy_class"
            not in df.columns
        ):
            raise RuntimeError(
                "El archivo de Anatomía V1 "
                "no contiene la columna "
                "'anatomy_class'."
            )

        # ----------------------------------------------------
        # Solo registros habilitados para entrenamiento.
        # ----------------------------------------------------

        df = df[
            df[
                "usable_for_anatomy_training"
            ] == 1
        ].copy()

        # ----------------------------------------------------
        # Solo las dos clases válidas.
        # ----------------------------------------------------

        df = df[
            df[
                "anatomy_class"
            ].isin(
                [
                    "admitida",
                    "no_admitida",
                ]
            )
        ].copy()

        df.reset_index(
            drop=True,
            inplace=True,
        )

        # ----------------------------------------------------
        # Verificación defensiva.
        # ----------------------------------------------------

        invalid_classes = set(
            df[
                "anatomy_class"
            ]
            .dropna()
            .astype(str)
            .unique()
        ) - {
            "admitida",
            "no_admitida",
        }

        if invalid_classes:

            raise RuntimeError(
                "Se encontraron clases "
                "anatómicas no permitidas: "
                f"{invalid_classes}"
            )

        frames[
            partition
        ] = df

    return frames


# ============================================================
# PREPARAR MURA
# ============================================================

def prepare_mura(
    existing_columns: list[str],
    existing_hashes: set[str],
):

    if not MURA_ARROW.exists():

        raise FileNotFoundError(
            "No existe el Arrow "
            "de MURA:\n"
            f"{MURA_ARROW}"
        )

    print(
        "\n2. LEYENDO MURA"
    )

    ds = Dataset.from_file(
        str(MURA_ARROW)
    )

    print(
        f"Total MURA: {len(ds)}"
    )

    MURA_IMAGES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    rows = []
    audit_rows = []

    category_counter = Counter()
    included_counter = Counter()
    excluded_counter = Counter()

    duplicate_against_btxrd = 0
    duplicate_inside_mura = 0
    unclassified = 0
    processing_errors = 0

    mura_hashes = set()

    for (
        index,
        record,
    ) in enumerate(ds):

        record_id = record.get(
            "id",
            index + 1,
        )

        category = (
            detect_mura_category(
                record
            )
        )

        # ====================================================
        # NO CLASIFICABLE
        # ====================================================

        if category is None:

            unclassified += 1

            audit_rows.append(
                {
                    "mura_id": record_id,
                    "category": (
                        "UNCLASSIFIED"
                    ),
                    "decision": (
                        "excluded"
                    ),
                    "reason": (
                        "No se pudo determinar "
                        "una categoría anatómica "
                        "única."
                    ),
                }
            )

            continue

        category_counter[
            category
        ] += 1

        # ====================================================
        # CATEGORÍAS AMBIGUAS
        # ====================================================

        if (
            category
            in MURA_EXCLUDED
        ):

            excluded_counter[
                category
            ] += 1

            audit_rows.append(
                {
                    "mura_id": record_id,
                    "category": category,
                    "decision": (
                        "excluded"
                    ),
                    "reason": (
                        "Categoría anatómica "
                        "ambigua para el alcance "
                        "del validador."
                    ),
                }
            )

            continue

        # ====================================================
        # CLASE ADMITIDA
        # ====================================================

        if (
            category
            in MURA_ADMITTED
        ):

            anatomy_class = (
                "admitida"
            )

            if (
                category
                == "HUMERUS"
            ):

                anatomy = "humerus"

                anatomy_labels = (
                    "humerus"
                )

            else:

                anatomy = "forearm"

                anatomy_labels = (
                    "radius|ulna"
                )

            anatomical_group = (
                "upper_long_bone"
            )

        # ====================================================
        # CLASE NO ADMITIDA
        # ====================================================

        elif (
            category
            in MURA_NOT_ADMITTED
        ):

            anatomy_class = (
                "no_admitida"
            )

            anatomy = (
                category.lower()
            )

            anatomy_labels = (
                category.lower()
            )

            anatomical_group = (
                "excluded_anatomy"
            )

        else:

            excluded_counter[
                category
            ] += 1

            continue

        # ====================================================
        # PROCESAR IMAGEN
        # ====================================================

        try:

            image = (
                get_image_from_record(
                    record
                )
            )

            image = image.convert(
                "RGB"
            )

            width, height = (
                image.size
            )

            image_bytes = (
                image_to_jpeg_bytes(
                    image
                )
            )

            image_hash = (
                sha256_bytes(
                    image_bytes
                )
            )

        except Exception as exc:

            processing_errors += 1

            audit_rows.append(
                {
                    "mura_id": record_id,
                    "category": category,
                    "decision": (
                        "excluded"
                    ),
                    "reason": (
                        "Error procesando "
                        f"imagen: {exc}"
                    ),
                }
            )

            continue

        # ====================================================
        # DUPLICADO CONTRA BTXRD
        # ====================================================

        if (
            image_hash
            in existing_hashes
        ):

            duplicate_against_btxrd += 1

            audit_rows.append(
                {
                    "mura_id": record_id,
                    "category": category,
                    "decision": (
                        "excluded"
                    ),
                    "reason": (
                        "Duplicado exacto "
                        "respecto a BTXRD."
                    ),
                }
            )

            continue

        # ====================================================
        # DUPLICADO DENTRO DE MURA
        # ====================================================

        if (
            image_hash
            in mura_hashes
        ):

            duplicate_inside_mura += 1

            audit_rows.append(
                {
                    "mura_id": record_id,
                    "category": category,
                    "decision": (
                        "excluded"
                    ),
                    "reason": (
                        "Duplicado exacto "
                        "dentro de MURA."
                    ),
                }
            )

            continue

        mura_hashes.add(
            image_hash
        )

        # ====================================================
        # GUARDAR IMAGEN NORMALIZADA
        # ====================================================

        filename = (
            f"mura_"
            f"{int(record_id):06d}_"
            f"{category.lower()}.jpg"
        )

        output_path = (
            MURA_IMAGES_DIR
            / filename
        )

        output_path.write_bytes(
            image_bytes
        )

        # ====================================================
        # CREAR FILA COMPATIBLE CON V1
        # ====================================================

        row = empty_like_v1(
            existing_columns
        )

        row.update(
            {
                "image_id": (
                    filename
                ),
                "source": (
                    "MURA"
                ),
                "center": None,
                "age": None,
                "gender": None,
                "tumor": None,
                "benign": None,
                "malignant": None,
                "osteosarcoma": None,
                "clinical_class": None,
                "diagnosis": None,
                "anatomy": anatomy,
                "body_region": (
                    "upper limb"
                ),
                "projection": None,
                "long_bone_scope": (
                    1
                    if anatomy_class
                    == "admitida"
                    else 0
                ),
                "image_path": (
                    "/datos_radiografias_san_juan_de_dios/"
                    "02_limpio/"
                    "mura_anatomia_v2/"
                    f"{filename}"
                ),
                "annotation_path": None,
                "file_size_bytes": (
                    len(
                        image_bytes
                    )
                ),
                "width": width,
                "height": height,
                "image_mode": (
                    "RGB"
                ),
                "sha256": (
                    image_hash
                ),
                "image_valid": 1,
                "annotation_exists": 0,
                "annotation_valid": None,
                "annotation_image_match": None,
                "annotation_shape_count": None,
                "annotation_labels": None,
                "issues_count": 0,
                "issues": None,
                "dataset_status": (
                    "usable"
                ),
                "duplicate_group_size": 1,
                "duplicate_rank": 0,
                "stratification_label": None,
                "partition": (
                    "train"
                ),
                "anatomy_labels": (
                    anatomy_labels
                ),
                "anatomy_class": (
                    anatomy_class
                ),
                "anatomical_group": (
                    anatomical_group
                ),
                "usable_for_anatomy_training": 1,
            }
        )

        rows.append(
            row
        )

        included_counter[
            category
        ] += 1

        audit_rows.append(
            {
                "mura_id": record_id,
                "category": category,
                "decision": (
                    "included_train"
                ),
                "reason": (
                    "Categoría anatómica "
                    "compatible con la política "
                    "de Anatomía V2."
                ),
            }
        )

    # ========================================================
    # DATAFRAMES
    # ========================================================

    mura_df = pd.DataFrame(
        rows,
        columns=existing_columns,
    )

    audit_df = pd.DataFrame(
        audit_rows
    )

    summary = {
        "total_mura": (
            len(ds)
        ),
        "detected_categories": dict(
            sorted(
                category_counter.items()
            )
        ),
        "included_categories": dict(
            sorted(
                included_counter.items()
            )
        ),
        "excluded_categories": dict(
            sorted(
                excluded_counter.items()
            )
        ),
        "unclassified": (
            unclassified
        ),
        "processing_errors": (
            processing_errors
        ),
        "duplicate_against_btxrd": (
            duplicate_against_btxrd
        ),
        "duplicate_inside_mura": (
            duplicate_inside_mura
        ),
        "included_total": (
            len(mura_df)
        ),
    }

    return (
        mura_df,
        audit_df,
        summary,
    )


# ============================================================
# VERIFICAR FUGAS
# ============================================================

def verify_no_leakage(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
):

    train_hashes = set(
        train[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    val_hashes = set(
        validation[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    test_hashes = set(
        test[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    leakage = {
        "train_validation_sha_overlap": (
            len(
                train_hashes
                & val_hashes
            )
        ),
        "train_test_sha_overlap": (
            len(
                train_hashes
                & test_hashes
            )
        ),
        "validation_test_sha_overlap": (
            len(
                val_hashes
                & test_hashes
            )
        ),
    }

    if any(
        value > 0
        for value
        in leakage.values()
    ):

        raise RuntimeError(
            "Se detectó fuga por "
            "SHA-256 entre particiones: "
            f"{leakage}"
        )

    return leakage


# ============================================================
# DISTRIBUCIÓN DE CLASES
# ============================================================

def class_distribution(
    df: pd.DataFrame,
):

    return {
        str(key): int(value)
        for (
            key,
            value,
        )
        in (
            df[
                "anatomy_class"
            ]
            .value_counts()
            .to_dict()
            .items()
        )
    }


# ============================================================
# VALIDAR QUE SOLO EXISTAN DOS CLASES
# ============================================================

def validate_binary_dataset(
    name: str,
    df: pd.DataFrame,
):

    allowed = {
        "admitida",
        "no_admitida",
    }

    present = set(
        df[
            "anatomy_class"
        ]
        .dropna()
        .astype(str)
        .unique()
    )

    invalid = (
        present
        - allowed
    )

    if invalid:

        raise RuntimeError(
            f"{name} contiene "
            "clases inválidas: "
            f"{invalid}"
        )

    if (
        "admitida"
        not in present
    ):

        raise RuntimeError(
            f"{name} no contiene "
            "la clase 'admitida'."
        )

    if (
        "no_admitida"
        not in present
    ):

        raise RuntimeError(
            f"{name} no contiene "
            "la clase 'no_admitida'."
        )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\n"
        "=============================================="
    )

    print(
        " PREPARACIÓN DATASET ANATÓMICO V2"
    )

    print(
        "=============================================="
    )

    ANATOMIA_V2_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORTES_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # 1. CARGAR V1
    # ========================================================

    print(
        "\n1. CARGANDO ANATOMÍA V1"
    )

    v1 = load_v1()

    train_v1 = (
        v1["train"].copy()
    )

    val_v1 = (
        v1["validation"].copy()
    )

    test_v1 = (
        v1["test"].copy()
    )

    print(
        f"TRAIN V1      : "
        f"{len(train_v1)}"
    )

    print(
        f"VALIDATION V1 : "
        f"{len(val_v1)}"
    )

    print(
        f"TEST V1       : "
        f"{len(test_v1)}"
    )

    print(
        "\nDistribución V1:"
    )

    print(
        " TRAIN      :",
        class_distribution(
            train_v1
        ),
    )

    print(
        " VALIDATION :",
        class_distribution(
            val_v1
        ),
    )

    print(
        " TEST       :",
        class_distribution(
            test_v1
        ),
    )

    # ========================================================
    # VERIFICAR V1
    # ========================================================

    validate_binary_dataset(
        "TRAIN V1",
        train_v1,
    )

    validate_binary_dataset(
        "VALIDATION V1",
        val_v1,
    )

    validate_binary_dataset(
        "TEST V1",
        test_v1,
    )

    columns = list(
        train_v1.columns
    )

    all_v1 = pd.concat(
        [
            train_v1,
            val_v1,
            test_v1,
        ],
        ignore_index=True,
    )

    existing_hashes = set(
        all_v1[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    # ========================================================
    # 2. PREPARAR MURA
    # ========================================================

    (
        mura_df,
        mura_audit,
        mura_summary,
    ) = prepare_mura(
        existing_columns=columns,
        existing_hashes=existing_hashes,
    )

    print(
        "\nMURA incorporado "
        "a TRAIN:"
    )

    for (
        category,
        count,
    ) in (
        mura_summary[
            "included_categories"
        ].items()
    ):

        print(
            f" - {category}: "
            f"{count}"
        )

    print(
        "\nTotal MURA incorporado: "
        f"{len(mura_df)}"
    )

    print(
        "MURA sin clasificar: "
        f"{mura_summary['unclassified']}"
    )

    print(
        "Errores de procesamiento: "
        f"{mura_summary['processing_errors']}"
    )

    print(
        "Duplicados contra BTXRD: "
        f"{mura_summary['duplicate_against_btxrd']}"
    )

    print(
        "Duplicados dentro de MURA: "
        f"{mura_summary['duplicate_inside_mura']}"
    )

    # ========================================================
    # 3. CONSTRUIR V2
    # ========================================================

    print(
        "\n3. GENERANDO ANATOMÍA V2"
    )

    # --------------------------------------------------------
    # MURA se añade EXCLUSIVAMENTE a TRAIN.
    #
    # VALIDATION y TEST permanecen exactamente con los
    # registros utilizables de Anatomía V1.
    # --------------------------------------------------------

    train_v2 = pd.concat(
        [
            train_v1,
            mura_df,
        ],
        ignore_index=True,
    )

    val_v2 = (
        val_v1.copy()
    )

    test_v2 = (
        test_v1.copy()
    )

    # ========================================================
    # VERIFICAR DATASET BINARIO
    # ========================================================

    validate_binary_dataset(
        "TRAIN V2",
        train_v2,
    )

    validate_binary_dataset(
        "VALIDATION V2",
        val_v2,
    )

    validate_binary_dataset(
        "TEST V2",
        test_v2,
    )

    # ========================================================
    # VERIFICAR FUGAS
    # ========================================================

    leakage = (
        verify_no_leakage(
            train_v2,
            val_v2,
            test_v2,
        )
    )

    # ========================================================
    # 4. DISTRIBUCIÓN
    # ========================================================

    print(
        "\n4. DISTRIBUCIÓN"
    )

    print(
        "\nTRAIN V2:",
        class_distribution(
            train_v2
        ),
    )

    print(
        "VALIDATION V2:",
        class_distribution(
            val_v2
        ),
    )

    print(
        "TEST V2:",
        class_distribution(
            test_v2
        ),
    )

    # ========================================================
    # COMPROBAR QUE NO HAYA INDETERMINADAS
    # ========================================================

    indeterminate_count = (
        pd.concat(
            [
                train_v2,
                val_v2,
                test_v2,
            ],
            ignore_index=True,
        )[
            "anatomy_class"
        ]
        .astype(str)
        .eq(
            "indeterminada"
        )
        .sum()
    )

    if (
        indeterminate_count
        != 0
    ):

        raise RuntimeError(
            "Se encontraron registros "
            "'indeterminada' en Anatomía V2."
        )

    print(
        "\nRegistros indeterminados "
        f"en V2: {indeterminate_count}"
    )

    # ========================================================
    # 5. TEST PRESERVADO
    # ========================================================

    print(
        "\n5. VERIFICANDO TEST INTACTO"
    )

    original_test_hashes = set(
        test_v1[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    new_test_hashes = set(
        test_v2[
            "sha256"
        ]
        .dropna()
        .astype(str)
    )

    test_unchanged = (
        original_test_hashes
        == new_test_hashes
        and
        len(test_v1)
        == len(test_v2)
    )

    if not test_unchanged:

        raise RuntimeError(
            "El TEST utilizable "
            "de Anatomía V1 fue alterado."
        )

    print(
        "TEST BTXRD V1 "
        "preservado: SÍ"
    )

    # ========================================================
    # GUARDAR CSV
    # ========================================================

    train_path = (
        ANATOMIA_V2_DIR
        / "train_anatomia_v2.csv"
    )

    validation_path = (
        ANATOMIA_V2_DIR
        / "validation_anatomia_v2.csv"
    )

    test_path = (
        ANATOMIA_V2_DIR
        / "test_anatomia_v2.csv"
    )

    train_v2.to_csv(
        train_path,
        index=False,
        encoding="utf-8-sig",
    )

    val_v2.to_csv(
        validation_path,
        index=False,
        encoding="utf-8-sig",
    )

    test_v2.to_csv(
        test_path,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # AUDITORÍA MURA
    # ========================================================

    mura_audit_path = (
        REPORTES_DIR
        / "auditoria_mura_anatomia_v2.csv"
    )

    mura_audit.to_csv(
        mura_audit_path,
        index=False,
        encoding="utf-8-sig",
    )

    # ========================================================
    # RESUMEN JSON
    # ========================================================

    summary = {
        "version": VERSION,

        "purpose": (
            "Clasificación binaria de anatomía "
            "radiográfica admitida/no admitida "
            "antes del análisis de osteosarcoma."
        ),

        "accepted_scope": [
            "humerus",
            "radius",
            "ulna",
            "femur",
            "tibia",
            "fibula",
        ],

        "sources": {
            "BTXRD": {
                "role": (
                    "Base anatómica original "
                    "de Anatomía V1."
                ),
                "only_usable_anatomy_records": (
                    True
                ),
                "indeterminate_records_excluded": (
                    True
                ),
            },

            "MURA": {
                "role": (
                    "Refuerzo anatómico "
                    "de extremidad superior "
                    "incorporado únicamente "
                    "en TRAIN."
                ),
                "total_available": (
                    mura_summary[
                        "total_mura"
                    ]
                ),
                "included_total": (
                    mura_summary[
                        "included_total"
                    ]
                ),
                "included_categories": (
                    mura_summary[
                        "included_categories"
                    ]
                ),
                "excluded_categories": (
                    mura_summary[
                        "excluded_categories"
                    ]
                ),
                "unclassified": (
                    mura_summary[
                        "unclassified"
                    ]
                ),
                "processing_errors": (
                    mura_summary[
                        "processing_errors"
                    ]
                ),
                "duplicate_against_btxrd": (
                    mura_summary[
                        "duplicate_against_btxrd"
                    ]
                ),
                "duplicate_inside_mura": (
                    mura_summary[
                        "duplicate_inside_mura"
                    ]
                ),
            },
        },

        "partition_policy": {
            "mura_added_only_to_train": (
                True
            ),
            "validation_v1_preserved": (
                True
            ),
            "test_v1_preserved": (
                True
            ),
            "indeterminate_excluded": (
                True
            ),
            "reason": (
                "Mantener la comparación "
                "entre versiones y evitar "
                "contaminación de los conjuntos "
                "de validación y prueba."
            ),
        },

        "counts": {
            "train": (
                len(train_v2)
            ),
            "validation": (
                len(val_v2)
            ),
            "test": (
                len(test_v2)
            ),
            "total": (
                len(train_v2)
                + len(val_v2)
                + len(test_v2)
            ),
            "indeterminate": (
                int(
                    indeterminate_count
                )
            ),
        },

        "class_distribution": {
            "train": (
                class_distribution(
                    train_v2
                )
            ),
            "validation": (
                class_distribution(
                    val_v2
                )
            ),
            "test": (
                class_distribution(
                    test_v2
                )
            ),
        },

        "leakage_check": (
            leakage
        ),

        "test_unchanged_from_v1": (
            test_unchanged
        ),

        "known_limitation": (
            "Esta versión incorpora BTXRD y "
            "MURA, pero todavía requiere "
            "negativos radiográficos fuera "
            "de distribución correspondientes "
            "a cráneo, tórax y columna antes "
            "de considerar definitivo el "
            "validador anatómico."
        ),
    }

    summary_path = (
        REPORTES_DIR
        / "resumen_anatomia_v2.json"
    )

    with summary_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            summary,
            file,
            ensure_ascii=False,
            indent=2,
        )

    # ========================================================
    # RESULTADO
    # ========================================================

    print(
        "\n"
        "=============================================="
    )

    print(
        " RESULTADO ANATOMÍA V2"
    )

    print(
        "=============================================="
    )

    print(
        f"TRAIN      : "
        f"{len(train_v2)}"
    )

    print(
        f"VALIDATION : "
        f"{len(val_v2)}"
    )

    print(
        f"TEST       : "
        f"{len(test_v2)}"
    )

    print(
        "\nMURA añadido a TRAIN: "
        f"{len(mura_df)}"
    )

    print(
        "\nCLASES TRAIN:"
    )

    for (
        class_name,
        count,
    ) in class_distribution(
        train_v2
    ).items():

        print(
            f" - {class_name}: "
            f"{count}"
        )

    print(
        "\nCLASES VALIDATION:"
    )

    for (
        class_name,
        count,
    ) in class_distribution(
        val_v2
    ).items():

        print(
            f" - {class_name}: "
            f"{count}"
        )

    print(
        "\nCLASES TEST:"
    )

    for (
        class_name,
        count,
    ) in class_distribution(
        test_v2
    ).items():

        print(
            f" - {class_name}: "
            f"{count}"
        )

    print(
        "\nINDETERMINADAS:"
    )

    print(
        f" - {indeterminate_count}"
    )

    print(
        "\nFUGAS SHA-256:"
    )

    print(
        " TRAIN/VAL :",
        leakage[
            "train_validation_sha_overlap"
        ],
    )

    print(
        " TRAIN/TEST:",
        leakage[
            "train_test_sha_overlap"
        ],
    )

    print(
        " VAL/TEST  :",
        leakage[
            "validation_test_sha_overlap"
        ],
    )

    print(
        "\nTEST original preservado: "
        f"{'SÍ' if test_unchanged else 'NO'}"
    )

    print(
        "\nArchivos generados:"
    )

    print(
        f" - {train_path}"
    )

    print(
        f" - {validation_path}"
    )

    print(
        f" - {test_path}"
    )

    print(
        f" - {mura_audit_path}"
    )

    print(
        f" - {summary_path}"
    )

    print(
        "\nNOTA:"
    )

    print(
        "Anatomía V2 ya excluye completamente "
        "los registros indeterminados."
    )

    print(
        "Todavía no debe entrenarse como versión "
        "definitiva hasta incorporar negativos OOD "
        "de cráneo, tórax y columna."
    )


if __name__ == "__main__":
    main()
