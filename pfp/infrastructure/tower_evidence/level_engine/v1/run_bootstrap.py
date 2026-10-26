"""Build every bootstrap record, deterministically.

Writes, under ``--out`` (default: the repository root):

* ``bundles/``: layer-1 witness bundles, challenge evidence and loss ledgers,
  named by their SHA-256, plus ``INDEX.json``.  No level numbers.
* ``bindings/generated/``: transport certificates, register entries,
  checker-input bundles, the computed grade table, and the lift records of
  the carrier's own reading ladder (``lifts/``).  Level numbers live here
  only.

AuthorityEffect: None
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from outward import bundles as B  # noqa: E402
from outward import reach as R  # noqa: E402
from engine.canon import dumps, load_path, sha256_hex, write_bytes  # noqa: E402
from engine.ladder_cert import certify_ladder, load_proposals  # noqa: E402
from engine.level import run_level  # noqa: E402
from outward.lift import ladder_document  # noqa: E402
from outward.qlevels import registrations  # noqa: E402
from tools.bind import LEVELS, TREE_REPLAYS, records  # noqa: E402


def build(out: Path) -> list[str]:
    for sub in ("bundles", "bindings/generated"):
        if (out / sub).exists():
            shutil.rmtree(out / sub)
    written: list[str] = []
    index: dict[str, object] = {}
    grades = []

    def put(rel: str, data: bytes) -> None:
        write_bytes(out / rel, data)
        written.append(rel)

    for tag, level, meta in records():
        cid = str(meta["challenge_id"])
        result = run_level(cid)
        inputs = B.fixture_inputs(cid)
        B.check_injective(inputs)
        ev = dumps(B.evidence(result))
        loss = dumps(B.loss_ledger(result))
        ev_sha, loss_sha = "sha256:" + sha256_hex(ev), "sha256:" + sha256_hex(loss)
        bundle = dumps(B.witness_bundle(result, ev_sha, loss_sha, inputs))
        b_sha = "sha256:" + sha256_hex(bundle)
        put(f"bundles/{sha256_hex(bundle)}.json", bundle)
        put(f"bundles/{sha256_hex(ev)}.evidence.json", ev)
        put(f"bundles/{sha256_hex(loss)}.loss.json", loss)
        index[cid] = {"bundle": b_sha, "evidence": ev_sha, "loss_ledger": loss_sha}
        binding = load_path(ROOT / "bindings" / f"{tag}.json")
        assert isinstance(binding, dict)
        gen = "bindings/generated"
        put(f"{gen}/certificates/{tag}.cert.json",
            dumps(B.transport_certificate(level, binding, result, b_sha, loss_sha, inputs)))
        put(f"{gen}/register/SC-{tag}.json", dumps(B.register_entry(level, result, tag)))
        put(f"{gen}/checker_input/{tag}.json", dumps(B.checker_input(level, binding, result, inputs)))
        grades.append(B.grade_row(level, result, binding))
        put(f"{gen}/reach/{tag}.stub.json", R.stub_bytes(level, result, inputs, tag))
        adapter = R.load_adapter(R.adapter_path(level, tag))
        if adapter is not None:
            positive = next(f["payload"] for f in adapter.fixtures(result, inputs) if f["kind"] == "positive")
            put(f"{gen}/reach/{tag}.positive.json", dumps(positive))
    put("bindings/generated/reach/axioms.reach.txt", R.axioms_report_bytes())
    put("bundles/INDEX.json", dumps({"authority_effect": "None", "records": index,
                                     "schema": "level-engine.bundle-index.v1"}))
    props = load_proposals()
    put("bindings/generated/lifts/record_reading.json",
        dumps(ladder_document(certify_ladder(props), props, B.sealed_commit())))
    put("bindings/generated/qlevels.json", dumps(registrations(LEVELS, TREE_REPLAYS)))
    put("bindings/generated/grade_table.json", dumps({
        "authority_effect": "None",
        "note": "computed by the harness; reach grades are the receiving side's and are not written here",
        "rows": grades,
        "schema": "level-engine.grade-table.v1",
    }))
    return sorted(written)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT)
    args = ap.parse_args(argv)
    files = build(args.out)
    print(f"wrote {len(files)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main())
