"""Grad-CAM privado para el modelo clínico V1. No hace predicciones nuevas para el caso.

Solo se publica si checkpoint PyTorch y ONNX dan probabilidades equivalentes
sobre EXACTAMENTE la entrada normalizada que evaluó el modelo clínico.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import numpy as np
from django.conf import settings
from PIL import Image

from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator

MODEL_PT_FILENAME = 'osteosarcoma_efficientnet_b0_finetuned_v1.pt'
MAX_PROBABILITY_DIFFERENCE = 0.015

# Indicadores exploratorios, NO pruebas de localización ni métricas clínicas.
BORDER_FRACTION = 0.15


def _validar_roi(coordenadas):
    """ROI normalizada; nunca adivinar una caja si el detector no la produjo."""
    if not isinstance(coordenadas, dict):
        raise ValueError('ROI_NO_DISPONIBLE')
    try:
        valores = [float(coordenadas[k]) for k in ('x1', 'y1', 'x2', 'y2')]
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError('ROI_INVALIDA') from exc
    x1, y1, x2, y2 = valores
    if not np.isfinite(valores).all() or not (0 <= x1 < x2 <= 1 and 0 <= y1 < y2 <= 1):
        raise ValueError('ROI_INVALIDA')
    return x1, y1, x2, y2


def ampliar_cam_para_auditoria(cam):
    """Interpola a la entrada 224px para medir ROI pequeñas. NO crea detalle espacial."""
    heat = np.asarray(cam, dtype=np.float32)
    if heat.ndim != 2 or not np.isfinite(heat).all() or np.any(heat < 0) or np.any(heat > 1):
        raise ValueError('CAM_INVALIDA')
    # float32 en PIL evita cuantizar artificialmente antes de la evaluación.
    return np.asarray(
        Image.fromarray(heat, mode='F').resize((224, 224), Image.Resampling.BILINEAR),
        dtype=np.float32,
    ).clip(0, 1)


def medir_atencion(cam, coordenadas=None):
    """Audita atención relativa al ROI, sin desplazar, recortar ni enmascarar Grad-CAM.

    La región debe venir de un detector independiente o anotación médica.
    No equivale a precisión diagnóstica ni delimitación tumoral.
    """
    heat = np.asarray(cam, dtype=np.float64)
    if heat.ndim != 2 or min(heat.shape) < 2 or not np.isfinite(heat).all():
        raise ValueError('CAM_INVALIDA')
    if np.any(heat < 0) or np.any(heat > 1):
        raise ValueError('CAM_INVALIDA')
    h, w = heat.shape
    total = heat.sum()
    if total <= 1e-12:
        raise ValueError('CAM_SIN_SENAL')
    borde_y = (np.arange(h) + 0.5) / h
    borde_x = (np.arange(w) + 0.5) / w
    mask_border = ((borde_y[:, None] < BORDER_FRACTION) |
                   (borde_y[:, None] > 1 - BORDER_FRACTION) |
                   (borde_x[None, :] < BORDER_FRACTION) |
                   (borde_x[None, :] > 1 - BORDER_FRACTION))
    result = {
        'version': 1,
        'fraccion_activacion_bordes': round(float(heat[mask_border].sum() / total), 4),
        'region_referencia': 'SIN_REFERENCIA',
        'coincidencia_exploratoria': 'NO_EVALUABLE',
    }
    if coordenadas is None:
        return result
    x1, y1, x2, y2 = _validar_roi(coordenadas)
    mask = ((borde_x[None, :] >= x1) & (borde_x[None, :] < x2) &
            (borde_y[:, None] >= y1) & (borde_y[:, None] < y2))
    area_fraction = float(mask.mean())
    if not mask.any() or area_fraction <= 0:
        raise ValueError('ROI_SIN_PIXELES')
    heat_fraction = float(heat[mask].sum() / total)
    max_position = np.unravel_index(int(heat.argmax()), heat.shape)
    hit = bool(mask[max_position])
    # Una señal distribuida uniformemente arroja densidad relativa ~1.
    relative = heat_fraction / area_fraction
    discordance = (not hit and relative < 0.8)
    result.update({
        'region_referencia': 'DETECTOR_O_ANOTACION',
        'fraccion_activacion_en_region': round(heat_fraction, 4),
        'fraccion_area_region': round(area_fraction, 4),
        'densidad_relativa_en_region': round(relative, 4),
        'maximo_en_region': hit,
        'coincidencia_exploratoria': (
            'REVISAR_DISCREPANCIA' if discordance else 'SIN_DISCREPANCIA_GROSERA'
        ),
    })
    return result


def camino_mapa_bruto(task_id):
    image_path, _ = artefact_paths(task_id)
    return image_path.with_suffix('.cam.png')


def artefact_paths(task_id):
    # task_id llega como UUID validado; no aceptar rutas manipuladas.
    from uuid import UUID
    identifier = str(UUID(str(task_id)))
    folder = Path(settings.MEDIA_ROOT) / 'gradcam_ia'
    return folder / f'{identifier}.png', folder / f'{identifier}.json'


def _sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def _softmax(logits):
    logits = np.asarray(logits, dtype=np.float64)
    logits -= logits.max()
    exp = np.exp(logits)
    return exp / exp.sum()


def verificar_equivalencia(prob_onnx, prob_pt, umbral, max_diff=MAX_PROBABILITY_DIFFERENCE):
    a, b = float(prob_onnx), float(prob_pt)
    return (
        np.isfinite([a, b]).all()
        and 0 <= a <= 1 and 0 <= b <= 1
        and abs(a - b) <= max_diff
        and (a >= umbral) == (b >= umbral)
    )


def _load_checkpoint(path):
    import torch
    from torch import nn
    from torchvision.models import efficientnet_b0
    # Nunca ejecutar objetos Python arbitrarios del checkpoint.
    checkpoint = torch.load(path, map_location='cpu', weights_only=True)
    if not isinstance(checkpoint, dict) or not isinstance(checkpoint.get('state_dict'), dict):
        raise ValueError('CHECKPOINT_FORMAT_INVALID')
    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, 2)
    model.load_state_dict(checkpoint['state_dict'], strict=True)
    model.eval()
    return model, checkpoint


def _write_status(task_id, data):
    image_path, metadata_path = artefact_paths(task_id)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = metadata_path.with_suffix('.json.tmp')
    temp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temp_path, metadata_path)
    return image_path


def consultar_estado(task_id):
    image_path, metadata_path = artefact_paths(task_id)
    if not metadata_path.exists():
        return {'estado': 'NO_DISPONIBLE'}
    try:
        data = json.loads(metadata_path.read_text(encoding='utf-8'))
        estado = data.get('estado', 'NO_DISPONIBLE')
        if estado == 'DISPONIBLE' and not image_path.is_file():
            return {'estado': 'NO_DISPONIBLE'}
        resultado = {'estado': estado, 'detalle': data.get('detalle', '')}
        if estado == 'DISPONIBLE' and isinstance(data.get('revision_espacial'), dict):
            resultado['revision_espacial'] = data['revision_espacial']
        return resultado
    except (OSError, ValueError):
        return {'estado': 'NO_DISPONIBLE'}


# Limitar tamaño para no consumir memoria excesiva en el worker.
# El modelo sigue procesando 224x224; esto solo mejora la presentación.
MAX_PRESENTATION_SIDE = 1200


def _reference_image(original_bytes, filename):
    """Recupera la geometría de la radiografía, sin recortes ni giros inventados.

    Se usa la misma normalización DICOM que el validador. El mapa CAM se
    redimensiona a esta geometría; jamás se reubican los máximos hacia el hueso.
    """
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension == 'dcm':
        import pydicom
        dicom = pydicom.dcmread(io.BytesIO(original_bytes))
        pixels = dicom.pixel_array.astype(np.float32)
        low = np.percentile(pixels, 1)
        high = np.percentile(pixels, 99)
        if high <= low:
            raise ValueError('DICOM_IMAGE_RANGE_INVALID')
        pixels = np.clip(pixels, low, high)
        pixels = ((pixels - low) / (high - low) * 255).astype(np.uint8)
        base = Image.fromarray(pixels).convert('RGB')
    else:
        with Image.open(io.BytesIO(original_bytes)) as uploaded:
            base = uploaded.convert('RGB')

    if not base.width or not base.height:
        raise ValueError('INVALID_IMAGE_DIMENSIONS')
    # thumbnail conserva la relación de aspecto y no aumenta el tamaño de origen.
    base.thumbnail((MAX_PRESENTATION_SIDE, MAX_PRESENTATION_SIDE), Image.Resampling.LANCZOS)
    return base


def crear_superposicion_proporcional(original_bytes, filename, cam_normalizada):
    """Devuelve el PNG con la relación de aspecto de la imagen radiográfica.

    La activación pertenece a una cuadrícula gruesa de EfficientNet; interpolar
    no aporta precisión clínica ni permite delimitar lesiones.
    """
    base = _reference_image(original_bytes, filename)
    cam = np.asarray(cam_normalizada, dtype=np.float32)
    if cam.ndim != 2 or not np.isfinite(cam).all() or not (0 <= cam).all() or not (cam <= 1).all():
        raise ValueError('GRADCAM_ARRAY_INVALID')
    heat = np.asarray(
        Image.fromarray(np.uint8(np.round(cam * 255)), mode='L').resize(
            base.size, Image.Resampling.BILINEAR,
        ), dtype=np.float32,
    ) / 255.0
    original = np.asarray(base, dtype=np.float32)
    tint = np.empty_like(original)
    tint[..., 0] = 247
    tint[..., 1] = 90 + 100 * (1 - heat)
    tint[..., 2] = 30 + 70 * (1 - heat)
    alpha = 0.64 * heat[..., None]
    overlay = np.clip(original * (1 - alpha) + tint * alpha, 0, 255).astype(np.uint8)
    return Image.fromarray(overlay, mode='RGB')


def generar_gradcam(task_id, original_bytes, filename, data, version):
    """Genera mapa explicativo. Los fallos NO alteran el resultado diagnóstico existente."""
    import torch
    validator = OsteosarcomaValidator()
    pt_path = validator.model_path.with_name(MODEL_PT_FILENAME)
    output_path, _ = artefact_paths(task_id)
    if version != validator.version or not validator.available:
        _write_status(task_id, {'estado': 'NO_DISPONIBLE', 'detalle': 'MODELO_ACTIVO_NO_DISPONIBLE'})
        return 'NO_DISPONIBLE'
    if not pt_path.is_file():
        _write_status(task_id, {'estado': 'NO_DISPONIBLE', 'detalle': 'CHECKPOINT_PT_AUSENTE'})
        return 'NO_DISPONIBLE'
    if not (data.get('analisis_osteosarcoma_evaluado') and data.get('analisis_osteosarcoma')):
        _write_status(task_id, {'estado': 'NO_APLICA', 'detalle': 'RADIOGRAFIA_NO_EVALUADA_POR_CLASIFICADOR'})
        return 'NO_APLICA'

    try:
        # Misma preparación utilizada en predict(): una sola entrada normalizada.
        input_array = validator._preprocess(original_bytes, filename)
        input_tensor = torch.from_numpy(input_array).requires_grad_(True)
        model, checkpoint = _load_checkpoint(pt_path)
        checkpoint_version = str(checkpoint.get('version', version))
        if checkpoint_version != version:
            raise ValueError('CHECKPOINT_VERSION_MISMATCH')

        with torch.no_grad():
            logits_onnx = validator.session.run(None, {validator.input_name: input_array})[0][0]
            probability_onnx = float(_softmax(logits_onnx)[1])
            logits_pt = model(input_tensor.detach())[0]
            probability_pt = float(torch.softmax(logits_pt, dim=0)[1].item())
        if not verificar_equivalencia(probability_onnx, probability_pt, validator.threshold):
            _write_status(task_id, {
                'estado': 'NO_DISPONIBLE', 'detalle': 'INFERENCIA_PT_ONNX_NO_EQUIVALENTE',
                'diferencia_absoluta': round(abs(probability_onnx-probability_pt), 6),
            })
            return 'NO_DISPONIBLE'
        recorded_probability = float(data['analisis_osteosarcoma']['probabilidad_osteosarcoma'])
        if not verificar_equivalencia(recorded_probability, probability_onnx, validator.threshold):
            _write_status(task_id, {'estado': 'NO_DISPONIBLE', 'detalle': 'INFERENCIA_NO_COINCIDE_CON_RESULTADO'})
            return 'NO_DISPONIBLE'

        activated = {}
        def capture(_module, _inputs, output):
            activated['features'] = output
            output.retain_grad()

        handle = model.features[-1].register_forward_hook(capture)
        try:
            model.zero_grad(set_to_none=True)
            logits = model(input_tensor)
            logits[0, 1].backward()  # Grad-CAM para clase osteosarcoma, no localizador.
            features = activated['features']
            gradients = features.grad
            if gradients is None:
                raise ValueError('GRADIENTS_NOT_AVAILABLE')
            weights = gradients.mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * features).sum(dim=1))[0].detach().numpy()
        finally:
            handle.remove()

        if not np.isfinite(cam).all() or cam.max() - cam.min() < 1e-9:
            _write_status(task_id, {'estado': 'NO_DISPONIBLE', 'detalle': 'ACTIVACION_SIN_SENAL'})
            return 'NO_DISPONIBLE'
        cam = ((cam - cam.min()) / (cam.max() - cam.min())).astype('float32')
        # La cuadrícula Grad-CAM corresponde a la imagen completa (sin crop);
        # regresar al formato original solo corrige la PRESENTACIÓN, no el modelo.
        overlay = crear_superposicion_proporcional(original_bytes, filename, cam)

        # Comparar con la caja independiente del detector solo cuando existe.
        # NO se proyecta esta caja sobre el calor ni se oculta el fondo.
        localizacion = data.get('localizacion_osteosarcoma') or {}
        region = (localizacion.get('coordenadas_normalizadas')
                  if localizacion.get('detectada') is True else None)
        cam_auditoria = ampliar_cam_para_auditoria(cam)
        try:
            revision = medir_atencion(cam_auditoria, region)
            if region is not None:
                revision['region_referencia'] = 'DETECTOR_INDEPENDIENTE'
        except ValueError:
            revision = medir_atencion(cam_auditoria)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        # Mapa monobanda original protegido para revisión posterior con ROI
        # anotadas por un especialista; no se expone como archivo público.
        raw_path = camino_mapa_bruto(task_id)
        raw_temp = raw_path.with_suffix('.png.tmp')
        Image.fromarray(np.uint8(np.round(cam * 255)), mode='L').save(raw_temp, format='PNG')
        os.replace(raw_temp, raw_path)
        tmp_path = output_path.with_suffix('.png.tmp')
        overlay.save(tmp_path, format='PNG')
        os.replace(tmp_path, output_path)
        _write_status(task_id, {
            'revision_espacial': revision,
            'estado': 'DISPONIBLE', 'detalle': 'ACTIVACION_CLASE_OSTEOSARCOMA',
            'version_modelo': version,
            'sha256_checkpoint_pt': _sha(pt_path),
            'sha256_checkpoint_onnx': _sha(validator.model_path),
            'probabilidad_pt': probability_pt,
            'probabilidad_onnx': probability_onnx,
            'umbral': validator.threshold,
            'clase_objetivo': 1,
            'capa': 'features[-1]',
            'resolucion_entrada_modelo': '224x224',
            'resolucion_mapa_presentado': f'{overlay.width}x{overlay.height}',
            'presentacion': 'relacion_aspecto_original_sin_mascara',
            'advertencia': 'Grad-CAM puede activar fondo o artefactos. No diagnostica ni delimita tumores; comprobar anatomía y calidad de explicación.',
        })
        return 'DISPONIBLE'
    except (OSError, ValueError, RuntimeError, TypeError, KeyError, IndexError):
        # Sin divulgar detalles del checkpoint, imagen o paciente por la API.
        _write_status(task_id, {'estado': 'NO_DISPONIBLE', 'detalle': 'GENERACION_NO_VALIDADA'})
        return 'NO_DISPONIBLE'
