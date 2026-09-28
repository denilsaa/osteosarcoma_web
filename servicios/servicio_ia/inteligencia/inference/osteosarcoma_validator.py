from __future__ import annotations

import io
import json
import os
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image


class OsteosarcomaModelUnavailable(RuntimeError):
    pass


class OsteosarcomaImageError(ValueError):
    pass


@dataclass(frozen=True)
class OsteosarcomaPrediction:
    is_suspicious: bool
    confidence: float
    osteosarcoma_probability: float
    non_osteosarcoma_probability: float
    threshold: float
    architecture: str
    version: str


class OsteosarcomaValidator:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        model_dir = Path(
            os.environ.get(
                "IA_MODEL_DIR",
                "/app/modelos",
            )
        )

        self.model_path = model_dir / (
            "osteosarcoma_efficientnet_b0_finetuned_v1.onnx"
        )

        self.metadata_path = model_dir / (
            "osteosarcoma_efficientnet_b0_finetuned_v1.json"
        )

        self.available = False
        self.session = None

        self.threshold = 0.06
        self.architecture = "efficientnet_b0"
        self.version = "osteosarcoma_finetuned_v1"

        if (
            not self.model_path.exists()
            or not self.metadata_path.exists()
        ):
            return

        try:
            metadata = json.loads(
                self.metadata_path.read_text(
                    encoding="utf-8"
                )
            )

            self.threshold = float(
                metadata.get(
                    "threshold",
                    self.threshold,
                )
            )

            self.architecture = str(
                metadata.get(
                    "architecture",
                    self.architecture,
                )
            )

            self.version = str(
                metadata.get(
                    "version",
                    self.version,
                )
            )

            self.session = ort.InferenceSession(
                str(self.model_path),
                providers=[
                    "CPUExecutionProvider"
                ],
            )

            self.input_name = (
                self.session
                .get_inputs()[0]
                .name
            )

            self.available = True

        except Exception:
            self.available = False
            self.session = None

    def _preprocess(
        self,
        raw: bytes,
        filename: str,
    ) -> np.ndarray:
        extension = (
            filename.rsplit(".", 1)[-1].lower()
            if "." in filename
            else ""
        )

        if extension == "dcm":
            try:
                import pydicom

                dataset = pydicom.dcmread(
                    io.BytesIO(raw)
                )

                pixels = (
                    dataset.pixel_array
                    .astype(np.float32)
                )

                low = np.percentile(
                    pixels,
                    1,
                )
                high = np.percentile(
                    pixels,
                    99,
                )

                if high <= low:
                    raise OsteosarcomaImageError(
                        "No fue posible normalizar "
                        "la imagen DICOM."
                    )

                pixels = np.clip(
                    pixels,
                    low,
                    high,
                )

                pixels = (
                    (pixels - low)
                    / (high - low)
                    * 255.0
                ).astype(np.uint8)

                image = Image.fromarray(
                    pixels
                ).convert("RGB")

            except OsteosarcomaImageError:
                raise

            except Exception as exc:
                raise OsteosarcomaImageError(
                    "No fue posible procesar "
                    "la imagen DICOM."
                ) from exc

        else:
            try:
                image = Image.open(
                    io.BytesIO(raw)
                ).convert("RGB")

            except Exception as exc:
                raise OsteosarcomaImageError(
                    "No fue posible procesar "
                    "la imagen."
                ) from exc

        image = image.resize(
            (224, 224),
            Image.Resampling.BILINEAR,
        )

        array = (
            np.asarray(
                image,
                dtype=np.float32,
            )
            / 255.0
        )

        mean = np.array(
            [0.485, 0.456, 0.406],
            dtype=np.float32,
        )

        std = np.array(
            [0.229, 0.224, 0.225],
            dtype=np.float32,
        )

        array = (
            array - mean
        ) / std

        array = np.transpose(
            array,
            (2, 0, 1),
        )

        array = np.expand_dims(
            array,
            axis=0,
        )

        return array.astype(
            np.float32
        )

    def predict(
        self,
        raw: bytes,
        filename: str,
    ) -> OsteosarcomaPrediction:
        if (
            not self.available
            or self.session is None
        ):
            raise OsteosarcomaModelUnavailable(
                "El modelo de análisis de "
                "osteosarcoma no está disponible."
            )

        tensor = self._preprocess(
            raw,
            filename,
        )

        outputs = self.session.run(
            None,
            {
                self.input_name: tensor
            },
        )

        logits = np.asarray(
            outputs[0][0],
            dtype=np.float64,
        )

        logits = logits - np.max(
            logits
        )

        exp = np.exp(logits)

        probabilities = (
            exp / np.sum(exp)
        )

        non_probability = float(
            probabilities[0]
        )

        osteosarcoma_probability = float(
            probabilities[1]
        )

        is_suspicious = (
            osteosarcoma_probability
            >= self.threshold
        )

        confidence = (
            osteosarcoma_probability
            if is_suspicious
            else non_probability
        )

        return OsteosarcomaPrediction(
            is_suspicious=is_suspicious,
            confidence=confidence,
            osteosarcoma_probability=(
                osteosarcoma_probability
            ),
            non_osteosarcoma_probability=(
                non_probability
            ),
            threshold=self.threshold,
            architecture=self.architecture,
            version=self.version,
        )
