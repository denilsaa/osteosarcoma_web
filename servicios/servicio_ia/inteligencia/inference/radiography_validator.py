from __future__ import annotations

import io
import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from threading import Lock

import numpy as np
import onnxruntime as ort
import pydicom
from PIL import Image, ImageOps, UnidentifiedImageError


IMAGENET_MEAN = np.array(
    [0.485, 0.456, 0.406],
    dtype=np.float32,
)
IMAGENET_STD = np.array(
    [0.229, 0.224, 0.225],
    dtype=np.float32,
)


class RadiographyModelUnavailable(RuntimeError):
    pass


class RadiographyImageError(ValueError):
    pass


@dataclass(frozen=True)
class RadiographyPrediction:
    is_radiography: bool
    confidence: float
    radiography_probability: float
    non_radiography_probability: float
    threshold: float
    architecture: str


class RadiographyValidator:
    _instance: "RadiographyValidator | None" = None
    _lock = Lock()

    def __new__(cls) -> "RadiographyValidator":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False

        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        base_dir = Path(__file__).resolve().parents[2]

        # ==========================================================
        # RADIOGRAPHY VALIDATOR V3
        # ==========================================================
        #
        # Se conserva V1 físicamente en /modelos como respaldo.
        # El servicio utiliza V3 por defecto.
        #
        default_model = (
            base_dir
            / "modelos"
            / "radiography_validator_efficientnet_b0_v3.onnx"
        )

        default_metadata = (
            base_dir
            / "modelos"
            / "radiography_validator_efficientnet_b0_v3.json"
        )

        self.model_path = Path(
            os.environ.get(
                "RADIOGRAPHY_VALIDATOR_MODEL_PATH",
                str(default_model),
            )
        )

        self.metadata_path = Path(
            os.environ.get(
                "RADIOGRAPHY_VALIDATOR_METADATA_PATH",
                str(default_metadata),
            )
        )

        self._session: ort.InferenceSession | None = None
        self._metadata: dict | None = None

        self._initialized = True

    @property
    def available(self) -> bool:
        return (
            self.model_path.is_file()
            and self.metadata_path.is_file()
        )

    def _load(self) -> None:
        if (
            self._session is not None
            and self._metadata is not None
        ):
            return

        if not self.available:
            raise RadiographyModelUnavailable(
                "El modelo EfficientNet V2 de validación "
                "radiográfica no está disponible."
            )

        try:
            metadata = json.loads(
                self.metadata_path.read_text(
                    encoding="utf-8"
                )
            )
        except Exception as exc:
            raise RadiographyModelUnavailable(
                "No fue posible leer los metadatos "
                "del modelo EfficientNet V2."
            ) from exc

        classes = metadata.get("classes")

        if classes != [
            "no_radiografia",
            "radiografia",
        ]:
            raise RadiographyModelUnavailable(
                "Las clases configuradas para el modelo "
                "EfficientNet V2 no son válidas."
            )

        try:
            session = ort.InferenceSession(
                str(self.model_path),
                providers=[
                    "CPUExecutionProvider",
                ],
            )
        except Exception as exc:
            raise RadiographyModelUnavailable(
                "No fue posible inicializar el modelo "
                "EfficientNet V2."
            ) from exc

        self._session = session
        self._metadata = metadata

    @staticmethod
    def _prepare_regular_image(
        raw: bytes,
    ) -> Image.Image:
        try:
            with Image.open(io.BytesIO(raw)) as image:
                image.load()

                return (
                    ImageOps
                    .exif_transpose(image)
                    .convert("RGB")
                )

        except (
            UnidentifiedImageError,
            OSError,
            ValueError,
        ) as exc:
            raise RadiographyImageError(
                "El archivo no contiene una imagen "
                "JPG o PNG interpretable."
            ) from exc

    @staticmethod
    def _dicom_to_image(
        raw: bytes,
    ) -> Image.Image:
        try:
            dataset = pydicom.dcmread(
                io.BytesIO(raw),
                force=False,
            )

        except Exception as exc:
            raise RadiographyImageError(
                "El archivo DICOM no pudo ser interpretado."
            ) from exc

        modality = str(
            getattr(
                dataset,
                "Modality",
                "",
            )
        ).strip().upper()

        allowed_modalities = {
            "DX",
            "CR",
            "DR",
            "RG",
        }

        if (
            modality
            and modality not in allowed_modalities
        ):
            raise RadiographyImageError(
                f"El DICOM corresponde a la modalidad "
                f"{modality}, no a una radiografía "
                f"convencional."
            )

        try:
            pixels = (
                dataset
                .pixel_array
                .astype(np.float32)
            )

        except Exception as exc:
            raise RadiographyImageError(
                "El DICOM no contiene píxeles "
                "radiográficos compatibles con "
                "el visor de validación."
            ) from exc

        while pixels.ndim > 2:
            pixels = pixels[0]

        if pixels.size == 0:
            raise RadiographyImageError(
                "El DICOM no contiene datos de imagen."
            )

        finite = np.isfinite(pixels)

        if not finite.any():
            raise RadiographyImageError(
                "El DICOM contiene valores de "
                "imagen no válidos."
            )

        valid_pixels = pixels[finite]

        low = float(
            np.percentile(
                valid_pixels,
                1.0,
            )
        )

        high = float(
            np.percentile(
                valid_pixels,
                99.0,
            )
        )

        if (
            not math.isfinite(low)
            or not math.isfinite(high)
            or high <= low
        ):
            low = float(
                valid_pixels.min()
            )
            high = float(
                valid_pixels.max()
            )

        if high <= low:
            raise RadiographyImageError(
                "El DICOM no contiene suficiente "
                "información visual."
            )

        pixels = np.clip(
            (pixels - low)
            / (high - low),
            0.0,
            1.0,
        )

        photometric = str(
            getattr(
                dataset,
                "PhotometricInterpretation",
                "",
            )
        ).strip().upper()

        if photometric == "MONOCHROME1":
            pixels = 1.0 - pixels

        image_u8 = (
            pixels * 255.0
        ).astype(np.uint8)

        return (
            Image
            .fromarray(
                image_u8,
                mode="L",
            )
            .convert("RGB")
        )

    @staticmethod
    def _preprocess(
        image: Image.Image,
        image_size: int,
    ) -> np.ndarray:
        resized = image.resize(
            (
                image_size,
                image_size,
            ),
            Image.Resampling.BILINEAR,
        )

        array = (
            np.asarray(
                resized,
                dtype=np.float32,
            )
            / 255.0
        )

        array = (
            array - IMAGENET_MEAN
        ) / IMAGENET_STD

        array = np.transpose(
            array,
            (
                2,
                0,
                1,
            ),
        )

        return np.expand_dims(
            array,
            axis=0,
        ).astype(np.float32)

    @staticmethod
    def _softmax(
        logits: np.ndarray,
    ) -> np.ndarray:
        logits = logits.astype(
            np.float64
        )

        logits = (
            logits
            - np.max(
                logits,
                axis=-1,
                keepdims=True,
            )
        )

        exp = np.exp(logits)

        return (
            exp
            / np.sum(
                exp,
                axis=-1,
                keepdims=True,
            )
        )

    def predict(
        self,
        raw: bytes,
        filename: str,
    ) -> RadiographyPrediction:
        self._load()

        assert self._session is not None
        assert self._metadata is not None

        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        if extension == ".dcm":
            image = self._dicom_to_image(
                raw
            )
        else:
            image = (
                self
                ._prepare_regular_image(
                    raw
                )
            )

        image_size = int(
            self._metadata.get(
                "image_size",
                224,
            )
        )

        # IMPORTANTE:
        # El umbral se obtiene del metadata V3.
        # No se fuerza manualmente 0.09 aquí.
        threshold = float(
            self._metadata.get(
                "threshold",
                0.50,
            )
        )

        architecture = str(
            self._metadata.get(
                "architecture",
                "efficientnet_b0",
            )
        )

        tensor = self._preprocess(
            image,
            image_size,
        )

        input_name = (
            self
            ._session
            .get_inputs()[0]
            .name
        )

        output = self._session.run(
            None,
            {
                input_name: tensor,
            },
        )[0]

        probabilities = (
            self
            ._softmax(output)[0]
        )

        if len(probabilities) != 2:
            raise RadiographyModelUnavailable(
                "La salida del modelo EfficientNet V2 "
                "no contiene las dos clases esperadas."
            )

        non_xray = float(
            probabilities[0]
        )

        xray = float(
            probabilities[1]
        )

        is_xray = (
            xray >= threshold
        )

        confidence = (
            xray
            if is_xray
            else non_xray
        )

        return RadiographyPrediction(
            is_radiography=is_xray,
            confidence=confidence,
            radiography_probability=xray,
            non_radiography_probability=non_xray,
            threshold=threshold,
            architecture=architecture,
        )
