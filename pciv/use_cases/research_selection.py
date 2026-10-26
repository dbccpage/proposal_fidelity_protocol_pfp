"""Exact, paired selection of experimental incumbents; no deployment authority."""

from fractions import Fraction

from omega_engine_operads.domain.autopoiesis.research import IncumbentDecisionV1
from omega_engine_prompt_civilization.use_cases.fitness import ParetoFrontSelectorV1


def metrics(rows):
    if not rows:
        raise ValueError("MISSING_MEASUREMENTS")
    return {
        "correctness": Fraction(sum(r.private_pass for r in rows), len(rows)),
        "cost": sum(r.cost for r in rows),
    }


def improved(candidate, incumbent):
    if not candidate or not incumbent:
        return False
    keys = lambda rows: sorted((r.task, r.family, r.repetition) for r in rows)
    if keys(candidate) != keys(incumbent):
        raise ValueError("UNPAIRED_EVALUATIONS")
    if any(r.status in ("INCOMPLETE", "INFRASTRUCTURE_ERROR") for r in (*candidate, *incumbent)):
        return False
    c, i = metrics(candidate), metrics(incumbent)
    fronts = ParetoFrontSelectorV1().partition_fronts(
        [{"id": "candidate", "metrics": c}, {"id": "incumbent", "metrics": i}]
    )
    ordered = sorted(
        fronts[0], key=lambda row: (-row["metrics"]["correctness"], row["metrics"]["cost"])
    )
    if c == i or ordered[0]["id"] != "candidate":
        return False
    for family in {r.family for r in candidate}:
        if (
            metrics([r for r in candidate if r.family == family])["correctness"]
            < metrics([r for r in incumbent if r.family == family])["correctness"]
        ):
            return False
    return True


def decide(experiment, incumbent, candidate, selection, confirmation, *, controls_pass):
    all_rows = (*selection, *confirmation)
    for row in all_rows:
        if (
            row.experiment,
            row.source,
            row.checker,
            row.split,
            row.configuration,
            row.budget_id,
        ) != (
            experiment.experiment_id,
            experiment.source,
            experiment.checker,
            experiment.split,
            experiment.configuration,
            experiment.budget_id,
        ):
            raise ValueError("FOREIGN_EVALUATION_BINDING")
        if row.candidate not in (incumbent.candidate_id, candidate.candidate_id):
            raise ValueError("FOREIGN_CANDIDATE")
        expected = candidate if row.candidate == candidate.candidate_id else incumbent
        if row.parent != expected.parent or row.model != experiment.inner_model:
            raise ValueError("STALE_PARENT_OR_MODEL")
    if candidate.parent != incumbent.candidate_id:
        raise ValueError("STALE_CANDIDATE_PARENT")
    occurrences = [r.occurrence for r in all_rows]
    if len(set(occurrences)) != len(occurrences):
        raise ValueError("CONFIRMATION_NOT_FRESH")
    split_rows = lambda rows: (
        [r for r in rows if r.candidate == candidate.candidate_id],
        [r for r in rows if r.candidate == incumbent.candidate_id],
    )
    accept = (
        controls_pass and improved(*split_rows(selection)) and improved(*split_rows(confirmation))
    )
    return IncumbentDecisionV1(
        experiment.experiment_id,
        incumbent.candidate_id,
        candidate.candidate_id,
        candidate.candidate_id if accept else incumbent.candidate_id,
        tuple(r.receipt_id for r in selection),
        tuple(r.receipt_id for r in confirmation),
        "CONFIRMED_IMPROVEMENT" if accept else "RETAIN_INCUMBENT",
    )
