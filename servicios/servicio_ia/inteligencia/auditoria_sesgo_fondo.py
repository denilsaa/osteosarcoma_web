"""Pruebas exploratorias, NO diagnósticas, de sensibilidad a perturbaciones de una radiografía.

No altera el modelo, la radiografía ni los resultados de la clínica. Las variantes
son deliberadamente artificiales: una diferencia de probabilidad NO demuestra
por sí sola sesgo de fondo ni localización correcta de enfermedad.
"""
from __future__ import annotations

import hashlib
import io
import math
from dataclasses import dataclass

import numpy as np
from PIL import Image

MAX_FILE_BYTES = 20 * 1024 * 1024
MAX_PIXELS = 35_000_000
SUPPORTED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tif', 'tiff', 'dcm'}


@dataclass(frozen=True)
class AuditImage:
    pixels: Image.Image
    digest: str
    original_bytes: bytes
    extension: str


def decode_original(raw: bytes, filename: str) -> AuditImage:
    """Iguala la decodificación clínica antes del resize a 224x224.

    DICOM: utiliza exactamente la ventana percentil 1/99 del validador V1,
    que debe ser auditada aparte por un especialista en imágenes médicas.
    """
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_FILE_BYTES:
        raise ValueError('TAMANO_ARCHIVO_INVALIDO')
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError('FORMATO_NO_ADMITIDO')
    if extension == 'dcm':
        try:
            import pydicom
            dataset = pydicom.dcmread(io.BytesIO(raw))
            pixels = dataset.pixel_array.astype(np.float32)
            if pixels.ndim != 2 or pixels.size > MAX_PIXELS:
                raise ValueError('DICOM_DIMENSIONES_INVALIDAS')
            low, high = np.percentile(pixels, [1, 99])
            if not np.isfinite([low, high]).all() or high <= low:
                raise ValueError('DICOM_RANGO_INVALIDO')
            pixels = (np.clip(pixels, low, high) - low) / (high - low) * 255
            image = Image.fromarray(pixels.astype(np.uint8)).convert('RGB')
        except ImportError as exc:
            raise ValueError('PYDICOM_NO_DISPONIBLE') from exc
    else:
        try:
            with Image.open(io.BytesIO(raw)) as opened:
                if opened.width * opened.height > MAX_PIXELS:
                    raise ValueError('IMAGEN_DEMASIADO_GRANDE')
                image = opened.convert('RGB')
        except (OSError, SyntaxError) as exc:
            raise ValueError('IMAGEN_ILEGIBLE') from exc
    if image.width < 32 or image.height < 32:
        raise ValueError('IMAGEN_DEMASIADO_PEQUENA')
    return AuditImage(image, hashlib.sha256(raw).hexdigest(), raw, extension)


