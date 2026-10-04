from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


DATA_ROOT = Path(
    "/datos_radiografias_san_juan_de_dios"
)

PARTITIONS_DIR = (
    DATA_ROOT
    / "03_particiones"
)

OUTPUT_DIR = (
    PARTITIONS_DIR
    / "localizacion_v1"
)


ALLOWED_ANATOMY = {
    "humerus",
    "radius",
    "ulna",
    "femur",
    "tibia",
    "fibula",
}


PARTITIONS = {
    "train": (
        PARTITIONS_DIR
        / "train_v1.csv"
    ),
    "validation": (
        PARTITIONS_DIR
        / "validation_v1.csv"
    ),
    "test": (
        PARTITIONS_DIR
        / "test_v1.csv"
    ),
}


def anatomy_allowed(
    anatomy: str,
) -> bool:
    parts = {
        part.strip().lower()
        for part in str(
            anatomy
        ).split("|")
        if part.strip()
    }

    if not parts:
        return False

    return parts.issubset(
        ALLOWED_ANATOMY
    )


def load_annotation(
    path: Path,
) -> dict:
    return json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )


def get_osteosarcoma_bbox(
    annotation: dict,
):
    width = int(
        annotation[
            "imageWidth"
        ]
    )

    height = int(
        annotation[
            "imageHeight"
        ]
    )

    all_points = []

    shapes = annotation.get(
        "shapes",
        []
    )

    for shape in shapes:
        label = str(
            shape.get(
                "label",
                "",
            )
        ).strip().lower()

        if label != "osteosarcoma":
            continue

        points = shape.get(
            "points",
            []
        )

        for point in points:
            if (
                not isinstance(
                    point,
                    (list, tuple),
                )
                or len(point) < 2
            ):
                continue

            x = float(
                point[0]
            )

            y = float(
                point[1]
            )

            all_points.append(
                (
                    x,
                    y,
                )
            )

    if not all_points:
        return None

    xs = [
        point[0]
        for point
        in all_points
    ]

    ys = [
        point[1]
        for point
        in all_points
    ]

    x1 = max(
        0.0,
        min(xs),
    )

    y1 = max(
        0.0,
        min(ys),
    )

    x2 = min(
        float(width - 1),
        max(xs),
    )

    y2 = min(
        float(height - 1),
        max(ys),
    )

    if (
        x2 <= x1
        or y2 <= y1
    ):
        return None

    return {
        "image_width": width,
        "image_height": height,

        "bbox_x1": x1,
        "bbox_y1": y1,
        "bbox_x2": x2,
        "bbox_y2": y2,

        "bbox_x1_norm": (
            x1 / width
        ),
        "bbox_y1_norm": (
            y1 / height
        ),
        "bbox_x2_norm": (
            x2 / width
        ),
        "bbox_y2_norm": (
            y2 / height
        ),
    }


def process_partition(
    partition_name: str,
    csv_path: Path,
):
    data = pd.read_csv(
        csv_path
    )

    records = []

    rejected_anatomy = 0
    rejected_annotation = 0

    positives = data[
        data[
            "osteosarcoma"
        ].astype(str)
        == "1"
    ]

    for _, row in (
        positives.iterrows()
    ):
        anatomy = str(
            row.get(
                "anatomy",
                "",
            )
        )

        if not anatomy_allowed(
            anatomy
        ):
            rejected_anatomy += 1
            continue

        annotation_exists = str(
            row.get(
                "annotation_exists",
                "0",
            )
        )

        annotation_valid = str(
            row.get(
                "annotation_valid",
                "0",
            )
        )

        if (
            annotation_exists != "1"
            or annotation_valid != "1"
        ):
            rejected_annotation += 1
            continue

        annotation_path = Path(
            str(
                row[
                    "annotation_path"
                ]
            )
        )

        image_path = Path(
            str(
                row[
                    "image_path"
                ]
            )
        )

        if (
            not annotation_path.exists()
            or not image_path.exists()
        ):
            rejected_annotation += 1
            continue

        try:
            annotation = (
                load_annotation(
                    annotation_path
                )
            )

            bbox = (
                get_osteosarcoma_bbox(
                    annotation
                )
            )

        except Exception:
            bbox = None

        if bbox is None:
            rejected_annotation += 1
            continue

        record = {
            "partition": (
                partition_name
            ),

            "image_id": str(
                row.get(
                    "image_id",
                    image_path.name,
                )
            ),

            "image_path": str(
                image_path
            ),

            "annotation_path": str(
                annotation_path
            ),

            "anatomy": anatomy,

            "diagnosis": str(
                row.get(
                    "diagnosis",
                    "",
                )
            ),

            "osteosarcoma": 1,

            **bbox,
        }

        if "patient_id" in row:
            record[
                "patient_id"
            ] = row[
                "patient_id"
            ]

        records.append(
            record
        )

    result = pd.DataFrame(
        records
    )

    output_path = (
        OUTPUT_DIR
        / (
            f"{partition_name}"
            "_localizacion_v1.csv"
        )
    )

    result.to_csv(
        output_path,
        index=False,
    )

    print()
    print(
        "=" * 72
    )

    print(
        partition_name.upper()
    )

    print(
        "=" * 72
    )

    print(
        "Positivos originales:",
        len(
            positives
        ),
    )

    print(
        "Localización válida:",
        len(
            result
        ),
    )

    print(
        "Excluidos anatomía:",
        rejected_anatomy,
    )

    print(
        "Excluidos anotación:",
        rejected_annotation,
    )

    if not result.empty:
        print()
        print(
            "Distribución anatómica:"
        )

        print(
            result[
                "anatomy"
            ]
            .value_counts()
            .to_string()
        )

    return {
        "partition": (
            partition_name
        ),

        "original_osteosarcoma": int(
            len(
                positives
            )
        ),

        "localization_total": int(
            len(
                result
            )
        ),

        "excluded_anatomy": int(
            rejected_anatomy
        ),

        "excluded_annotation": int(
            rejected_annotation
        ),

        "csv": str(
            output_path
        ),
    }


def main():
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary = {
        "version": (
            "localizacion_v1"
        ),

        "allowed_anatomy": sorted(
            ALLOWED_ANATOMY
        ),

        "method": (
            "Bounding box calculado "
            "como unión espacial de "
            "todas las anotaciones "
            "osteosarcoma disponibles "
            "por imagen."
        ),

        "partitions": [],
    }

    print()
    print(
        "=" * 72
    )

    print(
        "PREPARACIÓN DATASET "
        "LOCALIZACIÓN OSTEOSARCOMA"
    )

    print(
        "=" * 72
    )

    for (
        partition_name,
        csv_path,
    ) in PARTITIONS.items():

        result = (
            process_partition(
                partition_name,
                csv_path,
            )
        )

        summary[
            "partitions"
        ].append(
            result
        )

    summary_path = (
        OUTPUT_DIR
        / "resumen_localizacion_v1.json"
    )

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "=" * 72
    )

    print(
        "DATASET LOCALIZACIÓN CREADO"
    )

    print(
        "=" * 72
    )

    print(
        "Directorio:",
        OUTPUT_DIR,
    )

    print(
        "Resumen:",
        summary_path,
    )


if __name__ == "__main__":
    main()
