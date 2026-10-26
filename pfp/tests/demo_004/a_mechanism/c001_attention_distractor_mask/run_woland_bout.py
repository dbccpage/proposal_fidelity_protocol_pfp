"""
run_woland_bout.py -- reference self-consistency bout and four-file run bundle for Challenge C001.

What this bout does, and what it does not do:

1. It generates one integer rank-difference case (seeded), perturbs one relation so that
   the case becomes contradictory, and asks the local reference exact solver for a
   single-edge repair. The host verdict before and after the repair, the signed claim
   sum on the witness cycle, the number of relations the repaired potential violates,
   and the number of invalid mutation certificates the checker rejects are all measured
   in the run and written into the bundle.
2. It exercises only the local reference solver and its checker. No model is evaluated,
   no attention intervention is executed, and nothing here is a Woland verdict: the Woland
   swarm is the only final evaluator. The bout returns ``Err`` unless every check passes;
   on success the label is ``REFERENCE_SELF_CONSISTENT`` with gate scope
   ``REFERENCE_SOLVER_SELF_CHECK``.
3. The 9-dot carrier lift adds a bridge vertex and triangular faces and is recorded on
   the action tape. It changes no original claim and the repair is computed on the
   unlifted system; the lift is not used by the repair.
4. Defect values (Phi_1, Gamma_2) are exact: ``int``, ``fractions.Fraction`` or a
   canonical exact string such as ``"0"``; ``None`` means "not measured". Floats and
   booleans are refused. The DDC letter ``E`` needs a measured Gamma_2 equal to 0.
5. The bundle (novella.md, dda_actions.jsonl, summary.json, receipt.json) is staged
   beside the destination and moved into place with ``os.replace``. An existing run
   folder is never replaced. If writing fails, a ``failure_receipt.json`` is written into
   the staging folder, which is then moved into place. Nothing is deleted.
6. The run store is ``resolve_intelligence_repo_root()``/_intelligence/_woland/runs.

AuthorityEffect: None.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

for _parent in Path(__file__).resolve().parents:
    if (_parent / "omega_engine_projects").exists() and (
        _parent / "omega_engine_providers"
    ).exists():
        if str(_parent) not in sys.path:
            sys.path.insert(0, str(_parent))
        break

from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.case_generator import (  # noqa: E402
    CaseGenerator,
    generate_mutation_cases,
    map_spans_to_token_positions,
)
from omega_engine_projects.mssn_sn_symgam.challenges.a_mechanism.c001_attention_distractor_mask.solver import (  # noqa: E402
    ConstraintSystem,
    format_int,
    host_verdict,
    parse_int_exact,
    solve_single_repair,
    verify_certificate,
)

from omega_engine_operating_system.adapters.intelligence_custody.intelligence_root import (  # noqa: E402
    try_resolve_intelligence_repo_root,
)
from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result  # noqa: E402
from omega_engine_woland.domain.providers.budget import BudgetController  # noqa: E402

# The bout records the legacy Symbol Game gate's label for a distractor span
# (Signal 1) and the carrier's measured contradiction cycle (Signal 2). It is a
# recorded label, not an OEEIS admission: the OEEIS gate's closed registry of host
# danger kinds has no kind for loop curvature, and nothing here masks or refuses on it.
from omega_engine_pfp.domain.immune.danger_gate import (  # noqa: E402
    DangerSeverity,
    Signal1AstMatch,
    Signal2DangerState,
    TwoSignalDangerGate,
)

TASK_KEY = "c001_mechanism_pilot"
RECEIPT_SCHEMA = "omega.woland.skill-run-receipt.v1"
DDC_LETTERS = frozenset({"E", "R", "C", "I", "Λ", "Lambda", "D", "M", "T"})
LOCUS = "omega_engine_projects.mssn_sn_symgam.c001.run_woland_bout"
OBJECTIVE = "Symbol Game Mechanism Challenge C001: Distractor-Key Attention Masking at Task Level"

GATE_SCOPE = "REFERENCE_SOLVER_SELF_CHECK"
TERMINAL_REFERENCE_SELF_CONSISTENT = "REFERENCE_SELF_CONSISTENT"
LABEL_NOTE = (
    "The local reference exact solver and its checker agree on one generated case. "
    "No model was evaluated and this is not a Woland verdict; the Woland swarm is the only final evaluator."
)
RUN_FOLDER_EXISTS = "RUN_FOLDER_EXISTS"
FAILURE_RECEIPT_NAME = "failure_receipt.json"


def exact_defect_value(name: str, value: Any) -> Fraction | None:
    """Return an exact defect value, or None when it was not measured.

    Accepts ``int``, ``Fraction`` and canonical exact strings (``"0"``, ``"-3"``,
    ``"1/2"``). Floats, booleans and non-canonical strings raise ``TypeError``.
    """
    if value is None:
        return None
    if type(value) is int or type(value) is Fraction:
        return Fraction(value)
    if type(value) is str:
        try:
            parsed = Fraction(value)
        except (ValueError, ZeroDivisionError):
            parsed = None
        if parsed is not None and str(parsed) == value:
            return parsed
        raise TypeError(f"{name} string {value!r} is not a canonical exact rational")
    raise TypeError(
        f"{name} must be an exact int, Fraction or canonical exact string, or None when not measured; "
        f"got {type(value).__name__}"
    )


def exact_wire(value: Fraction | int | None) -> str | None:
    """Serialise an exact value as a string ('p/q', integers without a slash); None stays None."""
    return None if value is None else str(Fraction(value))


@dataclass(frozen=True)
class LiftedCarrier:
    """The carrier after the 9-dot lift: original vertices plus a bridge vertex and triangular faces."""

    nodes: tuple[str, ...]
    edges: tuple[tuple[str, str, int], ...]
    claims: dict[tuple[str, str], int]
    faces: tuple[tuple[str, str, str], ...]
    bridge_node: str = "9"


def execute_9dot_gauge_break(
    system: ConstraintSystem,
    phi1: object = None,
    gamma2: object = None,
    *,
    bridge_node: str = "9",
) -> LiftedCarrier:
    """Lift the carrier by adding a bridge vertex and triangular faces.

    For the first two edges (u, v) the lift adds edges (u, bridge) and (v, bridge) with
    claim 0 and the face (u, v, bridge). Every original claim is kept unchanged. The lift
    is combinatorial: it does not repair anything, and the bout computes its repair on
    the original, unlifted system. ``phi1`` and ``gamma2`` are accepted for backward
    compatibility and are not read.
    """
    del phi1, gamma2
    lifted_nodes = tuple(system.items) + (bridge_node,)
    new_edges: list[tuple[str, str, int]] = []
    new_claims: dict[tuple[str, str], int] = dict(system.claims)

    candidate_edges = system.edges[:2] if len(system.edges) >= 2 else system.edges
    for u, v, _w in candidate_edges:
        for cand in ((u, bridge_node, 1), (v, bridge_node, 1)):
            cu, cv, _cw = cand
            if (cu, cv) not in new_claims and (cv, cu) not in new_claims:
                new_edges.append(cand)
                new_claims[(cu, cv)] = 0

    return LiftedCarrier(
        nodes=lifted_nodes,
        edges=tuple(system.edges) + tuple(new_edges),
        claims=new_claims,
        faces=tuple((u, v, bridge_node) for u, v, _w in candidate_edges),
        bridge_node=bridge_node,
    )


def assert_witness_dominance(letter: str, gamma2: object) -> Result[None, Refusal]:
    """Witness dominance: DDC letter 'E' needs a measured, exact Gamma_2 equal to 0.

    Any non-zero Gamma_2 refuses 'E' (no tolerance). An unmeasured Gamma_2 (None) also
    refuses 'E'. A float or boolean Gamma_2 is refused for every letter.
    """
    try:
        g2 = exact_defect_value("gamma2", gamma2)
    except TypeError as exc:
        return Err(Refusal(code="NON_EXACT_DEFECT_VALUE", message=str(exc), locus=LOCUS))
    if letter != "E":
        return Ok(None)
    if g2 is None:
        return Err(
            Refusal(
                code="WITNESS_DOMINANCE_UNMEASURED",
                message="Gamma_2 was not measured; DDC letter 'E' (Exact Repair) needs a measured Gamma_2 = 0",
                locus=LOCUS,
            )
        )
    if g2 != 0:
        return Err(
            Refusal(
                code="WITNESS_DOMINANCE_VIOLATION",
                message=(
                    f"Witness dominance violated: Gamma_2={g2} is not 0; a non-zero Gamma_2 "
                    "strictly prevents DDC letter 'E' (Exact Repair)"
                ),
                locus=LOCUS,
            )
        )
    return Ok(None)


def cycle_signed_sum(system: ConstraintSystem, cycle: Sequence[str]) -> int | None:
    """Exact signed claim sum along a closed walk, or None when it cannot be measured.

    None is returned when the walk is not closed, or when a step is not exactly one
    declared relation (missing, or declared in both directions).
    """
    if len(cycle) < 2 or cycle[0] != cycle[-1]:
        return None
    total = 0
    for a, b in zip(cycle, cycle[1:]):
        forward = (a, b) in system.claims
        backward = (b, a) in system.claims
        if forward == backward:
            return None
        total += system.claims[(a, b)] if forward else -system.claims[(b, a)]
    return total


def count_violated_relations(system: ConstraintSystem, potential: Mapping[str, int]) -> int:
    """Number of relations (u, v) with potential(v) - potential(u) != claim."""
    violated = 0
    for (u, v), claim in system.claims.items():
        if u not in potential or v not in potential or potential[v] - potential[u] != claim:
            violated += 1
    return violated


def measure_repair(
    system: ConstraintSystem,
    repaired_system: ConstraintSystem,
    contradiction_cycle: Sequence[str],
) -> dict[str, Any]:
    """Measure the host verdicts and exact defect values before and after the repair."""
    before_status, _before = host_verdict(system)
    after_status, after_result = host_verdict(repaired_system)
    violated: int | None = None
    if after_status == "CONSISTENT" and isinstance(after_result, dict):
        violated = count_violated_relations(repaired_system, after_result)
    exact_zero = after_status == "CONSISTENT" and violated == 0
    return {
        "host_verdict_before": before_status,
        "host_verdict_after": after_status,
        "cycle_signed_sum_before": cycle_signed_sum(system, contradiction_cycle),
        "cycle_signed_sum_after": cycle_signed_sum(repaired_system, contradiction_cycle),
        "violated_relations_after": violated,
        "phi1_after": Fraction(0) if exact_zero else None,
        "gamma2_after": Fraction(0) if exact_zero else None,
    }


def _shown(value: object) -> str:
    return "not measured" if value is None else str(value)


def render_7act_novella(
    *,
    seed: int,
    system: ConstraintSystem,
    potential: Mapping[str, str],
    perturbed_edge: tuple[str, str],
    original_claim: int,
    perturbed_claim: int,
    repair_edge: tuple[str, str],
    repair_val: str,
    contradiction_cycle: Sequence[str],
    measured: Mapping[str, Any],
    token_positions: Sequence[int],
    danger_decision: str,
    budget_limit_microusd: int,
    budget_spent_microusd: int,
    lifted: LiftedCarrier,
    mutation_outcomes: Sequence[tuple[str, str, bool]],
) -> str:
    """Render novella.md. The scenes are illustrative framing; every number comes from the run."""
    cycle_str = " -> ".join(contradiction_cycle) if contradiction_cycle else "none"
    tok_pos_str = ", ".join(str(p) for p in token_positions)
    killed = sum(1 for _mid, _desc, was_killed in mutation_outcomes if was_killed)
    total = len(mutation_outcomes)
    max_abs_claim = max((abs(c) for c in system.claims.values()), default=0)
    added_edges = len(lifted.edges) - len(system.edges)
    phi1_after = _shown(exact_wire(measured["phi1_after"]))
    gamma2_after = _shown(exact_wire(measured["gamma2_after"]))
    sum_before = _shown(measured["cycle_signed_sum_before"])
    sum_after = _shown(measured["cycle_signed_sum_after"])
    violated_after = _shown(measured["violated_relations_after"])
    mutation_lines = "\n".join(
        f"   - `{mid}` ({desc}): **{'KILLED' if was_killed else 'SURVIVED'}**"
        for mid, desc, was_killed in mutation_outcomes
    )
    potential_lines = "\n".join(f"- $\\phi({k}) = {v}$" for k, v in sorted(potential.items()))

    return f"""# The Master and Margarita at the Terminal Reality Gate: Symbol Game Mechanism Challenge C001

