"""Tests de guardas Grad-CAM: sin acceso a radiografías ni uso de BD."""
from unittest import mock
from uuid import uuid4

from django.test import SimpleTestCase

from inteligencia.gradcam_clinico import artefact_paths, verificar_equivalencia, consultar_estado


class GradCamGuardTests(SimpleTestCase):
    def test_probabilidades_iguales_mismo_resultado(self):
        self.assertTrue(verificar_equivalencia(0.83, 0.8299, 0.06))

    def test_predicciones_distintas_rechazadas(self):
        self.assertFalse(verificar_equivalencia(0.059, 0.061, 0.06))

    def test_desvio_grande_rechazado(self):
        self.assertFalse(verificar_equivalencia(0.15, 0.37, 0.06))

    def test_valores_no_finitos_rechazados(self):
        self.assertFalse(verificar_equivalencia(float('nan'), 0.4, 0.06))

    def test_uuid_fuera_de_ruta(self):
        with self.assertRaises(ValueError):
            artefact_paths('../../datos-privados')

    def test_sin_mapa_devuelve_no_disponible(self):
        with mock.patch('inteligencia.gradcam_clinico.artefact_paths') as paths:
            paths.return_value = (mock.Mock(), mock.Mock())
            paths.return_value[1].exists.return_value = False
            self.assertEqual(consultar_estado(uuid4())['estado'], 'NO_DISPONIBLE')


class GradCamSpatialTests(SimpleTestCase):
    """Solo patrones sintéticos; ninguna imagen clínica ni movimiento artificial de calor."""

    def test_senal_en_caja_coincide(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        heat = np.zeros((20, 20), dtype=np.float32)
        heat[5:10, 5:10] = 1.0
        roi = {'x1': 0.25, 'y1': 0.25, 'x2': 0.50, 'y2': 0.50}
        result = medir_atencion(heat, roi)
        self.assertTrue(result['maximo_en_region'])
        self.assertAlmostEqual(result['fraccion_activacion_en_region'], 1.0)
        self.assertEqual(result['coincidencia_exploratoria'], 'SIN_DISCREPANCIA_GROSERA')

    def test_senal_fuera_de_caja_alerta(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        heat = np.zeros((20, 20), dtype=np.float32)
        heat[13:18, 13:18] = 1.0
        roi = {'x1': 0.25, 'y1': 0.25, 'x2': 0.50, 'y2': 0.50}
        result = medir_atencion(heat, roi)
        self.assertFalse(result['maximo_en_region'])
        self.assertEqual(result['coincidencia_exploratoria'], 'REVISAR_DISCREPANCIA')

    def test_sin_region_no_inventa_localizacion(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        heat = np.ones((20, 20), dtype=np.float32)
        result = medir_atencion(heat)
        self.assertEqual(result['region_referencia'], 'SIN_REFERENCIA')
        self.assertNotIn('maximo_en_region', result)

    def test_coordenadas_invalidas_rechazadas(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        with self.assertRaises(ValueError):
            medir_atencion(np.ones((20, 20)), {'x1': .6, 'y1': .3, 'x2': .3, 'y2': .8})

    def test_cam_invalida_rechazada(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        with self.assertRaises(ValueError):
            medir_atencion(np.array([[np.nan, .5], [.1, .2]]))

    def test_no_modifica_entrada(self):
        import numpy as np
        from inteligencia.gradcam_clinico import medir_atencion
        heat = np.random.default_rng(123).uniform(0, 1, (20, 20)).astype('float32')
        before = heat.copy()
        medir_atencion(heat, {'x1': .3, 'y1': .2, 'x2': .8, 'y2': .7})
        self.assertTrue(np.array_equal(heat, before))
