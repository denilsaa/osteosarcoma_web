"""Verifica paridad básica ONNX/PyTorch sin radiografías de pacientes."""
import numpy as np
import torch
from django.core.management.base import BaseCommand, CommandError

from inteligencia.gradcam_clinico import (
    MODEL_PT_FILENAME, _load_checkpoint, _softmax, verificar_equivalencia,
)
from inteligencia.inference.osteosarcoma_validator import OsteosarcomaValidator


class Command(BaseCommand):
    help = 'Compara ONNX y .pt con entradas sintéticas; sin datos clínicos ni modificación de archivos.'

    def handle(self, *args, **options):
        validator = OsteosarcomaValidator()
        if not validator.available:
            raise CommandError('El modelo ONNX no está disponible.')
        checkpoint_path = validator.model_path.with_name(MODEL_PT_FILENAME)
        if not checkpoint_path.exists():
            raise CommandError(f'Falta el checkpoint {MODEL_PT_FILENAME} en /app/modelos.')
        try:
            model, checkpoint = _load_checkpoint(checkpoint_path)
        except Exception as exc:
            raise CommandError('No fue posible cargar el checkpoint seguro de PyTorch.') from exc
        if str(checkpoint.get('version', validator.version)) != validator.version:
            raise CommandError('La versión del checkpoint no coincide con la del ONNX activo.')

        rng = np.random.default_rng(20261007)
        samples = [
            np.zeros((1, 3, 224, 224), dtype=np.float32),
            np.ones((1, 3, 224, 224), dtype=np.float32) * 0.125,
            rng.uniform(-1, 1, (1, 3, 224, 224)).astype(np.float32),
        ]
        for i, tensor in enumerate(samples, start=1):
            onnx_logits = validator.session.run(None, {validator.input_name: tensor})[0][0]
            with torch.no_grad():
                pt_logits = model(torch.from_numpy(tensor))[0]
                prob_pt = float(torch.softmax(pt_logits, dim=0)[1].item())
            prob_onnx = float(_softmax(onnx_logits)[1])
            if not verificar_equivalencia(prob_onnx, prob_pt, validator.threshold):
                raise CommandError(f'DIFERENCIA EN ENTRADA SINTÉTICA {i}; NO ACTIVAR GRAD-CAM.')
            self.stdout.write(f'Caso sintético {i}: coincidencia (diferencia={abs(prob_onnx-prob_pt):.7f})')
        self.stdout.write(self.style.SUCCESS('ONNX_PT_COMPATIBLE | Prueba sintética superada.'))
        self.stdout.write('Cada Grad-CAM clínico vuelve a comprobar la paridad con la radiografía real.')