def png_bytes(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    image.save(stream, format='PNG')
    return stream.getvalue()


def _fill_stripes(image: Image.Image, fractions: tuple[float, float]) -> Image.Image:
    """Perturbación controlada de márgenes laterales con gris constante.

    NO constituye una máscara de hueso y NO pretende eliminar solo el fondo.
    """
    left, right = fractions
    if not (0 <= left <= .4 and 0 <= right <= .4):
        raise ValueError('FRANJA_INVALIDA')
    canvas = image.copy()
    width, height = image.size
    from PIL import ImageDraw
    painter = ImageDraw.Draw(canvas)
    left_pixels = round(width * left)
    right_pixels = round(width * right)
    if left_pixels:
        painter.rectangle((0, 0, left_pixels - 1, height - 1), fill=(127, 127, 127))
    if right_pixels:
        painter.rectangle((width - right_pixels, 0, width - 1, height - 1), fill=(127, 127, 127))
    return canvas


def _fill_center(image: Image.Image, fraction: float = .15) -> Image.Image:
    """Control positivo anatómico aproximado: puede incluir tejido y no es una ROI experta."""
    canvas = image.copy()
    width, height = image.size
    start = round(width * (1 - fraction) / 2)
    end = round(width * (1 + fraction) / 2)
    from PIL import ImageDraw
    ImageDraw.Draw(canvas).rectangle((start, 0, end - 1, height - 1), fill=(127, 127, 127))
    return canvas


def validate_roi(roi) -> tuple[float, float, float, float]:
    try:
        values = tuple(float(v) for v in roi)
    except (ValueError, TypeError) as exc:
        raise ValueError('ROI_INVALIDA') from exc
    if len(values) != 4 or not all(math.isfinite(v) for v in values):
        raise ValueError('ROI_INVALIDA')
    x1, y1, x2, y2 = values
    if not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise ValueError('ROI_INVALIDA')
    return values


def _fill_roi(image: Image.Image, roi) -> Image.Image:
    x1, y1, x2, y2 = validate_roi(roi)
    canvas = image.copy()
    width, height = canvas.size
    from PIL import ImageDraw
    ImageDraw.Draw(canvas).rectangle(
        (round(x1 * width), round(y1 * height), round(x2 * width) - 1, round(y2 * height) - 1),
        fill=(127, 127, 127),
    )
    return canvas


def build_variants(image: Image.Image, roi=None):
    """Retorna imágenes en memoria, sin modificar el original ni guardarlas a disco."""
    result = [
        ('izquierda_15pct', _fill_stripes(image, (.15, 0))),
        ('derecha_15pct', _fill_stripes(image, (0, .15))),
        ('ambos_margenes_15pct', _fill_stripes(image, (.15, .15))),
        ('ambos_margenes_25pct', _fill_stripes(image, (.25, .25))),
        ('control_central_15pct', _fill_center(image)),
    ]
    if roi is not None:
        result.append(('roi_anotada_ocluida', _fill_roi(image, roi)))
    return result


def audit_predictions(image_data: AuditImage, predictor, roi=None):
    """Usa predictor.predict(...) de la versión clínica activa, sin cambiar su umbral.

    Compara primero el archivo original con su decodificación convertida a PNG:
    deben dar la misma predicción. Este control detecta inconsistencias del
    procesamiento (en particular DICOM) antes de aceptar las comparaciones.
    """
    if roi is not None:
        roi = validate_roi(roi)
    baseline = predictor.predict(image_data.original_bytes, 'original.' + image_data.extension)
    equivalent = predictor.predict(png_bytes(image_data.pixels), 'control.png')
    p0, p_equiv = float(baseline.osteosarcoma_probability), float(equivalent.osteosarcoma_probability)
    if not all(math.isfinite(p) and 0 <= p <= 1 for p in (p0, p_equiv)):
        raise ValueError('PREDICCION_NO_VALIDA')
    if abs(p0 - p_equiv) > 0.001:
        raise ValueError('PREPROCESAMIENTO_NO_EQUIVALENTE')
    results = []
    for label, altered in build_variants(image_data.pixels, roi):
        pred = predictor.predict(png_bytes(altered), label + '.png')
        p = float(pred.osteosarcoma_probability)
        if not math.isfinite(p) or not 0 <= p <= 1:
            raise ValueError('PREDICCION_NO_VALIDA')
        results.append({
            'prueba': label,
            'probabilidad_osteosarcoma': round(p, 6),
            'variacion_puntos_porcentuales': round(100 * (p - p0), 3),
            'cambio_clase_umbral': bool((p >= predictor.threshold) != (p0 >= predictor.threshold)),
        })
    return {
        'tipo': 'AUDITORIA_EXPLORATORIA_NO_CLINICA',
        'sha256_imagen_original': image_data.digest,
        'dimensiones_originales': [image_data.pixels.width, image_data.pixels.height],
        'version_modelo': str(predictor.version),
        'umbral': float(predictor.threshold),
        'probabilidad_original': round(p0, 6),
        'diferencia_control_decodificacion_pp': round(100 * abs(p_equiv - p0), 5),
        'variantes': results,
        'limitaciones': (
            'Las franjas modifican píxeles de forma artificial y pueden incluir anatomía. '
            'Diferencias no prueban causalidad, sesgo ni delimitación de un tumor. '
            'No utilizar para decisiones clínicas ni ajustar umbrales con este caso.'
        ),
    }
