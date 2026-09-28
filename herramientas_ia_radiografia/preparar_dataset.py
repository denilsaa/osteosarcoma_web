from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

from datasets import load_dataset
from PIL import Image, ImageFile
from torchvision.datasets import CIFAR10


ImageFile.LOAD_TRUNCATED_IMAGES = False

XRAY_DATASET = "MEDIFICS/MURADATASETSU"

CLASS_XRAY = "radiografia"
CLASS_NON_XRAY = "no_radiografia"

ALLOWED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp",
}


def find_image(value: Any) -> Image.Image | None:
    if isinstance(value, Image.Image):
        return value

    if isinstance(value, dict):
        for child in value.values():
            image = find_image(child)

            if image is not None:
                return image

    if isinstance(value, (list, tuple)):
        for child in value:
            image = find_image(child)

            if image is not None:
                return image

    return None


def normalize_image(
    image: Image.Image,
) -> Image.Image:
    image.load()

    return image.convert("RGB")


def calculate_image_hash(
    image: Image.Image,
) -> str:
    rgb = normalize_image(image)

    payload = (
        f"{rgb.width}x{rgb.height}|RGB|".encode(
            "utf-8"
        )
        +
        rgb.tobytes()
    )

    return hashlib.sha256(
        payload
    ).hexdigest()


def save_image(
    image: Image.Image,
    destination: Path,
) -> None:
    destination.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    normalize_image(
        image
    ).save(
        destination,
        format="JPEG",
        quality=95,
        subsampling=0,
        optimize=True,
    )


