from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from PIL import Image, UnidentifiedImageError


# ============================================================
# CONFIGURACIÓN
# ============================================================

BASE = Path("/datos_radiografias_san_juan_de_dios")

ORIGINAL = (
    BASE
    / "01_original"
    / "BTXRD_EXTRAIDO"
    / "BTXRD"
)

IMAGES_DIR = ORIGINAL / "images"
ANNOTATIONS_DIR = ORIGINAL / "Annotations"
EXCEL_PATH = ORIGINAL / "dataset.xlsx"

CLEAN_DIR = BASE / "02_limpio"
REPORT_DIR = BASE / "04_reportes"

MANIFEST_PATH = CLEAN_DIR / "manifest_dataset_v1.csv"

LOG_PATH = REPORT_DIR / "bitacora_limpieza_v1.csv"
SUMMARY_PATH = REPORT_DIR / "resumen_limpieza_v1.json"
DUPLICATES_PATH = REPORT_DIR / "duplicados_v1.csv"
INCONSISTENCIES_PATH = REPORT_DIR / "inconsistencias_v1.csv"
VERSION_PATH = REPORT_DIR / "version_dataset_v1.json"

DATASET_NAME = "dataset_radiografias_tumores_v1"
DATASET_VERSION = "1.0.0"

SOURCE_NAME = "BTXRD"
SOURCE_VERSION = "v1"
SOURCE_DOI = "10.6084/m9.figshare.27865398.v1"
SOURCE_ARTICLE_ID = "27865398"
SOURCE_FILE_ID = "50653575"

SOURCE_ZIP_SHA256 = (
    "E7C800C3B4E090262B160525A0765F9D"
    "93BCC53D639C03806A3AC47B0DED3373"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
}

ANATOMY_COLUMNS = [
    "hand",
    "ulna",
    "radius",
    "humerus",
    "foot",
    "tibia",
    "fibula",
    "femur",
    "hip bone",
    "ankle-joint",
    "knee-joint",
    "hip-joint",
    "wrist-joint",
    "elbow-joint",
    "shoulder-joint",
]

DIAGNOSIS_COLUMNS = [
    "osteochondroma",
    "multiple osteochondromas",
    "simple bone cyst",
    "giant cell tumor",
    "osteofibroma",
    "synovial osteochondroma",
    "other bt",
    "osteosarcoma",
    "other mt",
]

BENIGN_DIAGNOSIS_COLUMNS = [
    "osteochondroma",
    "multiple osteochondromas",
    "simple bone cyst",
    "giant cell tumor",
    "osteofibroma",
    "synovial osteochondroma",
    "other bt",
]

MALIGNANT_DIAGNOSIS_COLUMNS = [
    "osteosarcoma",
    "other mt",
]

PROJECTION_COLUMNS = [
    "frontal",
    "lateral",
    "oblique",
]

LONG_BONE_COLUMNS = [
    "ulna",
    "radius",
    "humerus",
    "tibia",
    "fibula",
    "femur",
]

BINARY_COLUMNS = [
    "tumor",
    "benign",
    "malignant",
    *ANATOMY_COLUMNS,
    *DIAGNOSIS_COLUMNS,
    "upper limb",
    "lower limb",
    "pelvis",
    *PROJECTION_COLUMNS,
]


# ============================================================
# UTILIDADES
# ============================================================

