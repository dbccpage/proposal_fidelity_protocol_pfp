"""The yardstick: how often an arm is right, and what each correct answer costs.

We never measure how close an answer is to the truth; we count independent checker
verdicts. For each arm (a model, or a Woland configuration) this reports the success
rate with a Wilson interval, mean rated cost, median wall time, cost and time per correct
answer, and, against a reference arm on the tasks both ran, the paired difference with an
exact McNemar test. Arms that no other arm beats on success, cost and time form the Pareto
frontier. Rated cost is a host estimate from a pinned price table, not a bill.
EPIC-OE-WOLAND-005 workstream Y2/Y4. AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from dataclasses import dataclass
from decimal import Decimal
from statistics import median
from typing import Any

Z95 = 1.959963984540054
MICRO = Decimal("0.000001")


def usd(value: Decimal) -> str:
    """Dollar amounts are reported to the micro-dollar; ledgers keep exact values."""
    return format(value.quantize(MICRO), "f")


@dataclass(frozen=True)
class Trial:
    arm: str
    task: str
    success: bool
    cost_usd: Decimal
    wall_seconds: float
    tokens: int
    declared: int = 0
    scheduled: int = 0
    contributed: int = 0
    failures_reproduced: int = 0
    false_alarms: int = 0
    initial_defects: int = 0
    final_defects: int = 0
    defect_reduction: int = 0
    rounds_executed: int = 0
    loop_status: str = ""
    preset: str = ""
    bundle_digest: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "arm": self.arm,
            "task": self.task,
            "success": self.success,
            "cost_usd": usd(self.cost_usd),
            "wall_seconds": round(self.wall_seconds, 2),
            "tokens": self.tokens,
            "declared": self.declared,
            "scheduled": self.scheduled,
            "contributed": self.contributed,
            "failures_reproduced": self.failures_reproduced,
            "false_alarms": self.false_alarms,
            "initial_defects": self.initial_defects,
            "final_defects": self.final_defects,
            "defect_reduction": self.defect_reduction,
            "rounds_executed": self.rounds_executed,
            "loop_status": self.loop_status,
            "preset": self.preset,
            "bundle_digest": self.bundle_digest,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Trial:
        return cls(
            arm=str(data["arm"]),
            task=str(data["task"]),
            success=bool(data["success"]),
            cost_usd=Decimal(str(data["cost_usd"])),
            wall_seconds=float(data["wall_seconds"]),
            tokens=int(data["tokens"]),
            declared=int(data.get("declared", 0)),
            scheduled=int(data.get("scheduled", 0)),
            contributed=int(data.get("contributed", 0)),
            failures_reproduced=int(data.get("failures_reproduced", 0)),
            false_alarms=int(data.get("false_alarms", 0)),
            initial_defects=int(data.get("initial_defects", 0)),
            final_defects=int(data.get("final_defects", 0)),
            defect_reduction=int(data.get("defect_reduction", 0)),
            rounds_executed=int(data.get("rounds_executed", 0)),
            loop_status=str(data.get("loop_status", "")),
            preset=str(data.get("preset", "")),
            bundle_digest=str(data.get("bundle_digest", "")),
        )

    @classmethod
    def from_run(
        cls,
        run: Any,
        *,
        arm: str,
        task: str,
        success: bool,
        cost_usd: Decimal,
        wall_seconds: float,
        tokens: int,
        initial_defects: int = 0,
        final_defects: int = 0,
        defect_reduction: int = 0,
        rounds_executed: int = 0,
        loop_status: str = "",
        preset: str = "",
        bundle_digest: str = "",
    ) -> Trial:
        cov = getattr(run, "retinue_coverage", {})
        if not isinstance(cov, dict):
            cov = {}
        return cls(
            arm=arm,
            task=task,
            success=success,
            cost_usd=cost_usd,
            wall_seconds=wall_seconds,
            tokens=tokens,
            declared=int(cov.get("declared", 0)),
            scheduled=int(cov.get("scheduled", 0)),
            contributed=int(cov.get("contributed", 0)),
            failures_reproduced=int(cov.get("failures_reproduced", 0)),
            false_alarms=int(cov.get("false_alarms", 0)),
            initial_defects=initial_defects or int(cov.get("initial_defects", 0)),
            final_defects=final_defects or int(cov.get("final_defects", 0)),
            defect_reduction=defect_reduction or int(cov.get("defect_reduction", 0)),
            rounds_executed=rounds_executed or int(cov.get("rounds_executed", 0)),
            loop_status=loop_status or str(cov.get("loop_status", "")),
            preset=preset or str(cov.get("preset", "")),
            bundle_digest=bundle_digest or str(cov.get("bundle_digest", "")),
        )


@dataclass(frozen=True)
class ArmStats:
    arm: str
    trials: int
    successes: int
    rate: float
    rate_low: float
    rate_high: float
    mean_cost_usd: Decimal
    cost_per_success_usd: Decimal | None
    median_wall_seconds: float
    wall_per_success_seconds: float | None
    mean_tokens: float
    declared: int = 0
    scheduled: int = 0
    contributed: int = 0
    failures_reproduced: int = 0
    false_alarms: int = 0
    mean_declared: float = 0.0
    mean_scheduled: float = 0.0
    mean_contributed: float = 0.0
    mean_failures_reproduced: float = 0.0
    mean_false_alarms: float = 0.0
    mean_defect_reduction: float = 0.0
    total_defect_reduction: int = 0
    mean_rounds_executed: float = 0.0
    total_rounds_executed: int = 0

    @property
    def total_declared(self) -> int:
        return self.declared

    @property
    def total_scheduled(self) -> int:
        return self.scheduled

    @property
    def total_contributed(self) -> int:
        return self.contributed

    @property
    def total_failures_reproduced(self) -> int:
        return self.failures_reproduced

    @property
    def total_false_alarms(self) -> int:
        return self.false_alarms

    def to_dict(self) -> dict[str, Any]:
        total_cost = self.mean_cost_usd * Decimal(self.trials)
        flagged_total = self.failures_reproduced + self.false_alarms
        return {
            "arm": self.arm,
            "trials": self.trials,
            "successes": self.successes,
            "rate": round(self.rate, 4),
            "rate_95": [round(self.rate_low, 4), round(self.rate_high, 4)],
            "mean_cost_usd": usd(self.mean_cost_usd),
            "cost_per_success_usd": None if self.cost_per_success_usd is None else usd(self.cost_per_success_usd),
            "median_wall_seconds": round(self.median_wall_seconds, 2),
            "wall_per_success_seconds": None if self.wall_per_success_seconds is None
                else round(self.wall_per_success_seconds, 2),
            "mean_tokens": round(self.mean_tokens, 1),
            "declared": self.declared,
            "scheduled": self.scheduled,
            "contributed": self.contributed,
            "failures_reproduced": self.failures_reproduced,
            "false_alarms": self.false_alarms,
            "false_alarm_rate": round(self.false_alarms / flagged_total, 4) if flagged_total > 0 else 0.0,
            "reproduced_failures_per_usd": round(float(Decimal(self.failures_reproduced) / total_cost), 4)
                if total_cost > 0 else None,
            "total_declared": self.declared,
            "total_scheduled": self.scheduled,
            "total_contributed": self.contributed,
            "total_failures_reproduced": self.failures_reproduced,
            "total_false_alarms": self.false_alarms,
            "mean_declared": round(self.mean_declared, 1),
            "mean_scheduled": round(self.mean_scheduled, 1),
            "mean_contributed": round(self.mean_contributed, 1),
            "mean_failures_reproduced": round(self.mean_failures_reproduced, 2),
            "mean_false_alarms": round(self.mean_false_alarms, 2),
            "total_defect_reduction": self.total_defect_reduction,
            "total_rounds_executed": self.total_rounds_executed,
            "mean_defect_reduction": round(self.mean_defect_reduction, 2),
            "mean_rounds_executed": round(self.mean_rounds_executed, 2),
        }


def wilson_interval(successes: int, trials: int, z: float = Z95) -> tuple[float, float]:
    """Score interval for a binomial rate; stays inside [0, 1] for small samples."""
    if type(successes) is not int or type(trials) is not int or not 0 <= successes <= trials:
        raise ValueError("WILSON_COUNTS_INVALID")
    if trials == 0:
        return 0.0, 1.0
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return max(0.0, centre - half), min(1.0, centre + half)


def summarize(trials: list[Trial]) -> dict[str, ArmStats]:
    arms: dict[str, list[Trial]] = {}
    for trial in trials:
        arms.setdefault(trial.arm, []).append(trial)
    result = {}
    for arm, rows in arms.items():
        n, wins = len(rows), sum(row.success for row in rows)
        low, high = wilson_interval(wins, n)
        total_cost = sum((row.cost_usd for row in rows), Decimal(0))
        total_wall = sum(row.wall_seconds for row in rows)
        tot_declared = sum(row.declared for row in rows)
        tot_scheduled = sum(row.scheduled for row in rows)
        tot_contributed = sum(row.contributed for row in rows)
        tot_reproduced = sum(row.failures_reproduced for row in rows)
        tot_false_alarms = sum(row.false_alarms for row in rows)
        tot_defect_reduction = sum(row.defect_reduction for row in rows)
        tot_rounds_executed = sum(row.rounds_executed for row in rows)
        result[arm] = ArmStats(
            arm=arm,
            trials=n,
            successes=wins,
            rate=(wins / n) if n else 0.0,
            rate_low=low,
            rate_high=high,
            mean_cost_usd=(total_cost / n) if n else Decimal(0),
            cost_per_success_usd=(total_cost / wins) if wins else None,
            median_wall_seconds=median(row.wall_seconds for row in rows) if rows else 0.0,
            wall_per_success_seconds=(total_wall / wins) if wins else None,
            mean_tokens=sum(row.tokens for row in rows) / n if n else 0.0,
            declared=tot_declared,
            scheduled=tot_scheduled,
            contributed=tot_contributed,
            failures_reproduced=tot_reproduced,
            false_alarms=tot_false_alarms,
            mean_declared=(tot_declared / n) if n else 0.0,
            mean_scheduled=(tot_scheduled / n) if n else 0.0,
            mean_contributed=(tot_contributed / n) if n else 0.0,
            mean_failures_reproduced=(tot_reproduced / n) if n else 0.0,
            mean_false_alarms=(tot_false_alarms / n) if n else 0.0,
            total_defect_reduction=tot_defect_reduction,
            total_rounds_executed=tot_rounds_executed,
            mean_defect_reduction=(tot_defect_reduction / n) if n else 0.0,
            mean_rounds_executed=(tot_rounds_executed / n) if n else 0.0,
        )
    return result


def mcnemar_exact(only_left: int, only_right: int) -> float:
    """Two-sided exact p-value for discordant pairs under no difference."""
    n = only_left + only_right
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(only_left, only_right) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def distance_to_reference(trials: list[Trial], arm: str, reference: str) -> dict:
    """Paired comparison on tasks both arms ran.

    The k-th trial of the arm on a task is paired with the k-th trial of the reference on
    that task, so repeats count; trials without a partner are left out of the pairing.
    """
    def by_task(name):
        verdicts: dict[str, list[Trial]] = {}
        for trial in trials:
            if trial.arm == name:
                verdicts.setdefault(trial.task, []).append(trial)
        return verdicts

    left, right = by_task(arm), by_task(reference)
    shared = sorted(set(left) & set(right))
    if not shared:
        return {"arm": arm, "reference": reference, "shared_tasks": 0}
    pairs = [(a, r) for task in shared for a, r in zip(left[task], right[task])]
    only_left = sum(a.success and not r.success for a, r in pairs)
    only_right = sum(r.success and not a.success for a, r in pairs)
    stats = summarize([*(a for a, _ in pairs), *(r for _, r in pairs)])
    a, r = stats[arm], stats[reference]

    def ratio(x, y):
        return None if not y else round(float(x) / float(y), 3)

    return {"arm": arm, "reference": reference, "shared_tasks": len(shared), "pairs": len(pairs),
        "rate_difference": round(a.rate - r.rate, 4),
        "only_arm_correct": only_left, "only_reference_correct": only_right,
        "mcnemar_p": round(mcnemar_exact(only_left, only_right), 4),
        "cost_ratio": ratio(a.mean_cost_usd, r.mean_cost_usd),
        "wall_ratio": ratio(a.median_wall_seconds, r.median_wall_seconds)}


def pareto_frontier(stats: dict[str, ArmStats]) -> list[str]:
    """Arms not dominated on (higher rate, lower mean cost, lower median wall time)."""
    def dominates(x: ArmStats, y: ArmStats) -> bool:
        better_or_equal = (x.rate >= y.rate and x.mean_cost_usd <= y.mean_cost_usd
                           and x.median_wall_seconds <= y.median_wall_seconds)
        strictly = (x.rate > y.rate or x.mean_cost_usd < y.mean_cost_usd
                    or x.median_wall_seconds < y.median_wall_seconds)
        return better_or_equal and strictly

    return sorted(name for name, item in stats.items()
                  if not any(dominates(other, item) for key, other in stats.items() if key != name))


@dataclass(frozen=True)
class SeatContribution:
    role_id: str
    phase: str
    findings: tuple[str, ...]
    cost_usd: Decimal
    tier: str = ""
    model: str = ""
    model_family: str = ""


def seat_value(runs: list[list[SeatContribution]]) -> list[dict]:
    """Zero-cost credit per seat across recorded runs.

    A finding is unique to a seat when no other seat in the same run raised the same text,
    and each distinct finding counts once per seat per run, however often the seat repeats it.
    This is an upper bound on a seat's marginal value: a unique finding may still be wrong.
    """
    table: dict[str, dict] = {}
    for contributions in runs:
        raised: dict[str, set[str]] = {}
        own: dict[str, set[str]] = {}
        for item in contributions:
            for finding in item.findings:
                key = finding.strip().lower()
                raised.setdefault(key, set()).add(item.role_id)
                own.setdefault(item.role_id, set()).add(key)
        for item in contributions:
            row = table.setdefault(item.role_id, {"role_id": item.role_id, "calls": 0, "findings": 0,
                "unique_findings": 0, "cost_usd": Decimal(0), "runs": 0})
            row["calls"] += 1
            row["cost_usd"] += item.cost_usd
        for role, keys in own.items():
            table[role]["findings"] += len(keys)
            table[role]["unique_findings"] += sum(raised[key] == {role} for key in keys)
        for role in {item.role_id for item in contributions}:
            table[role]["runs"] += 1
    rows = sorted(table.values(), key=lambda row: (-row["unique_findings"], row["cost_usd"]))
    for row in rows:
        row["cost_per_unique_finding_usd"] = (usd(row["cost_usd"] / row["unique_findings"])
                                              if row["unique_findings"] else None)
        row["cost_usd"] = usd(row["cost_usd"])
    return rows


def measure_loop_defect_reduction(loop_outcome: dict[str, Any]) -> dict[str, Any]:
    """Extract standardized yardstick defect metrics from a bounded loop outcome."""
    return {
        "status": loop_outcome["status"],
        "loop_status": loop_outcome["status"],
        "rounds_executed": loop_outcome["rounds_executed"],
        "initial_defects": loop_outcome["initial_defects"],
        "final_defects": loop_outcome["final_defects"],
        "defect_reduction": loop_outcome["defect_reduction"],
        "resolved_all": loop_outcome["final_defects"] == 0,
    }


def compute_bundle_digest(
    preset_name: str,
    prompt_family_versions: dict[str, str],
    checker_ids: list[str],
) -> str:
    """Compute SHA-256 digest-pinned bundle for yardstick trials.

    bundle_digest = sha256(canonical_json({"preset": preset_name, "prompt_family_versions": prompt_family_versions, "checker_ids": sorted(checker_ids)}))
    """
    payload = {
        "preset": str(preset_name),
        "prompt_family_versions": {str(k): str(v) for k, v in prompt_family_versions.items()},
        "checker_ids": sorted(str(cid) for cid in checker_ids),
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def evaluate_cross_family_metrics(
    evaluations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate cross-family falsifier metrics (within-family vs cross-family reproduction)."""
    within_family_claims = 0
    within_family_reproduced = 0
    cross_family_claims = 0
    cross_family_reproduced = 0

    for ev in evaluations:
        origin_family = ev["origin_model_family"]
        falsifier_family = ev["falsifier_model_family"]
        reproduced = bool(ev["reproduced_by_host"])

        if origin_family == falsifier_family:
            within_family_claims += 1
            if reproduced:
                within_family_reproduced += 1
        else:
            cross_family_claims += 1
            if reproduced:
                cross_family_reproduced += 1

    within_rate = (within_family_reproduced / within_family_claims) if within_family_claims else 0.0
    cross_rate = (cross_family_reproduced / cross_family_claims) if cross_family_claims else 0.0

    return {
        "within_family_claims": within_family_claims,
        "within_family_reproduced": within_family_reproduced,
        "within_family_rate": round(within_rate, 4),
        "cross_family_claims": cross_family_claims,
        "cross_family_reproduced": cross_family_reproduced,
        "cross_family_rate": round(cross_rate, 4),
        "cross_family_divergence": round(abs(within_rate - cross_rate), 4),
    }


