"""Revisión técnica documentada de BAL-03 sin despliegue automático.

Las decisiones aprobadas aquí habilitan únicamente PRUEBAS técnicas controladas;
NO son autorización clínica ni sustituyen una validación externa.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
from datetime import datetime, timezone

SALIDA = Path('/datos_radiografias_san_juan_de_dios/04_reportes/evaluacion_final_BAL03')
NOMBRE = 'BAL-03'
MATRICES_ESPERADAS = {
    'validation': {'tn': 485, 'fp': 29, 'fn': 4, 'tp': 41},
    'test': {'tn': 480, 'fp': 35, 'fn': 7, 'tp': 37},
}
ESTADOS = {
    'aprobacion_tecnica': 'APROBADO_TECNICAMENTE_SOLO_PRUEBAS',
    'correcciones': 'REQUIERE_CORRECCIONES',
    'rechazo': 'RECHAZADO',
}


def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open('rb') as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b''):
            digest.update(bloque)
    return digest.hexdigest()


def guardar_json_atomico(ruta: Path, data: dict) -> None:
    temporal = ruta.with_name(ruta.name + '.tmp')
    with temporal.open('w', encoding='utf-8', newline='\n') as archivo:
        json.dump(data, archivo, ensure_ascii=False, indent=2)
        archivo.write('\n')
        archivo.flush()
        os.fsync(archivo.fileno())
    temporal.replace(ruta)


def validar_expediente(doc: dict, *, verificar_archivos: bool = True) -> list[str]:
    errores = []
    if doc.get('experimento') != NOMBRE:
        errores.append('El experimento no es BAL-03')
    if doc.get('estado_revision') != 'PENDIENTE_REVISION':
        errores.append('El expediente original no está pendiente de revisión')
    if doc.get('autorizado_despliegue') is not False:
        errores.append('El expediente original no mantiene el despliegue deshabilitado')
    umbral = doc.get('umbral_checkpoint')
    if not isinstance(umbral, (float, int)) or not math.isclose(umbral, 0.21, abs_tol=1e-8):
        errores.append('El umbral no coincide con BAL-03 (0,21)')
    hashes = []
    if isinstance(doc.get('modelo'), dict):
        hashes.append(('modelo', doc['modelo']))
    else:
        errores.append('Falta referencia del checkpoint')
    partes = doc.get('particiones') or {}
    for fase, matriz in MATRICES_ESPERADAS.items():
        p = partes.get(fase)
        if not isinstance(p, dict):
            errores.append(f'Falta partición {fase}')
            continue
        if not p.get('correcto') or not p.get('coincide_historico') or not p.get('coincide_repeticion') or not (p.get('repeticion') or {}).get('repeticion_consistente'):
            errores.append(f'La evaluación de {fase} no demuestra concordancia/repetición')
        if p.get('n') != 559:
            errores.append(f'Cantidad inesperada de imágenes en {fase}')
        m = p.get('metricas') or {}
        for clave, esperado in matriz.items():
            if m.get(clave) != esperado:
                errores.append(f'Matriz {fase}: {clave} debe ser {esperado}')
        if not isinstance(p.get('umbral'), (int, float)) or not math.isclose(p['umbral'], 0.21, abs_tol=1e-8):
            errores.append(f'Umbral incorrecto en {fase}')
        for clave in ('csv', 'reporte_historico', 'predicciones_run1', 'predicciones_run2'):
            if isinstance(p.get(clave), dict):
                hashes.append((f'{fase}.{clave}', p[clave]))
            else:
                errores.append(f'Falta archivo fuente {fase}.{clave}')
    if verificar_archivos:
        for nombre, elemento in hashes:
            ruta = Path(elemento.get('ruta_local') or '')
            esperado = elemento.get('sha256')
            if not ruta.is_file() or not esperado or sha256_archivo(ruta) != esperado:
                errores.append(f'Hash ausente o inconsistente: {nombre}')
    return errores


def datos_html(doc: dict, revision: dict) -> str:
    fila = []
    for fase in ('validation', 'test'):
        p = doc['particiones'][fase]
        m = p['metricas']
        fila.append('<tr><td>'+html.escape(fase)+'</td><td>'+str(p['n'])+'</td><td>'+f"{m['sensibilidad']*100:.2f}%"+'</td><td>'+f"{m['especificidad']*100:.2f}%"+'</td><td>'+str(m['fn'])+'</td><td>'+str(m['fp'])+'</td></tr>')
    limites = ''.join(f'<li>{html.escape(str(x))}</li>' for x in doc.get('limitaciones', []))
    registro = revision.get('ultima_decision')
    info = '<p>Pendiente de decisión y responsable autorizado.</p>'
    if registro:
        info = '<p><b>Responsable:</b> '+html.escape(registro['responsable'])+'<br><b>Fecha UTC:</b> '+html.escape(registro['fecha_utc'])+'<br><b>Motivo:</b> '+html.escape(registro['motivo'])+'</p>'
    ck = doc['modelo']['sha256']
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Revisión técnica BAL-03</title><style>body{{font:16px system-ui,sans-serif;background:#f3f6fa;color:#16253a;max-width:900px;margin:30px auto;padding:0 18px}}main{{background:white;padding:26px;border-radius:14px}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;padding:10px;border-bottom:1px solid #cfd8e3}}a:focus{{outline:3px solid #176be8}}.warn{{border-left:4px solid #b86d00;padding:12px;background:#fff6e5}}code{{overflow-wrap:anywhere}}a{{color:#1256af}}</style></head><body><main><h1>Revisión del modelo BAL-03</h1><p><b>Versión:</b> {html.escape(str(doc.get('version_candidata')))} · <b>Umbral:</b> 0,21 · <b>Estado:</b> {html.escape(revision['estado'])}</p><p><b>Checkpoint SHA-256:</b> <code>{html.escape(ck)}</code></p><h2>Métricas reproducidas</h2><table><thead><tr><th>Conjunto</th><th>Imágenes</th><th>Sensibilidad</th><th>Especificidad</th><th>FN</th><th>FP</th></tr></thead><tbody>{''.join(fila)}</tbody></table><h2>Curvas de umbral</h2><p><a href="validation/comparador_umbrales.html">Comparador de validación</a> · <a href="test/comparador_umbrales.html">Evaluación TEST (umbral bloqueado)</a></p><h2>Decisión registrada</h2>{info}<h2>Alcance y limitaciones</h2><ul>{limites}</ul><p class="warn"><b>Limitación importante:</b> En TEST se registraron 7 falsos negativos de 44 positivos. Este expediente no certifica seguridad clínica, calibración, independencia entre pacientes ni localización Grad-CAM. Una aprobación técnica solo habilita pruebas controladas, no uso clínico.</p><p><b>Despliegue clínico:</b> No autorizado.</p></main></body></html>'''


def resolver_revision(expediente: Path, salida: Path, decision: str | None, responsable: str | None, motivo: str | None) -> dict:
    doc = json.loads(expediente.read_text(encoding='utf-8'))
    problemas = validar_expediente(doc)
    if problemas:
        raise ValueError('No se puede preparar/registrar revisión:\n- ' + '\n- '.join(problemas))
    salida.mkdir(parents=True, exist_ok=True)
    actual_path = salida/'revision_BAL03.json'
    exp_hash = sha256_archivo(expediente)
    revision = {'modelo': NOMBRE, 'version': doc['version_candidata'], 'checkpoint_sha256': doc['modelo']['sha256'],
                'expediente_sha256': exp_hash, 'umbral': doc['umbral_checkpoint'], 'estado': 'PENDIENTE_APROBACION',
                'ultima_decision': None, 'autorizado_despliegue_clinico': False, 'desplegado': False,
                'advertencia': 'Aprobación técnica para pruebas controladas no constituye validación clínica.'}
    if actual_path.is_file():
        actual = json.loads(actual_path.read_text(encoding='utf-8'))
        if actual.get('expediente_sha256') != exp_hash:
            raise ValueError('El expediente cambió después de la revisión inicial. Requiere expediente nuevo; no sobrescribir decisión anterior.')
        revision = actual
    if decision:
        if revision.get('ultima_decision'):
            raise ValueError('La revisión ya tiene decisión. Se requiere nueva versión/expediente para volver a decidir.')
        if not responsable or len(responsable.strip()) < 5 or responsable.strip().lower() in ('pendiente', 'no consignado', 'admin'):
            raise ValueError('Indique nombre completo del responsable autorizado (mínimo 5 caracteres).')
        if not motivo or len(motivo.strip()) < 15:
            raise ValueError('Registre un motivo razonado de al menos 15 caracteres, incluyendo limitaciones.')
        if decision not in ESTADOS:
            raise ValueError('Decisión no reconocida')
        revision['estado'] = ESTADOS[decision]
        revision['ultima_decision'] = {'fecha_utc': datetime.now(timezone.utc).isoformat(),
                                       'responsable': responsable.strip(), 'motivo': motivo.strip(),
                                       'tipo': decision}
        # La aprobación solo queda registrada para pruebas técnicas; nunca cambia la app clínica.
    guardar_json_atomico(actual_path, revision)
    (salida/'revision_BAL03.html').write_text(datos_html(doc, revision), encoding='utf-8')
    return revision


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--expediente', type=Path, default=SALIDA/'expediente_tecnico_BAL03.json')
    p.add_argument('--salida', type=Path, default=SALIDA)
    p.add_argument('--decision', choices=tuple(ESTADOS))
    p.add_argument('--responsable')
    p.add_argument('--motivo')
    a = p.parse_args()
    try:
        resultado = resolver_revision(a.expediente, a.salida, a.decision, a.responsable, a.motivo)
    except (ValueError, KeyError, OSError, TypeError) as error:
        p.error(str(error))
    print('Revisión:', a.salida/'revision_BAL03.json')
    print('Vista:', a.salida/'revision_BAL03.html')
    print('Estado:', resultado['estado'])
    print('Despliegue clínico: NO AUTORIZADO | Modelo actual sin cambios')


if __name__ == '__main__':
    main()