def utc_now_iso() -> str:
    return datetime.now(
        timezone.utc
    ).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as file:
        for block in iter(
            lambda: file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(block)

    return digest.hexdigest().upper()


def safe_int(
    value,
    default: int = 0,
) -> int:
    if pd.isna(value):
        return default

    try:
        return int(value)
    except (
        TypeError,
        ValueError,
    ):
        return default


def normalize_text(value) -> str:
    if pd.isna(value):
        return ""

    return str(value).strip()


def active_labels(
    row: pd.Series,
    columns: list[str],
) -> list[str]:
    return [
        column
        for column in columns
        if safe_int(
            row.get(column, 0)
        ) == 1
    ]


def write_json(
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


def save_csv(
    records: list[dict],
    path: Path,
    columns: list[str],
) -> None:
    if records:
        df = pd.DataFrame(records)

        for column in columns:
            if column not in df.columns:
                df[column] = ""

        df = df[columns]

    else:
        df = pd.DataFrame(
            columns=columns
        )

    df.to_csv(
        path,
        index=False,
        encoding="utf-8-sig",
    )


def print_section(
    title: str,
) -> None:
    print()
    print("=" * 72)
    print(title)
    print("=" * 72)


# ============================================================
# CLASIFICACIONES DERIVADAS
# ============================================================

def determine_clinical_class(
    row: pd.Series,
) -> str:
    tumor = safe_int(
        row.get("tumor")
    )

    benign = safe_int(
        row.get("benign")
    )

    malignant = safe_int(
        row.get("malignant")
    )

    if tumor == 0:
        return "normal"

    if (
        benign == 1
        and malignant == 0
    ):
        return "benign"

    if (
        malignant == 1
        and benign == 0
    ):
        return "malignant"

    return "inconsistent"


def determine_diagnosis(
    row: pd.Series,
) -> str:
    if safe_int(
        row.get("tumor")
    ) == 0:
        return "normal"

    labels = active_labels(
        row,
        DIAGNOSIS_COLUMNS,
    )

    if len(labels) == 1:
        return labels[0]

    if not labels:
        return "tumor_unspecified"

    return "|".join(labels)


def determine_anatomy(
    row: pd.Series,
) -> str:
    labels = active_labels(
        row,
        ANATOMY_COLUMNS,
    )

    # BTXRD puede marcar más de una estructura anatómica
    # visible en una misma radiografía. Eso NO constituye
    # por sí mismo una inconsistencia.
    if labels:
        return "|".join(labels)

    if safe_int(
        row.get("pelvis")
    ) == 1:
        return "pelvis_unspecified"

    if safe_int(
        row.get("upper limb")
    ) == 1:
        return "upper_limb_unspecified"

    if safe_int(
        row.get("lower limb")
    ) == 1:
        return "lower_limb_unspecified"

    return "unspecified"


def determine_body_region(
    row: pd.Series,
) -> str:
    regions = []

    if safe_int(
        row.get("upper limb")
    ):
        regions.append(
            "upper_limb"
        )

    if safe_int(
        row.get("lower limb")
    ):
        regions.append(
            "lower_limb"
        )

    if safe_int(
        row.get("pelvis")
    ):
        regions.append(
            "pelvis"
        )

    if not regions:
        return "unspecified"

    return "|".join(regions)


def determine_projection(
    row: pd.Series,
) -> str:
    labels = active_labels(
        row,
        PROJECTION_COLUMNS,
    )

    if not labels:
        return "unspecified"

    return "|".join(labels)


def is_long_bone_scope(
    row: pd.Series,
) -> bool:
    """
    Alcance anatómico inicial del proyecto:
    huesos largos de extremidades superiores e inferiores.

    Se consideran:
    - húmero
    - radio
    - cúbito/ulna
    - fémur
    - tibia
    - peroné/fíbula

    Una radiografía puede contener más de uno.
    """

    return any(
        safe_int(
            row.get(column)
        ) == 1
        for column
        in LONG_BONE_COLUMNS
    )


# ============================================================
# VALIDACIONES DE METADATOS
# ============================================================

def validate_binary_columns(
    row: pd.Series,
    image_id: str,
    inconsistencies: list[dict],
) -> None:
    for column in BINARY_COLUMNS:
        value = row.get(column)

        if pd.isna(value):
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "valor_binario_vacio"
                    ),
                    "campo": column,
                    "detalle": (
                        "Valor vacío en "
                        "columna binaria."
                    ),
                }
            )
            continue

        try:
            numeric = int(value)

        except (
            TypeError,
            ValueError,
        ):
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "valor_binario_invalido"
                    ),
                    "campo": column,
                    "detalle": (
                        f"Valor encontrado: "
                        f"{value}"
                    ),
                }
            )
            continue

        if numeric not in {
            0,
            1,
        }:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "valor_binario_fuera_rango"
                    ),
                    "campo": column,
                    "detalle": (
                        f"Valor encontrado: "
                        f"{value}"
                    ),
                }
            )


