import importlib.util
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from validar_final_BAL03 import cifras_historicas, comparar_matriz, hay_identidad

class PruebaValidacionFinal(unittest.TestCase):
    def test_parse_historico(self):
        d = {'true_negative':480,'false_positive':35,'false_negative':7,'true_positive':37}
        self.assertEqual(cifras_historicas(d), {'tn':480,'fp':35,'fn':7,'tp':37})
    def test_concordancia(self):
        self.assertTrue(comparar_matriz({'tn':480,'fp':35,'fn':7,'tp':37}, {'tn':480,'fp':35,'fn':7,'tp':37}))
        self.assertFalse(comparar_matriz({'tn':480,'fp':35,'fn':5,'tp':39}, {'tn':480,'fp':35,'fn':7,'tp':37}))
    def test_repeticion(self):
        import numpy as np
        a = (np.array([0,1]),np.array([0.05,0.89]),np.array([0,1]))
        self.assertTrue(hay_identidad(a,a)['repeticion_consistente'])
        b = (np.array([0,1]),np.array([0.05,0.89]),np.array([1,0]))
        self.assertFalse(hay_identidad(a,b)['repeticion_consistente'])
    def test_mismatched_probabilities(self):
        import numpy as np
        a=(np.array([1]),np.array([0.21]),np.array([0]))
        b=(np.array([1]),np.array([0.10]),np.array([0]))
        self.assertFalse(hay_identidad(a,b)['repeticion_consistente'])

if __name__ == '__main__':
    unittest.main()
