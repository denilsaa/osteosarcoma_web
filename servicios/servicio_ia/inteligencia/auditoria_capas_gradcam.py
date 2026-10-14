"""Auditoría de Grad-CAM multicapas (SOLO INVESTIGACIÓN).

Las capas tempranas pueden producir mapas más detallados pero menos específicos.
Comparar contra una caja generada por otro modelo NO equivale a validación clínica.
"""
from __future__ import annotations

import numpy as np


def obtener_maps_capas(model, tensor, indices=(-1, -2, -3, -4, -5)):
    """Una sola inferencia/backpropagation; no cambia pesos ni estado del modelo."""
    import torch

    if tensor.ndim != 4 or tensor.shape[0] != 1:
        raise ValueError('TENSOR_INVALIDO')
    if len(set(indices)) != len(indices):
        raise ValueError('CAPAS_REPETIDAS')
    if any(not isinstance(i, int) or i >= 0 or abs(i) > len(model.features) for i in indices):
        raise ValueError('CAPAS_INVALIDAS')

    activaciones = {}
    handles = []
    try:
        for idx in indices:
            def hook(_module, _args, output, capa=idx):
                activaciones[capa] = output
                output.retain_grad()
            handles.append(model.features[idx].register_forward_hook(hook))

        model.eval()
        model.zero_grad(set_to_none=True)
        salida = model(tensor.detach().clone().requires_grad_(True))
        if salida.ndim != 2 or tuple(salida.shape) != (1, 2):
            raise ValueError('SALIDA_MODELO_INVALIDA')
        salida[0, 1].backward()
        maps = {}
        for idx in indices:
            activation = activaciones.get(idx)
            if activation is None or activation.grad is None:
                maps[idx] = None
                continue
            gradients = activation.grad
            weights = gradients.mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * activation).sum(dim=1))[0]
            cam_np = cam.detach().cpu().numpy()
            if not np.isfinite(cam_np).all() or cam_np.max() - cam_np.min() < 1e-9:
                maps[idx] = None
            else:
                maps[idx] = ((cam_np - cam_np.min()) / (cam_np.max() - cam_np.min())).astype(np.float32)
        return maps
    finally:
        for h in handles:
            h.remove()
        model.zero_grad(set_to_none=True)
