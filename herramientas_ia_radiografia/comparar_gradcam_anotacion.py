from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
from PIL import Image, ImageDraw

from generar_gradcam_osteosarcoma import (
    GradCAM,
    cargar_modelo,
    crear_heatmap,
    crear_superposicion,
    obtener_probabilidades,
    preparar_imagen,
)


def cargar_anotacion(
    annotation_path: Path,
):
    if not annotation_path.exists():
        raise FileNotFoundError(
            f"No existe la anotación: "
            f"{annotation_path}"
        )

    return json.loads(
        annotation_path.read_text(
            encoding="utf-8"
        )
    )


def crear_mascara_ground_truth(
    annotation: dict,
    image_size: tuple[int, int],
):
    width, height = image_size

    mask_image = Image.new(
        "L",
        (width, height),
        0,
    )

    draw = ImageDraw.Draw(
        mask_image
    )

    shapes = annotation.get(
        "shapes",
        []
    )

    for shape in shapes:
        if (
            str(
                shape.get(
                    "label",
                    "",
                )
            ).lower()
            != "osteosarcoma"
        ):
            continue

        points = shape.get(
            "points",
            []
        )

        shape_type = shape.get(
            "shape_type"
        )

        if (
            shape_type == "rectangle"
            and len(points) >= 2
        ):
            x1, y1 = points[0]
            x2, y2 = points[1]

            draw.rectangle(
                [
                    (
                        int(x1),
                        int(y1),
                    ),
                    (
                        int(x2),
                        int(y2),
                    ),
                ],
                fill=255,
            )

        elif (
            shape_type == "polygon"
            and len(points) >= 3
        ):
            polygon = [
                (
                    int(point[0]),
                    int(point[1]),
                )
                for point in points
            ]

            draw.polygon(
                polygon,
                fill=255,
            )

    return (
        np.asarray(
            mask_image,
            dtype=np.uint8,
        )
        > 0
    )


def dibujar_ground_truth(
    image: Image.Image,
    annotation: dict,
):
    result = image.copy()

    draw = ImageDraw.Draw(
        result
    )

    line_width = max(
        4,
        int(
            min(image.size)
            * 0.004
        ),
    )

    for shape in annotation.get(
        "shapes",
        []
    ):
        if (
            str(
                shape.get(
                    "label",
                    "",
                )
            ).lower()
            != "osteosarcoma"
        ):
            continue

        points = shape.get(
            "points",
            []
        )

        shape_type = shape.get(
            "shape_type"
        )

        if (
            shape_type == "rectangle"
            and len(points) >= 2
        ):
            x1, y1 = points[0]
            x2, y2 = points[1]

            draw.rectangle(
                [
                    (
                        int(x1),
                        int(y1),
                    ),
                    (
                        int(x2),
                        int(y2),
                    ),
                ],
                outline=(
                    0,
                    255,
                    0,
                ),
                width=line_width,
            )

        elif (
            shape_type == "polygon"
            and len(points) >= 3
        ):
            polygon = [
                (
                    int(point[0]),
                    int(point[1]),
                )
                for point in points
            ]

            polygon.append(
                polygon[0]
            )

            draw.line(
                polygon,
                fill=(
                    0,
                    255,
                    0,
                ),
                width=line_width,
            )

    return result


def calcular_metricas_localizacion(
    cam: np.ndarray,
    gt_mask: np.ndarray,
    threshold: float = 0.65,
):
    cam_mask = (
        cam >= threshold
    )

    intersection = np.logical_and(
        cam_mask,
        gt_mask,
    ).sum()

    union = np.logical_or(
        cam_mask,
        gt_mask,
    ).sum()

    iou = (
        float(intersection / union)
        if union > 0
        else 0.0
    )

    total_energy = float(
        cam.sum()
    )

    energy_inside = float(
        cam[
            gt_mask
        ].sum()
    )

    energy_ratio = (
        energy_inside
        / total_energy
        if total_energy > 0
        else 0.0
    )

    peak_position = np.unravel_index(
        np.argmax(cam),
        cam.shape,
    )

    peak_y = int(
        peak_position[0]
    )

    peak_x = int(
        peak_position[1]
    )

    peak_inside = bool(
        gt_mask[
            peak_y,
            peak_x,
        ]
    )

    return {
        "cam_threshold": float(
            threshold
        ),
        "iou_cam_ground_truth": (
            float(iou)
        ),
        "cam_energy_inside_ground_truth": (
            float(energy_ratio)
        ),
        "peak_x": peak_x,
        "peak_y": peak_y,
        "peak_inside_ground_truth": (
            peak_inside
        ),
    }