> *«Свежесть бывает только одна — первая, она же и последняя. А если сыр второй свежести, то это означает, что он просто тухлый!»*
> — Воланд, «Мастер и Маргарита»
>
> *«Рукописи не горят.»* — Воланд
> *«Трусость — самый страшный порок.»* — Иешуа Га-Ноцри

> **Scope.** Label `{TERMINAL_REFERENCE_SELF_CONSISTENT}` (scope `{GATE_SCOPE}`). {LABEL_NOTE} No attention intervention was run. The scenes below are illustrative framing; every number in them is taken from the measured values.

## Measured values

| Quantity | Value |
| --- | --- |
| Generator seed | {seed} |
| Items / relations | {len(system.items)} / {len(system.edges)} |
| Largest claim magnitude | {max_abs_claim} |
| Perturbed relation | ({perturbed_edge[0]}, {perturbed_edge[1]}): {original_claim} -> {perturbed_claim} |
| Host verdict before repair | {measured["host_verdict_before"]} |
| Witness cycle | {cycle_str} |
| Signed claim sum on the witness cycle before repair | {sum_before} |
| Repaired relation | ({repair_edge[0]}, {repair_edge[1]}) -> {repair_val} |
| Host verdict after repair | {measured["host_verdict_after"]} |
| Relations violated by the repaired potential | {violated_after} |
| Signed claim sum on the witness cycle after repair | {sum_after} |
| Phi_1 after repair (exact) | {phi1_after} |
| Gamma_2 after repair (exact) | {gamma2_after} |
| Invalid mutation certificates rejected by the checker | {killed} of {total} |
| Distractor token positions | [{tok_pos_str}] |
| Danger gate decision | {danger_decision} |
| Budget controller limit / recorded spend (micro-USD) | {budget_limit_microusd} / {budget_spent_microusd} |
| Lifted vertices / added edges / triangular faces | {len(lifted.nodes)} / {added_edges} / {len(lifted.faces)} |

