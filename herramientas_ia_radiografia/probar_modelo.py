from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image


MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


def preprocess(image_path: Path, image_size: int) -> np.ndarray:
    with Image.open(image_path) as image:
        image = image.convert("RGB")
        image = image.resize((image_size, image_size), Image.Resampling.BILINEAR)
        array = np.asarray(image, dtype=np.float32) / 255.0

    array = (array - MEAN) / STD
    array = np.transpose(array, (2, 0, 1))
    return np.expand_dims(array, axis=0).astype(np.float32)


def softmax(values: np.ndarray) -> np.ndarray:
    values = values.astype(np.float64)
    values -= np.max(values, axis=-1, keepdims=True)
    exp = np.exp(values)
    return exp / exp.sum(axis=-1, keepdims=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument(
        "--model",
        type=Path,
        default=Path("radiography_validator_efficientnet_b0.onnx"),
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("radiography_validator_efficientnet_b0.json"),
    )
    args = parser.parse_args()

    metadata = json.loads(args.metadata.read_text(encoding="utf-8"))
    session = ort.InferenceSession(
        str(args.model),
        providers=["CPUExecutionProvider"],
    )

    x = preprocess(args.image, int(metadata["image_size"]))
    input_name = session.get_inputs()[0].name
    logits = session.run(None, {input_name: x})[0]
    probabilities = softmax(logits)[0]

    p_non_xray = float(probabilities[0])
    p_xray = float(probabilities[1])
    threshold = float(metadata["threshold"])
    is_xray = p_xray >= threshold

    print(f"familia={metadata.get('family', 'EfficientNet')}")
    print(f"arquitectura={metadata['architecture']}")
    print(f"es_radiografia={str(is_xray).lower()}")
    print(f"probabilidad_radiografia={p_xray:.4f}")
    print(f"probabilidad_no_radiografia={p_non_xray:.4f}")
    print(f"umbral={threshold:.2f}")


if __name__ == "__main__":
    main()
