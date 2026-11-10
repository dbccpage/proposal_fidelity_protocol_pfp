"""Run bounded synthetic tests and record public implementation hashes only."""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys

from reference_runner import HERE, PLANS, canonical, sha
from rational_workflows import EXPERIMENTS
from rational_panel import CONTRACT_SHA256


def main():
    root = HERE.parents[1]
    tests = ['test_rational_panel.py', 'test_rational_workflows.py', 'test_reference_runner.py',
             'test_live_admission.py', 'test_budget_ledger.py', 'test_summarize_runs.py']
    command = [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', *['dag/benchmark/' + name for name in tests]]
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, encoding='utf-8', timeout=60)
    output = completed.stdout + completed.stderr
    passed = re.search(r'(\d+) passed', output)
    implementation = ['rational_panel.py', 'rational_workflows.py', 'reference_runner.py',
                      'live_campaign.py', 'budget_ledger.py', 'campaign_ledger.py',
                      'openrouter_provider.py', 'summarize_runs.py', 'validate_rational_panel.py']
    receipt = {
        'schema_version': '1.0', 'status': 'passed' if completed.returncode == 0 else 'failed',
        'checked_at_utc': datetime.now(timezone.utc).isoformat(),
        'command': command, 'exit_code': completed.returncode, 'output': output,
        'passed': int(passed.group(1)) if passed else None,
        'contract_sha256': CONTRACT_SHA256,
        'plan_sha256': {name: sha(canonical(PLANS[name])) for name in EXPERIMENTS},
        'source_sha256': {name: sha((HERE / name).read_bytes()) for name in implementation + tests},
        'external_provider_requests': 0, 'private_answer_access': False,
        'controls': [
            'Exact false-equality witness versus finite success without universal proof',
            'False antecedents, out-of-domain points, undefined guards and partial expressions',
            'Noncanonical rational/float/Boolean/duplicate-key/binding/extra-field refusals',
            'Unsupported or missing evidence and resource limits remain open',
            'Blind request invariance under candidate changes; visible ablation carries candidate',
            'Complete solver prose retained; critic never replaces it; exact seed present each call',
            'Shared aggregate cap, ambiguous charge hold and no second dispatch after refusal',
            'Synthetic guarded OpenRouter campaign dispatch, usage and durable account settlement',
            'Host artifact errors/refutations remain separate from post-freeze accuracy',
        ],
        'limits': [
            'Synthetic tests are not a live-provider or model-performance observation.',
            'Finite controls do not prove checker completeness or semantic adequacy for QM.',
            'The implementation covers rational substitutions only, not all R05-I02 query kinds.',
            'No full repository test-suite claim or private evaluator execution.',
        ],
    }
    (HERE / 'rational_panel_validation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: receipt[key] for key in ('status', 'passed', 'exit_code', 'external_provider_requests')}))
    return completed.returncode


if __name__ == '__main__':
    raise SystemExit(main())
