"""Pruebas visualizacion investigativa; no validan localizacion medica."""
import io
from unittest import TestCase
import numpy as np
from PIL import Image
from inteligencia.visualizacion_capas_gradcam import crear_montaje_capas

class PruebasMontajeCapas(TestCase):
    def setUp(self):
        self.raw=io.BytesIO()
        Image.new('RGB',(600,800),(110,110,110)).save(self.raw,format='PNG')
        self.cams={i:np.ones((7 if i >= -3 else 14,7 if i >= -3 else 14),dtype=np.float32)*.25 for i in (-1,-2,-3,-4,-5)}
        for i, arr in self.cams.items():
            arr[0,0]=1.0
        self.roi={'x1':.3,'y1':.15,'x2':.8,'y2':.73}

    def test_montaje_sin_roi(self):
        output=crear_montaje_capas(self.raw.getvalue(),'demo.png',self.cams,None,.15,'modelo_demo')
        with Image.open(io.BytesIO(output)) as png:
            self.assertEqual(png.format,'PNG')
            self.assertGreater(png.width,1000)

    def test_montaje_con_roi(self):
        output=crear_montaje_capas(self.raw.getvalue(),'demo.png',self.cams,self.roi,.15,'modelo_demo')
        self.assertGreater(len(output),10000)

    def test_roi_invalida(self):
        with self.assertRaises(ValueError):
            crear_montaje_capas(self.raw.getvalue(),'demo.png',self.cams,
                                {'x1':.9,'x2':.1,'y1':.1,'y2':.9})

    def test_no_cambia_cam(self):
        before={idx:arr.copy() for idx,arr in self.cams.items()}
        crear_montaje_capas(self.raw.getvalue(),'demo.png',self.cams,self.roi)
        for idx in self.cams:
            np.testing.assert_array_equal(before[idx],self.cams[idx])
