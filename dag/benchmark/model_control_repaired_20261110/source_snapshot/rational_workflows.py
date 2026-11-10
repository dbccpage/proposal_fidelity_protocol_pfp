"""Concrete limited adaptations of R05-I02, plus two mechanism ablations.

These specifications pin visibility, checker bytes, caps and schemas. They do
not claim to implement every query kind or any native OPERADS/PFP proof rule.
"""
from pathlib import Path
import hashlib

from rational_panel import CONTRACT, CONTRACT_SHA256, fixed_panel


HERE = Path(__file__).resolve().parent
SOLVE = (
    'Solve ALL parts of the unchanged original task, including conventions and exceptional cases. '
    'Return one strict JSON object under candidate_grammar from the supplied public contract; no Markdown fences. '
    'Put the complete mathematical solution in answer_text. Add only useful, accurately encoded claims in the allowed '
    'rational language; use unsupported records for mathematics outside it. Claims may use only the five public '
    'variables. Do not introduce substitute variable meanings, remove assumptions, hide an antecedent, or call finite '
    'tests proofs. Use the exact supplied seed_sha256 and contract_sha256. Empty evidence cannot certify your answer.'
)
CHALLENGE = (
    'Design at most twelve rational-substitution challenges for the unchanged original task using the supplied '
    'public contract. Return one strict JSON object under panel_grammar; no Markdown fences. Target public obligation '
    'IDs, include all five variable assignments, and respect t>=0 and beta>=0. Include boundary and non-boundary '
    'cases. Provide tests, not a solution or verdict; expected answers and executable code are forbidden. '
    'Use the exact supplied seed_sha256 and contract_sha256.'
)


def specification(visibility, source_idea):
    stages = [{'id': 'solve', 'instruction': SOLVE, 'max_output_tokens': 3000, 'visible_artifacts': []}]
    if visibility != 'fixed':
        stages.append({'id': 'challenge', 'instruction': CHALLENGE, 'max_output_tokens': 1500,
                       'visible_artifacts': ['solve'] if visibility == 'visible' else []})
    return {
        'version': '1.0', 'source_idea': source_idea, 'adaptation': 'rational_substitution_only',
        'visibility': visibility, 'stages': stages, 'contract': CONTRACT, 'contract_sha256': CONTRACT_SHA256,
        'host_action': 'Freeze all returned artifacts; check exact rational witnesses; retain the complete original solver answer without repair.',
        'selection': 'solve.answer_text if the full envelope is valid, otherwise the original raw solver text with an artifact error',
        'execution': 'Serial dispatch, one aggregate run ledger, no retries. A failed admission or ambiguous charge stops further dispatch.',
        'source_pins': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                        for name in ('rational_panel.py', 'rational_workflows.py', 'reference_runner.py',
                                     'live_campaign.py', 'budget_ledger.py', 'campaign_ledger.py', 'openrouter_provider.py')},
        'scope': 'A bounded adaptation, not full implementation of R05-I02; semantic alignment, analytic identities, prerequisite queries and native system bindings remain OPEN.',
    }


EXPERIMENTS = {
    'rational_blind_panel_v1': specification('blind', 'R05-I02'),
    'rational_visible_panel_v1': specification('visible', 'R05-I02:visibility-ablation'),
    'rational_fixed_panel_v1': specification('fixed', 'R05-I02:deterministic-panel-ablation'),
}

# An exploratory repair after the first live pilot. Keep v1 instructions intact
# so its observed failures remain reproducible; this is a revision, not a new
# mathematical mechanism. No reference-answer content enters this instruction.
EXPERIMENTS['rational_fixed_panel_v2'] = specification('fixed', 'R05-I02:contract-repair')
EXPERIMENTS['rational_fixed_panel_v2']['version'] = '2.0'
EXPERIMENTS['rational_fixed_panel_v2']['stages'][0]['instruction'] = (
    'Solve ALL parts of the unchanged task in one compact, self-contained answer. '
    'Your entire response must be one JSON object with EXACTLY these five TOP-LEVEL keys: '
    'schema_version, seed_sha256, contract_sha256, answer_text, claims. '
    'Do NOT wrap it inside candidate_grammar, candidate, or any other object. '
    'schema_version must be the string 1.0; copy both hashes exactly from the public context. '
    'answer_text must contain your complete solution, including every requested result, derivation, '
    'exceptional case and independent check. Budget about 2000 tokens for this text; use compact '
    'plain-text mathematical notation, no introduction or repeated question, and cover every part '
    'before expanding explanations. Escape all strings as valid JSON; avoid LaTeX backslashes. '
    'claims must be a JSON list of at most five records from the supplied candidate grammar. '
    'Encode useful equalities only when they fit the exact rational language faithfully; use '
    'unsupported records for other mathematics. Do not invent variable meanings or irrelevant '
    'identities to obtain passing checks. Empty or unsupported evidence cannot certify the answer. '
    'Finish and close the JSON within the 3000-token total output ceiling. No Markdown fences.'
)


def public_context(seed_sha256):
    return {'seed_sha256': seed_sha256, 'contract_sha256': CONTRACT_SHA256, 'public_contract': CONTRACT}


def panel_for(plan, responses, seed_sha256, serialize):
    if EXPERIMENTS[plan]['visibility'] == 'fixed':
        return serialize(fixed_panel(seed_sha256)).decode('utf-8')
    return responses.get('challenge')
