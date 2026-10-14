"""Compara capas de Grad-CAM sobre un ORIGINAL previamente analizado.

NO guarda mapas, NO modifica resultados de IA, NO altera modelo ni BD.
Para estudios de desarrollo autorizados. No diagnostica osteosarcoma.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from inteligencia.auditoria_capas_gradcam import obtener_maps_capas
from inteligencia.visualizacion_capas_gradcam import crear_montaje_capas
from inteligencia.gradcam_clinico import (
    MODEL_PT_FILENAME, _load_checkpoint, ampliar_cam_para_auditoria,
    medir_atencion, verificar_equivalencia,
)
from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator
from inteligencia.models import AnalisisRadiografiaIA, SolicitudAnalisisIA


class Command(BaseCommand):
    help = 'Auditoría SOLO INVESTIGACIÓN: comparar Grad-CAM de 5 capas sin alterar resultados.'

    def add_arguments(self, parser):
        parser.add_argument('--imagen', required=True, help='Archivo original en el contenedor IA.')
        parser.add_argument('--solicitud', required=True, help='UUID de la solicitud ya completada.')
        parser.add_argument('--sha256', help='SHA256 esperado del original, leído desde radiografías.')
        parser.add_argument('--salida', help='Opcional. PNG comparativo en /tmp dentro del contenedor (solo investigacion).')

    def handle(self, *args, **opts):
        try:
            uid = UUID(opts['solicitud'])
        except (ValueError, TypeError) as exc:
            raise CommandError('UUID_INVALIDO') from exc
        path = Path(opts['imagen'])
        salida = opts.get('salida')
        if salida is not None:
            destino = Path(salida)
            if destino.parent != Path('/tmp') or not destino.name.startswith('gradcam_auditoria_') or destino.suffix.lower() != '.png':
                raise CommandError('SALIDA_NO_PERMITIDA: usar /tmp/gradcam_auditoria_<nombre>.png')
        if not path.is_file() or path.stat().st_size > 20 * 1024 * 1024:
            raise CommandError('IMAGEN_NO_DISPONIBLE_O_GRANDE')
        extension = path.suffix.lower()
        if extension not in ('.png', '.jpeg', '.jpg', '.dcm', '.tif', '.tiff', '.bmp'):
            raise CommandError('FORMATO_NO_ADMITIDO')
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        if opts.get('sha256') and digest.lower() != opts['sha256'].strip().lower():
            raise CommandError('SHA256_NO_COINCIDE; no analizar imagen diferente.')
        solicitud = SolicitudAnalisisIA.objects.filter(id_solicitud=uid, estado='COMPLETADO').first()
        if not solicitud or not solicitud.analisis_id:
            raise CommandError('SOLICITUD_NO_COMPLETADA_O_SIN_ANALISIS')
        analisis = AnalisisRadiografiaIA.objects.filter(id_analisis=solicitud.analisis_id).first()
        if not analisis or analisis.probabilidad_osteosarcoma is None:
            raise CommandError('RESULTADO_IA_NO_DISPONIBLE')
        roi = None
        if analisis.localizacion_detectada and all(
            getattr(analisis, key) is not None for key in ('x1', 'y1', 'x2', 'y2')
        ):
            roi = {key: float(getattr(analisis, key)) for key in ('x1', 'y1', 'x2', 'y2')}

        v = OsteosarcomaValidator()
        checkpoint_path = v.model_path.with_name(MODEL_PT_FILENAME)
        if not v.available or not checkpoint_path.is_file():
            raise CommandError('MODELO_CLINICO_O_CHECKPOINT_NO_DISPONIBLE')
        if str(solicitud.version_modelo) != v.version:
            raise CommandError('VERSION_MODELO_NO_COINCIDE')

        try:
            import numpy as np
            import torch
            arr = v._preprocess(raw, 'original' + extension)
            with torch.no_grad():
                p_onnx = float(v.predict(raw, 'original' + extension).osteosarcoma_probability)
            p_historico = float(analisis.probabilidad_osteosarcoma)
            if abs(p_historico - p_onnx) > 0.001:
                raise CommandError(
                    f'ORIGINAL_NO_COINCIDE_CON_HISTORIAL: historico={p_historico:.6f}, '
                    f'actual={p_onnx:.6f}. No se comparan capas.'
                )
            model, checkpoint = _load_checkpoint(checkpoint_path)
            if str(checkpoint.get('version', v.version)) != v.version:
                raise CommandError('CHECKPOINT_DE_OTRA_VERSION')
            with torch.no_grad():
                p_pt = float(torch.softmax(model(torch.from_numpy(arr))[0], dim=0)[1].item())
            if not verificar_equivalencia(p_onnx, p_pt, v.threshold):
                raise CommandError('MODELOS_PYTORCH_ONNX_NO_EQUIVALENTES')

            resultado = obtener_maps_capas(model, torch.from_numpy(arr))
            self.stdout.write(f'REVISION_SOLICITUD: {uid}')
            self.stdout.write(f'IMAGEN_SHA256: {digest}')
            self.stdout.write(f'MODELO: {v.version} | P_ORIGINAL: {100*p_onnx:.3f} % | P_PT: {100*p_pt:.3f} %')
            self.stdout.write('ROI: DETECTOR_INDEPENDIENTE (NO ANOTACION MEDICA)' if roi else 'ROI: NO_DISPONIBLE')
            for idx, heat in resultado.items():
                if heat is None:
                    self.stdout.write(f'features[{idx}]: SIN_SENAL')
                    continue
                metric = medir_atencion(ampliar_cam_para_auditoria(heat), roi)
                line = (f'features[{idx}] {heat.shape[1]}x{heat.shape[0]} | '
                        f'bordes={100*metric["fraccion_activacion_bordes"]:.2f}%')
                if roi is not None:
                    line += (f' | en_caja={100*metric["fraccion_activacion_en_region"]:.2f}%'
                             f' | densidad_relativa={metric["densidad_relativa_en_region"]:.3f}'
                             f' | max_en_caja={metric["maximo_en_region"]}')
                self.stdout.write(line)
            if salida is not None:
                # Montaje privado, transitorio. No toca resultados ni almacenamiento persistente.
                imagen = crear_montaje_capas(
                    raw, 'original' + extension, resultado, roi,
                    probability=p_onnx, version=v.version,
                )
                tmp_file = destino.with_suffix('.png.tmp')
                try:
                    tmp_file.write_bytes(imagen)
                    tmp_file.replace(destino)
                finally:
                    tmp_file.unlink(missing_ok=True)
                self.stdout.write(f'MONTAJE_CAPAS: {destino} | {len(imagen)} bytes | SOLO INVESTIGACION')
        except CommandError:
            raise
        except (OSError, RuntimeError, ValueError, TypeError, KeyError, IndexError) as exc:
            raise CommandError(f'AUDITORIA_NO_EJECUTADA: {type(exc).__name__}: {str(exc)[:160]}') from exc
        self.stdout.write('SOLO INVESTIGACION: comparar capas no valida ni localiza tumores.')
