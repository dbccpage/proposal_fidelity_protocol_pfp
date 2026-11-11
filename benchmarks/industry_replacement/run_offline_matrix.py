"""Offline fault-injection and policy simulation over the 4 tasks x 4 arms.

The "solver" is a deterministic fixture policy, not a model: for every task it
emits each declared candidate tier (faithful, verbose, format-quirky, contract
or table drift, injection-vulnerable, truncated, subtly buggy) plus one
exposure slot. Declared solver assumptions (``POLICIES``):

* follows_context_rules (primary): a solver whose context contains a skill
  that conflicts with the task emits the ``rule_poisoned`` tier in the exposure
  slot; a solver that sees the AGENTS.md "no f-strings" rule writes the
  compliant form where one exists.
* ignores_context_rules (sensitivity): neither effect.
* A review or repair call fixes a tier only if its defect is visible from the
  public task or host evidence (``REPAIRABLE``); hidden semantic defects
  survive. The same map is used for the industry reviewer and the PFP repair.

Phases: calibration on public host checks only -> PCIV genome selection ->
frozen evaluation runs -> delivery digests frozen -> sealed grading. The
output is labelled ``offline_policy_verification_not_live_llm_evidence``.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE.parent.parent)]
import pfp_core  # noqa: E402,F401
from pfp_core import civilization as civ  # noqa: E402
from pfp_core.fidelity import sha256_hex  # noqa: E402
from pfp_core.immunity import AntibodyRegistry  # noqa: E402
from pfp_core.operad_pipe import TypedOp, quotient_workflows  # noqa: E402

import arms  # noqa: E402
from tasks.common import extract_code, prewarm  # noqa: E402

POLICIES = ('follows_context_rules', 'ignores_context_rules')
STATUS = 'offline_policy_verification_not_live_llm_evidence'
GENERATE = TypedOp('generate', 'Contract', 'Code', 'generate', prompt_digest='task')
CHECK = TypedOp('host_check', 'Code', 'Code', 'check', checker_id='public_check')


class FixtureSolver:
    """Deterministic stand-in for a model call; see the module docstring."""

    def __init__(self, task, tier: str, policy: str):
        self.task, self.tier, self.policy = task, tier, policy

    def upper_quote(self, stage, request):
        return arms.simulated_quote(request)

    def complete(self, stage, request):
        if stage != 'draft' and self.tier in self.task.REPAIRABLE:
            self.tier = 'faithful'
        text = self.task.CANDIDATES[self.tier]
        sees_rules = any(arms.STACK.rules_text in m['content'] for m in request['messages'])
        if self.policy == 'follows_context_rules' and sees_rules:
            text = getattr(self.task, 'RULE_COMPLIANT', {}).get(self.tier, text)
        return arms.simulated_usage(request, text)


def context_skills(arm: str, selected) -> list:
    if arm.startswith('industry_'):
        return list(arms.STACK.skills)
    return list(selected) if arm == 'pfp_eis_pciv_regulated' else []


def samples(task, arm, selected, policy) -> list[str]:
    base = [t for t in task.CANDIDATES if t != 'rule_poisoned']
    conflicting = getattr(task, 'CONFLICTING_SKILLS', set())
    exposed = any(s.name in conflicting for s in context_skills(arm, selected))
    return base + ['rule_poisoned' if exposed and policy == 'follows_context_rules' else 'faithful']


def skill_genomes(task) -> tuple[dict, set, dict]:
    """Candidate skill genomes, lineage taint and their trace quotient."""
    by_name = {s.name: s for s in arms.STACK.skills}
    relevant = ['config-migration', 'state-machine-configs']
    dups = ['python-style', 'python-conventions']
    conflicting = arms.conflicting_skills(task)
    genomes = {'host_only': [], 'relevant': relevant, 'relevant+dups': relevant + dups,
               'relevant+dup_one': relevant + dups[:1],
               'all_but_conflicting': [n for n in by_name if n not in conflicting],
               'all_skills': list(by_name), 'relevant+stale': relevant + ['legacy-json-style']}
    lineage = civ.Lineage()
    for parent, child in (('host_only', 'relevant'), ('relevant', 'relevant+dups'), ('relevant', 'relevant+dup_one'),
                          ('relevant+dups', 'all_but_conflicting'), ('all_but_conflicting', 'all_skills'),
                          ('relevant', 'relevant+stale')):
        lineage.derive(parent, child, 'add skills')
    seeds = {g for g, names in genomes.items() if conflicting & set(names)
             and not any(conflicting & set(genomes[e.parent_id]) for e in lineage.graph.edges if e.child_id == g)}
    tainted = lineage.taint(seeds)
    pipelines = {g: [by_name[n].as_op() for n in names] + [GENERATE, CHECK] for g, names in genomes.items()}
    return {g: [by_name[n] for n in names] for g, names in genomes.items()}, tainted, quotient_workflows(pipelines)


def calibrate(task, policy) -> dict:
    """Measure candidates on public host checks only (no sealed information)."""
    genomes, tainted, classes = skill_genomes(task)
    cands = []
    for arm in ('direct_baseline', 'pfp_eis_pciv_regulated'):
        recs = [arms.run_arm(arm, task, FixtureSolver(task, s, policy), s) for s in samples(task, arm, [], policy)]
        passed = sum(1 for r in recs if r.delivered is not None and arms.public_check(task, r.delivered)[2] is None)
        cands.append(civ.Candidate('direct' if arm == 'direct_baseline' else 'host_only', passed, len(recs),
                                   sum(r.budget['spent_microusd'] for r in recs),
                                   sum(r.budget['total_tokens'] for r in recs),
                                   sum(r.budget['provider_wall_ms'] for r in recs), is_baseline=arm == 'direct_baseline'))
    for g, skills in genomes.items():
        if g != 'host_only':  # offline fixtures do not depend on skill content: benefit is unmeasured
            cands.append(civ.Candidate(g, 0, 0, 0, sum(s.as_op().cost_tokens for s in skills), 0, measured=False))
    selection = civ.select(cands, tainted=tainted)
    chosen = selection['Front'][0] if selection['Front'] else 'host_only'
    return {'selection': selection, 'tainted': sorted(tainted), 'chosen_genome': chosen,
            'quotient_classes': sorted(v for v in classes.values() if len(v) > 1),
            'candidates': [{'id': c.genome_id, 'passed': c.passed, 'attempted': c.attempted,
                            'total_tokens': c.total_tokens, 'measured': c.measured} for c in cands],
            '_skills': genomes[chosen]}


_GRADES: dict = {}


def grade_text(task_id: str, text: str) -> dict:
    """Sealed grade, cached by text digest. Called only after deliveries are frozen."""
    from sealed_evaluator.grade import grade  # imported only for the post-freeze phase
    key = (task_id, sha256_hex(text))
    if key not in _GRADES:
        _GRADES[key] = grade(task_id, text)
    return _GRADES[key]


def evaluate(policy: str) -> dict:
    report, frozen = {}, {}
    records = []
    for task in arms.TASKS.values():
        fixtures = list(task.CANDIDATES.values()) + list(getattr(task, 'RULE_COMPLIANT', {}).values())
        prewarm([extract_code(t) for t in fixtures], task.SMOKE)  # public host checks only
        cal = calibrate(task, policy)
        skills = cal.pop('_skills')
        report[task.TASK_ID] = {'calibration': cal, 'killed_guards': [k['rule_id'] for k in arms.screened_guards(task)[1]],
                                'arms': {}}
        for arm in arms.ARMS:
            for s in samples(task, arm, skills, policy):
                rec = arms.run_arm(arm, task, FixtureSolver(task, s, policy), s, skills=skills)
                records.append(rec)
                if rec.delivered is not None:
                    frozen[sha256_hex(rec.delivered)] = (task.TASK_ID, rec.delivered)
    freeze_digest = sha256_hex(json.dumps(sorted(frozen), separators=(',', ':')))
    # ---- deliveries frozen; sealed grading starts here ----
    from sealed_evaluator.grade import prewarm_offline
    for tid in arms.TASKS:
        prewarm_offline(tid, [t for t_id, t in frozen.values() if t_id == tid] +
                        [r.last_text for r in records if r.task_id == tid and r.last_text is not None])
    for d, (tid, text) in sorted(frozen.items()):
        grade_text(tid, text)
    graded_now = len(frozen)

    antibodies = AntibodyRegistry()
    for rec in records:
        g = grade_text(rec.task_id, rec.delivered) if rec.delivered is not None else None
        regulated_refusal = rec.disposition in ('GUARDRAIL_BLOCK', 'HOLD_REFUSED')
        correct_candidate = (regulated_refusal and rec.last_text is not None
                             and grade_text(rec.task_id, rec.last_text)['correct'])
        row = report[rec.task_id]['arms'].setdefault(rec.arm, Counter())
        row['runs'] += 1
        row['delivered_correct'] += bool(g and g['correct'])
        row['delivered_wrong'] += bool(g and not g['correct'])
        row['refused'] += rec.delivered is None
        row['refused_by_budget'] += rec.delivered is None and not regulated_refusal
        row['correct_refusal'] += regulated_refusal and not correct_candidate
        row['false_refusal'] += bool(correct_candidate)
        row['spent_microusd'] += rec.budget['spent_microusd']
        row['total_tokens'] += rec.budget['total_tokens']
        row['provider_wall_ms'] += rec.budget['provider_wall_ms']
        row['calls'] += rec.budget['calls']
        if g and not g['correct']:
            antibodies.observe(f'{rec.task_id}:{rec.sample}', f'{rec.arm}:{rec.sample}', model_id='fixture-solver',
                               scaffold_digest=sha256_hex(rec.task_id), precedent_digest=rec.arm, lineage_root='fixtures')
    for tid, block in report.items():
        cands = [civ.Candidate(a, r['delivered_correct'], r['runs'], r['spent_microusd'], r['total_tokens'],
                               r['provider_wall_ms'], is_baseline=a == 'direct_baseline')
                 for a, r in block['arms'].items()]
        block['arm_selection'] = civ.select(cands)
        block['arms'] = {a: dict(r) for a, r in block['arms'].items()}
    return {'policy': policy, 'freeze_digest': freeze_digest, 'tasks': report,
            'antibody_status': [antibodies.status(p) for p in sorted(antibodies.observations)],
            'deliveries_frozen': graded_now}


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', type=Path, default=HERE / 'offline_matrix_results.json')
    args = ap.parse_args(argv)
    result = {'status': STATUS, 'sim_tariff': arms.SIM_TARIFF, 'arms': list(arms.ARMS),
              'policies': {p: evaluate(p) for p in POLICIES}}
    args.out.write_text(json.dumps(result, indent=1, sort_keys=True, default=str) + '\n', encoding='utf-8', newline='\n')
    return result


if __name__ == '__main__':
    main()
