"""Read-only pure-function probes, with bytecode generation disabled by invocation."""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'pilots/anomalon_woland'
out = []
methods = {46:'get_core', 47:'dependency', 48:'evaluate', 49:'replay', 50:'render'}
for i in range(46,51):
    path = BASE / f'pilot_{i:07d}' / 'run.py'
    try:
        spec = importlib.util.spec_from_file_location(f'triage_pilot_{i}', path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)
        result = getattr(mod, methods[i])() if i < 48 else getattr(mod, methods[i])(mod.default_job())
        data = result.model_dump() if hasattr(result, 'model_dump') else result
        out.append({'pilot':i, 'outcome':'returned', 'status':data.get('status'),
                    'provider_calls':data.get('provider_calls',data.get('model_calls')), 'differs':data.get('differs'), 'answer':data.get('answer')})
    except Exception as error:
        out.append({'pilot':i,'outcome':'raised','error_type':type(error).__name__, 'reason':str(error)})
Path(__file__).with_suffix('.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