---

## Dramatis Personae

- **Воланд (Woland)** — Prince of Darkness, Professor of Black Magic, Terminal Reality Gatekeeper.
- **Коровьев-Фагот (Koroviev)** — Ex-choirmaster in cracked pince-nez, structural inquisitor.
- **Бегемот (Begemot)** — Black tomcat with a primus stove, who performs the 9-dot lift.
- **Азазелло (Azazello)** — Fang-toothed demon of direct action, enforcer of boundary cleanliness.
- **Гелла (Hella)** — Crimson-haired maid, auditor of claim hygiene.
- **Мастер (The Master)** — Author of the manuscript, keeper of exact potentials.
- **Маргарита (Margarita)** — Queen of the Ball.
- **Доктор Стравинский (Dr. Stravinsky)** — Chief of the the city clinic, master of loop quarantine.
- **Иван Бездомный (Ivan Bezdomny)** — Reformed poet, witness of the Patriarchs' Ponds encounter.
- **Джереми (Jeremy)** — Systems engineer, keeper of the budget ledger.
- **Людмила (Liudmila)** — Systems stabilizer, keeper of the samovar.

---

## Act I: Patriarchs' Ponds — The Cold Pre-filter

*DDC letter: `C` (context exposure)*
*Host verdict: `{measured["host_verdict_before"]}`; signed claim sum on the witness cycle: `{sum_before}`*

The sunset at Patriarchs' Ponds burned yellow. Woland sat upon a park bench, his chin resting on the poodle-head of his cane.

"Look at this case, Koroviev," Woland remarked. "A rank-difference system with {len(system.items)} items and {len(system.edges)} relations, wrapped in prose. The largest claim magnitude is {max_abs_claim}."

Koroviev adjusted his cracked pince-nez. "Messire, the host solver answers `{measured["host_verdict_before"]}`. And the text carries distractor spans that map to token positions `[{tok_pos_str}]`."

"Then expose the context without pretending it is solved," Woland said. "Write the letter **`C`** on the action tape."

---

## Act II: The Griboedov Restaurant — Cache & Compute Allocation

*DDC letter: `I` (intake)*
*Budget controller limit {budget_limit_microusd} micro-USD; recorded spend {budget_spent_microusd} micro-USD*

At an oak table in the Griboedov, Jeremy and Liudmila reviewed the micro-USD ledger.

"No provider was called in this bout," Jeremy said. "The budget controller's limit is {budget_limit_microusd} micro-USD and it recorded {budget_spent_microusd} micro-USD."

Liudmila poured tea. "Distractor character spans are mapped to token positions by coordinate containment, not by token-ID matching. Intake is admitted under letter **`I`**."

---

## Act III: Dr. Stravinsky's Clinic — Loop Quarantine

*DDC letters: `R` (residual projection), `M` (typed refusal)*
*Witness cycle: `{cycle_str}`; signed claim sum `{sum_before}`; danger gate decision `{danger_decision}`*

"Doctor!" cried Ivan Bezdomny. "Walk along the cycle `{cycle_str}`: the signed sum of the relation claims is {sum_before}, not zero!"

"Then no integer potential satisfies every relation," Dr. Stravinsky said quietly.

Koroviev waved a certificate. "Citizens! Let us declare the solution exact under letter `E`!"

Woland's cane struck the marble floor. "While the cycle sum is not zero, the letter **`E`** is refused. The two-signal danger gate answers **`{danger_decision}`**. Project the residual under **`R`** and refuse the contradictory state under **`M`**."

---

## Act IV: The Variety Theatre — Adversarial Dialectic Performance & 9-Dot Gauge Break

*DDC letter: `Λ` (structural lift)*
*Lifted vertices {len(lifted.nodes)}; added edges {added_edges}; triangular faces {len(lifted.faces)}*