def validate_clinical_labels(
    row: pd.Series,
    image_id: str,
    inconsistencies: list[dict],
) -> None:
    tumor = safe_int(
        row.get("tumor")
    )

    benign = safe_int(
        row.get("benign")
    )

    malignant = safe_int(
        row.get("malignant")
    )

    benign_labels = active_labels(
        row,
        BENIGN_DIAGNOSIS_COLUMNS,
    )

    malignant_labels = active_labels(
        row,
        MALIGNANT_DIAGNOSIS_COLUMNS,
    )

    all_diagnoses = (
        benign_labels
        + malignant_labels
    )

    # --------------------------------------------------------
    # NORMAL
    # --------------------------------------------------------

    if tumor == 0:
        if (
            benign != 0
            or malignant != 0
        ):
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "inconsistencia_tumor_clase"
                    ),
                    "campo": (
                        "tumor/benign/malignant"
                    ),
                    "detalle": (
                        "tumor=0 pero benign "
                        "o malignant está activo."
                    ),
                }
            )

        if all_diagnoses:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "diagnostico_en_normal"
                    ),
                    "campo": "diagnostico",
                    "detalle": "|".join(
                        all_diagnoses
                    ),
                }
            )

        return

    # --------------------------------------------------------
    # TUMOR
    # --------------------------------------------------------

    if benign + malignant != 1:
        inconsistencies.append(
            {
                "image_id": image_id,
                "tipo": (
                    "clase_tumoral_invalida"
                ),
                "campo": (
                    "benign/malignant"
                ),
                "detalle": (
                    f"benign={benign}; "
                    f"malignant={malignant}"
                ),
            }
        )

    if not all_diagnoses:
        inconsistencies.append(
            {
                "image_id": image_id,
                "tipo": (
                    "diagnostico_tumoral_invalido"
                ),
                "campo": "diagnostico",
                "detalle": (
                    "Tumor sin diagnóstico "
                    "específico."
                ),
            }
        )

    # --------------------------------------------------------
    # BENIGNO
    # --------------------------------------------------------

    if benign == 1:
        if len(
            benign_labels
        ) != 1:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "diagnostico_benigno_invalido"
                    ),
                    "campo": "diagnostico",
                    "detalle": (
                        "|".join(
                            benign_labels
                        )
                        if benign_labels
                        else (
                            "Sin diagnóstico "
                            "benigno."
                        )
                    ),
                }
            )

        if malignant_labels:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "benigno_con_etiqueta_maligna"
                    ),
                    "campo": "diagnostico",
                    "detalle": "|".join(
                        malignant_labels
                    ),
                }
            )

    # --------------------------------------------------------
    # MALIGNO
    # --------------------------------------------------------

    if malignant == 1:
        if len(
            malignant_labels
        ) != 1:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "diagnostico_maligno_invalido"
                    ),
                    "campo": (
                        "osteosarcoma/other mt"
                    ),
                    "detalle": (
                        "|".join(
                            malignant_labels
                        )
                        if malignant_labels
                        else (
                            "Sin diagnóstico "
                            "maligno."
                        )
                    ),
                }
            )

        if benign_labels:
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "maligno_con_etiqueta_benigna"
                    ),
                    "campo": "diagnostico",
                    "detalle": "|".join(
                        benign_labels
                    ),
                }
            )


def validate_anatomy(
    row: pd.Series,
    image_id: str,
    inconsistencies: list[dict],
) -> None:
    """
    BTXRD permite que una radiografía tenga múltiples
    estructuras anatómicas activas.

    Ejemplos válidos:
    - tibia + fibula
    - ulna + radius
    - femur + hip bone

    Por ello NO se exige exactamente una anatomía.

    Solo comprobamos la coherencia de la región corporal
    general: upper limb, lower limb o pelvis.
    """

    upper = safe_int(
        row.get("upper limb")
    )

    lower = safe_int(
        row.get("lower limb")
    )

    pelvis = safe_int(
        row.get("pelvis")
    )

    if (
        upper
        + lower
        + pelvis
        != 1
    ):
        inconsistencies.append(
            {
                "image_id": image_id,
                "tipo": (
                    "region_corporal_invalida"
                ),
                "campo": (
                    "upper/lower/pelvis"
                ),
                "detalle": (
                    f"upper={upper}; "
                    f"lower={lower}; "
                    f"pelvis={pelvis}"
                ),
            }
        )


def validate_projection(
    row: pd.Series,
    image_id: str,
    inconsistencies: list[dict],
) -> None:
    projections = active_labels(
        row,
        PROJECTION_COLUMNS,
    )

    if len(projections) != 1:
        inconsistencies.append(
            {
                "image_id": image_id,
                "tipo": (
                    "proyeccion_invalida"
                ),
                "campo": "proyeccion",
                "detalle": (
                    "|".join(
                        projections
                    )
                    if projections
                    else "Sin proyección."
                ),
            }
        )


# ============================================================
# VALIDACIÓN JSON
# ============================================================

