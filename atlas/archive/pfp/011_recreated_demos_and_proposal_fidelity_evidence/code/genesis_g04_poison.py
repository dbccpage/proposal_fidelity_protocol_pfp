"""Separately declared universal fixed-stake poison; never a recovered held-out."""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

PAPER = Path(__file__).resolve().parent.parent
MAIN_PATH = PAPER / "code/genesis_g04_replay.py"
# No import occurs until the closed original receipts and helper are verified.
BUILD = PAPER / "docs/history_recovery/g04/native_build_v1/receipt.json"
MAIN_RUN = PAPER / "docs/history_recovery/g04/full_rectangle_v2/receipt.json"
BUILD_SHA = "1f5867b3763a733c0dcc6cca042a352345e3e7e1b721330ad17edd756a71cd80"
MAIN_RUN_SHA = "aa3fee6d6bbcc2dbd2faf0f370e2165f1ae041e33d2d12c1918f8940edd60602"


def load_main():
    import hashlib
    raw = BUILD.read_bytes()
    if hashlib.sha256(raw).hexdigest() != BUILD_SHA or hashlib.sha256(MAIN_RUN.read_bytes()).hexdigest() != MAIN_RUN_SHA:
        raise ValueError("CLOSED_G04_RECEIPT_CHANGED")
    build = json.loads(raw)
    for path, digest in build["inputs_after"].items():
        if hashlib.sha256(Path(path).read_bytes()).hexdigest() != digest:
            raise ValueError("ORIGINAL_G04_BUILD_INPUT_CHANGED:" + path)
    expected = build["inputs_after"][str(MAIN_PATH.resolve())]
    if hashlib.sha256(MAIN_PATH.read_bytes()).hexdigest() != expected:
        raise ValueError("CLOSED_G04_HELPER_CHANGED")
    spec = importlib.util.spec_from_file_location("g04_bound_composition", MAIN_PATH)
    if spec is None or spec.loader is None:
        raise ValueError("G04_COMPOSITION_LOADER")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def dependencies(g04) -> dict:
    paths = [Path(path) for path in g04.native_dependencies()]
    manifest = g04.verify_sources()
    paths += [PAPER / row["path"] for row in manifest["files"]]
    paths += [Path(__file__), g04.PACKAGE / "fixed_stake_poison.rs", g04.AREA / "source_manifest.json", BUILD, MAIN_RUN]
    return g04.files(paths)


def build_native(g04, identity: str) -> dict:
    destination = g04.AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    before = dependencies(g04)
    executable = destination / "g04_fixed_stake_poison.exe"
    argv = [str(g04.RUSTC), "--edition", "2021", "--crate-name", "paper011_g04_fixed_stake_poison",
        str(g04.PACKAGE / "fixed_stake_poison.rs"), "-L", "dependency=" + str(g04.DEPS),
        "--extern", "core_ooutwire_primitives=" + str(g04.DEPS / "libcore_ooutwire_primitives-7419c0b1b3d813be.rlib"),
        "--extern", "serde_json=" + str(g04.DEPS / "libserde_json-1a3e70913255bad6.rlib"), "-o", str(executable)]
    process = subprocess.run(argv, capture_output=True, check=False, timeout=300, cwd=g04.PACKAGE)
    after = dependencies(g04)
    if before != after:
        raise ValueError("POISON_BUILD_INPUT_DRIFT")
    (destination / "stdout.bin").write_bytes(process.stdout)
    (destination / "stderr.bin").write_bytes(process.stderr)
    return g04.save(destination / "receipt.json", {"schema": "paper011.g04-poison-build.v1", "AuthorityEffect": "None",
        "argv": argv, "returncode": process.returncode, "inputs_before": before, "inputs_after": after,
        "stdout_sha256": g04.sha(process.stdout), "stderr_sha256": g04.sha(process.stderr),
        "executable": str(executable), "executable_sha256": g04.sha(executable.read_bytes()) if executable.exists() else None,
        "scope": "Separate supplemental fixture, exact existing native archives and original G04 import closure. No owner mathematics, providers or Cargo; original complete rectangle remains frozen."})


