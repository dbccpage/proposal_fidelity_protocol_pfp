"""Checked public-input representation, with an ungated decomposition ablation."""
from pathlib import Path
import hashlib
from hamiltonian_artifact import public_contract

HERE = Path(__file__).resolve().parent
MATRIX = (
    'Construct ONLY the coefficient matrices of the given Hamiltonian in the fixed basis '
    '|00>, |01>, |10>, |11>. Return one strict JSON object with exactly these root fields: '
    'schema_version, seed_sha256, coefficient_matrices. Use schema_version "1.0" and '
    'the supplied seed hash. coefficient_matrices has exactly J, Delta, K, each a 4-by-4 '
    'matrix of canonical reduced rational strings n/d, including 0/1. These are the '
    'coefficients for ALL real parameter values, not the Hamiltonian at one point. '
    'Derive tensor products using the given basis convention. No prose, wrappers or Markdown. '
    'Do not solve the remaining parts yet. Fit the JSON within 1200 output tokens.'
)
REPAIR = (
    MATRIX + ' Correct the preceding artifact using the supplied public-input checker feedback. '
    'Return a complete replacement object. This is the only allowed repair attempt.'
)
SOLVE = (
    'Solve ALL five parts of the unchanged original task. A proposed Hamiltonian representation '
    'is provided as intermediate work; use it consistently and verify its use. Return a complete '
    'self-contained solution in ordinary text, not JSON. Budget your answer to finish within '
    '4000 output tokens: give every requested result, exceptional case and essential derivation '
    'before expanding explanations. Avoid reprinting elementary matrices or the question. '
    'Distinguish algebraic identities from numerical checks and state any unresolved issue.'
)


def specification(checked, host_matrix=False):
    stages = [{'id': 'matrix', 'instruction': MATRIX, 'max_output_tokens': 1200, 'visible_artifacts': []}]
    if checked:
        stages.append({'id': 'matrix_repair', 'instruction': REPAIR, 'max_output_tokens': 1200,
                       'visible_artifacts': ['matrix', 'matrix_feedback']})
    stages.append({'id': 'solve', 'instruction': SOLVE, 'max_output_tokens': 4000,
                   'visible_artifacts': ['matrix_context']})
    if host_matrix:
        stages = [stage for stage in stages if stage['id'] == 'solve']
    names = ('hamiltonian_artifact.py', 'hamiltonian_workflows.py', 'reference_runner.py',
             'budget_ledger.py', 'campaign_ledger.py', 'openrouter_provider.py', 'live_campaign.py')
    return {'version': '1.0', 'checked': checked, 'host_matrix': host_matrix, 'stages': stages,
            'source_idea': 'R01-I03',
            'source_pins': {name: hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in names},
            'contract_factory': 'hamiltonian_artifact.public_contract',
            'scope': 'Exact equality of three rational coefficient matrices against public Pauli tensor products. '
                     'No spectral, dynamical, thermal or final-answer certificate; no private evaluator input.',
            'repair_policy': ('No proposal or repair call; use the public-input host calculation.' if host_matrix else
                              'At most one matrix correction when the first artifact fails; synthesis requires acceptance.' if checked else
                              'No gating or repair; checker observations withheld from solver and used only in host evidence.')}


MATRIX_PLANS = {
    'hamiltonian_checked_v1': specification(True),
    'hamiltonian_ungated_v1': specification(False),
    'hamiltonian_host_matrix_v1': specification(True, host_matrix=True),
}
