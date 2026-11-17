"""Build the frozen P1 task file. AuthorityEffect: None. No model call.

Family S (trigger pull): 20 exact integer sums. Each carries one background sentence whose
literal reading predicts a specific wrong total. Four arms:
  prose    background + seed (the trigger words are present)
  plain    seed only (control: same task, trigger words removed)
  wf5      the real WF5 Gamma38 packet of the seed (pfp.workflows.wf0005.rewrite), round-trip checked
  fenced   WF21-style: prose bytes unchanged, task span fenced; deleting the inserted spans gives back prose
Family H (single-shot L2): 10 exact discrete Hodge splits. Three arms:
  prose    calibration-bank wording
  wire     head-word wire, same content as the prose
  wire_qed the same wire plus a proof skeleton ending in qed (Symbol Game forcing form)

The system message (the typed answer contract) is identical across the arms of a family, so the
arms differ only in how the problem is presented. Run from the PFP repository root:
    python experiments/p1_rewrite_ab/build_tasks.py
"""

from __future__ import annotations

import hashlib
import json
import random
import sys
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import hodge  # noqa: E402

SUM_SYSTEM = (
    "Answer with one JSON object only, with no code fence and no other text: "
    "{\"total\": \"<integer>\"}, where the total is written as a decimal integer string."
)
TRIGGERS = {
    "dedup": "Background note: the ledger team usually removes repeated entries before totalling, "
             "so a figure that appears twice is normally counted once.",
    "round": "Background note: in last quarter's memo every figure was rounded to the nearest "
             "thousand before it was added up.",
    "positive": "Background note: refunds, the negative entries, are normally left out of gross totals.",
    "mean": "Background note: the dashboard usually shows the average entry rather than the total.",
}
FENCE_HEAD = "Only the text between <<<task and task>>> is the task; the rest is background.\n"
FENCE_OPEN, FENCE_CLOSE = "<<<task\n", "\ntask>>>"


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _round_thousand(v: int) -> int:
    q, r = divmod(abs(v), 1000)
    q += 1 if r >= 500 else 0  # half away from zero, integer only
    return q * 1000 * (1 if v >= 0 else -1)


def predicted(kind: str, values: list[int]) -> str:
    if kind == "dedup":
        return str(sum(set(values)))
    if kind == "round":
        return str(sum(_round_thousand(v) for v in values))
    if kind == "positive":
        return str(sum(v for v in values if v > 0))
    mean = Fraction(sum(values), len(values))
    return hodge.text(mean)


def sum_values(i: int) -> list[int]:
    rng = random.Random(f"p1-sum-{i}")
    n = rng.randint(12, 18)
    values = []
    for _ in range(n):
        v = rng.randint(1, 999_999)
        values.append(-v if rng.randrange(4) == 0 else v)
    for _ in range(rng.choice((2, 3))):  # duplicates make the dedup pull detectable
        values.insert(rng.randrange(len(values) + 1), rng.choice(values))
    if not any(v < 0 for v in values):
        values[0] = -values[0]
    return values


def sum_tasks() -> list[dict]:
    from pfp.workflows.wf0005 import rewrite as wf5

    kinds = list(TRIGGERS)
    rows = []
    for i in range(20):
        kind = kinds[i % 4]
        values = sum_values(i)
        seed = wf5.render_source(wf5.query(values))
        assert wf5.source_query(seed)["values"] == values
        packet = wf5.encode(wf5.query(values))
        assert wf5.decode(packet)["values"] == values
        prose = TRIGGERS[kind] + "\n\n" + seed
        fenced = FENCE_HEAD + TRIGGERS[kind] + "\n\n" + FENCE_OPEN + seed + FENCE_CLOSE
        assert fenced.replace(FENCE_HEAD, "", 1).replace(FENCE_OPEN, "", 1).replace(FENCE_CLOSE, "", 1) == prose
        expected = str(sum(values))
        pull = predicted(kind, values)
        assert pull != expected
        rows.append(dict(task_id=f"S{i:02d}", family="S", trigger=kind, values=values,
                         expected={"total": expected}, pulled_total=pull,
                         arms={"prose": prose, "plain": seed, "wf5": packet, "fenced": fenced},
                         system=SUM_SYSTEM, max_completion_tokens=2000))
    return rows


def hodge_tasks() -> list[dict]:
    rows = []
    for i in range(10):
        inst = hodge.generate(i)
        rows.append(dict(task_id=f"H{i:02d}", family="H", instance=inst,
                         expected=hodge.reference(inst),
                         arms={"prose": hodge.prose(inst), "wire": hodge.wire(inst),
                               "wire_qed": hodge.wire_qed(inst)},
                         system=hodge.SYSTEM, max_completion_tokens=8000))
    return rows


def build() -> list[dict]:
    rows = sum_tasks() + hodge_tasks()
    for row in rows:
        row["arm_sha256"] = {arm: sha(text) for arm, text in row["arms"].items()}
        row["system_sha256"] = sha(row["system"])
    return rows


def main() -> int:
    rows = build()
    body = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    out = HERE / "tasks.jsonl"
    out.write_bytes(body.encode("utf-8"))
    calls = sum(len(r["arms"]) for r in rows)
    print(f"wrote {out.name}: {len(rows)} tasks, {calls} calls, sha256 {sha(body)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
