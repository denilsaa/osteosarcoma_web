from __future__ import annotations

import io
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
import torch

from PIL import Image

from torchvision.models.detection import (
    fasterrcnn_resnet50_fpn,
)

from torchvision.models.detection.faster_rcnn import (
    FastRCNNPredictor,
)

from torchvision.transforms.functional import (
    to_tensor,
)


# ==========================================================
# ERRORES
# ==========================================================


class OsteosarcomaDetectorUnavailable(
    RuntimeError
):
    pass


class OsteosarcomaDetectorImageError(
    ValueError
):
    pass


# ==========================================================
# RESULTADO
# ==========================================================


@dataclass(
    frozen=True
)
class OsteosarcomaLocalizationPrediction:
    detected: bool

    confidence: float

    threshold: float

    x1: Optional[float]
    y1: Optional[float]
    x2: Optional[float]
    y2: Optional[float]

    architecture: str
    version: str


# ==========================================================
# DETECTOR
# ==========================================================


class OsteosarcomaDetector:
    _instance = None

    def __new__(
        cls,
    ):
        if cls._instance is None:
            cls._instance = (
                super().__new__(
                    cls
                )
            )

            cls._instance._initialize()

        return cls._instance


    # ======================================================
    # INICIALIZACIÓN
    # ======================================================

    def _initialize(
        self,
    ):
        model_dir = Path(
            os.environ.get(
                "IA_MODEL_DIR",
                "/app/modelos",
            )
        )

        self.model_path = (
            model_dir
            / (
                "osteosarcoma_detector_"
                "fasterrcnn_v2.pt"
            )
        )

        self.threshold = float(
            os.environ.get(
                "IA_OSTEOSARCOMA_"
                "DETECTOR_THRESHOLD",
                "0.70",
            )
        )

        self.architecture = (
            "fasterrcnn_resnet50_fpn"
        )

        self.version = (
            "osteosarcoma_detector_v2"
        )

        self.device = torch.device(
            "cpu"
        )

        self.model = None

        self.available = False

        self.error = None


        if not self.model_path.exists():
            self.error = (
                "No se encontró el "
                "modelo del detector."
            )

            return


        try:
            checkpoint = torch.load(
                self.model_path,
                map_location=self.device,
                weights_only=False,
            )


            min_size = int(
                checkpoint.get(
                    "min_size",
                    512,
                )
            )

            max_size = int(
                checkpoint.get(
                    "max_size",
                    768,
                )
            )


            model = (
                fasterrcnn_resnet50_fpn(
                    weights=None,
                    weights_backbone=None,
                    min_size=min_size,
                    max_size=max_size,
                )
            )


            in_features = (
                model
                .roi_heads
                .box_predictor
                .cls_score
                .in_features
            )


            model.roi_heads.box_predictor = (
                FastRCNNPredictor(
                    in_features,
                    2,
                )
            )


            state_dict = checkpoint.get(
                "state_dict"
            )

            if state_dict is None:
                raise ValueError(
                    "El checkpoint no contiene "
                    "state_dict."
                )


            model.load_state_dict(
                state_dict
            )


            model.to(
                self.device
            )

            model.eval()


            self.architecture = str(
                checkpoint.get(
                    "architecture",
                    self.architecture,
                )
            )

            self.version = str(
                checkpoint.get(
                    "version",
                    self.version,
                )
            )


            self.model = model

            self.available = True

            self.error = None


        except Exception as exc:
            self.available = False

            self.model = None

            self.error = str(
                exc
            )


    # ======================================================
    # CARGA DE IMAGEN
    # ======================================================

    def _load_image(
        self,
        raw: bytes,
        filename: str,
    ) -> Image.Image:
        extension = (
            filename
            .rsplit(
                ".",
                1,
            )[-1]
            .lower()
            if "." in filename
            else ""
        )


        # ==================================================
        # DICOM
        # ==================================================

        if extension == "dcm":

            try:
                import pydicom

                dataset = (
                    pydicom.dcmread(
                        io.BytesIO(
                            raw
                        )
                    )
                )

                pixels = (
                    dataset
                    .pixel_array
                    .astype(
                        np.float32
                    )
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
                    raise (
                        OsteosarcomaDetectorImageError(
                            "No fue posible "
                            "normalizar la "
                            "imagen DICOM."
                        )
                    )


                pixels = np.clip(
                    pixels,
                    low,
                    high,
                )


                pixels = (
                    (
                        pixels
                        - low
                    )
                    /
                    (
                        high
                        - low
                    )
                    * 255.0
                ).astype(
                    np.uint8
                )


                image = (
                    Image
                    .fromarray(
                        pixels
                    )
                    .convert(
                        "RGB"
                    )
                )


                return image


            except (
                OsteosarcomaDetectorImageError
            ):
                raise


            except Exception as exc:
                raise (
                    OsteosarcomaDetectorImageError(
                        "No fue posible procesar "
                        "la imagen DICOM."
                    )
                ) from exc


        # ==================================================
        # JPG / PNG
        # ==================================================

        try:
            return (
                Image
                .open(
                    io.BytesIO(
                        raw
                    )
                )
                .convert(
                    "RGB"
                )
            )

        except Exception as exc:
            raise (
                OsteosarcomaDetectorImageError(
                    "No fue posible procesar "
                    "la imagen."
                )
            ) from exc


    # ======================================================
    # PREDICCIÓN
    # ======================================================

    def predict(
        self,
        raw: bytes,
        filename: str,
    ) -> OsteosarcomaLocalizationPrediction:

        if (
            not self.available
            or self.model is None
        ):
            raise (
                OsteosarcomaDetectorUnavailable(
                    "El modelo de localización "
                    "de osteosarcoma no está "
                    "disponible."
                )
            )


        image = self._load_image(
            raw,
            filename,
        )


        width, height = (
            image.size
        )


        tensor = (
            to_tensor(
                image
            )
            .to(
                self.device
            )
        )


        try:
            with torch.inference_mode():

                outputs = (
                    self.model(
                        [
                            tensor
                        ]
                    )
                )


            output = outputs[0]


        except Exception as exc:
            raise (
                OsteosarcomaDetectorUnavailable(
                    "No fue posible ejecutar "
                    "el modelo de localización."
                )
            ) from exc


        boxes = (
            output[
                "boxes"
            ]
            .detach()
            .cpu()
        )


        scores = (
            output[
                "scores"
            ]
            .detach()
            .cpu()
        )


        labels = (
            output[
                "labels"
            ]
            .detach()
            .cpu()
        )


        # ==================================================
        # BUSCAR MEJOR DETECCIÓN DE OSTEOSARCOMA
        # ==================================================

        candidate_indices = [
            index
            for index, label
            in enumerate(
                labels.tolist()
            )
            if int(
                label
            ) == 1
        ]


        if not candidate_indices:
            return (
                OsteosarcomaLocalizationPrediction(
                    detected=False,
                    confidence=0.0,
                    threshold=(
                        self.threshold
                    ),
                    x1=None,
                    y1=None,
                    x2=None,
                    y2=None,
                    architecture=(
                        self.architecture
                    ),
                    version=(
                        self.version
                    ),
                )
            )


        best_index = max(
            candidate_indices,
            key=lambda index: float(
                scores[
                    index
                ].item()
            ),
        )


        confidence = float(
            scores[
                best_index
            ].item()
        )


        # ==================================================
        # UMBRAL DEFINIDO CON VALIDATION
        # ==================================================

        if confidence < self.threshold:
            return (
                OsteosarcomaLocalizationPrediction(
                    detected=False,
                    confidence=confidence,
                    threshold=(
                        self.threshold
                    ),
                    x1=None,
                    y1=None,
                    x2=None,
                    y2=None,
                    architecture=(
                        self.architecture
                    ),
                    version=(
                        self.version
                    ),
                )
            )


        box = (
            boxes[
                best_index
            ]
            .numpy()
        )


        x1 = float(
            box[0]
        )

        y1 = float(
            box[1]
        )

        x2 = float(
            box[2]
        )

        y2 = float(
            box[3]
        )


        # ==================================================
        # LIMITAR A DIMENSIONES DE LA IMAGEN
        # ==================================================

        x1 = max(
            0.0,
            min(
                x1,
                float(
                    width
                ),
            ),
        )

        y1 = max(
            0.0,
            min(
                y1,
                float(
                    height
                ),
            ),
        )

        x2 = max(
            x1,
            min(
                x2,
                float(
                    width
                ),
            ),
        )

        y2 = max(
            y1,
            min(
                y2,
                float(
                    height
                ),
            ),
        )


        # ==================================================
        # COORDENADAS NORMALIZADAS 0..1
        #
        # Esto permite que React dibuje la caja sobre
        # cualquier tamaño de visualización.
        # ==================================================

        x1_normalized = (
            x1
            /
            max(
                width,
                1,
            )
        )

        y1_normalized = (
            y1
            /
            max(
                height,
                1,
            )
        )

        x2_normalized = (
            x2
            /
            max(
                width,
                1,
            )
        )

        y2_normalized = (
            y2
            /
            max(
                height,
                1,
            )
        )


        return (
            OsteosarcomaLocalizationPrediction(
                detected=True,
                confidence=confidence,
                threshold=(
                    self.threshold
                ),
                x1=(
                    x1_normalized
                ),
                y1=(
                    y1_normalized
                ),
                x2=(
                    x2_normalized
                ),
                y2=(
                    y2_normalized
                ),
                architecture=(
                    self.architecture
                ),
                version=(
                    self.version
                ),
            )
        )
