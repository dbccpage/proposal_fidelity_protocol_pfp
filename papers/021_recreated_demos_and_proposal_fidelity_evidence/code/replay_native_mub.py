"""Replay the retained native MUB catalog with an explicit output directory.

The adaptation changes one filesystem destination in the original binary.
The native mathematical owner and all positive catalog inputs stay unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import subprocess
import sys
from pathlib import Path

SOURCE = "omega_engine/crates_rs/omega_mub/src/bin/mub6_conj2_verifier.rs"
SOURCE_SHA256 = "208041dfea0b11c8ab460a355446513d9261b06fe492380d90b56e5d07820bbe"
OLD_DESTINATION = (
    'let out_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("artifacts");'
)
NEW_DESTINATION = (
    "let out_dir = std::path::PathBuf::from(std::env::args().nth(1)"
    '.expect("Paper 011 requires an explicit output directory"));'
)
CRATE = Path(__file__).resolve().parent / "native_mub_replay"
SCHEMA = "paper011.native-mub-replay.v1"


class ReplayFailure(ValueError):
    """A source, process, or output obligation failed."""


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def regular(path: Path, *, directory: bool = False) -> None:
    for ancestor in (path, *path.parents):
        metadata = ancestor.lstat()
        if stat.S_ISLNK(metadata.st_mode) or getattr(metadata, "st_file_attributes", 0) & 0x400:
            raise ReplayFailure(f"REDIRECTED_PATH:{ancestor}")
    if directory != stat.S_ISDIR(path.lstat().st_mode):
        raise ReplayFailure(f"WRONG_PATH_KIND:{path}")
    if not directory and not stat.S_ISREG(path.lstat().st_mode):
        raise ReplayFailure(f"NONREGULAR_FILE:{path}")


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode(
        "utf-8"
    )


def strict_json(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ReplayFailure(f"DUPLICATE_JSON_KEY:{key}")
            result[key] = value
        return result

    def nonfinite(value):
        raise ReplayFailure(f"NONFINITE_JSON:{value}")

    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=nonfinite)
    if not isinstance(value, dict):
        raise ReplayFailure("REPORT_NOT_OBJECT")
    return value


def adapted_source(original: bytes) -> bytes:
    if sha(original) != SOURCE_SHA256:
        raise ReplayFailure("ORIGINAL_SOURCE_DIGEST_MISMATCH")
    # Preserve raw line endings and every mathematical/source byte except this destination.
    old = OLD_DESTINATION.encode("utf-8")
    if original.count(old) != 1:
        raise ReplayFailure("OUTPUT_ADAPTATION_NOT_UNIQUE")
    return original.replace(old, NEW_DESTINATION.encode("utf-8"), 1)


def native_sources(repo: Path) -> dict:
    regular(repo, directory=True)
    command = ["git", "ls-files", "-z", "--", "omega_engine/crates_rs"]
    run = subprocess.run(command, cwd=repo, capture_output=True, check=True)
    names = run.stdout.decode("utf-8").rstrip("\0").split("\0")
    if not names or names == [""]:
        raise ReplayFailure("EMPTY_NATIVE_SOURCE_INVENTORY")
    files = []
    for name in sorted(names, key=lambda value: value.encode("utf-8")):
        path = repo / name
        regular(path)
        data = path.read_bytes()
        files.append({"path": name, "sha256": sha(data), "size_bytes": len(data)})
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, check=True, text=True
    ).stdout.strip()
    clean = subprocess.run(
        ["git", "diff", "--quiet", "HEAD", "--", "omega_engine/crates_rs"], cwd=repo, check=False
    )
    if clean.returncode != 0:
        raise ReplayFailure("NATIVE_TRACKED_SOURCE_DRIFT")
    return {"git_head": head, "files": files, "inventory_sha256": sha(canonical(files))}


def validate_report(raw: bytes, retained: bytes) -> dict:
    report = strict_json(raw)
    payload = {key: value for key, value in report.items() if key != "sha256"}
    if report.get("sha256") != sha(canonical(payload)):
        raise ReplayFailure("PAYLOAD_DIGEST_MISMATCH")
    expected = strict_json(retained)
    if report != expected:
        raise ReplayFailure("RETAINED_CATALOG_RESULT_MISMATCH")
    if report.get("schema") != "omega.mub6.conj2-verification.v3":
        raise ReplayFailure("REPORT_SCHEMA_MISMATCH")
    for key, expected_value in (
        ("total_triples_tested", 7),
        ("total_triples_passed", 7),
        ("total_triples_failed", 0),
    ):
        if type(report.get(key)) is not int or report[key] != expected_value:
            raise ReplayFailure(f"CATALOG_COUNT_MISMATCH:{key}")
    ids = [
        "T0_canonical",
        "Dita_F6_0_8_Y2Q1",
        "Dita_F6_8_0_Y2Q1",
        "Dita_F6_16_16_Y2Q1",
        "Dita_F6_0_16_Y2Q2",
        "Dita_F6_8_8_Y2Q2",
        "Dita_F6_16_0_Y2Q2",
    ]
    rows = report.get("results")
    if not isinstance(rows, list) or [row.get("triple_id") for row in rows] != ids:
        raise ReplayFailure("CATALOG_ID_MISMATCH")
    for row in rows:
        if row.get("all_hold") is not True:
            raise ReplayFailure("TRIPLE_NOT_CHECKED")
        for matrix in ("h12", "h23", "h31"):
            value = row[matrix]
            if value.get("matrix_id") != f"{row['triple_id']}_{matrix.upper()}":
                raise ReplayFailure("MATRIX_ID_MISMATCH")
            for flag in ("gamma1_all_zero", "gamma2_product_all_zero", "conjecture_2_holds"):
                if value.get(flag) is not True:
                    raise ReplayFailure("MATRIX_OBLIGATION_FAILED")
            for count in ("gamma1_failures", "gamma2_failures"):
                if type(value.get(count)) is not int or value[count] != 0:
                    raise ReplayFailure("MATRIX_FAILURE_COUNT")
    return {"triples": 7, "transition_matrices": 21, "payload_sha256": report["sha256"]}


def replay(repo: Path, binary: Path, binary_sha256: str, output: Path, timeout: int) -> dict:
    if output.exists():
        raise ReplayFailure("OUTPUT_DIRECTORY_ALREADY_EXISTS")
    regular(output.parent, directory=True)
    regular(binary)
    if sha(binary.read_bytes()) != binary_sha256:
        raise ReplayFailure("EXECUTABLE_DIGEST_MISMATCH")
    original = repo / SOURCE
    regular(original)
    source = original.read_bytes()
    expected_adaptation = adapted_source(source)
    runner = CRATE / "src/main.rs"
    regular(runner)
    if runner.read_bytes() != expected_adaptation:
        raise ReplayFailure("RUNNER_NOT_OUTPUT_ONLY_ADAPTATION")
    control_paths = [
        Path(__file__),
        runner,
        CRATE / "Cargo.toml",
        CRATE / "Cargo.lock",
        CRATE / "tests/native_controls.rs",
    ]
    controls_before = []
    for path in control_paths:
        regular(path)
        controls_before.append({"path": str(path), "sha256": sha(path.read_bytes())})
    retained_path = repo / "omega_engine/crates_rs/omega_mub/artifacts/mub6_conj2_verification.json"
    regular(retained_path)
    retained = retained_path.read_bytes()
    before = native_sources(repo)
    output.mkdir()
    command = [str(binary.resolve()), str(output.resolve())]
    process = subprocess.run(command, capture_output=True, timeout=timeout, check=False, cwd=output)
    (output / "stdout.bin").write_bytes(process.stdout)
    (output / "stderr.bin").write_bytes(process.stderr)
    if process.returncode != 0:
        raise ReplayFailure(f"NONZERO_NATIVE_EXIT:{process.returncode}")
    report_path = output / "mub6_conj2_verification.json"
    regular(report_path)
    report = report_path.read_bytes()
    controls = validate_report(report, retained)
    after = native_sources(repo)
    if before != after or binary_sha256 != sha(binary.read_bytes()):
        raise ReplayFailure("POST_EXECUTION_CUSTODY_DRIFT")
    for control in controls_before:
        path = Path(control["path"])
        regular(path)
        if sha(path.read_bytes()) != control["sha256"]:
            raise ReplayFailure("POST_EXECUTION_RUNNER_DRIFT")
    artifacts = [
        {"path": path.name, "sha256": sha(path.read_bytes()), "size_bytes": path.stat().st_size}
        for path in sorted(output.iterdir(), key=lambda path: path.name.encode("utf-8"))
    ]
    result = {
        "schema_version": SCHEMA,
        "status": "NATIVE_FINITE_CATALOG_REPLAYED",
        "source": {"path": SOURCE, "sha256": sha(source)},
        "adaptation": {
            "sha256": sha(expected_adaptation),
            "permitted_change": "output directory only",
        },
        "binary_sha256": binary_sha256,
        "native_source_snapshot": before,
        "runner_controls": controls_before,
        "request": {"argv": command, "stdin": "none; original fixed seven-triple catalog"},
        "process_exit_code": process.returncode,
        "artifacts": artifacts,
        "checked_observations": controls,
        "post_execution_custody": "UNCHANGED",
        "scope": "Exact native calculation on the original seven catalog triples; no generic Conjecture 2 or MUB(6) bound is established.",
    }
    (output / "receipt.json").write_bytes(canonical(result) + b"\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--binary", type=Path)
    parser.add_argument("--binary-sha256")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args()
    if args.prepare:
        data = (args.source_repo / SOURCE).read_bytes()
        target = CRATE / "src/main.rs"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(adapted_source(data))
        print(
            json.dumps({"original_sha256": sha(data), "adapted_sha256": sha(target.read_bytes())})
        )
        return 0
    if not args.binary or not args.binary_sha256 or not args.output_dir or args.timeout <= 0:
        parser.error(
            "replay requires explicit binary, digest, output directory, and positive timeout"
        )
    result = replay(
        args.source_repo, args.binary, args.binary_sha256, args.output_dir, args.timeout
    )
    print(json.dumps({"status": result["status"], **result["checked_observations"]}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ReplayFailure, OSError, subprocess.SubprocessError) as exc:
        print(f"NATIVE_MUB_REPLAY_REFUSED:{exc}", file=sys.stderr)
        sys.exit(2)
