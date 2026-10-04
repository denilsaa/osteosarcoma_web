from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
from PIL import Image, ImageDraw
from torch import nn
from torchvision import models, transforms


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

CLASSES = [
    "no_osteosarcoma",
    "osteosarcoma",
]


class GradCAM:
    def __init__(
        self,
        model: nn.Module,
        target_layer: nn.Module,
    ):
        self.model = model
        self.target_layer = target_layer

        self.activations = None
        self.gradients = None

        self.forward_handle = (
            target_layer.register_forward_hook(
                self._forward_hook
            )
        )

        self.backward_handle = (
            target_layer.register_full_backward_hook(
                self._backward_hook
            )
        )

    def _forward_hook(
        self,
        module,
        inputs,
        output,
    ):
        self.activations = output.detach()

    def _backward_hook(
        self,
        module,
        grad_input,
        grad_output,
    ):
        self.gradients = (
            grad_output[0]
            .detach()
        )

    def generate(
        self,
        input_tensor: torch.Tensor,
        target_class: int,
        original_size: tuple[int, int],
    ) -> np.ndarray:

        self.model.zero_grad(
            set_to_none=True
        )

        logits = self.model(
            input_tensor
        )

        score = logits[
            0,
            target_class,
        ]

        score.backward()

        if (
            self.activations is None
            or self.gradients is None
        ):
            raise RuntimeError(
                "No fue posible obtener "
                "activaciones o gradientes."
            )

        weights = (
            self.gradients
            .mean(
                dim=(2, 3),
                keepdim=True,
            )
        )

        cam = (
            weights
            * self.activations
        ).sum(
            dim=1,
            keepdim=True,
        )

        cam = F.relu(cam)

        cam = F.interpolate(
            cam,
            size=(
                original_size[1],
                original_size[0],
            ),
            mode="bilinear",
            align_corners=False,
        )

        cam = (
            cam[0, 0]
            .detach()
            .cpu()
            .numpy()
        )

        minimum = float(
            cam.min()
        )

        maximum = float(
            cam.max()
        )

        if maximum > minimum:
            cam = (
                (cam - minimum)
                / (maximum - minimum)
            )
        else:
            cam = np.zeros_like(
                cam,
                dtype=np.float32,
            )

        return cam.astype(
            np.float32
        )

    def close(self):
        self.forward_handle.remove()
        self.backward_handle.remove()


def cargar_modelo(
    checkpoint_path: Path,
    device: torch.device,
):
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"No existe el modelo: "
            f"{checkpoint_path}"
        )

    checkpoint = torch.load(
        checkpoint_path,
        map_location="cpu",
        weights_only=False,
    )

    model = models.efficientnet_b0(
        weights=None
    )

    in_features = (
        model.classifier[1]
        .in_features
    )

    model.classifier[1] = nn.Linear(
        in_features,
        2,
    )

    state_dict = checkpoint.get(
        "state_dict"
    )

    if state_dict is None:
        raise RuntimeError(
            "El checkpoint no contiene "
            "'state_dict'."
        )

    model.load_state_dict(
        state_dict
    )

    model.to(device)

    model.eval()

    threshold = float(
        checkpoint.get(
            "threshold",
            0.50,
        )
    )

    version = str(
        checkpoint.get(
            "version",
            "osteosarcoma_finetuned_v1",
        )
    )

    best_epoch = checkpoint.get(
        "best_epoch"
    )

    return (
        model,
        threshold,
        version,
        best_epoch,
    )


def preparar_imagen(
    image_path: Path,
    device: torch.device,
):
    with Image.open(
        image_path
    ) as image:
        image = (
            image
            .convert("RGB")
        )

    original = image.copy()

    transform = transforms.Compose(
        [
            transforms.Resize(
                (224, 224)
            ),
            transforms.ToTensor(),
            transforms.Normalize(
                IMAGENET_MEAN,
                IMAGENET_STD,
            ),
        ]
    )

    tensor = (
        transform(image)
        .unsqueeze(0)
        .to(device)
    )

    return (
        original,
        tensor,
    )