def register_image(
    *,
    image: Image.Image,
    class_name: str,
    source: str,
    source_reference: str,
    destination_dir: Path,
    prefix: str,
    seen_hashes: set[str],
    manifest: list[dict[str, Any]],
    incidents: list[dict[str, str]],
) -> bool:
    try:
        rgb = normalize_image(
            image
        )

        image_hash = calculate_image_hash(
            rgb
        )

        if image_hash in seen_hashes:
            incidents.append(
                {
                    "tipo": "DUPLICADO",
                    "clase": class_name,
                    "origen": source,
                    "referencia": source_reference,
                    "detalle": image_hash,
                }
            )

            return False

        seen_hashes.add(
            image_hash
        )

        class_index = sum(
            1
            for row in manifest
            if row["clase"] == class_name
        )

        filename = (
            f"{prefix}_"
            f"{class_index:06d}.jpg"
        )

        destination = (
            destination_dir
            /
            filename
        )

        save_image(
            rgb,
            destination,
        )

        manifest.append(
            {
                "archivo": str(
                    destination.as_posix()
                ),
                "clase": class_name,
                "origen": source,
                "referencia_origen": (
                    source_reference
                ),
                "sha256_imagen": image_hash,
                "ancho_original": rgb.width,
                "alto_original": rgb.height,
                "modo": "RGB",
            }
        )

        return True

    except Exception as exc:
        incidents.append(
            {
                "tipo": "ARCHIVO_INVALIDO",
                "clase": class_name,
                "origen": source,
                "referencia": source_reference,
                "detalle": (
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            }
        )

        return False


def import_extra_images(
    *,
    source_dir: Path,
    class_name: str,
    destination_dir: Path,
    prefix: str,
    seen_hashes: set[str],
    manifest: list[dict[str, Any]],
    incidents: list[dict[str, str]],
) -> int:
    if not source_dir.exists():
        return 0

    added = 0

    for path in sorted(
        source_dir.rglob("*")
    ):
        if (
            not path.is_file()
            or
            path.suffix.lower()
            not in ALLOWED_EXTENSIONS
        ):
            continue

        try:
            with Image.open(
                path
            ) as image:
                accepted = register_image(
                    image=image,
                    class_name=class_name,
                    source="EXTRA_LOCAL",
                    source_reference=str(path),
                    destination_dir=(
                        destination_dir
                    ),
                    prefix=prefix,
                    seen_hashes=seen_hashes,
                    manifest=manifest,
                    incidents=incidents,
                )

                if accepted:
                    added += 1

        except Exception as exc:
            incidents.append(
                {
                    "tipo": "ARCHIVO_INVALIDO",
                    "clase": class_name,
                    "origen": "EXTRA_LOCAL",
                    "referencia": str(path),
                    "detalle": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }
            )

    return added


def write_csv(
    path: Path,
    rows: list[dict[str, Any]],
    fields: list[str],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=fields,
        )

        writer.writeheader()
        writer.writerows(
            rows
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara Dataset V2 para "
            "radiografia / no radiografia."
        )
    )

    parser.add_argument(
        "--max-radiografias",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--max-no-radiografias",
        type=int,
        default=5000,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "dataset_radiografia_v2"
        ),
    )

    parser.add_argument(
        "--cifar-cache",
        type=Path,
        default=Path(
            ".cache_datasets/cifar10"
        ),
    )

    parser.add_argument(
        "--extra-radiografias",
        type=Path,
        default=Path(
            "extras/radiografia"
        ),
    )

    parser.add_argument(
        "--extra-no-radiografias",
        type=Path,
        default=Path(
            "extras/no_radiografia"
        ),
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Elimina solamente el Dataset V2 "
            "generado anteriormente."
        ),
    )

    args = parser.parse_args()

    random.seed(
        args.seed
    )

    root = args.output

    if (
        args.clean
        and
        root.exists()
    ):
        print(
            "Eliminando Dataset V2 anterior..."
        )

        shutil.rmtree(
            root
        )

    xray_dir = (
        root
        /
        CLASS_XRAY
    )

    non_xray_dir = (
        root
        /
        CLASS_NON_XRAY
    )

    xray_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    non_xray_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.cifar_cache.mkdir(
        parents=True,
        exist_ok=True,
    )

    manifest: list[
        dict[str, Any]
    ] = []

    incidents: list[
        dict[str, str]
    ] = []

    seen_hashes: set[str] = set()

    print()
    print(
        "========================================"
    )
    print(
        " DATASET V2 - RADIOGRAFIA / NO RADIOGRAFIA"
    )
    print(
        "========================================"
    )

    # ==================================================
    # RADIOGRAFIAS
    # ==================================================

    print()
    print(
        "1/4 Descargando radiografias "
        "musculoesqueleticas..."
    )

    dataset = load_dataset(
        XRAY_DATASET,
        split="train",
    )

    indices = list(
        range(
            len(
                dataset
            )
        )
    )

    random.shuffle(
        indices
    )

    public_xray_count = 0

    for source_index in indices:
        if (
            public_xray_count
            >=
            args.max_radiografias
        ):
            break

        try:
            row = dataset[
                source_index
            ]

            image = find_image(
                row
            )

            if image is None:
                incidents.append(
                    {
                        "tipo": "SIN_IMAGEN",
                        "clase": CLASS_XRAY,
                        "origen": XRAY_DATASET,
                        "referencia": str(
                            source_index
                        ),
                        "detalle": (
                            "El registro no contiene "
                            "una imagen reconocible."
                        ),
                    }
                )

                continue

            accepted = register_image(
                image=image,
                class_name=CLASS_XRAY,
                source=XRAY_DATASET,
                source_reference=str(
                    source_index
                ),
                destination_dir=xray_dir,
                prefix="mura",
                seen_hashes=seen_hashes,
                manifest=manifest,
                incidents=incidents,
            )

            if accepted:
                public_xray_count += 1

                if (
                    public_xray_count
                    % 500
                    ==
                    0
                ):
                    print(
                        "    Radiografias "
                        f"procesadas: "
                        f"{public_xray_count}"
                    )

        except Exception as exc:
            incidents.append(
                {
                    "tipo": "ERROR_LECTURA",
                    "clase": CLASS_XRAY,
                    "origen": XRAY_DATASET,
                    "referencia": str(
                        source_index
                    ),
                    "detalle": (
                        f"{type(exc).__name__}: "
                        f"{exc}"
                    ),
                }
            )

    print(
        "    Radiografias publicas validas: "
        f"{public_xray_count}"
    )

    # ==================================================
    # NO RADIOGRAFIAS
    # ==================================================

    print()
    print(
        "2/4 Preparando imagenes "
        "no radiograficas..."
    )

    cifar = CIFAR10(
        root=str(
            args.cifar_cache
        ),
        train=True,
        download=True,
    )

    negative_indices = list(
        range(
            len(
                cifar
            )
        )
    )

    random.shuffle(
        negative_indices
    )

    public_non_xray_count = 0

    for source_index in negative_indices:
        if (
            public_non_xray_count
            >=
            args.max_no_radiografias
        ):
            break

        image, label = cifar[
            source_index
        ]

        accepted = register_image(
            image=image,
            class_name=CLASS_NON_XRAY,
            source="CIFAR10",
            source_reference=(
                f"{source_index}:"
                f"label={label}"
            ),
            destination_dir=non_xray_dir,
            prefix="natural",
            seen_hashes=seen_hashes,
            manifest=manifest,
            incidents=incidents,
        )

        if accepted:
            public_non_xray_count += 1

            if (
                public_non_xray_count
                % 500
                ==
                0
            ):
                print(
                    "    No radiografias "
                    f"procesadas: "
                    f"{public_non_xray_count}"
                )

    print(
        "    No radiografias publicas validas: "
        f"{public_non_xray_count}"
    )

    # ==================================================
    # EXTRAS
    # ==================================================

    print()
    print(
        "3/4 Incorporando imagenes "
        "adicionales..."
    )

    extra_xray_count = import_extra_images(
        source_dir=(
            args.extra_radiografias
        ),
        class_name=CLASS_XRAY,
        destination_dir=xray_dir,
        prefix="extra_xray",
        seen_hashes=seen_hashes,
        manifest=manifest,
        incidents=incidents,
    )

    extra_non_xray_count = (
        import_extra_images(
            source_dir=(
                args.extra_no_radiografias
            ),
            class_name=CLASS_NON_XRAY,
            destination_dir=non_xray_dir,
            prefix="extra_non_xray",
            seen_hashes=seen_hashes,
            manifest=manifest,
            incidents=incidents,
        )
    )

    print(
        "    Radiografias adicionales: "
        f"{extra_xray_count}"
    )

    print(
        "    No radiografias adicionales: "
        f"{extra_non_xray_count}"
    )

    # ==================================================
    # TRAZABILIDAD
    # ==================================================

    print()
    print(
        "4/4 Generando trazabilidad "
        "y estadisticas..."
    )

    manifest_path = (
        root
        /
        "manifest.csv"
    )

    incidents_path = (
        root
        /
        "incidencias.csv"
    )

    statistics_path = (
        root
        /
        "estadisticas.json"
    )

    write_csv(
        manifest_path,
        manifest,
        [
            "archivo",
            "clase",
            "origen",
            "referencia_origen",
            "sha256_imagen",
            "ancho_original",
            "alto_original",
            "modo",
        ],
    )

    write_csv(
        incidents_path,
        incidents,
        [
            "tipo",
            "clase",
            "origen",
            "referencia",
            "detalle",
        ],
    )

    class_counts = Counter(
        row["clase"]
        for row in manifest
    )

    source_counts = Counter(
        row["origen"]
        for row in manifest
    )

    incident_counts = Counter(
        row["tipo"]
        for row in incidents
    )

    statistics = {
        "version_dataset": (
            "radiografia_v2"
        ),
        "objetivo": (
            "Clasificacion binaria "
            "radiografia / no radiografia"
        ),
        "seed": args.seed,
        "total_imagenes_validas": (
            len(
                manifest
            )
        ),
        "clases": dict(
            sorted(
                class_counts.items()
            )
        ),
        "origenes": dict(
            sorted(
                source_counts.items()
            )
        ),
        "incidencias": dict(
            sorted(
                incident_counts.items()
            )
        ),
        "duplicados_descartados": (
            incident_counts.get(
                "DUPLICADO",
                0,
            )
        ),
        "archivos_invalidos": (
            incident_counts.get(
                "ARCHIVO_INVALIDO",
                0,
            )
            +
            incident_counts.get(
                "ERROR_LECTURA",
                0,
            )
        ),
        "radiografias_publicas": (
            public_xray_count
        ),
        "no_radiografias_publicas": (
            public_non_xray_count
        ),
        "radiografias_adicionales": (
            extra_xray_count
        ),
        "no_radiografias_adicionales": (
            extra_non_xray_count
        ),
        "nota": (
            "CIFAR-10 se conserva como fuente "
            "inicial de negativos. El conjunto "
            "debe complementarse posteriormente "
            "con negativos dificiles y evaluacion "
            "independiente."
        ),
    }

    statistics_path.write_text(
        json.dumps(
            statistics,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "========================================"
    )
    print(
        " DATASET V2 PREPARADO"
    )
    print(
        "========================================"
    )

    print(
        json.dumps(
            statistics,
            indent=2,
            ensure_ascii=False,
        )
    )

    print()
    print(
        f"Dataset:      {root.resolve()}"
    )

    print(
        f"Manifest:     "
        f"{manifest_path.resolve()}"
    )

    print(
        f"Incidencias:  "
        f"{incidents_path.resolve()}"
    )

    print(
        f"Estadisticas: "
        f"{statistics_path.resolve()}"
    )

    print()
    print(
        "IMPORTANTE:"
    )

    print(
        "Este paso prepara y audita los datos. "
        "NO reemplaza el modelo V1."
    )


if __name__ == "__main__":
    main()
