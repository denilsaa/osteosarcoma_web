"""Pruebas sin datos clínicos, con predicciones sintéticas."""
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from comparador_umbrales_osteosarcoma import (metricas, wilson95, leer_predicciones,
    comparar_repeticion, ejecutar)


class ComparadorTests(unittest.TestCase):
    def setUp(self):
        self.y=[1,1,0,0]
        self.p=[0.9,0.3,0.4,0.1]

    def test_matriz_y_metricas(self):
        m=metricas(self.y,self.p,0.5)
        self.assertEqual((m['tp'],m['fn'],m['tn'],m['fp']),(1,1,2,0))
        self.assertEqual(m['sensibilidad'],0.5)
        self.assertEqual(m['especificidad'],1)

    def test_umbral_cambia_falsos_negativos(self):
        self.assertEqual(metricas(self.y,self.p,0.2)['fn'],0)
        self.assertEqual(metricas(self.y,self.p,0.5)['fn'],1)
        self.assertEqual(metricas(self.y,self.p,0.95)['fn'],2)

    def test_ic_wilson(self):
        self.assertEqual(wilson95(0,0),None)
        lo,hi=wilson95(1,2)
        self.assertLess(lo,0.5)
        self.assertGreater(hi,0.5)

    def test_rechaza_probabilidad_no_finita(self):
        with self.assertRaises(ValueError):
            metricas(self.y,[0.1,0.2,float('nan'),0.4],0.5)

    def test_repeticion(self):
        self.assertTrue(comparar_repeticion(self.y,self.p,self.y,self.p)['coincide'])
        self.assertFalse(comparar_repeticion(self.y,self.p,self.y,[0.9,0.3,0.4,0.5])['coincide'])

    def test_flujo_csv_html_y_expediente_pendiente(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);input_file=root/'pred.csv'
            with input_file.open('w',newline='',encoding='utf-8') as file:
                writer=csv.writer(file);writer.writerow(['y_true','y_prob'])
                writer.writerows(zip(self.y,self.p))
            ejecutar(SimpleNamespace(datos=str(input_file),salida=str(root/'out'),fase='validation',
                umbral=0.5,modelo='prueba',repeticion=None,checkpoint=None,responsable='Evaluador'))
            out=root/'out'
            with (out/'comparacion_umbrales.csv').open(encoding='utf-8-sig') as fd:
                self.assertEqual(len(list(csv.DictReader(fd))),101)
            expediente=json.loads((out/'expediente_modelo_pendiente.json').read_text(encoding='utf-8'))
            self.assertEqual(expediente['estado_aprobacion'],'PENDIENTE_REVISION')
            self.assertIn('input type="range"',(out/'comparador_umbrales.html').read_text(encoding='utf-8'))

    def test_test_no_optimiza_umbral(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);f=root/'pred.json'
            f.write_text(json.dumps({'y_true':self.y,'y_prob':self.p}),encoding='utf-8')
            ejecutar(SimpleNamespace(datos=str(f),salida=str(root/'out'),fase='test',
                umbral=0.5,modelo='prueba',repeticion=None,checkpoint=None,responsable='Evaluador'))
            with (root/'out'/'comparacion_umbrales.csv').open(encoding='utf-8-sig') as fd:
                rows=list(csv.DictReader(fd))
            self.assertEqual(len(rows),1)
            self.assertIn('disabled aria-disabled="true"',(root/'out'/'comparador_umbrales.html').read_text(encoding='utf-8'))


if __name__=='__main__':
    unittest.main()