def obtener_probabilidades(
    model: nn.Module,
    tensor: torch.Tensor,
):
    with torch.no_grad():
        logits = model(
            tensor
        )

        probabilities = (
            torch.softmax(
                logits,
                dim=1,
            )[0]
            .detach()
            .cpu()
            .numpy()
        )

    return probabilities


def crear_heatmap(
    cam: np.ndarray,
) -> np.ndarray:

    cmap = plt.get_cmap(
        "jet"
    )

    heatmap = cmap(
        cam
    )[:, :, :3]

    heatmap = (
        heatmap
        * 255
    ).astype(
        np.uint8
    )

    return heatmap


def crear_superposicion(
    original: Image.Image,
    heatmap: np.ndarray,
    alpha: float = 0.42,
) -> Image.Image:

    original_array = np.asarray(
        original,
        dtype=np.float32,
    )

    heatmap_array = (
        heatmap
        .astype(np.float32)
    )

    overlay = (
        original_array
        * (1.0 - alpha)
        +
        heatmap_array
        * alpha
    )

    overlay = np.clip(
        overlay,
        0,
        255,
    ).astype(
        np.uint8
    )

    return Image.fromarray(
        overlay
    )


def obtener_bounding_box(
    cam: np.ndarray,
    threshold: float = 0.65,
):
    mask = (
        cam >= threshold
    )

    coordinates = np.argwhere(
        mask
    )

    if coordinates.size == 0:
        return None

    y_min = int(
        coordinates[:, 0].min()
    )

    y_max = int(
        coordinates[:, 0].max()
    )

    x_min = int(
        coordinates[:, 1].min()
    )

    x_max = int(
        coordinates[:, 1].max()
    )

    return (
        x_min,
        y_min,
        x_max,
        y_max,
    )


def dibujar_zona_activacion(
    overlay: Image.Image,
    box,
) -> Image.Image:

    result = overlay.copy()

    if box is None:
        return result

    draw = ImageDraw.Draw(
        result
    )

    x_min, y_min, x_max, y_max = box

    line_width = max(
        2,
        int(
            min(result.size)
            * 0.008
        ),
    )

    draw.rectangle(
        [
            x_min,
            y_min,
            x_max,
            y_max,
        ],
        outline=(
            255,
            255,
            0,
        ),
        width=line_width,
    )

    return result


