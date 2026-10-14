"""Comparador técnico de umbrales para probabilidades de osteosarcoma.

No entrena, no aprueba, ni reemplaza un modelo clínico. Seleccionar umbral
solo en validación; informar TEST únicamente con el umbral ya congelado.

Ejemplos:
  python comparador_umbrales_osteosarcoma.py --datos predicciones_validation.npz \
      --fase validation --umbral 0.21 --modelo BAL-03 --salida reportes/umbrales
  python comparador_umbrales_osteosarcoma.py --datos predicciones_test.npz \
      --fase test --umbral 0.21 --modelo BAL-03 --salida reportes/test
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _validar_valores(labels, scores):
    if len(labels) != len(scores) or not labels:
        raise ValueError('Las etiquetas y probabilidades deben tener igual tamaño no vacío.')
    clean_labels, clean_scores = [], []
    for label, score in zip(labels, scores):
        if isinstance(label, bool) or float(label) not in (0.0, 1.0):
            raise ValueError('Las etiquetas reales deben ser 0 o 1.')
        value = float(score)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError('Cada probabilidad debe ser finita y estar entre 0 y 1.')
        clean_labels.append(int(label))
        clean_scores.append(value)
    if 0 not in clean_labels or 1 not in clean_labels:
        raise ValueError('Se requieren ambas clases para calcular sensibilidad y especificidad.')
    return clean_labels, clean_scores


def leer_predicciones(path: Path):
    if not path.is_file():
        raise FileNotFoundError(f'No existe el archivo: {path}')
    if path.suffix.lower() == '.npz':
        try:
            import numpy as np
        except ImportError as exc:
            raise RuntimeError('Para leer .npz instala numpy o utiliza CSV.') from exc
        with np.load(path, allow_pickle=False) as data:
            return _validar_valores(data['y_true'].tolist(), data['y_prob'].tolist())
    if path.suffix.lower() == '.json':
        data = json.loads(path.read_text(encoding='utf-8'))
        return _validar_valores(data['y_true'], data['y_prob'])
    if path.suffix.lower() == '.csv':
        with path.open('r', newline='', encoding='utf-8-sig') as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError('El CSV está vacío.')
        def get(row, names):
            for name in names:
                if name in row and row[name] not in ('', None):
                    return row[name]
            raise ValueError(f'El CSV requiere alguna de las columnas: {names}')
        labels = [get(r, ('y_true', 'real', 'osteosarcoma', 'label')) for r in rows]
        scores = [get(r, ('y_prob', 'probability_osteosarcoma', 'probabilidad_osteosarcoma')) for r in rows]
        return _validar_valores(labels, scores)
    raise ValueError('Formato admitido: CSV, JSON o NPZ.')


def wilson95(aciertos: int, total: int):
    if not total:
        return None
    z = 1.959963984540054
    p = aciertos / total
    denom = 1 + z*z/total
    center = (p + z*z/(2*total)) / denom
    radius = z * math.sqrt((p*(1-p) + z*z/(4*total))/total) / denom
    return [max(0.0, center-radius), min(1.0, center+radius)]


def metricas(labels, scores, umbral):
    if not math.isfinite(umbral) or not 0 <= umbral <= 1:
        raise ValueError('El umbral debe estar entre 0 y 1.')
    labels, scores = _validar_valores(labels, scores)
    tp = sum(y == 1 and p >= umbral for y, p in zip(labels, scores))
    fn = sum(y == 1 and p < umbral for y, p in zip(labels, scores))
    tn = sum(y == 0 and p < umbral for y, p in zip(labels, scores))
    fp = sum(y == 0 and p >= umbral for y, p in zip(labels, scores))
    sensitivity = tp/(tp+fn)
    specificity = tn/(tn+fp)
    return {
        'umbral': umbral,
        'total': len(labels),
        'tp': tp, 'tn': tn, 'fp': fp, 'fn': fn,
        'sensibilidad': sensitivity,
        'especificidad': specificity,
        'exactitud': (tp+tn)/len(labels),
        'precision_vpp': tp/(tp+fp) if tp+fp else None,
        'vpn': tn/(tn+fn) if tn+fn else None,
        'exactitud_balanceada': (sensitivity+specificity)/2,
        'ic95_sensibilidad_wilson': wilson95(tp, tp+fn),
        'ic95_especificidad_wilson': wilson95(tn, tn+fp),
        'brier': sum((p-y)**2 for y,p in zip(labels,scores))/len(labels),
    }


def comparar_repeticion(labels, scores, second_labels, second_scores, tolerancia=1e-6):
    second_labels, second_scores = _validar_valores(second_labels, second_scores)
    same_labels = labels == second_labels
    dif = max((abs(a-b) for a,b in zip(scores,second_scores)), default=float('inf')) if len(scores) == len(second_scores) else float('inf')
    return {
        'coincide': same_labels and math.isfinite(dif) and dif <= tolerancia,
        'cantidad': len(labels),
        'diferencia_maxima': dif if math.isfinite(dif) else None,
        'tolerancia': tolerancia,
        'advertencia': 'Compara dos ejecuciones de inferencia del mismo modelo; no prueba reproducibilidad del entrenamiento ni validez externa.',
    }


def guardar_html(path, labels, scores, selected, model, phase):
    # La visualización se mantiene fuera de la interfaz del oncólogo.
    payload = json.dumps({'labels':labels, 'scores':scores, 'selected':selected}, separators=(',', ':'))
    payload = payload.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    editable = phase == 'validation'
    title = html.escape(model)
    markup = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Comparador técnico de umbrales</title><style>body{font:16px system-ui,sans-serif;color:#14253d;background:#f5f7fa;max-width:900px;margin:30px auto;padding:0 18px}main{background:white;padding:25px;border-radius:14px;box-shadow:0 2px 12px #10233815}h1{font-size:1.7rem}.muted{color:#4c5d72}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:20px 0}.card{border:1px solid #dce4ed;border-radius:10px;padding:14px}.card strong{font-size:1.55rem;display:block}input[type=range]{width:100%;accent-color:#144fb2}table{border-collapse:collapse;width:100%;margin-top:10px}th,td{border-bottom:1px solid #dce4ed;padding:8px;text-align:left}svg{width:100%;height:auto}a:focus,input:focus{outline:3px solid #1b67e4;outline-offset:2px}.warn{border-left:4px solid #cc8a00;padding:12px;background:#fff8eb}</style></head><body><main>
<h1>Comparador técnico de umbrales</h1><p class="muted">Modelo: <b>__MODEL__</b> · Conjunto: <b>__FASE__</b>. Sólo uso técnico, no diagnóstico.</p>
<label for="threshold">Umbral: <strong id="thresholdText"></strong></label><input type="range" id="threshold" min="0" max="1" step="0.01" __DISABLED__>
<div class="cards"><div class="card">Sensibilidad<strong id="sens"></strong></div><div class="card">Especificidad<strong id="spec"></strong></div><div class="card">Falsos negativos<strong id="fn"></strong></div><div class="card">Falsos positivos<strong id="fp"></strong></div></div>
<p id="intervals"></p><p id="predictive"></p><svg id="graph" viewBox="0 0 700 220" role="img" aria-label="Curvas de sensibilidad y especificidad según umbral"></svg>
<table><caption>Matriz de confusión</caption><thead><tr><th>Real</th><th>Predicción negativa</th><th>Predicción positiva</th></tr></thead><tbody><tr><th>No osteosarcoma</th><td id="tn"></td><td id="fp2"></td></tr><tr><th>Osteosarcoma</th><td id="fn2"></td><td id="tp"></td></tr></tbody></table>
<p class="warn">Los intervalos Wilson al 95% cuantifican incertidumbre de sensibilidad y especificidad sobre esta muestra; NO prueban confiabilidad clínica ni calibración de las probabilidades. Evaluar y elegir umbral sólo en validación, luego medir en test con umbral fijo. La decisión clínica corresponde al oncólogo.</p></main>
<script>const D=__DATA__;const $=id=>document.getElementById(id);const input=$('threshold');input.value=D.selected;
function m(t){let tp=0,tn=0,fp=0,fn=0;D.labels.forEach((y,i)=>{const p=D.scores[i]>=t;if(y===1){if(p)tp++;else fn++}else{if(p)fp++;else tn++}});return {tp,tn,fp,fn,s:tp/(tp+fn),e:tn/(tn+fp),vpp:tp+fp?tp/(tp+fp):null,vpn:tn+fn?tn/(tn+fn):null}}
function ci(k,n){const z=1.959963984540054,p=k/n,d=1+z*z/n,c=(p+z*z/(2*n))/d,r=z*Math.sqrt((p*(1-p)+z*z/(4*n))/n)/d;return [Math.max(0,c-r),Math.min(1,c+r)]}
const pct=x=>x===null?'No definido':(x*100).toFixed(2)+'%';
function line(values,color){return '<polyline fill="none" stroke="'+color+'" stroke-width="3" points="'+values.map((v,i)=>(40+i*6.2)+','+(192-v*165)).join(' ')+'"/>'}
const sen=[],esp=[];for(let i=0;i<=100;i++){const a=m(i/100);sen.push(a.s);esp.push(a.e)}$('graph').innerHTML='<path d="M40 15 V192 H670" stroke="#64748b" fill="none" stroke-width="2"/>'+line(sen,'#155bd4')+line(esp,'#aa4a09')+'<text x="40" y="213" fill="#334155" font-size="12">0</text><text x="636" y="213" fill="#334155" font-size="12">1.0</text><text x="95" y="18" fill="#155bd4" font-size="14">Sensibilidad</text><text x="230" y="18" fill="#aa4a09" font-size="14">Especificidad</text>';
function update(){const t=Number(input.value),a=m(t),si=ci(a.tp,a.tp+a.fn),sp=ci(a.tn,a.tn+a.fp);$('thresholdText').textContent=t.toFixed(2);$('sens').textContent=pct(a.s);$('spec').textContent=pct(a.e);['fn','fn2'].forEach(x=>$(x).textContent=a.fn);['fp','fp2'].forEach(x=>$(x).textContent=a.fp);$('tn').textContent=a.tn;$('tp').textContent=a.tp;$('intervals').textContent='IC95% sensibilidad: '+pct(si[0])+'–'+pct(si[1])+' · especificidad: '+pct(sp[0])+'–'+pct(sp[1]);$('predictive').textContent='Valor predictivo positivo: '+pct(a.vpp)+' · valor predictivo negativo: '+pct(a.vpn)}input.addEventListener('input',update);update();</script></body></html>'''
    markup = markup.replace('__MODEL__', title).replace('__FASE__', html.escape(phase)).replace('__DISABLED__', 'disabled aria-disabled="true"' if not editable else '').replace('__DATA__', payload)
    path.write_text(markup, encoding='utf-8')


def ejecutar(args):
    src = Path(args.datos).resolve()
    labels, scores = leer_predicciones(src)
    output = Path(args.salida)
    output.mkdir(parents=True, exist_ok=True)
    selected = float(args.umbral)
    current = metricas(labels,scores,selected)
    repeat = None
    if args.repeticion:
        other_labels, other_scores = leer_predicciones(Path(args.repeticion))
        repeat = comparar_repeticion(labels,scores,other_labels,other_scores)
        if not repeat['coincide']:
            raise ValueError('La repetición no coincide: no se puede marcar reproducibilidad.')
    phase = args.fase
    rows = [metricas(labels,scores,round(i/100,2)) for i in range(101)] if phase == 'validation' else [current]
    with (output/'comparacion_umbrales.csv').open('w',encoding='utf-8-sig', newline='') as fp:
        writer = csv.DictWriter(fp, fieldnames=['umbral','total','tp','tn','fp','fn','sensibilidad','especificidad','exactitud','precision_vpp','vpn','exactitud_balanceada','brier'],extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    manifest = {
        'modelo_reportado': args.modelo, 'fase': phase,
        'fecha_utc': datetime.now(timezone.utc).isoformat(),
        'fuente_predicciones_sha256': sha256_file(src),
        'modelo_checkpoint_sha256': sha256_file(Path(args.checkpoint)) if args.checkpoint else None,
        'metricas_umbral_propuesto': current,
        'repeticion': repeat,
        'estado_aprobacion': 'PENDIENTE_REVISION',
        'responsable_tecnico': args.responsable,
        'version_modelo_verificada': False,
        'limitaciones': [
          'No usar para diagnóstico definitivo; requiere valoración del oncólogo.',
          'Las probabilidades no deben interpretarse como confianza calibrada sin evaluación de calibración.',
          'El conjunto debe ser independiente por paciente y representativo para validar utilidad clínica.',
          'Este registro por sí solo no demuestra validación externa, aprobación ni reproducibilidad del entrenamiento.',
          'No mover umbral usando datos de test; seleccionar en validación y confirmar en test.',
        ],
        'advertencia': 'El registro NO habilita automáticamente el modelo en producción.'
    }
    (output/'expediente_modelo_pendiente.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    guardar_html(output/'comparador_umbrales.html',labels,scores,selected,args.modelo,phase)
    print(f'Comparación generada: {output.resolve()}')
    print(json.dumps({'fase':phase,'umbral':selected,'sensibilidad':current['sensibilidad'],'especificidad':current['especificidad'],'fn':current['fn'],'reproducible_misma_inferencia': repeat['coincide'] if repeat else 'NO_COMPROBADO','aprobacion':'PENDIENTE_REVISION'},indent=2))


def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('--datos',required=True,help='CSV, JSON o NPZ con y_true, y_prob')
    parser.add_argument('--fase',required=True,choices=['validation','test'])
    parser.add_argument('--umbral',type=float,required=True,help='Umbral elegido de validation, nunca de test')
    parser.add_argument('--modelo',required=True)
    parser.add_argument('--salida',required=True)
    parser.add_argument('--repeticion',help='Segundo archivo de predicciones obtenido de una NUEVA ejecución de inferencia')
    parser.add_argument('--checkpoint',help='Ruta del modelo físico para registrar hash SHA-256')
    parser.add_argument('--responsable',default='No consignado')
    args=parser.parse_args()
    try:
        ejecutar(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))


if __name__=='__main__':
    main()
