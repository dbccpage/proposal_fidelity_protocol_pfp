"""Isolated obstruction-path probe; a stub terminalizer is disclosed explicitly."""
from pathlib import Path
from fractions import Fraction
from types import SimpleNamespace
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from pfp.use_cases.detector_adequacy import detectors

def main():
    missing = not (ROOT / detectors.PI_RELATIVE_PATH).is_file()
    saved_module = detectors._PI_MODULE
    name = 'audit_stub_extractor'
    edge = ('a', 'b')
    detectors._PI_MODULE = SimpleNamespace(
        CarrierGraph=SimpleNamespace(create=lambda vertices, edges: (vertices, edges)),
        TraceValidator=SimpleNamespace(validate_trace=lambda graph, omega: SimpleNamespace(
            diagnostics={'certified': True}, status='obstruction', phi_1=Fraction(1), dual_witness={edge: Fraction(1)})),
        STATUS_EXACT='exact', STATUS_OBSTRUCTION='obstruction')
    detectors.EXTRACTORS[name] = lambda trace: (['a', 'b'], [edge], {edge: Fraction(1)}, {edge: 's1'})
    try:
        detectors.run_detector(name, {})
        result = {'status': 'unexpected_success'}
    except Exception as exc:
        result = {'status': 'reproduced', 'exception': type(exc).__name__, 'message': str(exc)}
        assert isinstance(exc, NameError) and 'core' in str(exc)
    finally:
        detectors._PI_MODULE = saved_module
        del detectors.EXTRACTORS[name]
    report = {'source_commit': '8050c66900899771766f33e8f5fdd200b7dd9120', 'status': 'bounded_detector_source_review',
        'claims': [], 'findings': [
            {'id': 'DETECTOR-MISSING-OWNER', 'priority': 'P1', 'path': 'pfp/use_cases/detector_adequacy/detectors.py', 'lines': [39, 68], 'claim': 'The pinned terminalizer path is absent from this checkout, so the current adequacy battery fails before detector execution.', 'reproduced': missing},
            {'id': 'DETECTOR-UNDEFINED-CORE', 'priority': 'P1', 'path': 'pfp/use_cases/detector_adequacy/detectors.py', 'lines': [319, 323], 'claim': 'The obstruction branch iterates core, which is never defined. If the terminalizer returns obstruction, this path raises NameError instead of producing a RED witness.', 'probe': result, 'scope': 'Isolated run_detector control path with a disclosed stub terminalizer; the absent real terminalizer was not substituted in production.'},
        ],
        'validation': [{'command': '.venv/Scripts/python.exe -X utf8 -m pytest pfp/tests/test_detector_adequacy_battery.py -q -p no:cacheprovider --maxfail=1 --tb=short', 'result': '1 passed, 1 failed; stopped at missing terminalizer FileNotFoundError'}, {'probe': result}],
        'file_reviews': [], 'remaining_work': ['Review historical terminalizer relocation and locked source custody before any repair or live adequacy inference.']}
    notes = {
        'pfp/use_cases/detector_adequacy/detectors.py': 'Full source: rational step relations, lenient/strict extraction, forest and separate-triangle diagnostics. The forest premise needs an acyclic trace; first-citation extraction alone does not establish it for arbitrary cyclic input. Independently observed missing terminalizer and undefined obstruction variable. Finite checks do not decide arbitrary reasoning truth.',
        'pfp/tests/test_detector_adequacy_battery.py': 'Full source: finite generated positive/mutant controls and known blind-spot assertions. One quantile test passes; detector run fails at absent terminalizer. The final LGGR test imports a separately owned adversary package and was not reached; no complete battery success claimed.',
    }
    for path, note in notes.items():
        data = (ROOT / path).read_bytes()
        report['file_reviews'].append({'path': path, 'sha256': hashlib.sha256(data).hexdigest(), 'full_source_read': True, 'assessment': note, 'reviewed_lines': [[1, len(data.decode().splitlines())]]})
    (ROOT / 'dag/reviews/additional_detector.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'missing_terminalizer': missing, 'isolated_obstruction_probe': result}))

if __name__ == '__main__':
    main()
