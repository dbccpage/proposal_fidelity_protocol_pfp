"""PREREG-DA-001 Stage B analysis: does the local detector add to the baselines (section 5.4, amendment 6.2)?

Logistic regression of terminal failure on (a) the baselines and (b) the baselines plus the
predictor. The statistic is ΔAUC = AUC(b) - AUC(a), refitted on each of 10,000 item-level
bootstrap resamples. AUC is the Mann-Whitney statistic with ties counted half.
AuthorityEffect: None.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any

import numpy as np

BOOTSTRAP = 10_000
RIDGE = 1e-2
MIN_EVENTS = 30
KILL = 0.05
FOLDS = 10
BASELINES = ("struct_share", "schema_valid", "n_steps", "output_tokens")
PREDICTORS = ("d4_red", "d4_noncertifying")


def features(record: dict[str, Any]) -> dict[str, float]:
    d4 = record["d4"]["status"]
    return {
        "struct_share": float(Fraction(record["struct_share"])),
        "schema_valid": float(record["schema_valid"]),
        "n_steps": float(record["n_steps"]),
        "output_tokens": float(record.get("output_tokens") or 0),
        "d4_red": float(d4 == "red"),
        "d4_noncertifying": float(d4 == "noncertifying"),
    }


def design(rows: list[dict[str, float]], names: tuple[str, ...]) -> np.ndarray:
    x = np.array([[r[n] for n in names] for r in rows], dtype=float)
    sd = x.std(axis=0)
    x = (x - x.mean(axis=0)) / np.where(sd > 0, sd, 1.0)
    return np.hstack([np.ones((len(rows), 1)), x])


def fit_logistic(x: np.ndarray, y: np.ndarray, ridge: float = RIDGE, iters: int = 50) -> np.ndarray:
    """Ridge-penalised IRLS; the intercept is not penalised."""
    beta = np.zeros(x.shape[1])
    penalty = ridge * np.eye(x.shape[1])
    penalty[0, 0] = 0.0
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(x @ beta, -30, 30)))
        w = p * (1.0 - p)
        hessian = x.T @ (x * w[:, None]) + penalty
        step = np.linalg.solve(hessian, x.T @ (y - p) - penalty @ beta)
        beta = beta + step
        if np.max(np.abs(step)) < 1e-10:
            break
    return beta


def auc(score: np.ndarray, y: np.ndarray) -> float:
    pos, neg = score[y == 1], score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    order = np.argsort(np.concatenate([pos, neg]), kind="mergesort")
    values = np.concatenate([pos, neg])[order]
    ranks = np.empty(len(values))
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and values[j + 1] == values[i]:
            j += 1
        ranks[i:j + 1] = (i + j) / 2.0 + 1.0
        i = j + 1
    pos_rank = np.empty(len(values))
    pos_rank[order] = ranks
    return float((pos_rank[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2.0) / (len(pos) * len(neg)))


def delta_auc(xa: np.ndarray, xb: np.ndarray, y: np.ndarray) -> float:
    return auc(xb @ fit_logistic(xb, y), y) - auc(xa @ fit_logistic(xa, y), y)


def out_of_fold_delta(xa: np.ndarray, xb: np.ndarray, y: np.ndarray, seed: int) -> float:
    fold = np.random.default_rng(seed).permutation(len(y)) % FOLDS
    sa, sb = np.zeros(len(y)), np.zeros(len(y))
    for k in range(FOLDS):
        tr, te = fold != k, fold == k
        sa[te] = xa[te] @ fit_logistic(xa[tr], y[tr])
        sb[te] = xb[te] @ fit_logistic(xb[tr], y[tr])
    return auc(sb, y) - auc(sa, y)


def bootstrap(xa: np.ndarray, xb: np.ndarray, y: np.ndarray, seed: int) -> tuple[list[float], int]:
    rng = np.random.default_rng(seed)
    out, skipped = [], 0
    for _ in range(BOOTSTRAP):
        idx = rng.integers(0, len(y), len(y))
        if y[idx].min() == y[idx].max():
            skipped += 1
            continue
        out.append(delta_auc(xa[idx], xb[idx], y[idx]))
    return out, skipped


def decide(point: float, low: float, high: float, failures: int, successes: int) -> str:
    if min(failures, successes) < MIN_EVENTS:
        return "BudgetUnknown:TOO_FEW_EVENTS"
    if high < KILL:
        return "DROPPED"
    if low > 0 and point >= KILL:
        return "SUPPORTED_AT_PILOT_SCALE"
    return "BudgetUnknown:INCONCLUSIVE"


def crosstab(records: list[dict[str, Any]], key: str) -> dict[str, dict[str, int]]:
    table: dict[str, dict[str, int]] = {}
    for r in records:
        cell = table.setdefault(r[key]["status"], {"failure": 0, "success": 0})
        cell["failure" if r["failure"] else "success"] += 1
    return dict(sorted(table.items()))


def oscillation(records: list[dict[str, Any]]) -> dict[str, Any]:
    by_item: dict[str, dict[int, Any]] = {}
    for r in records:
        if not r.get("transport_error"):
            by_item.setdefault(r["item_id"], {})[r["call"]] = r.get("answer")
    pairs = [v for v in by_item.values() if 0 in v and 1 in v]
    differ = sum(1 for v in pairs if v[0] is None or v[1] is None or v[0] != v[1])
    return {"pairs": len(pairs), "answers_differ": differ}


def analyse(records: list[dict[str, Any]], seed: int) -> dict[str, Any]:
    primary = [r for r in records if r["call"] == 0 and not r.get("transport_error")]
    summary: dict[str, Any] = {
        "n_primary": len(primary), "failures": sum(1 for r in primary if r["failure"]),
        "transport_errors": sum(1 for r in records if r.get("transport_error")),
        "oscillation": oscillation(records), "baselines": list(BASELINES), "predictors": list(PREDICTORS),
    }
    if not primary:
        summary["decision"] = "BudgetUnknown:NO_DATA"
        return summary
    summary.update({"d4_by_outcome": crosstab(primary, "d4"), "d3_by_outcome": crosstab(primary, "d3"),
                    "d2_by_outcome": crosstab(primary, "d2")})
    rows = [features(r) for r in primary]
    y = np.array([1.0 if r["failure"] else 0.0 for r in primary])
    failures, successes = int(y.sum()), int(len(y) - y.sum())
    if min(failures, successes) == 0:
        summary["decision"] = "BudgetUnknown:TOO_FEW_EVENTS"
        return summary
    xa, xb = design(rows, BASELINES), design(rows, BASELINES + PREDICTORS)
    point = delta_auc(xa, xb, y)
    draws, skipped = bootstrap(xa, xb, y, seed)
    low, high = (float(np.percentile(draws, 2.5)), float(np.percentile(draws, 97.5))) if draws else (float("nan"),) * 2
    summary.update({
        "auc_baselines": auc(xa @ fit_logistic(xa, y), y), "auc_with_predictor": auc(xb @ fit_logistic(xb, y), y),
        "delta_auc": point, "ci95": [low, high], "bootstrap_used": len(draws), "bootstrap_skipped": skipped,
        "delta_auc_out_of_fold": out_of_fold_delta(xa, xb, y, seed),
        "decision": decide(point, low, high, failures, successes),
    })
    return summary
