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
import sys
from pathlib import Path

if __name__ == "__main__":
    import runpy

    sys.argv = [sys.argv[0], "bootstrap", *sys.argv[1:]]
    raise SystemExit(runpy.run_module(
        "operations.infrastructure.level_engine_ports",
        run_name="__main__",
    ))

from operations.domain.level_engine_context import (
    LevelEngineOperationPorts,
    current_context,
)

ROOT = current_context().runtime_root

from operations.use_cases.level_engine.research_engine.canon import (  # noqa: E402
    dumps,
    load_path,
    sha256_hex,
    write_bytes,
)
from operations.use_cases.level_engine.research_engine.ladder_cert import (  # noqa: E402
    certify_ladder,
    load_proposals,
)
from operations.use_cases.level_engine.research_engine.level import (
    run_level,  # noqa: E402
)

from .bind import LEVELS, TREE_REPLAYS, records  # noqa: E402


def build(out: Path, ports: LevelEngineOperationPorts) -> list[str]:
    bundles, reach = ports.bundles, ports.reach
    if out.exists() and any(path.name != "bindings" for path in out.iterdir()):
        raise ValueError("OUTPUT_DIRECTORY_OCCUPIED")
    if (out / "bindings/generated").exists():
        raise ValueError("OUTPUT_DIRECTORY_OCCUPIED")
    out.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    index: dict[str, object] = {}
    grades = []

    def put(rel: str, data: bytes) -> None:
        write_bytes(out / rel, data)
        written.append(rel)

    for tag, level, meta in records():
        cid = str(meta["challenge_id"])
        result = run_level(cid)
        inputs = bundles.fixture_inputs(cid)
        bundles.check_injective(inputs)
        ev = dumps(bundles.evidence(result))
        loss = dumps(bundles.loss_ledger(result))
        ev_sha, loss_sha = "sha256:" + sha256_hex(ev), "sha256:" + sha256_hex(loss)
        bundle = dumps(bundles.witness_bundle(result, ev_sha, loss_sha, inputs))
        b_sha = "sha256:" + sha256_hex(bundle)
        put(f"bundles/{sha256_hex(bundle)}.json", bundle)
        put(f"bundles/{sha256_hex(ev)}.evidence.json", ev)
        put(f"bundles/{sha256_hex(loss)}.loss.json", loss)
        index[cid] = {"bundle": b_sha, "evidence": ev_sha, "loss_ledger": loss_sha}
        binding = load_path(current_context().current_path(f"bindings/{tag}.json"))
        assert isinstance(binding, dict)
        gen = "bindings/generated"
        put(f"{gen}/certificates/{tag}.cert.json",
            dumps(bundles.transport_certificate(level, binding, result, b_sha, loss_sha, inputs)))
        put(f"{gen}/register/SC-{tag}.json", dumps(bundles.register_entry(level, result, tag)))
        put(f"{gen}/checker_input/{tag}.json", dumps(bundles.checker_input(level, binding, result, inputs)))
        grades.append(bundles.grade_row(level, result, binding))
        put(f"{gen}/reach/{tag}.stub.json", reach.stub_bytes(level, result, inputs, tag))
        adapter = reach.load_adapter(reach.adapter_path(level, tag))
        if adapter is not None:
            positive = next(f["payload"] for f in adapter.fixtures(result, inputs) if f["kind"] == "positive")
            put(f"{gen}/reach/{tag}.positive.json", dumps(positive))
    put("bindings/generated/reach/axioms.reach.txt", reach.axioms_report_bytes())
    put("bundles/INDEX.json", dumps({"authority_effect": "None", "records": index,
                                     "schema": "level-engine.bundle-index.v1"}))
    props = load_proposals()
    put("bindings/generated/lifts/record_reading.json",
        dumps(ports.ladder_document(certify_ladder(props), props, bundles.sealed_commit())))
    put("bindings/generated/qlevels.json", dumps(ports.registrations(LEVELS, TREE_REPLAYS)))
    put("bindings/generated/grade_table.json", dumps({
        "authority_effect": "None",
        "note": "computed by the harness; reach grades are the receiving side's and are not written here",
        "rows": grades,
        "schema": "level-engine.grade-table.v1",
    }))
    return sorted(written)


def main(argv: list[str] | None = None, ports: LevelEngineOperationPorts | None = None) -> int:
    if ports is None:
        raise ValueError("LEVEL_ENGINE_PORTS_REQUIRED")
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)
    files = build(args.out, ports)
    print(f"wrote {len(files)} files")
    return 0
