"""Pruebas sintéticas rápidas del cálculo de mapas por capa."""
from django.test import SimpleTestCase
import torch
from torch import nn
from inteligencia.auditoria_capas_gradcam import obtener_maps_capas


class ModeloMinimo(nn.Module):
    def __init__(self):
        super().__init__()
        self.features = nn.Sequential(*[
            nn.Sequential(nn.Conv2d(3, 3, 3, padding=1), nn.ReLU())
            for _ in range(5)
        ])
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.classifier = nn.Linear(3, 2)

    def forward(self, x):
        x = self.features(x)
        return self.classifier(self.pool(x).flatten(1))


class CapasGradCamTests(SimpleTestCase):
    def setUp(self):
        torch.manual_seed(8)
        self.model = ModeloMinimo().eval()
        self.tensor = torch.rand(1, 3, 16, 16)

    def test_captura_cinco_capas(self):
        resultado = obtener_maps_capas(self.model, self.tensor)
        self.assertEqual(set(resultado.keys()), {-1, -2, -3, -4, -5})
        self.assertTrue(all(m is None or m.shape == (16, 16) for m in resultado.values()))

    def test_no_deja_hooks(self):
        before = [len(l._forward_hooks) for l in self.model.features]
        obtener_maps_capas(self.model, self.tensor)
        self.assertEqual(before, [len(l._forward_hooks) for l in self.model.features])

    def test_rechaza_capas_incorrectas(self):
        with self.assertRaises(ValueError):
            obtener_maps_capas(self.model, self.tensor, (10,))

    def test_rechaza_tensor_invalido(self):
        with self.assertRaises(ValueError):
            obtener_maps_capas(self.model, torch.rand(3, 16, 16))
