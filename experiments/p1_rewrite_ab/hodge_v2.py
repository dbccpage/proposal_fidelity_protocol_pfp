"""P1 Hodge rerun v2: same 10 instances and 4 arms; only the integer-field contract sentence is fixed. AuthorityEffect: None."""
import hashlib, json, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tier_s  # noqa: E402
SYSTEM_V2 = (
    "Answer with one JSON object only, with no code fence and no other text. Fields: "
    "b0 and b1, the Betti numbers over the rationals; euler_characteristic, vertices minus edges "
    "plus filled triangles. Write these three as JSON integers, not strings, for example 1, not \"1\". "
    "potential, p at each vertex in order with p(0) = \"0\"; gradient, d0 p by edge position; curl, "
    "d1^T q by edge position; harmonic, h by edge position; harmonic_norm_squared, the sum of the "
    "squares of the entries of h. Write every one of these other values as a string in lowest terms, "
    "such as \"-3/2\" or \"4\"."
)
def sha(text): return hashlib.sha256(text.encode("utf-8")).hexdigest()
def build():
    rows = []
    for line in (HERE / "tasks.jsonl").read_text(encoding="utf-8").splitlines():
        t = json.loads(line)
        if t["family"] != "H":
            continue
        arms = dict(t["arms"], tier_s_qed=tier_s.tier_s_qed(t["instance"]))
        rows.append(dict(task_id=t["task_id"], family="H", instance=t["instance"], expected=t["expected"],
                         arms=arms, arm_sha256={a: sha(x) for a, x in arms.items()},
                         system=SYSTEM_V2, system_sha256=sha(SYSTEM_V2),
                         max_completion_tokens=t["max_completion_tokens"], kit="hodge_v2"))
    return rows


def main():
    rows = build()
    body = "".join(json.dumps(r, sort_keys=True, ensure_ascii=False) + "\n" for r in rows)
    (HERE / "tasks_hodge_v2.jsonl").write_bytes(body.encode("utf-8"))
    print(f"wrote tasks_hodge_v2.jsonl: {len(rows)} tasks, {sum(len(r['arms']) for r in rows)} calls, sha256 {sha(body)}")


if __name__ == "__main__":
    main()