On the stage of the Variety Theatre, Begemot uncorked his primus stove and set bridge vertex **`{lifted.bridge_node}`** into the complex: {added_edges} connecting edges with claim 0 and {len(lifted.faces)} triangular faces `(u, v, {lifted.bridge_node})`.

The lift is recorded on the tape under letter **`Λ`**. It changes no original claim, and the repair in the next act is computed on the original, unlifted system: the lift is not used by it. Eager attention key masking at token positions `[{tok_pos_str}]` is specified for a later neural run and was not executed here.

---

## Act V: Apartment No. 50 — Epistemic Grounding & Refusal Semantics

*DDC letters: `D` (descent with loss ledger), `E` (exact repair)*
*Repaired relation `({repair_edge[0]}, {repair_edge[1]}) -> {repair_val}`; host verdict after repair `{measured["host_verdict_after"]}`; Phi_1 = {phi1_after}, Gamma_2 = {gamma2_after}*

In Apartment No. 50, The Master leaned over the parchment. "The single-edge repair search replaces the claim on `({repair_edge[0]}, {repair_edge[1]})` with `{repair_val}`. The potential is computed by exact integer propagation:"

{potential_lines}

"Verify the descent," Azazello growled. The loss ledger records the replaced relation. Relations violated by this potential: {violated_after}. Signed sum on the old witness cycle: {sum_after}.

"Now Gamma_2 has been measured as {gamma2_after}," Woland said. "Log descent under **`D`** and record exact repair under **`E`**."

---

## Act VI: The Great Ball at Satan's — Truth Firewall & Claim Hygiene

*Invalid mutation certificates rejected by the checker: {killed} of {total}*

At the Great Ball, Hella presented the mutation ledger to Margarita. "The checker was run on {total} invalid certificates:
{mutation_lines}

It rejected {killed} of {total}."

---

## Act VII: Satan's Gate — Terminal Adjudication & The Manuscripts Don't Burn

*DDC letter: `T` (terminalization)*
*Label: `{TERMINAL_REFERENCE_SELF_CONSISTENT}` (scope `{GATE_SCOPE}`)*

Dawn broke over the city from the Sparrow Hills. The Master held his manuscript, unburnt.

"The observables of this run," Woland said. "Phi_1 = {phi1_after}. Gamma_2 = {gamma2_after}. Relations violated: {violated_after}. Invalid certificates rejected: {killed} of {total}. The label is **`{TERMINAL_REFERENCE_SELF_CONSISTENT}`**: the reference solver and its checker agree on this one generated case. It is not a verdict on any model."

