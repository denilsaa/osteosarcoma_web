"""Pruebas sin radiografías reales, BD ni inferencia ONNX."""
import io
from types import SimpleNamespace
from unittest import TestCase

import numpy as np
from PIL import Image

from inteligencia.auditoria_sesgo_fondo import (
    audit_predictions, build_variants, decode_original, png_bytes, validate_roi,
)


class FakePredictor:
    version = 'fake'
    threshold = .5

    def predict(self, raw, filename):
        with Image.open(io.BytesIO(raw)) as im:
            mean = float(np.asarray(im.convert('RGB'), dtype=np.float32).mean()) / 255
        return SimpleNamespace(osteosarcoma_probability=mean)


class BackgroundAuditTests(TestCase):
    def _image(self):
        image = Image.new('RGB', (200, 100), (20, 20, 20))
        for x in range(75, 125):
            for y in range(100):
                image.putpixel((x, y), (230, 230, 230))
        return image

    def test_variantes_sin_modificar_original(self):
        image = self._image()
        before = image.tobytes()
        variations = build_variants(image)
        self.assertEqual(len(variations), 5)
        self.assertEqual(image.tobytes(), before)
        self.assertTrue(all(v.size == image.size for _, v in variations))

    def test_control_central_cambia_centro_no_bordes(self):
        image = self._image()
        changed = dict(build_variants(image))['control_central_15pct']
        self.assertEqual(changed.getpixel((0, 50)), image.getpixel((0, 50)))
        self.assertNotEqual(changed.getpixel((100, 50)), image.getpixel((100, 50)))

    def test_roi_invalida_rechazada(self):
        for roi in ((.7, .2, .4, .8), (0, 0, 2, 1), (float('nan'), 0, 1, 1)):
            with self.assertRaises(ValueError):
                validate_roi(roi)

    def test_decode_y_ejecuta_con_roi(self):
        source = decode_original(png_bytes(self._image()), 'rx.png')
        report = audit_predictions(source, FakePredictor(), (.3, .1, .7, .8))
        self.assertEqual(len(report['variantes']), 6)
        self.assertEqual(report['dimensiones_originales'], [200, 100])
        self.assertEqual(report['diferencia_control_decodificacion_pp'], 0.0)
        self.assertIn('sha256_imagen_original', report)
        self.assertNotIn('nombre_paciente', report)

    def test_tamano_y_extension(self):
        raw = png_bytes(self._image())
        with self.assertRaises(ValueError):
            decode_original(raw, 'rx.exe')
        with self.assertRaises(ValueError):
            decode_original(b'', 'rx.png')