def guardar_panel(
    original: Image.Image,
    heatmap: np.ndarray,
    overlay: Image.Image,
    overlay_box: Image.Image,
    output_path: Path,
    probability: float,
    prediction: str,
):

    figure = plt.figure(
        figsize=(16, 5)
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
        heatmap
    )

    axis2.set_title(
        "Grad-CAM"
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
        overlay
    )

    axis3.set_title(
        "Superposición"
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
        overlay_box
    )

    axis4.set_title(
        "Zona de mayor activación"
    )

    axis4.axis(
        "off"
    )

    figure.suptitle(
        (
            f"Predicción: {prediction} | "
            f"P(osteosarcoma): "
            f"{probability:.4f}"
        ),
        fontsize=13,
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


def procesar_imagen(
    image_path: Path,
    output_root: Path,
    model: nn.Module,
    gradcam: GradCAM,
    threshold: float,
    version: str,
    best_epoch,
    device: torch.device,
):

    (
        original,
        tensor,
    ) = preparar_imagen(
        image_path,
        device,
    )

    probabilities = (
        obtener_probabilidades(
            model,
            tensor,
        )
    )

    probability_no = float(
        probabilities[0]
    )

    probability_yes = float(
        probabilities[1]
    )

    suspicious = (
        probability_yes
        >= threshold
    )

    predicted_class = (
        "osteosarcoma"
        if suspicious
        else "no_osteosarcoma"
    )

    # Grad-CAM dirigido específicamente
    # a la clase osteosarcoma.
    target_class = 1

    cam = gradcam.generate(
        tensor,
        target_class,
        original.size,
    )

    heatmap = crear_heatmap(
        cam
    )

    overlay = crear_superposicion(
        original,
        heatmap,
    )

    box = obtener_bounding_box(
        cam,
        threshold=0.65,
    )

    overlay_box = (
        dibujar_zona_activacion(
            overlay,
            box,
        )
    )

    image_output = (
        output_root
        / image_path.stem
    )

    image_output.mkdir(
        parents=True,
        exist_ok=True,
    )

    original.save(
        image_output
        / "01_original.png"
    )

    Image.fromarray(
        heatmap
    ).save(
        image_output
        / "02_gradcam.png"
    )

    overlay.save(
        image_output
        / "03_superposicion.png"
    )

    overlay_box.save(
        image_output
        / "04_zona_activacion.png"
    )

    guardar_panel(
        original=original,
        heatmap=heatmap,
        overlay=overlay,
        overlay_box=overlay_box,
        output_path=(
            image_output
            / "05_panel_gradcam.png"
        ),
        probability=probability_yes,
        prediction=predicted_class,
    )

    metadata = {
        "image": str(
            image_path
        ),
        "model_version": version,
        "architecture": (
            "efficientnet_b0"
        ),
        "image_size": 224,
        "target_class_gradcam": (
            "osteosarcoma"
        ),
        "target_class_index": (
            target_class
        ),
        "threshold": float(
            threshold
        ),
        "probability_no_osteosarcoma": (
            probability_no
        ),
        "probability_osteosarcoma": (
            probability_yes
        ),
        "prediction": (
            predicted_class
        ),
        "suspicious": bool(
            suspicious
        ),
        "best_epoch": best_epoch,
        "hotspot_box": (
            list(box)
            if box is not None
            else None
        ),
        "hotspot_threshold": (
            0.65
        ),
        "important_note": (
            "La zona resaltada representa "
            "la región de mayor activación "
            "Grad-CAM para la clase "
            "osteosarcoma. No constituye "
            "una segmentación ni una "
            "localización clínica "
            "confirmada de la lesión."
        ),
    }

    (
        image_output
        / "metadata.json"
    ).write_text(
        json.dumps(
            metadata,
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
        f"Imagen: {image_path.name}"
    )

    print(
        f"P(no osteosarcoma): "
        f"{probability_no:.6f}"
    )

    print(
        f"P(osteosarcoma):    "
        f"{probability_yes:.6f}"
    )

    print(
        f"Umbral:              "
        f"{threshold:.6f}"
    )

    print(
        f"Predicción:          "
        f"{predicted_class}"
    )

    print(
        f"Salida:              "
        f"{image_output}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Genera Grad-CAM para el "
            "modelo EfficientNetB0 de "
            "osteosarcoma."
        )
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
            "gradcam_osteosarcoma_v1"
        ),
    )

    parser.add_argument(
        "--image",
        action="append",
        type=Path,
        required=True,
        help=(
            "Ruta de una imagen. "
            "Puede repetirse varias veces."
        ),
    )

    return parser.parse_args()


def main():
    args = parse_args()

    device = torch.device(
        "cuda"
        if torch.cuda.is_available()
        else "cpu"
    )

    print()
    print(
        "=" * 72
    )

    print(
        "GRAD-CAM OSTEOSARCOMA"
    )

    print(
        "=" * 72
    )

    print(
        f"Dispositivo: {device}"
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

    # Último bloque convolucional
    # de EfficientNetB0.
    target_layer = (
        model.features[-1]
    )

    gradcam = GradCAM(
        model,
        target_layer,
    )

    try:
        for image_path in args.image:

            if not image_path.exists():
                print(
                    f"NO EXISTE: "
                    f"{image_path}"
                )
                continue

            procesar_imagen(
                image_path=image_path,
                output_root=args.output,
                model=model,
                gradcam=gradcam,
                threshold=threshold,
                version=version,
                best_epoch=best_epoch,
                device=device,
            )

    finally:
        gradcam.close()

    print()
    print(
        "=" * 72
    )

    print(
        "GRAD-CAM TERMINADO"
    )

    print(
        "=" * 72
    )

    print(
        f"Resultados: "
        f"{args.output}"
    )


if __name__ == "__main__":
    main()