def inspect_annotation(
    json_path: Path,
    expected_image_id: str,
) -> dict:
    result = {
        "annotation_exists": (
            json_path.exists()
        ),
        "annotation_valid": False,
        "annotation_image_match": False,
        "annotation_shape_count": 0,
        "annotation_labels": "",
        "annotation_width": None,
        "annotation_height": None,
        "annotation_error": "",
    }

    if not json_path.exists():
        return result

    try:
        with json_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)

        result[
            "annotation_valid"
        ] = True

        image_path = normalize_text(
            data.get("imagePath")
        )

        result[
            "annotation_image_match"
        ] = (
            Path(image_path).name
            == expected_image_id
        )

        shapes = data.get(
            "shapes",
            [],
        )

        if not isinstance(
            shapes,
            list,
        ):
            raise ValueError(
                "'shapes' no es una lista."
            )

        labels = []

        for shape in shapes:
            if not isinstance(
                shape,
                dict,
            ):
                continue

            label = normalize_text(
                shape.get("label")
            )

            if label:
                labels.append(label)

        result[
            "annotation_shape_count"
        ] = len(shapes)

        result[
            "annotation_labels"
        ] = "|".join(
            sorted(
                set(labels)
            )
        )

        result[
            "annotation_width"
        ] = data.get(
            "imageWidth"
        )

        result[
            "annotation_height"
        ] = data.get(
            "imageHeight"
        )

    except Exception as exc:
        result[
            "annotation_error"
        ] = str(exc)

    return result


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main() -> int:
    print_section(
        "PREPARACIÓN DATASET DE TUMORES ÓSEOS - V1"
    )

    print(
        "Fuente :",
        SOURCE_NAME,
    )

    print(
        "Versión:",
        SOURCE_VERSION,
    )

    print(
        "Ruta   :",
        ORIGINAL,
    )

    # ========================================================
    # ENTRADAS
    # ========================================================

    required = [
        IMAGES_DIR,
        ANNOTATIONS_DIR,
        EXCEL_PATH,
    ]

    missing = [
        str(path)
        for path in required
        if not path.exists()
    ]

    if missing:
        print()
        print(
            "ERROR: faltan entradas requeridas:"
        )

        for path in missing:
            print(
                " -",
                path,
            )

        return 1

    CLEAN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # ========================================================
    # EXCEL
    # ========================================================

    print_section(
        "1. LEYENDO METADATOS"
    )

    df = pd.read_excel(
        EXCEL_PATH,
        sheet_name="Sheet1",
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    print(
        "Registros Excel:",
        len(df),
    )

    if "image_id" not in df.columns:
        raise RuntimeError(
            "dataset.xlsx no contiene image_id."
        )

    df["image_id"] = (
        df["image_id"]
        .astype(str)
        .str.strip()
    )

    duplicated_excel_ids = df[
        df["image_id"].duplicated(
            keep=False
        )
    ].copy()

    print(
        "image_id duplicados en Excel:",
        len(
            duplicated_excel_ids
        ),
    )

    # ========================================================
    # INVENTARIO
    # ========================================================

    print_section(
        "2. INVENTARIO DE ARCHIVOS"
    )

    image_files = {
        path.name: path
        for path
        in IMAGES_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    }

    annotation_files = {
        path.stem: path
        for path
        in ANNOTATIONS_DIR.glob(
            "*.json"
        )
        if path.is_file()
    }

    excel_ids = set(
        df["image_id"]
    )

    image_ids = set(
        image_files.keys()
    )

    images_without_excel = sorted(
        image_ids
        - excel_ids
    )

    excel_without_image = sorted(
        excel_ids
        - image_ids
    )

    print(
        "Imágenes:",
        len(image_files),
    )

    print(
        "JSON:",
        len(annotation_files),
    )

    print(
        "Imágenes sin Excel:",
        len(
            images_without_excel
        ),
    )

    print(
        "Excel sin imagen:",
        len(
            excel_without_image
        ),
    )

    # ========================================================
    # AUDITORÍA
    # ========================================================

    print_section(
        "3. AUDITANDO RADIOGRAFÍAS"
    )

    manifest = []
    log = []
    inconsistencies = []

    hashes = defaultdict(list)

    total = len(df)

    for index, (_, row) in enumerate(
        df.iterrows(),
        start=1,
    ):
        image_id = normalize_text(
            row.get("image_id")
        )

        image_path = image_files.get(
            image_id
        )

        valid_image = False
        image_error = ""

        width = None
        height = None
        image_mode = ""

        file_size = None
        file_hash = ""

        # ====================================================
        # IMAGEN
        # ====================================================

        if image_path is None:
            image_error = (
                "Imagen referenciada en Excel "
                "no encontrada."
            )

            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "imagen_faltante"
                    ),
                    "campo": "image_id",
                    "detalle": image_error,
                }
            )

        else:
            file_size = (
                image_path
                .stat()
                .st_size
            )

            try:
                with Image.open(
                    image_path
                ) as image:
                    image.verify()

                with Image.open(
                    image_path
                ) as image:
                    width, height = (
                        image.size
                    )

                    image_mode = (
                        image.mode
                    )

                valid_image = True

                file_hash = sha256_file(
                    image_path
                )

                hashes[
                    file_hash
                ].append(
                    image_id
                )

            except (
                UnidentifiedImageError,
                OSError,
                ValueError,
            ) as exc:
                image_error = str(
                    exc
                )

                inconsistencies.append(
                    {
                        "image_id": image_id,
                        "tipo": (
                            "imagen_corrupta"
                        ),
                        "campo": "archivo",
                        "detalle": (
                            image_error
                        ),
                    }
                )

        # ====================================================
        # METADATOS
        # ====================================================

        validate_binary_columns(
            row,
            image_id,
            inconsistencies,
        )

        validate_clinical_labels(
            row,
            image_id,
            inconsistencies,
        )

        validate_anatomy(
            row,
            image_id,
            inconsistencies,
        )

        validate_projection(
            row,
            image_id,
            inconsistencies,
        )

        clinical_class = (
            determine_clinical_class(
                row
            )
        )

        diagnosis = (
            determine_diagnosis(
                row
            )
        )

        anatomy = (
            determine_anatomy(
                row
            )
        )

        body_region = (
            determine_body_region(
                row
            )
        )

        projection = (
            determine_projection(
                row
            )
        )

        # ====================================================
        # JSON
        # ====================================================

        annotation_path = (
            ANNOTATIONS_DIR
            / (
                f"{Path(image_id).stem}"
                ".json"
            )
        )

        annotation = inspect_annotation(
            annotation_path,
            image_id,
        )

        tumor = safe_int(
            row.get("tumor")
        )

        if tumor == 1:
            if not annotation[
                "annotation_exists"
            ]:
                inconsistencies.append(
                    {
                        "image_id": image_id,
                        "tipo": (
                            "tumor_sin_json"
                        ),
                        "campo": (
                            "annotation"
                        ),
                        "detalle": (
                            "Registro tumoral "
                            "sin anotación JSON."
                        ),
                    }
                )

            elif not annotation[
                "annotation_valid"
            ]:
                inconsistencies.append(
                    {
                        "image_id": image_id,
                        "tipo": (
                            "json_invalido"
                        ),
                        "campo": (
                            "annotation"
                        ),
                        "detalle": (
                            annotation[
                                "annotation_error"
                            ]
                        ),
                    }
                )

            elif not annotation[
                "annotation_image_match"
            ]:
                inconsistencies.append(
                    {
                        "image_id": image_id,
                        "tipo": (
                            "json_imagen_no_coincide"
                        ),
                        "campo": (
                            "imagePath"
                        ),
                        "detalle": (
                            "imagePath del JSON "
                            "no coincide con "
                            "image_id."
                        ),
                    }
                )

        else:
            if annotation[
                "annotation_exists"
            ]:
                inconsistencies.append(
                    {
                        "image_id": image_id,
                        "tipo": (
                            "normal_con_json"
                        ),
                        "campo": (
                            "annotation"
                        ),
                        "detalle": (
                            "Imagen marcada "
                            "como normal posee "
                            "anotación JSON."
                        ),
                    }
                )

        # ====================================================
        # DIMENSIONES JSON
        # ====================================================

        if (
            valid_image
            and annotation[
                "annotation_valid"
            ]
        ):
            json_width = annotation[
                "annotation_width"
            ]

            json_height = annotation[
                "annotation_height"
            ]

            if (
                json_width is not None
                and json_height is not None
            ):
                if (
                    safe_int(
                        json_width
                    )
                    != width
                    or safe_int(
                        json_height
                    )
                    != height
                ):
                    inconsistencies.append(
                        {
                            "image_id": image_id,
                            "tipo": (
                                "dimensiones_json_no_coinciden"
                            ),
                            "campo": (
                                "imageWidth/imageHeight"
                            ),
                            "detalle": (
                                f"imagen="
                                f"{width}x{height}; "
                                f"json="
                                f"{json_width}x"
                                f"{json_height}"
                            ),
                        }
                    )

        # ====================================================
        # MANIFEST
        # ====================================================

        manifest.append(
            {
                "image_id": image_id,
                "source": SOURCE_NAME,
                "center": safe_int(
                    row.get("center")
                ),
                "age": safe_int(
                    row.get("age")
                ),
                "gender": normalize_text(
                    row.get("gender")
                ),
                "tumor": tumor,
                "benign": safe_int(
                    row.get("benign")
                ),
                "malignant": safe_int(
                    row.get(
                        "malignant"
                    )
                ),
                "osteosarcoma": (
                    safe_int(
                        row.get(
                            "osteosarcoma"
                        )
                    )
                ),
                "clinical_class": (
                    clinical_class
                ),
                "diagnosis": diagnosis,
                "anatomy": anatomy,
                "body_region": (
                    body_region
                ),
                "projection": (
                    projection
                ),
                "long_bone_scope": int(
                    is_long_bone_scope(
                        row
                    )
                ),
                "image_path": (
                    str(image_path)
                    if image_path
                    else ""
                ),
                "annotation_path": (
                    str(
                        annotation_path
                    )
                    if annotation[
                        "annotation_exists"
                    ]
                    else ""
                ),
                "file_size_bytes": (
                    file_size
                ),
                "width": width,
                "height": height,
                "image_mode": (
                    image_mode
                ),
                "sha256": file_hash,
                "image_valid": int(
                    valid_image
                ),
                "annotation_exists": int(
                    annotation[
                        "annotation_exists"
                    ]
                ),
                "annotation_valid": int(
                    annotation[
                        "annotation_valid"
                    ]
                ),
                "annotation_image_match": int(
                    annotation[
                        "annotation_image_match"
                    ]
                ),
                "annotation_shape_count": (
                    annotation[
                        "annotation_shape_count"
                    ]
                ),
                "annotation_labels": (
                    annotation[
                        "annotation_labels"
                    ]
                ),
            }
        )

        log.append(
            {
                "image_id": image_id,
                "accion": "auditada",
                "resultado": (
                    "valida"
                    if valid_image
                    else "invalida"
                ),
                "detalle": (
                    image_error
                    if image_error
                    else (
                        "Imagen procesada "
                        "correctamente."
                    )
                ),
            }
        )

        if (
            index % 250 == 0
            or index == total
        ):
            print(
                f"Procesadas "
                f"{index}/{total}"
            )

    # ========================================================
    # IMÁGENES SIN EXCEL
    # ========================================================

    for image_id in (
        images_without_excel
    ):
        inconsistencies.append(
            {
                "image_id": image_id,
                "tipo": (
                    "imagen_sin_excel"
                ),
                "campo": "image_id",
                "detalle": (
                    "Archivo de imagen "
                    "sin registro en "
                    "dataset.xlsx."
                ),
            }
        )

    # ========================================================
    # JSON HUÉRFANOS
    # ========================================================

    image_stems = {
        Path(name).stem
        for name in image_ids
    }

    orphan_json = sorted(
        set(
            annotation_files.keys()
        )
        - image_stems
    )

    for stem in orphan_json:
        inconsistencies.append(
            {
                "image_id": (
                    f"{stem}.jpeg"
                ),
                "tipo": (
                    "json_sin_imagen"
                ),
                "campo": (
                    "annotation"
                ),
                "detalle": (
                    "Anotación JSON "
                    "sin imagen "
                    "correspondiente."
                ),
            }
        )

    # ========================================================
    # DUPLICADOS EXACTOS
    # ========================================================

    print_section(
        "4. DETECTANDO DUPLICADOS"
    )

    duplicate_records = []

    for (
        file_hash,
        ids,
    ) in hashes.items():

        if len(ids) <= 1:
            continue

        group = "|".join(
            ids
        )

        for image_id in ids:
            duplicate_records.append(
                {
                    "sha256": (
                        file_hash
                    ),
                    "image_id": (
                        image_id
                    ),
                    "cantidad_grupo": (
                        len(ids)
                    ),
                    "grupo": group,
                }
            )

            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "duplicado_exacto"
                    ),
                    "campo": "sha256",
                    "detalle": (
                        f"{len(ids)} "
                        "archivos comparten "
                        "el mismo SHA-256."
                    ),
                }
            )

    print(
        "Imágenes en grupos duplicados:",
        len(
            duplicate_records
        ),
    )

    # ========================================================
    # IMAGE_ID DUPLICADO EN EXCEL
    # ========================================================

    if not (
        duplicated_excel_ids.empty
    ):
        for image_id in (
            duplicated_excel_ids[
                "image_id"
            ].tolist()
        ):
            inconsistencies.append(
                {
                    "image_id": image_id,
                    "tipo": (
                        "image_id_duplicado_excel"
                    ),
                    "campo": "image_id",
                    "detalle": (
                        "image_id aparece "
                        "más de una vez "
                        "en dataset.xlsx."
                    ),
                }
            )

    # ========================================================
    # ESTADO POR REGISTRO
    # ========================================================

    issues_by_image = defaultdict(
        list
    )

    for issue in inconsistencies:
        issues_by_image[
            issue["image_id"]
        ].append(
            issue["tipo"]
        )

    # Los duplicados exactos se registran para auditoría,
    # pero no se excluyen automáticamente aquí.
    # La selección de una única copia se hará antes de
    # generar las particiones para mantener trazabilidad.

    critical_types = {
        "imagen_faltante",
        "imagen_corrupta",
        "image_id_duplicado_excel",
        "valor_binario_vacio",
        "valor_binario_invalido",
        "valor_binario_fuera_rango",
        "inconsistencia_tumor_clase",
        "clase_tumoral_invalida",
        "diagnostico_tumoral_invalido",
        "diagnostico_benigno_invalido",
        "diagnostico_maligno_invalido",
        "benigno_con_etiqueta_maligna",
        "maligno_con_etiqueta_benigna",
        "diagnostico_en_normal",
        "region_corporal_invalida",
        "proyeccion_invalida",
        "tumor_sin_json",
        "json_invalido",
        "json_imagen_no_coincide",
        "dimensiones_json_no_coinciden",
    }

    for record in manifest:
        image_id = record[
            "image_id"
        ]

        issues = issues_by_image.get(
            image_id,
            [],
        )

        critical = any(
            issue
            in critical_types
            for issue in issues
        )

        record[
            "issues_count"
        ] = len(issues)

        record["issues"] = "|".join(
            sorted(
                set(issues)
            )
        )

        record[
            "dataset_status"
        ] = (
            "exclude"
            if critical
            else "usable"
        )

    # ========================================================
    # DATAFRAMES
    # ========================================================

    manifest_df = pd.DataFrame(
        manifest
    )

    usable_df = manifest_df[
        manifest_df[
            "dataset_status"
        ] == "usable"
    ].copy()

    # ========================================================
    # ESTADÍSTICAS
    # ========================================================

    print_section(
        "5. GENERANDO REPORTES"
    )

    clinical_counts = (
        manifest_df[
            "clinical_class"
        ]
        .value_counts()
        .to_dict()
    )

    diagnosis_counts = (
        manifest_df[
            "diagnosis"
        ]
        .value_counts()
        .to_dict()
    )

    anatomy_counts = (
        manifest_df[
            "anatomy"
        ]
        .value_counts()
        .to_dict()
    )

    projection_counts = (
        manifest_df[
            "projection"
        ]
        .value_counts()
        .to_dict()
    )

    issue_counts = Counter(
        issue["tipo"]
        for issue
        in inconsistencies
    )

    # ========================================================
    # RESUMEN
    # ========================================================

    summary = {
        "dataset": (
            DATASET_NAME
        ),
        "version": (
            DATASET_VERSION
        ),
        "generated_at_utc": (
            utc_now_iso()
        ),
        "source": {
            "name": (
                SOURCE_NAME
            ),
            "version": (
                SOURCE_VERSION
            ),
            "doi": (
                SOURCE_DOI
            ),
            "article_id": (
                SOURCE_ARTICLE_ID
            ),
            "file_id": (
                SOURCE_FILE_ID
            ),
            "original_zip_sha256": (
                SOURCE_ZIP_SHA256
            ),
        },
        "original": {
            "excel_rows": int(
                len(df)
            ),
            "image_files": int(
                len(
                    image_files
                )
            ),
            "annotation_json_files": int(
                len(
                    annotation_files
                )
            ),
        },
        "quality": {
            "usable_records": int(
                len(
                    usable_df
                )
            ),
            "excluded_records": int(
                len(
                    manifest_df
                )
                - len(
                    usable_df
                )
            ),
            "images_without_excel": int(
                len(
                    images_without_excel
                )
            ),
            "excel_without_image": int(
                len(
                    excel_without_image
                )
            ),
            "orphan_json": int(
                len(
                    orphan_json
                )
            ),
            "duplicate_image_records": int(
                len(
                    duplicate_records
                )
            ),
            "inconsistencies_total": int(
                len(
                    inconsistencies
                )
            ),
            "inconsistencies_by_type": {
                str(key): int(value)
                for key, value
                in sorted(
                    issue_counts.items()
                )
            },
        },
        "classes": {
            "clinical_class": {
                str(key): int(value)
                for key, value
                in clinical_counts.items()
            },
            "diagnosis": {
                str(key): int(value)
                for key, value
                in diagnosis_counts.items()
            },
            "anatomy": {
                str(key): int(value)
                for key, value
                in anatomy_counts.items()
            },
            "projection": {
                str(key): int(value)
                for key, value
                in projection_counts.items()
            },
            "osteosarcoma_total": int(
                manifest_df[
                    "osteosarcoma"
                ].sum()
            ),
            "long_bone_scope_total": int(
                manifest_df[
                    "long_bone_scope"
                ].sum()
            ),
        },
    }

    # ========================================================
    # VERSIONADO
    # ========================================================

    version = {
        "dataset_name": (
            DATASET_NAME
        ),
        "dataset_version": (
            DATASET_VERSION
        ),
        "state": "AUDITED",
        "generated_at_utc": (
            utc_now_iso()
        ),
        "responsible": (
            "Proyecto de grado - "
            "Sistema de apoyo al análisis "
            "de radiografías óseas"
        ),
        "source": {
            "dataset": (
                SOURCE_NAME
            ),
            "source_version": (
                SOURCE_VERSION
            ),
            "doi": (
                SOURCE_DOI
            ),
            "figshare_article_id": (
                SOURCE_ARTICLE_ID
            ),
            "figshare_file_id": (
                SOURCE_FILE_ID
            ),
            "original_zip_sha256": (
                SOURCE_ZIP_SHA256
            ),
        },
        "processing": {
            "original_data_modified": False,
            "image_integrity_check": True,
            "sha256_per_image": True,
            "exact_duplicate_detection": True,
            "excel_metadata_validation": True,
            "annotation_json_validation": True,
            "anatomical_validation": True,
            "clinical_label_validation": True,
            "patient_level_split": False,
            "split_generated": False,
            "preprocessing_generated": False,
        },
        "notes": [
            (
                "Los archivos originales BTXRD "
                "permanecen sin modificación."
            ),
            (
                "Esta versión corresponde a "
                "auditoría y limpieza lógica."
            ),
            (
                "BTXRD puede marcar múltiples "
                "estructuras anatómicas visibles "
                "en una misma radiografía; dichas "
                "combinaciones no se consideran "
                "errores por sí mismas."
            ),
            (
                "Los duplicados exactos se "
                "registran mediante SHA-256 y "
                "se resolverán al construir las "
                "particiones."
            ),
            (
                "No se atribuye el origen de "
                "BTXRD a la Clínica San Juan "
                "de Dios."
            ),
            (
                "No se generan particiones "
                "train/validation/test en esta "
                "etapa."
            ),
        ],
    }

    # ========================================================
    # GUARDAR
    # ========================================================

    manifest_df.to_csv(
        MANIFEST_PATH,
        index=False,
        encoding="utf-8-sig",
    )

    save_csv(
        log,
        LOG_PATH,
        [
            "image_id",
            "accion",
            "resultado",
            "detalle",
        ],
    )

    save_csv(
        duplicate_records,
        DUPLICATES_PATH,
        [
            "sha256",
            "image_id",
            "cantidad_grupo",
            "grupo",
        ],
    )

    save_csv(
        inconsistencies,
        INCONSISTENCIES_PATH,
        [
            "image_id",
            "tipo",
            "campo",
            "detalle",
        ],
    )

    write_json(
        SUMMARY_PATH,
        summary,
    )

    write_json(
        VERSION_PATH,
        version,
    )

    # ========================================================
    # RESULTADO
    # ========================================================

    print_section(
        "RESULTADO"
    )

    print(
        "Registros originales :",
        len(
            manifest_df
        ),
    )

    print(
        "Registros utilizables:",
        len(
            usable_df
        ),
    )

    print(
        "Registros excluidos  :",
        len(
            manifest_df
        )
        - len(
            usable_df
        ),
    )

    print(
        "Osteosarcoma         :",
        int(
            manifest_df[
                "osteosarcoma"
            ].sum()
        ),
    )

    print(
        "Huesos largos        :",
        int(
            manifest_df[
                "long_bone_scope"
            ].sum()
        ),
    )

    print(
        "Inconsistencias      :",
        len(
            inconsistencies
        ),
    )

    print(
        "Duplicados exactos   :",
        len(
            duplicate_records
        ),
    )

    print()
    print(
        "Generados:"
    )

    for path in [
        MANIFEST_PATH,
        LOG_PATH,
        SUMMARY_PATH,
        DUPLICATES_PATH,
        INCONSISTENCIES_PATH,
        VERSION_PATH,
    ]:
        print(
            " -",
            path,
        )

    print()

    print(
        "Dataset V1 auditado correctamente."
    )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(
            main()
        )

    except KeyboardInterrupt:
        print(
            "\nProceso cancelado."
        )

        sys.exit(130)

    except Exception as exc:
        print()

        print(
            "ERROR:",
            type(exc).__name__,
            "-",
            str(exc),
        )

        raise