def guardar_panel(
    original: Image.Image,
    ground_truth: Image.Image,
    heatmap: np.ndarray,
    overlay: Image.Image,
    output_path: Path,
    probability: float,
    metrics: dict,
):
    figure = plt.figure(
        figsize=(17, 5)
    )

    axis1 = figure.add_subplot(
        1,
        4,
        1,
    )

    axis1.imshow(
        original
    )

    axis1.set_title(
        "Radiografía original"
    )

    axis1.axis(
        "off"
    )

    axis2 = figure.add_subplot(
        1,
        4,
        2,
    )

    axis2.imshow(
        ground_truth
    )

    axis2.set_title(
        "Anotación real"
    )

    axis2.axis(
        "off"
    )

    axis3 = figure.add_subplot(
        1,
        4,
        3,
    )

    axis3.imshow(
        heatmap
    )

    axis3.set_title(
        "Grad-CAM"
    )

    axis3.axis(
        "off"
    )

    axis4 = figure.add_subplot(
        1,
        4,
        4,
    )

    axis4.imshow(
        overlay
    )

    axis4.set_title(
        "Superposición"
    )

    axis4.axis(
        "off"
    )

    figure.suptitle(
        (
            f"P(osteosarcoma): "
            f"{probability:.4f} | "
            f"IoU: "
            f"{metrics['iou_cam_ground_truth']:.4f} | "
            f"Energía en lesión: "
            f"{metrics['cam_energy_inside_ground_truth']:.2%}"
        ),
        fontsize=12,
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--image",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--annotation",
        required=True,
        type=Path,
    )

    parser.add_argument(
        "--model",
        type=Path,
        default=Path(
            "/modelos/"
            "osteosarcoma_"
            "efficientnet_b0_"
            "finetuned_v1.pt"
        ),
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "/datos_radiografias_"
            "san_juan_de_dios/"
            "04_reportes/"
            "comparacion_gradcam_ground_truth"
        ),
    )

    args = parser.parse_args()

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        "=============================================="
    )
    print(
        " GRAD-CAM VS ANOTACIÓN REAL"
    )
    print(
        "=============================================="
    )
    print(
        "Dispositivo:",
        device,
    )

    if device.type == "cuda":
        print(
            "GPU:",
            torch.cuda.get_device_name(
                0
            ),
        )

    (
        model,
        threshold,
        version,
        best_epoch,
    ) = cargar_modelo(
        args.model,
        device,
    )

    (
        original,
        tensor,
    ) = preparar_imagen(
        args.image,
        device,
    )

    probabilities = (
        obtener_probabilidades(
            model,
            tensor,
        )
    )

    osteosarcoma_probability = float(
        probabilities[1]
    )

    annotation = cargar_anotacion(
        args.annotation
    )

    gt_mask = crear_mascara_ground_truth(
        annotation,
        original.size,
    )

    gt_image = dibujar_ground_truth(
        original,
        annotation,
    )

    gradcam = GradCAM(
        model,
        model.features[-1],
    )

    try:
        cam = gradcam.generate(
            tensor,
            1,
            original.size,
        )
    finally:
        gradcam.close()

    heatmap = crear_heatmap(
        cam
    )

    overlay = crear_superposicion(
        original,
        heatmap,
        alpha=0.42,
    )

    # Dibujar ground truth también
    # sobre la superposición.
    overlay_gt = dibujar_ground_truth(
        overlay,
        annotation,
    )

    metrics = (
        calcular_metricas_localizacion(
            cam,
            gt_mask,
            threshold=0.65,
        )
    )

    args.output.mkdir(
        parents=True,
        exist_ok=True,
    )

    panel_path = (
        args.output
        / (
            args.image.stem
            + "_comparacion.png"
        )
    )

    guardar_panel(
        original=original,
        ground_truth=gt_image,
        heatmap=heatmap,
        overlay=overlay_gt,
        output_path=panel_path,
        probability=(
            osteosarcoma_probability
        ),
        metrics=metrics,
    )

    result = {
        "image": (
            args.image.name
        ),
        "annotation": (
            args.annotation.name
        ),
        "model_version": version,
        "best_epoch": best_epoch,
        "classification_threshold": (
            threshold
        ),
        "probability_osteosarcoma": (
            osteosarcoma_probability
        ),
        "prediction": (
            "osteosarcoma"
            if osteosarcoma_probability
            >= threshold
            else "no_osteosarcoma"
        ),
        **metrics,
        "interpretation_note": (
            "Grad-CAM representa las zonas "
            "que más influyeron en la "
            "clasificación. La anotación "
            "del dataset representa la "
            "región de referencia de la "
            "lesión. No son equivalentes."
        ),
    }

    result_path = (
        args.output
        / (
            args.image.stem
            + "_metricas.json"
        )
    )

    result_path.write_text(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print(
        "Imagen:",
        args.image.name,
    )

    print(
        "P(osteosarcoma):",
        round(
            osteosarcoma_probability,
            6,
        ),
    )

    print(
        "IoU CAM/GT:",
        round(
            metrics[
                "iou_cam_ground_truth"
            ],
            6,
        ),
    )

    print(
        "Energía CAM dentro de GT:",
        round(
            metrics[
                "cam_energy_inside_ground_truth"
            ],
            6,
        ),
    )

    print(
        "Pico CAM dentro de GT:",
        metrics[
            "peak_inside_ground_truth"
        ],
    )

    print()
    print(
        "Panel:",
        panel_path,
    )

    print(
        "Métricas:",
        result_path,
    )


if __name__ == "__main__":
    main()
