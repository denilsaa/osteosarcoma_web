import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from diagnosticar_diferencias_BAL03 import matriz, valores_historicos, distancias_umbral, contar_cambios_umbral


class DiagnosticoTests(unittest.TestCase):
    def test_matriz(self):
        actual = matriz([0, 0, 1, 1], [0.01, 0.80, 0.99, 0.10], 0.21)
        self.assertEqual([actual[x] for x in ('tn','fp','fn','tp')], [1,1,1,1])
        self.assertEqual(actual['sensibilidad'], 0.5)

    def test_threshold_exacto(self):
        self.assertEqual(matriz([0,1],[0.1,0.21],0.21)['fn'], 0)
        self.assertEqual(matriz([0,1],[0.1,0.21],0.21000000000000002)['fn'], 1)

    def test_valores_historicos(self):
        self.assertEqual(valores_historicos(dict(true_negative=1,false_positive=2,
                                                false_negative=3,true_positive=4)),
                         dict(tn=1, fp=2,fn=3,tp=4))

    def test_cambios_con_listas_y_arrays(self):
        import numpy as np
        self.assertEqual(
            contar_cambios_umbral([0.20, 0.40, 0.21], np.array([0.25, 0.41, 0.19]), 0.21),
            2,
        )
        self.assertEqual(contar_cambios_umbral([0.1, 0.8], [0.1, 0.8], 0.21), 0)

    def test_cambios_rechaza_longitudes_diferentes(self):
        with self.assertRaises(ValueError):
            contar_cambios_umbral([0.1], [0.1, 0.2], 0.21)

    def test_cercania(self):
        self.assertEqual(distancias_umbral([0.21, 0.3], 0.21)['menor_que_0.0001'],1)


if __name__ == '__main__':
    unittest.main()
