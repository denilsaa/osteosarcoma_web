"""Montaje visual de capas Grad-CAM. NO publica ni altera resultados clinicos.

Cada mapa está NORMALIZADO INDEPENDIENTEMENTE (0 a 1), por lo que comparar
intensidades absolutas entre capas carece de sentido. No mueve las activaciones.
"""
from __future__ import annotations
import io
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from inteligencia.gradcam_clinico import _reference_image, _validar_roi, ampliar_cam_para_auditoria, medir_atencion

ROWS, COLS = 2, 3
CARD_W, CARD_H = 430, 560
IMAGE_W, IMAGE_H = 390, 440
GAP, HEADER = 16, 92


def _fuente(size):
    for font in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                 '/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf'):
        try:
            return ImageFont.truetype(font, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _superponer(base: Image.Image, heat: np.ndarray):
    """Overlay proporcional, misma geometría; fuerza de color = CAM real normalizado."""
    h = np.asarray(heat, dtype=np.float32)
    if h.ndim != 2 or min(h.shape) < 2 or not np.isfinite(h).all() or h.min() < 0 or h.max() > 1:
        raise ValueError('CAM_INVALIDA')
    heat_image = Image.fromarray(h, mode='F').resize(base.size, Image.Resampling.BILINEAR)
    h2 = np.asarray(heat_image, dtype=np.float32).clip(0, 1)
    arr = np.asarray(base.convert('RGB'), dtype=np.float32)
    # Amarillo suave en medias activaciones, rojo en máximas; alpha nula en 0.
    color = np.empty_like(arr)
    color[..., 0] = 255.0
    color[..., 1] = 180.0 * (1.0 - h2)
    color[..., 2] = 12.0
    alpha = np.power(h2, 1.5) * .70
    rgb = (arr * (1-alpha[...,None]) + color * alpha[...,None]).clip(0,255).astype(np.uint8)
    return Image.fromarray(rgb, mode='RGB')


def crear_montaje_capas(original_bytes, filename, mapas, region=None, probability=None, version=''):
    if not isinstance(mapas, dict) or not mapas:
        raise ValueError('SIN_CAPAS')
    if region is not None:
        _validar_roi(region)
    base = _reference_image(original_bytes, filename)
    if base.width < 2 or base.height < 2:
        raise ValueError('IMAGEN_INVALIDA')
    # Ajusta solo para VISUALIZAR. La métrica se calcula sobre CAM 224 normalizada.
    preview = base.copy()
    preview.thumbnail((IMAGE_W,IMAGE_H), Image.Resampling.LANCZOS)
    prepared = [('Original', None, None)]
    for idx in [-1,-2,-3,-4,-5]:
        heat = mapas.get(idx)
        stat = medir_atencion(ampliar_cam_para_auditoria(heat), region) if heat is not None else None
        prepared.append((f'features[{idx}]', heat, stat))

    page_w=COLS*CARD_W+(COLS+1)*GAP
    page_h=HEADER+ROWS*CARD_H+(ROWS+1)*GAP+56
    output=Image.new('RGB',(page_w,page_h),(240,244,249))
    draw=ImageDraw.Draw(output)
    draw.text((GAP,14),'AUDITORIA GRAD-CAM · 5 CAPAS',fill=(21,47,81),font=_fuente(25))
    prob = 'N/D' if probability is None else f'{100*float(probability):.3f}%'
    draw.text((GAP,52),f'Modelo: {str(version)[:48]} | Prediccion: {prob} | ROI: detector independiente',fill=(64,76,93),font=_fuente(15))
    for num,(label,cam,stat) in enumerate(prepared):
        col,row=num%COLS,num//COLS
        x=GAP+col*(CARD_W+GAP); y=HEADER+GAP+row*(CARD_H+GAP)
        draw.rounded_rectangle([x,y,x+CARD_W,y+CARD_H],radius=12,fill=(255,255,255),outline=(210,221,233),width=2)
        draw.text((x+15,y+12),label,fill=(18,51,89),font=_fuente(20))
        if cam is None and num>0:
            display=preview.copy()
            summary='Sin senal Grad-CAM'
        elif cam is None:
            display=preview.copy()
            summary='Imagen original (sin Grad-CAM)'
        else:
            display=_superponer(preview,cam)
            summary=(f'En caja: {100*stat["fraccion_activacion_en_region"]:.1f}% | '
                     f'Bordes: {100*stat["fraccion_activacion_bordes"]:.1f}%') if region is not None else 'ROI no disponible'
        xx=x+(CARD_W-display.width)//2
        yy=y+51+(IMAGE_H-display.height)//2
        output.paste(display,(xx,yy))
        if region is not None:
            x1,y1,x2,y2=_validar_roi(region)
            bbox=(xx+round(x1*display.width), yy+round(y1*display.height),
                  xx+round(x2*display.width), yy+round(y2*display.height))
            draw.rectangle(bbox,outline=(235,50,66),width=3)
        draw.text((x+12,y+505),summary,fill=(64,76,93),font=_fuente(14))
        if cam is not None and stat is not None and region is not None:
            draw.text((x+12,y+527),f'Maximo en caja: {"SI" if stat["maximo_en_region"] else "NO"}',fill=(155,65,66),font=_fuente(14))
    bottom=page_h-41
    draw.text((GAP,bottom),'SOLO INVESTIGACION · Las capas se normalizan por separado. La caja no es anotacion medica.',
              fill=(130,67,53),font=_fuente(15))
    buffer=io.BytesIO()
    output.save(buffer,format='PNG',optimize=True)
    return buffer.getvalue()
