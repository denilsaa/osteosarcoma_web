import unittest
import importlib.util
from pathlib import Path
import tempfile
import json
import hashlib

PATH = Path(__file__).resolve().parents[1] / 'revisar_aprobacion_BAL03.py'
spec = importlib.util.spec_from_file_location('revision_mod', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class RevisionTests(unittest.TestCase):
    def fixture(self, root):
        root = Path(root)
        filepaths = []
        def ref(name):
            p = root/name
            p.write_text('evidencia estable', encoding='utf-8')
            filepaths.append(p)
            return {'ruta_local': str(p), 'sha256': mod.sha256_archivo(p)}
        d = {'experimento': 'BAL-03', 'estado_revision': 'PENDIENTE_REVISION', 'autorizado_despliegue': False,
             'umbral_checkpoint': 0.21000000000000002, 'version_candidata': 'BAL-03-candidata-1',
             'modelo': ref('modelo.pt'), 'limitaciones': ['No diagnóstico definitivo'], 'particiones': {}}
        for fase, matriz in mod.MATRICES_ESPERADAS.items():
            d['particiones'][fase] = {
                'n': 559, 'umbral': 0.21, 'correcto': True, 'coincide_historico': True,
                'coincide_repeticion': True, 'repeticion': {'repeticion_consistente': True},
                'metricas': {**matriz, 'sensibilidad': matriz['tp']/(matriz['tp']+matriz['fn']),
                            'especificidad': matriz['tn']/(matriz['tn']+matriz['fp'])},
                **{k: ref(f'{fase}_{k}.npz') for k in ('csv', 'reporte_historico', 'predicciones_run1', 'predicciones_run2')}
            }
        expediente = root/'expediente_tecnico_BAL03.json'
        expediente.write_text(json.dumps(d), encoding='utf-8')
        return expediente, d

    def test_verificar_expediente_completo(self):
        with tempfile.TemporaryDirectory() as t:
            _, d = self.fixture(t)
            self.assertEqual(mod.validar_expediente(d), [])

    def test_bloquear_matriz_incorrecta(self):
        with tempfile.TemporaryDirectory() as t:
            _, d = self.fixture(t)
            d['particiones']['test']['metricas']['fn'] = 5
            self.assertIn('Matriz test: fn debe ser 7', mod.validar_expediente(d))

    def test_bloquear_checkpoint_modificado(self):
        with tempfile.TemporaryDirectory() as t:
            _, d = self.fixture(t)
            Path(d['modelo']['ruta_local']).write_text('manipulado', encoding='utf-8')
            self.assertIn('Hash ausente o inconsistente: modelo', mod.validar_expediente(d))

    def test_revision_pendiente_y_decision(self):
        with tempfile.TemporaryDirectory() as t:
            expediente, _ = self.fixture(t)
            r = mod.resolver_revision(expediente, Path(t), None, None, None)
            self.assertEqual(r['estado'], 'PENDIENTE_APROBACION')
            self.assertFalse(r['autorizado_despliegue_clinico'])
            self.assertTrue((Path(t)/'revision_BAL03.html').is_file())
            r = mod.resolver_revision(expediente, Path(t), 'aprobacion_tecnica', 'Responsable Técnico', 'Uso restringido a ensayos; pendiente validación externa.')
            self.assertEqual(r['estado'], 'APROBADO_TECNICAMENTE_SOLO_PRUEBAS')
            self.assertFalse(r['autorizado_despliegue_clinico'])
            with self.assertRaisesRegex(ValueError, 'ya tiene decisión'):
                mod.resolver_revision(expediente, Path(t), 'rechazo', 'Responsable Técnico', 'Hay una nueva discrepancia documental.')

    def test_exige_responsable_y_motivo(self):
        with tempfile.TemporaryDirectory() as t:
            expediente, _ = self.fixture(t)
            with self.assertRaisesRegex(ValueError, 'responsable autorizado'):
                mod.resolver_revision(expediente, Path(t), 'aprobacion_tecnica', 'admin', 'Motivo aceptable y suficientemente razonado.')

    def test_no_se_sobrescribe_si_cambio_fuente(self):
        with tempfile.TemporaryDirectory() as t:
            expediente, _ = self.fixture(t)
            mod.resolver_revision(expediente, Path(t), None, None, None)
            expediente.write_text(expediente.read_text(encoding='utf-8')+'\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'cambió después'):
                mod.resolver_revision(expediente, Path(t), None, None, None)


if __name__ == '__main__':
    unittest.main()