def record_schedule_telemetry(
    run_id: str,
    schedule: str,
    contributions: list[SeatContribution],
    resolved_obstructions: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Consolidate per-run schedule, seat findings, cost, and obstruction resolutions (L1)."""
    valued = seat_value([contributions])
    total_cost = sum((c.cost_usd for c in contributions), Decimal(0))
    return {
        "run_id": str(run_id),
        "schedule": str(schedule),
        "total_cost_usd": usd(total_cost),
        "seat_value": valued,
        "resolved_obstructions": list(resolved_obstructions),
    }


def thompson_sampling_schedule(
    schedules: list[str] | tuple[str, ...],
    arm_history: dict[str, dict[str, Any]],
    random_seed: int = 42,
) -> str:
    """Select a schedule via Thompson sampling over measured correctness-per-unit-cost (L2)."""
    if not schedules:
        raise ValueError("SCHEDULE_CANDIDATES_EMPTY")
    rng = random.Random(random_seed)
    scores: dict[str, float] = {}
    for sched in schedules:
        stats = arm_history.get(sched, {"successes": 1, "failures": 1})
        alpha = max(1, int(stats.get("successes", 1)))
        beta = max(1, int(stats.get("failures", 1)))
        cost_factor = float(stats.get("mean_cost_usd", 1.0) or 1.0)
        sample_val = rng.betavariate(alpha, beta) / max(cost_factor, 1e-6)
        scores[sched] = sample_val
    return max(scores, key=lambda s: scores[s])


def promote_candidate_operand(
    candidate: dict[str, Any],
    baseline_yield: float,
    trial_yield: float,
    threshold_delta: float = 0.05,
) -> dict[str, Any]:
    """Promote recurring seat composition operand if yardstick improvement meets threshold (L3)."""
    if "operand_id" not in candidate or "composition" not in candidate:
        raise ValueError("OPERAND_CANDIDATE_INVALID")
    delta = trial_yield - baseline_yield
    promoted = delta >= threshold_delta - 1e-12
    return {
        "operand_id": str(candidate["operand_id"]),
        "composition": list(candidate["composition"]),
        "baseline_yield": round(baseline_yield, 4),
        "trial_yield": round(trial_yield, 4),
        "yield_delta": round(delta, 4),
        "promoted": promoted,
        "disposition": "ADMITTED_OPERAND" if promoted else "RETAINED_CANDIDATE",
    }


def operad_yield_per_dollar(unique_failures_found: int, cost_usd: Decimal) -> Decimal:
    """Compute operad yield-per-dollar: unique_failures_found / cost_usd (S6)."""
    if type(unique_failures_found) is not int or unique_failures_found < 0:
        raise ValueError("OPERAD_YIELD_COUNTS_INVALID")
    if cost_usd <= Decimal(0):
        return Decimal(0)
    return Decimal(unique_failures_found) / cost_usd


def operad_retirement_audit(
    operad_stats: list[dict[str, Any]],
    min_evaluation_runs: int = 3,
) -> tuple[list[str], list[str]]:
    """Classify operads into (active, retired) based on measured yield across runs (S6)."""
    active: list[str] = []
    retired: list[str] = []
    for op in operad_stats:
        op_id = str(op["operad_id"])
        runs = int(op.get("eval_runs", 0))
        raw_yield = op.get("yield_per_dollar", Decimal(0))
        yield_val = raw_yield if isinstance(raw_yield, Decimal) else Decimal(str(raw_yield))
        if runs >= min_evaluation_runs and yield_val <= Decimal(0):
            retired.append(op_id)
        else:
            active.append(op_id)
    return active, retired


