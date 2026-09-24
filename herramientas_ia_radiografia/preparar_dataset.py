from __future__ import annotations

import argparse
import random
import shutil
from pathlib import Path
from typing import Any

from PIL import Image
from datasets import load_dataset
from torchvision.datasets import CIFAR10


XRAY_DATASET = "MEDIFICS/MURADATASETSU"


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


def save_image(
    image: Image.Image,
    path: Path,
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.convert(
        "RGB",
    ).save(
        path,
        format="JPEG",
        quality=95,
        subsampling=0,
    )


def copy_extra_images(
    source: Path,
    destination: Path,
    prefix: str,
) -> int:
    if not source.exists():
        return 0

    allowed = {
        ".jpg",
        ".jpeg",
        ".png",
    }

    count = 0

    for path in sorted(
        source.rglob("*"),
    ):
        if (
            not path.is_file()
            or
            path.suffix.lower()
            not in allowed
        ):
            continue

        try:
            with Image.open(
                path,
            ) as image:
                save_image(
                    image,
                    destination
                    /
                    f"{prefix}_{count:05d}.jpg",
                )

            count += 1

        except Exception:
            continue

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Prepara un dataset prototipo "
            "radiografia / no radiografia."
        )
    )

    parser.add_argument(
        "--max-per-class",
        type=int,
        default=700,
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
            "dataset_radiografia",
        ),
    )

    parser.add_argument(
        "--cifar-cache",
        type=Path,
        default=Path(
            ".cache_datasets/cifar10",
        ),
        help=(
            "Carpeta de cache para CIFAR-10. "
            "Se mantiene FUERA del dataset."
        ),
    )

    parser.add_argument(
        "--extra-radiografias",
        type=Path,
        default=Path(
            "extras/radiografia",
        ),
    )

    parser.add_argument(
        "--extra-no-radiografias",
        type=Path,
        default=Path(
            "extras/no_radiografia",
        ),
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help=(
            "Elimina solo el dataset generado. "
            "La cache descargada se conserva."
        ),
    )

    args = parser.parse_args()

    random.seed(
        args.seed,
    )

    root = args.output

    if (
        args.clean
        and
        root.exists()
    ):
        shutil.rmtree(
            root,
        )

    positive_dir = (
        root
        /
        "radiografia"
    )

    negative_dir = (
        root
        /
        "no_radiografia"
    )

    positive_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    negative_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    args.cifar_cache.mkdir(
        parents=True,
        exist_ok=True,
    )

    print(
        "1/3 Descargando radiografias "
        "musculoesqueleticas publicas..."
    )

    dataset = load_dataset(
        XRAY_DATASET,
        split="train",
    )

    indices = list(
        range(
            len(
                dataset,
            )
        )
    )

    random.shuffle(
        indices,
    )

    positive_count = 0

    for source_idx in indices:
        row = dataset[
            source_idx
        ]

        image = find_image(
            row,
        )

        if image is None:
            continue

        save_image(
            image,
            positive_dir
            /
            f"mura_{positive_count:05d}.jpg",
        )

        positive_count += 1

        if (
            positive_count
            >=
            args.max_per_class
        ):
            break

    if (
        positive_count
        ==
        0
    ):
        raise RuntimeError(
            "No fue posible obtener radiografias."
        )

    print(
        "2/3 Descargando imagenes naturales "
        "para la clase no radiografia..."
    )

    cifar = CIFAR10(
        root=str(
            args.cifar_cache,
        ),
        train=True,
        download=True,
    )

    negative_indices = list(
        range(
            len(
                cifar,
            )
        )
    )

    random.shuffle(
        negative_indices,
    )

    negative_count = 0

    for source_idx in negative_indices[
        :
        args.max_per_class
    ]:
        image, _ = cifar[
            source_idx
        ]

        save_image(
            image,
            negative_dir
            /
            f"natural_{negative_count:05d}.jpg",
        )

        negative_count += 1

    print(
        "3/3 Incorporando imagenes adicionales "
        "si existen..."
    )

    extra_positive = copy_extra_images(
        args.extra_radiografias,
        positive_dir,
        "extra_xray",
    )

    extra_negative = copy_extra_images(
        args.extra_no_radiografias,
        negative_dir,
        "extra_non_xray",
    )

    print()

    print(
        "Dataset preparado"
    )

    print(
        f"  Radiografias publicas:        "
        f"{positive_count}"
    )

    print(
        f"  No radiografias publicas:     "
        f"{negative_count}"
    )

    print(
        f"  Radiografias adicionales:     "
        f"{extra_positive}"
    )

    print(
        f"  No radiografias adicionales:  "
        f"{extra_negative}"
    )

    print(
        f"  Carpeta dataset: "
        f"{root.resolve()}"
    )

    print(
        f"  Cache CIFAR-10: "
        f"{args.cifar_cache.resolve()}"
    )

    print()

    print(
        "IMPORTANTE: este conjunto sirve para "
        "integrar y demostrar el filtro. "
        "Antes de reportar rendimiento academico "
        "definitivo debe ampliarse y evaluarse "
        "con un conjunto independiente."
    )


if __name__ == "__main__":
    main()