Terminal letter **`T`** is inscribed on the tape, and the retinue vanished into the morning sky.
"""


def build_c001_ddc_action_tape(
    system: ConstraintSystem,
    repaired_system: ConstraintSystem,
    contradiction_cycle: list[str],
    repair_edge: tuple[str, str],
    repair_val: str,
    danger_decision: str,
    lifted: LiftedCarrier,
    *,
    budget_spent_microusd: int | None = None,
) -> Result[list[dict[str, Any]], Refusal]:
    """Build the eight DDC steps {C, I, R, M, Λ, D, E, T} from measured values.

    Phi_1 and Gamma_2 are written only where they were measured (as exact strings);
    otherwise they are null. The 'E' step is refused unless Gamma_2 after the repair
    was measured as exactly 0.
    """
    measured = measure_repair(system, repaired_system, contradiction_cycle)
    if measured["host_verdict_before"] != "CONTRADICTION":
        return Err(
            Refusal(
                code="NO_CONTRADICTION_WITNESS",
                message=f"The unrepaired system has host verdict {measured['host_verdict_before']}, not CONTRADICTION",
                locus=LOCUS,
            )
        )
    phi1_after = exact_wire(measured["phi1_after"])
    gamma2_after = exact_wire(measured["gamma2_after"])
    carrier = f"IntegerRankDifferenceSystem(V={len(system.items)}, E={len(system.edges)})"
    claims_preserved = all(lifted.claims.get(k) == c for k, c in system.claims.items())

    steps: list[dict[str, Any]] = [
        {
            "act": "Act I: Patriarchs' Ponds",
            "action_id": "ddc-step-001",
            "actor": "Woland",
            "authority_effect": "None",
            "carrier": carrier,
            "diagnostic_after": "CARRIER_EXPOSED",
            "diagnostic_before": "UNEXPOSED_STATE",
            "gamma2": None,
            "host_verdict": measured["host_verdict_before"],
            "law_enforced": "Law 8: Context Exposure Is Not Repair",
            "letter": "C",
            "name": "Context Exposure",
            "phi1": None,
            "witness": "WIT_COLD_PREFILTER",
        },
        {
            "act": "Act II: Griboedov Restaurant",
            "action_id": "ddc-step-002",
            "actor": "Jeremy & Liudmila",
            "authority_effect": "None",
            "carrier": "LocalExactSolver",
            "diagnostic_after": "BUDGET_CONFIRMED",
            "diagnostic_before": "CARRIER_EXPOSED",
            "gamma2": None,
            "law_enforced": "Law 1: Step Conservation",
            "letter": "I",
            "name": "Compute & Cache Allocation",
            "phi1": None,
            "provider_spend_microusd": budget_spent_microusd,
            "witness": "WIT_BUDGET_HEADROOM",
        },
        {
            "act": "Act III: Dr. Stravinsky's Clinic",
            "action_id": "ddc-step-003",
            "actor": "Dr. Stravinsky",
            "authority_effect": "None",
            "carrier": "ContradictionCycle(" + "->".join(contradiction_cycle) + ")",
            "cycle_signed_sum": exact_wire(measured["cycle_signed_sum_before"]),
            "diagnostic_after": "CYCLE_QUARANTINED",
            "diagnostic_before": "BUDGET_CONFIRMED",
            "gamma2": None,
            "law_enforced": "CODA-19: Residuals Tracked Explicitly",
            "letter": "R",
            "name": "Residual Holonomy Projection",
            "phi1": None,
            "witness": "WIT_HOLONOMY_CURVATURE_OBSTRUCTION",
        },
        {
            "act": "Act III: Dr. Stravinsky's Clinic",
            "action_id": "ddc-step-004",
            "actor": "Woland & Behemoth",
            "authority_effect": "None",
            "carrier": "TwoSignalDangerGate",
            "danger_decision": danger_decision,
            "diagnostic_after": "UNMASKED_PARSE_REFUSED",
            "diagnostic_before": "CYCLE_QUARANTINED",
            "gamma2": None,
            "law_enforced": "Law 3: Refusal Absorption Unless Lifted",
            "letter": "M",
            "name": "Typed Refusal on Cycle Obstruction",
            "phi1": None,
            "refusal_reason": "CYCLE_CURVATURE_OBSTRUCTION_DETECTED",
            "witness": "WIT_DANGER_GATE_QUARANTINE",
        },
        {
            "act": "Act IV: Variety Theatre",
            "action_id": "ddc-step-005",
            "actor": "Behemoth & Margarita",
            "authority_effect": "None",
            "bridge_node": lifted.bridge_node,
            "carrier": f"SimplicialComplex(V={len(lifted.nodes)}, E={len(lifted.edges)}, F={len(lifted.faces)})",
            "diagnostic_after": "9DOT_GAUGE_BREAK_EXECUTED",
            "diagnostic_before": "UNMASKED_PARSE_REFUSED",
            "gamma2": None,
            "law_enforced": "Law 4: Lift Trigger Law",
            "letter": "Λ",
            "lift_preserves_original_claims": claims_preserved,
            "lift_used_by_repair": False,
            "name": "9-Dot Gauge Break",
            "phi1": None,
            "witness": "WIT_SIMPLICIAL_CARRIER_LIFT",
        },
        {
            "act": "Act V: Apartment No. 50",
            "action_id": "ddc-step-006",
            "actor": "The Master & Jeremy",
            "authority_effect": "None",
            "carrier": carrier,
            "diagnostic_after": "DESCENT_WITH_LOSS_LEDGER",
            "diagnostic_before": "9DOT_GAUGE_BREAK_EXECUTED",
            "gamma2": gamma2_after,
            "host_verdict": measured["host_verdict_after"],
            "law_enforced": "Law 6: Descent Requires Loss Ledger",
            "letter": "D",
            "loss_ledger": [
                f"Replaced claim on relation ({repair_edge[0]}, {repair_edge[1]}) with {repair_val}"
            ],
            "name": "Descent to Consistent Subsystem",
            "phi1": phi1_after,
            "witness": "WIT_SINGLE_EDGE_REPAIR",
        },
    ]

    wd_check = assert_witness_dominance("E", gamma2_after)
    if wd_check.is_err:
        return Err(wd_check.unwrap_err())

    steps.append(
        {
            "act": "Act V: Apartment No. 50",
            "action_id": "ddc-step-007",
            "actor": "The Master & Hella",
            "authority_effect": "None",
            "carrier": "CertifiedPotentialSolution",
            "diagnostic_after": "EXACT_POTENTIAL_VERIFIED",
            "diagnostic_before": "DESCENT_WITH_LOSS_LEDGER",
            "gamma2": gamma2_after,
            "law_enforced": "Law 7: Exact Repair Monotonicity",
            "letter": "E",
            "name": "Exact Potential Propagation",
            "phi1": phi1_after,
            "violated_relations": measured["violated_relations_after"],
            "witness": "WIT_EXACT_ZERO_DEFECT",
        }
    )
    steps.append(
        {
            "act": "Act VII: Satan's Gate",
            "action_id": "ddc-step-008",
            "actor": "Woland",
            "authority_effect": "None",
            "carrier": "ReferenceSelfCheck",
            "diagnostic_after": TERMINAL_REFERENCE_SELF_CONSISTENT,
            "diagnostic_before": "EXACT_POTENTIAL_VERIFIED",
            "gamma2": gamma2_after,
            "gate_scope": GATE_SCOPE,
            "law_enforced": "Law 2: Terminal Absorption",
            "letter": "T",
            "name": "Reference Self-Consistency Label",
            "phi1": phi1_after,
            "terminal_verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
            "witness": "WIT_MANUSCRIPTS_DONT_BURN",
        }
    )
    return Ok(steps)


def reference_claim_discipline(
    *,
    seed: int,
    n_items: int,
    n_relations: int,
    measured: Mapping[str, Any],
    mutations_killed: int,
    mutations_total: int,
    budget_spent_microusd: int,
) -> dict[str, Any]:
    """Claim discipline derived from the measured values of this run."""
    phi1_after = _shown(exact_wire(measured["phi1_after"]))
    gamma2_after = _shown(exact_wire(measured["gamma2_after"]))
    return {
        "does_not_support": [
            "Does not claim that attention intervention was executed (no neural model was run in this bout).",
            "Does not claim that attention mass explains correctness across arbitrary transformer architectures.",
            "Does not claim that distractor masking generalizes to hosted APIs that do not expose attention tensors.",
            "Does not claim that toy test outcomes represent mathematical proof of transformer cognition.",
            "Does not support any statement about a model (none was evaluated) and is not a Woland verdict.",
            "Does not claim that the 9-dot carrier lift contributes to the repair; the repair is computed on the unlifted system.",
        ],
        "narrowest_defensible_claim": (
            f"Label {TERMINAL_REFERENCE_SELF_CONSISTENT} on one generated case (seed {seed}, {n_items} items, "
            f"{n_relations} relations): after the reference solver's single-edge repair the host verdict is "
            f"{measured['host_verdict_after']} with Phi_1 = {phi1_after} and Gamma_2 = {gamma2_after}, the checker "
            f"rejected {mutations_killed} of {mutations_total} invalid mutation certificates, and the budget "
            f"controller recorded {budget_spent_microusd} micro-USD of provider spend."
        ),
        "next_test_needed": (
            "Execute neural model inference with eager attention hooks recording output token IDs across "
            "intervention arms, followed by pre-registered McNemar testing on hidden base cases, and have the "
            "Woland swarm evaluate the bound checker receipts."
        ),
        "supports": [
            (
                f"On this generated case the host verdict changed from {measured['host_verdict_before']} to "
                f"{measured['host_verdict_after']} after a single-edge repair, with "
                f"{_shown(measured['violated_relations_after'])} relations violated by the repaired potential."
            ),
            (
                f"The signed claim sum on the witness cycle was {_shown(measured['cycle_signed_sum_before'])} "
                f"before the repair and {_shown(measured['cycle_signed_sum_after'])} after it."
            ),
            f"The certificate checker rejected {mutations_killed} of {mutations_total} invalid mutation certificates.",
        ],
    }


def build_summary_payload(
    task_key: str,
    receipt_id: str,
    objective: str,
    potential: Mapping[str, str],
    repair_edge: tuple[str, str],
    repair_val: str,
    lifted: LiftedCarrier,
    *,
    seed: int,
    measured: Mapping[str, Any],
    claim_discipline: Mapping[str, Any],
    letter_tape: Sequence[str],
    mutations_killed: int,
    mutations_total: int,
    budget_spent_microusd: int,
) -> dict[str, Any]:
    """Compile summary.json from measured values only."""
    return {
        "authority_effect": "None",
        "bridge_node": lifted.bridge_node,
        "claim_discipline": dict(claim_discipline),
        "cycle_signed_sum_after": exact_wire(measured["cycle_signed_sum_after"]),
        "cycle_signed_sum_before": exact_wire(measured["cycle_signed_sum_before"]),
        "dda_actions_supplied": True,
        "defect_count": measured["violated_relations_after"],
        "gamma2": exact_wire(measured["gamma2_after"]),
        "gate_scope": GATE_SCOPE,
        "gauge_break_executed": True,
        "host_verdict_after": measured["host_verdict_after"],
        "host_verdict_before": measured["host_verdict_before"],
        "letter_tape": list(letter_tape),
        "mutation_kill_rate": exact_wire(Fraction(mutations_killed, mutations_total)),
        "mutations_killed": mutations_killed,
        "mutations_total": mutations_total,
        "objective": objective,
        "phi1": exact_wire(measured["phi1_after"]),
        "provider_spend_microusd": budget_spent_microusd,
        "receipt_id": receipt_id,
        "repair_edge": list(repair_edge),
        "repair_value": repair_val,
        "seed": seed,
        "source": "c001_run_woland_bout",
        "status": "COMPLETED",
        "task_key": task_key,
        "terminal_verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
        "verdict_note": LABEL_NOTE,
        "verified_potential": dict(potential),
    }


def _validate_steps(dda_steps: Sequence[Mapping[str, Any]]) -> Result[None, Refusal]:
    """Exact defect values on every step; witness dominance on 'E'. Runs before any disk write."""
    for seq, step in enumerate(dda_steps):
        try:
            exact_defect_value("phi1", step.get("phi1"))
        except TypeError as exc:
            return Err(
                Refusal(code="NON_EXACT_DEFECT_VALUE", message=f"Step {seq}: {exc}", locus=LOCUS)
            )
        check = assert_witness_dominance(str(step.get("letter")), step.get("gamma2"))
        if check.is_err:
            refusal = check.unwrap_err()
            return Err(
                Refusal(code=refusal.code, message=f"Step {seq}: {refusal.message}", locus=LOCUS)
            )
    return Ok(None)


def _dda_tape_bytes(dda_steps: Sequence[Mapping[str, Any]]) -> tuple[bytes, str | None]:
    lines: list[str] = []
    head: str | None = None
    for seq, step in enumerate(dda_steps):
        payload = {k: step[k] for k in sorted(step.keys(), key=lambda s: s.encode("utf-8"))}
        material = json.dumps(
            {"parent_sha256": head, "payload": payload, "sequence": seq},
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        record_sha256 = hashlib.sha256(material).hexdigest()
        lines.append(
            json.dumps(
                {
                    "parent_sha256": head,
                    "payload": payload,
                    "record_sha256": record_sha256,
                    "sequence": seq,
                },
                sort_keys=True,
            )
        )
        head = record_sha256
    return ("\n".join(lines) + ("\n" if lines else "")).encode("utf-8"), head


def _write_failure_receipt(staging_dir: Path, target_dir: Path, error: BaseException) -> None:
    payload = {
        "authority_effect": "None",
        "error_message": str(error),
        "error_type": type(error).__name__,
        "files_present": sorted(p.name for p in staging_dir.iterdir()),
        "status": "RUN_FAILED",
        "target_dir": target_dir.name,
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    (staging_dir / FAILURE_RECEIPT_NAME).write_bytes(
        (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    )


def persist_quad_bundle(
    target_dir: Path,
    task_key: str,
    novella_md: str,
    dda_steps: Sequence[Mapping[str, Any]],
    summary_data: Mapping[str, Any],
    receipt_data: Mapping[str, Any],
    *,
    force: bool = True,
) -> Result[Path, Refusal]:
    """Persist novella.md, dda_actions.jsonl, summary.json and receipt.json (reverse write order).

    The steps are validated before anything is written. An existing ``target_dir`` is
    never replaced: ``force`` is accepted for compatibility and has no effect. The bundle
    is staged in a sibling folder and moved into place with ``os.replace``. If writing
    fails, ``failure_receipt.json`` is written into the staging folder, which is moved
    into place; if that move fails the staging folder stays where it is. Nothing is deleted.
    """
    del force
    del task_key  # historical parameter; the staging prefix is derived from the target name
    validation = _validate_steps(dda_steps)
    if validation.is_err:
        return Err(validation.unwrap_err())

    clean_target = Path(target_dir).resolve()
    if clean_target.exists():
        return Err(
            Refusal(
                code=RUN_FOLDER_EXISTS,
                message=f"Refusing to overwrite existing run folder: {clean_target}",
                locus=LOCUS,
            )
        )
    clean_target.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(
        tempfile.mkdtemp(prefix=f".{clean_target.name}.staging.", dir=clean_target.parent)
    )

    try:
        novella_bytes = (novella_md.rstrip("\n") + "\n").encode("utf-8")
        (staging / "novella.md").write_bytes(novella_bytes)

        dda_bytes, dda_head_sha256 = _dda_tape_bytes(dda_steps)
        (staging / "dda_actions.jsonl").write_bytes(dda_bytes)

        summary_bytes = (json.dumps(dict(summary_data), indent=2, sort_keys=True) + "\n").encode(
            "utf-8"
        )
        (staging / "summary.json").write_bytes(summary_bytes)

        sealed_receipt = dict(receipt_data)
        sealed_receipt["dda_actions_sha256"] = hashlib.sha256(dda_bytes).hexdigest()
        sealed_receipt["dda_head_sha256"] = dda_head_sha256
        sealed_receipt["novella_sha256"] = hashlib.sha256(novella_bytes).hexdigest()
        sealed_receipt["summary_sha256"] = hashlib.sha256(summary_bytes).hexdigest()
        (staging / "receipt.json").write_bytes(
            (json.dumps(sealed_receipt, indent=2, sort_keys=True) + "\n").encode("utf-8")
        )
        os.replace(staging, clean_target)
    except Exception as exc:
        kept_at = clean_target
        try:
            _write_failure_receipt(staging, clean_target, exc)
            os.replace(staging, clean_target)
        except OSError:
            kept_at = staging
        return Err(
            Refusal(
                code="PERSISTENCE_FAILED",
                message=f"Failed to persist the run bundle: {exc!r}; failure receipt kept at {kept_at}",
                locus=LOCUS,
            )
        )
    return Ok(clean_target)


def _default_run_dir() -> Result[Path, Refusal]:
    root = try_resolve_intelligence_repo_root()
    if root.is_err:
        return Err(root.unwrap_err())
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return Ok(root.unwrap() / "_ic/darpa/woland" / "runs" / f"{TASK_KEY}_{stamp}")


def run_woland_c001_bout(
    *,
    custom_run_dir: Path | str | None = None,
    force: bool = True,
    seed: int = 42,
) -> Result[dict[str, Any], Refusal]:
    """Run the C001 reference self-consistency bout and persist its four-file bundle.

    Returns Ok(run_info) only when every check passes, otherwise Err(Refusal). Without
    ``custom_run_dir`` the bundle goes to a new, time-stamped folder under the
    intelligence root. ``force`` is accepted for compatibility; an existing folder is
    never replaced.
    """
    # 1. Deterministic generated case
    gen = CaseGenerator(seed=seed)
    items, edges, claims, _true_ranks = gen.generate_random_system(
        n_items=8, n_relations=14, disconnected=False
    )
    base_system = ConstraintSystem(items=items, edges=edges, claims=claims)

    base_status, _base_res = host_verdict(base_system)
    if base_status != "CONSISTENT":
        return Err(
            Refusal(
                code="BASE_GRAPH_INCONSISTENT",
                message="Expected base graph to be consistent",
                locus=LOCUS,
            )
        )

    # 2. Perturb one relation so that a contradiction cycle appears
    u, v, _w = edges[0]
    original_val = claims[(u, v)]
    perturbed_val = original_val + 7
    perturbed_claims = dict(claims)
    perturbed_claims[(u, v)] = perturbed_val
    perturbed_system = ConstraintSystem(items=items, edges=edges, claims=perturbed_claims)

    pert_status, pert_res = host_verdict(perturbed_system)
    contradiction_cycle: list[str] = (
        pert_res if pert_status == "CONTRADICTION" and isinstance(pert_res, list) else []
    )
    if not contradiction_cycle:
        return Err(
            Refusal(
                code="NO_CONTRADICTION_WITNESS",
                message="Perturbation did not produce the required contradiction cycle",
                locus=LOCUS,
            )
        )
    pre_sum = cycle_signed_sum(perturbed_system, contradiction_cycle)

    # 3. Two-signal danger gate on the distractor span and the measured witness cycle
    prompt_text = (
        f"Solve rank differences for items {items}. "
        f"Fluff distractor span contains irrelevant values like {original_val + 99}. "
        f"Relation {u}->{v} is perturbed."
    )
    distractor_spans = [(45, 95)]
    token_positions = map_spans_to_token_positions(prompt_text, distractor_spans)
    evidence = json.dumps(
        {"cycle": contradiction_cycle, "signed_sum": pre_sum}, sort_keys=True
    ).encode("utf-8")
    sig1 = Signal1AstMatch(
        epitope_name="distractor_span",
        pattern_matched="fluff_span",
        confidence=Fraction(1, 1),
        offset=distractor_spans[0][0],
    )
    sig2 = Signal2DangerState(
        danger_type="loop_curvature",
        severity=DangerSeverity.HIGH,
        defect_count=1,
        evidence_digest="sha256:" + hashlib.sha256(evidence).hexdigest(),
    )
    danger_decision = TwoSignalDangerGate.evaluate([sig1], sig2).decision.name

    # 4. Budget controller: no provider is called here, so nothing is charged
    budget_ctrl = BudgetController(limit_microusd=250_000)
    budget_spent = budget_ctrl.spent_microusd

    # 5. Carrier lift (recorded; not used by the repair)
    lifted = execute_9dot_gauge_break(perturbed_system, bridge_node="9")

    # 6. Single-edge repair on the unlifted system
    repair_solution = solve_single_repair(perturbed_system)
    if repair_solution.get("status") != "SOLVED":
        return Err(
            Refusal(code="REPAIR_FAILED", message="Failed to solve single-edge repair", locus=LOCUS)
        )
    repair_edge = (repair_solution["edge"][0], repair_solution["edge"][1])
    repair_val = repair_solution["value"]
    repaired_claims = dict(perturbed_claims)
    repaired_claims[repair_edge] = parse_int_exact(repair_val)
    repaired_system = ConstraintSystem(items=items, edges=edges, claims=repaired_claims)

    rep_status, rep_res = host_verdict(repaired_system)
    if rep_status != "CONSISTENT" or not isinstance(rep_res, dict):
        return Err(
            Refusal(
                code="REPAIRED_GRAPH_NOT_CONSISTENT",
                message="Repaired graph did not yield Phi_1 = 0",
                locus=LOCUS,
            )
        )
    potential = {k: format_int(val) for k, val in rep_res.items()}
    measured = measure_repair(perturbed_system, repaired_system, contradiction_cycle)
    if measured["violated_relations_after"] != 0:
        return Err(
            Refusal(
                code="REPAIRED_POTENTIAL_VIOLATES_RELATIONS",
                message=f"Repaired potential violates {measured['violated_relations_after']} relations",
                locus=LOCUS,
            )
        )

    # 7. Checker mutation audit: every invalid certificate must be rejected
    mutation_cases = generate_mutation_cases()
    if not mutation_cases:
        return Err(
            Refusal(
                code="EMPTY_MUTATION_AUDIT",
                message="A passing bout requires non-empty mutation evidence",
                locus=LOCUS,
            )
        )
    mutation_outcomes: list[tuple[str, str, bool]] = []
    for m_entry in mutation_cases:
        is_valid, _msg = verify_certificate(
            m_entry.get("case", m_entry), m_entry.get("solution", {})
        )
        mutation_outcomes.append(
            (
                str(m_entry.get("mutation_id", "unnamed")),
                str(m_entry.get("description", "")),
                not is_valid,
            )
        )
    mutations_total = len(mutation_outcomes)
    mutations_killed = sum(1 for _mid, _desc, killed in mutation_outcomes if killed)
    if mutations_killed != mutations_total:
        return Err(
            Refusal(
                code="MUTATION_AUDIT_FAILED",
                message=f"Verifier accepted {mutations_total - mutations_killed} invalid mutation certificates",
                locus=LOCUS,
            )
        )

    # 8. Action tape (measured values only; 'E' needs measured Gamma_2 = 0)
    tape_res = build_c001_ddc_action_tape(
        system=perturbed_system,
        repaired_system=repaired_system,
        contradiction_cycle=contradiction_cycle,
        repair_edge=repair_edge,
        repair_val=repair_val,
        danger_decision=danger_decision,
        lifted=lifted,
        budget_spent_microusd=budget_spent,
    )
    if tape_res.is_err:
        return Err(tape_res.unwrap_err())
    dda_steps = tape_res.unwrap()

    novella_md = render_7act_novella(
        seed=seed,
        system=perturbed_system,
        potential=potential,
        perturbed_edge=(u, v),
        original_claim=original_val,
        perturbed_claim=perturbed_val,
        repair_edge=repair_edge,
        repair_val=repair_val,
        contradiction_cycle=contradiction_cycle,
        measured=measured,
        token_positions=token_positions,
        danger_decision=danger_decision,
        budget_limit_microusd=budget_ctrl.limit_microusd,
        budget_spent_microusd=budget_spent,
        lifted=lifted,
        mutation_outcomes=mutation_outcomes,
    )

    # 9. Receipt identity and summary
    created_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt_material = {
        "created_utc": created_utc,
        "gate_scope": GATE_SCOPE,
        "objective": OBJECTIVE,
        "source": "c001_run_woland_bout",
        "task_key": TASK_KEY,
        "terminal_verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
    }
    receipt_id = hashlib.sha256(
        json.dumps(receipt_material, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()

    claim_discipline = reference_claim_discipline(
        seed=seed,
        n_items=len(items),
        n_relations=len(edges),
        measured=measured,
        mutations_killed=mutations_killed,
        mutations_total=mutations_total,
        budget_spent_microusd=budget_spent,
    )
    summary_data = build_summary_payload(
        task_key=TASK_KEY,
        receipt_id=receipt_id,
        objective=OBJECTIVE,
        potential=potential,
        repair_edge=repair_edge,
        repair_val=repair_val,
        lifted=lifted,
        seed=seed,
        measured=measured,
        claim_discipline=claim_discipline,
        letter_tape=[str(step["letter"]) for step in dda_steps],
        mutations_killed=mutations_killed,
        mutations_total=mutations_total,
        budget_spent_microusd=budget_spent,
    )
    receipt_data = {
        "authority_effect": "None",
        "created_utc": created_utc,
        "gate_scope": GATE_SCOPE,
        "objective": OBJECTIVE,
        "receipt_id": receipt_id,
        "schema": RECEIPT_SCHEMA,
        "source": "c001_run_woland_bout",
        "task_key": TASK_KEY,
        "terminal_verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
        "verdict_note": LABEL_NOTE,
    }

    # 10. One run store: the intelligence root (or an explicit folder)
    if custom_run_dir is not None:
        target = Path(custom_run_dir).resolve()
    else:
        default_dir = _default_run_dir()
        if default_dir.is_err:
            return Err(default_dir.unwrap_err())
        target = default_dir.unwrap()

    persist_res = persist_quad_bundle(
        target_dir=target,
        task_key=TASK_KEY,
        novella_md=novella_md,
        dda_steps=dda_steps,
        summary_data=summary_data,
        receipt_data=receipt_data,
        force=force,
    )
    if persist_res.is_err:
        return Err(persist_res.unwrap_err())

    return Ok(
        {
            "gamma2": summary_data["gamma2"],
            "gate_scope": GATE_SCOPE,
            "mutation_kill_rate": summary_data["mutation_kill_rate"],
            "mutations_killed": mutations_killed,
            "mutations_total": mutations_total,
            "phi1": summary_data["phi1"],
            "receipt_id": receipt_id,
            "run_dir": str(persist_res.unwrap()),
            "status": "COMPLETED",
            "task_key": TASK_KEY,
            "terminal_verdict": TERMINAL_REFERENCE_SELF_CONSISTENT,
        }
    )


if __name__ == "__main__":
    print(f"=== C001 reference self-consistency bout: {TASK_KEY} ===")
    res = run_woland_c001_bout()
    if res.is_ok:
        info = res.unwrap()
        print(
            f"Label: {info['terminal_verdict']} (scope {info['gate_scope']}; not a Woland verdict)"
        )
        print(f"Run folder: {info['run_dir']}")
        print(f"Phi_1: {info['phi1']}, Gamma_2: {info['gamma2']}")
        print(
            f"Invalid mutation certificates rejected: {info['mutations_killed']} of {info['mutations_total']}"
        )
        sys.exit(0)
    refusal = res.unwrap_err()
    print(f"REFUSAL [{refusal.code}]: {refusal.message} at {refusal.locus}", file=sys.stderr)
    sys.exit(1)
