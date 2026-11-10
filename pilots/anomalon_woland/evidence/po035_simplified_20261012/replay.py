"""Replay from frozen source bytes even after later prompt versions are added."""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    evidence = Path(__file__).resolve().parent
    repository = next(p for p in evidence.parents if (p / ".git").exists())
    pins = json.loads((evidence / "sources.json").read_text(encoding="utf-8"))
    dependencies = json.loads((evidence / "replay_dependencies.json").read_text(encoding="utf-8"))
    if set(pins["files"]) & set(dependencies["files"]):
        raise ValueError("DUPLICATE_REPLAY_SOURCE")
    scratch = repository / "scratch" / "po035-frozen-replay"
    scratch.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="snapshot-", dir=scratch)).resolve()
    # The temporary tree and its eventual cleanup are constrained to this workspace.
    if not stage.is_relative_to(scratch.resolve()):
        raise ValueError("INVALID_REPLAY_TEMP_ROOT")
    try:
        (stage / ".git").mkdir()
        files = [
            (name, sha, evidence / kind)
            for kind, inventory in (
                ("source_snapshot", pins),
                ("replay_dependencies", dependencies),
            )
            for name, sha in inventory["files"].items()
        ]
        for name, sha, source_root in files:
            relative = Path(name)
            source = (source_root / relative).resolve()
            target = (stage / relative).resolve()
            if not source.is_relative_to(source_root.resolve()) or not target.is_relative_to(stage):
                raise ValueError("INVALID_SOURCE_SNAPSHOT_PATH")
            raw = source.read_bytes()
            if hashlib.sha256(raw).hexdigest() != sha:
                raise ValueError("SOURCE_SNAPSHOT_DIGEST_MISMATCH")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            if target.suffix == ".py":
                # Empty package markers isolate the retained modules from any
                # editable installation or future checkout on Python's path.
                for parent in target.parents:
                    if parent == stage:
                        break
                    (parent / "__init__.py").touch()
        frozen_evidence = stage / evidence.relative_to(repository)
        shutil.copytree(
            evidence,
            frozen_evidence,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__"),
        )
        environment = dict(
            os.environ,
            PYTHONPATH=str(stage),
            PYTHONIOENCODING="utf-8",
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "omega_engine_education.pfp.infrastructure.po035.simplified_round",
                "replay",
            ],
            cwd=stage,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=60,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError("FROZEN_REPLAY_FAILED:\n" + completed.stderr)
        rows = json.loads(completed.stdout)
        expected = {f"pilot_{number:07d}" for number in range(199, 204)}
        if (
            {row["pilot_id"] for row in rows} != expected
            or len(rows) != 5
            or any(row["replayed_calls"] != 3 or row["new_provider_calls"] != 0 for row in rows)
        ):
            raise ValueError("INCOMPLETE_FROZEN_REPLAY")
        print(
            json.dumps(
                {
                    "source_files": len(pins["files"]),
                    "replay_only_dependency_files": len(dependencies["files"]),
                    "replayed_calls": 15,
                    "new_provider_calls": 0,
                    "runtime": "retained source snapshot",
                    "replays": rows,
                }
            )
        )
    finally:
        if stage.is_relative_to(scratch.resolve()) and stage.name.startswith("snapshot-"):
            shutil.rmtree(stage)


if __name__ == "__main__":
    main()