def run(g04, identity: str, build_path: Path) -> dict:
    destination = g04.AREA / identity
    destination.mkdir(parents=True, exist_ok=False)
    raw_build = build_path.read_bytes()
    build = json.loads(raw_build)
    if build["returncode"] != 0 or build["inputs_before"] != build["inputs_after"]:
        raise ValueError("SUPPLEMENT_BUILD_NOT_CLOSED")
    before = dependencies(g04)
    for path, digest in build["inputs_after"].items():
        if before.get(path) != digest:
            raise ValueError("SUPPLEMENT_DEPENDENCY_DRIFT:" + path)
    executable = Path(build["executable"])
    if g04.sha(executable.read_bytes()) != build["executable_sha256"]:
        raise ValueError("SUPPLEMENT_EXECUTABLE_DRIFT")
    original_run = json.loads(MAIN_RUN.read_bytes())
    source_ref = original_run["source_census"]
    source_path = PAPER / source_ref["path"]
    raw_source = source_path.read_bytes()
    if g04.sha(raw_source) != source_ref["sha256"]:
        raise ValueError("ORIGINAL_CENSUS_BYTES_CHANGED")
    source = json.loads(raw_source)
    histories = [[{"kind": "AdmitForm", "arity": 1}, {"kind": "AdmitInst", "form": 0, "args": [i]},
                  {"kind": "AdmitDatum", "token": "<n0>"}] for i in (0, 1)]
    base = next(base for base in source["bases"] if base["name"] == "L")
    rows = [next(row for row in base["rows"] if row["history"] == h) for h in histories]
    pi, phi = [1, 0, 2], [0]
    relation = next(r for r in base["relations"] if r["pi"] == pi and r["phi"] == phi
                    and r["source"] == next(g["representative"] for g in base["groups"] if rows[0]["id"] in g["members"])
                    and r["target"] == next(g["representative"] for g in base["groups"] if rows[1]["id"] in g["members"]))
    original, finder = g04.load_original()
    index, nf, model, iso = (original[name] for name in ("index", "nofirst", "model", "iso"))
    stake = nf.Stake("G04_SUPPLEMENT_APART_0_2", lambda i, j: "apart" if (i, j) == (0, 2) else "free")
    inverse = [pi.index(i) for i in range(len(pi))]
    transported = nf.Stake("G04_SUPPLEMENT_APART_0_2_TRANSPORTED", lambda i, j: stake.label(inverse[i], inverse[j]))
    base_regime = index.base_regime("L")
    hs = [tuple(g04.parse_event(e, model) for e in h) for h in histories]
    traces = [[model.replay(h[:n], base_regime) for n in range(len(h) + 1)] for h in hs]
    for n, (a, b) in enumerate(zip(*traces, strict=True)):
        if iso.serialize(a, pi, phi) != iso.serialize(b, range(b.n_data()), range(len(b.forms))):
            raise ValueError("SOURCE_COMMON_MAPPING_FAILED:" + str(n))
    seen = index.Observations()
    fixed = [index.first_index_forward(base_regime, h, stake, seen) for h in hs]
    scan = [index.first_index_scan(base_regime, h, stake, seen) for h in hs]
    transported_first = [fixed[0], index.first_index_forward(base_regime, hs[1], transported, seen)]
    if fixed != scan or fixed != [None, 3] or transported_first != [None, None]:
        raise ValueError("SUPPLEMENT_SOURCE_WITNESS_FAILED")
    labels = [[stake.label(i, j) for j in range(3)] for i in range(3)]
    transported_labels = [[transported.label(i, j) for j in range(3)] for i in range(3)]
    request = {"id": "universal_fixed_stake_counterexample", "mode": "compute", "base": "L", "histories": histories,
        "pi": pi, "phi": phi, "labels": labels, "reported_transported_labels": transported_labels,
        "original_row_ids": [row["id"] for row in rows], "original_common_mapping": relation}
    compute = g04.native_call(executable, request, destination, "counterexample")
    value = compute["value"]
    if value["fixed_first"] != fixed or value["transported_first"] != transported_first:
        raise ValueError("SUPPLEMENT_NATIVE_INDEX_DISAGREEMENT")
    if value["source_prefixes"] != rows[0]["prefixes"] or value["target_prefixes"] != rows[1]["prefixes"]:
        raise ValueError("SUPPLEMENT_NATIVE_PREFIX_DISAGREEMENT")
    controls = [compute["receipt"]]
    bad = {**request, "id": "universal_fixed_stake_poison", "mode": "assert_universal_fixed"}
    controls.append(g04.native_call(executable, bad, destination, bad["id"], "UNIVERSAL_FIXED_STAKE_POISON:[null,3]")["receipt"])
    bad = {**request, "id": "wrong_common_data_mapping", "pi": [0, 1, 2]}
    controls.append(g04.native_call(executable, bad, destination, bad["id"], "COMMON_PREFIX_ISOMORPHISM:2")["receipt"])
    bad = {**request, "id": "untransported_supplement_stake", "mode": "assert_transported", "reported_transported_labels": labels}
    controls.append(g04.native_call(executable, bad, destination, bad["id"], "STAKE_TRANSPORT_MISMATCH")["receipt"])
    after = dependencies(g04)
    if before != after or g04.sha(source_path.read_bytes()) != source_ref["sha256"]:
        raise ValueError("SUPPLEMENT_POSTFLIGHT_DRIFT")
    receipt = {"schema": "paper011.g04-universal-poison.v1", "AuthorityEffect": "None",
        "original_full_rectangle_receipt": {"path": MAIN_RUN.relative_to(PAPER).as_posix(), "sha256": g04.sha(MAIN_RUN.read_bytes())},
        "original_source_census": source_ref, "supplement_build": {"path": build_path.relative_to(PAPER).as_posix(), "sha256": g04.sha(raw_build)},
        "inputs_before": before, "inputs_after": after, "source_row_ids": [row["id"] for row in rows],
        "fixed_first_forward": fixed, "fixed_first_scan": scan, "transported_first": transported_first,
        "declared_supplement_stake": "apart only on unordered {0,2}; free on every other pair", "labels": labels,
        "histories": histories, "pi": pi, "phi": phi, "source_common_mapping": relation,
        "native_controls": controls, "controls_passed": len(controls), "new_poison_refusals": 3,
        "import_journal": finder.journal, "provider_calls": 0,
        "empty_cache_prefix": sys.pycache_prefix, "dont_write_bytecode": sys.dont_write_bytecode,
        "verdict": "UNIVERSAL_FIXED_STAKE_CLAIM_REFUTED",
        "historical_operator_heldout": False, "historical_heldout_gate_complete": False,
        "scope": "Separate mathematical counterexample on exact histories already in the original full rectangle. This is neither of the unavailable operator stakes, and supplies no unavailable length-five sample. Original seven-stake fixed invariance remains HOLDS_ON_RECTANGLE."}
    return g04.save(destination / "receipt.json", receipt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("build", "run"))
    parser.add_argument("--identity", required=True)
    parser.add_argument("--build-receipt", type=Path)
    args = parser.parse_args()
    g04 = load_main()
    result = build_native(g04, args.identity) if args.action == "build" else run(g04, args.identity, args.build_receipt.resolve())
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
