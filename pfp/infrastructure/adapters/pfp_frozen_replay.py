"""Run an explicitly retained PFP runtime offline after active code moves.

The bundle pins historical sources; it never installs a legacy import facade in
the active application. All execution occurs in a disposable local directory.
AuthorityEffect: None.
"""

from __future__ import annotations

import argparse
import hashlib
from importlib import resources
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


_PROMPT_SOURCE_PREFIX = "education/pfp/infrastructure/yaml/prompts/versioned/"
_PROMPT_RESOURCE_PREFIX = "infrastructure/yaml/prompts/versioned/"
# Original identities and original byte digests; not current-render input pins.
_FROZEN_PROMPT_SOURCES = {
    "PFP-prompt-role-registry-v1.0.0.yaml": (
        "PFP-prompt-role-registry-v1.0.0.yaml",
        "34df63f05c168570e7942dc7cd4c4ddd4911723f35996dc008390bdc4e504d68",
    ),
    "PFP-R0001-v1.0.0.yaml": (
        "PFP-R0001-v1.0.0.yaml",
        "b742ae28054e7745ce29820f594b52f217379154778b9b24e79fd70f8ac0babe",
    ),
    "PFP-T0001-v1.0.0.yaml": (
        "PFP-T0001-v1.0.0.yaml",
        "d5da7ada446ade90d33ba3910838bb1f74eaa9a645243c20b39a39d484638195",
    ),
    "PFP-T0002-v1.0.0.yaml": (
        "PFP-T0002-v1.0.0.yaml",
        "783ba0fc4f809a9aa663e181e03912aaf91907fdac3b4d22232788b85201e3e0",
    ),
    "PFP-T0003-v1.0.0.yaml": (
        "PFP-T0003-v1.0.0.yaml",
        "4da19cc6a7430a6d584c95abfa30ac92f756f716f4f73975244a802ea7626ecd",
    ),
    "README.md": (
        "historical/v1.0.0/README.md",
        "9fc9e32004dc0328441da20b6aa52bb2ffa52b4352447f635f65a897c54f7e82",
    ),
}


def read_frozen_prompt_source(original_path: str) -> bytes:
    """Read one explicitly relocated v1.0.0 source by its original identity.

    Reads packaged historical data when present; otherwise uses the pinned Git
    object. Main retired v1.0.0 assets to Git, so an installation without those
    objects returns FROZEN_SOURCE_UNAVAILABLE. It never substitutes current data.
    Executing an old campaign still requires its bound replay bundle.
    No prefix rewrite, current-profile fallback or legacy import is installed.
    """
    if type(original_path) is not str or not original_path.startswith(_PROMPT_SOURCE_PREFIX):
        raise ValueError("UNKNOWN_FROZEN_PROMPT_SOURCE")
    selected = _FROZEN_PROMPT_SOURCES.get(original_path[len(_PROMPT_SOURCE_PREFIX):])
    if selected is None:
        raise ValueError("UNKNOWN_FROZEN_PROMPT_SOURCE")
    relative, expected = selected
    target = resources.files("pfp").joinpath(_PROMPT_RESOURCE_PREFIX + relative)
    try:
        raw = target.read_bytes()
    except FileNotFoundError as exc:
        try:
            raw = subprocess.check_output(
                ["git", "show", f"56e1e552c5:pfp/{_PROMPT_RESOURCE_PREFIX}{relative}"],
                cwd=Path(__file__).resolve().parents[3],
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            raise ValueError("FROZEN_SOURCE_UNAVAILABLE:" + original_path) from exc
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("FROZEN_SOURCE_DIGEST_MISMATCH:" + original_path)
    return raw


def inside(root: Path, name: str) -> Path:
    relative = Path(name)
    target = (root / relative).resolve()
    if (
        relative.is_absolute()
        or not target.is_relative_to(root.resolve())
        or relative.drive
        or any(part.casefold() == ".git" for part in relative.parts)
    ):
        raise ValueError("FROZEN_REPLAY_PATH_ESCAPE")
    return target


def replay_bundle(repository: Path, bundle: Path, profile: str) -> object:
    repository, bundle = repository.resolve(), bundle.resolve()
    if not bundle.is_relative_to(repository):
        raise ValueError("BUNDLE_OUTSIDE_REPOSITORY")
    manifest = json.loads((bundle / "frozen_runtime.json").read_bytes())
    if manifest["schema"] != "pfp.frozen-runtime-bundle.v1":
        raise ValueError("UNKNOWN_FROZEN_RUNTIME_SCHEMA")
    selected = manifest["profiles"][profile]
    scratch = repository / "scratch" / "pfp-frozen-replay"
    scratch.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix="snapshot-", dir=scratch)).resolve()
    if not stage.is_relative_to(scratch.resolve()):
        raise ValueError("INVALID_REPLAY_TEMP_ROOT")
    try:
        (stage / ".git").mkdir()
        # Copy records before installing verified executables. Evidence may
        # contain replay scripts; it must never replace a pinned source.
        for name in manifest["evidence_paths"]:
            source_name = (
                "adversary/tests/pilots" + name[len("education/pilots"):]
                if name == "education/pilots" or name.startswith("education/pilots/")
                else name
            )
            shutil.copytree(
                inside(repository, source_name),
                inside(stage, name),
                ignore=shutil.ignore_patterns("__pycache__"),
                dirs_exist_ok=True,
            )
        for name, expected in manifest["files"].items():
            raw = inside(bundle / "frozen_sources", name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != expected:
                raise ValueError("FROZEN_SOURCE_DIGEST_MISMATCH:" + name)
            target = inside(stage, name)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            if target.suffix == ".py":
                for parent in target.parents:
                    if parent == stage:
                        break
                    marker = parent / "__init__.py"
                    if marker.relative_to(stage).as_posix() not in manifest["files"]:
                        marker.write_bytes(b"")
        # Block network access before importing the historical application.
        driver = """import importlib, json, runpy, socket, sys
def deny(*args, **kwargs):
    raise RuntimeError("OFFLINE_REPLAY_NETWORK_FORBIDDEN")
socket.create_connection = deny
socket.socket.connect = deny
socket.socket.connect_ex = deny
socket.socket.sendto = deny
if hasattr(socket.socket, "sendmsg"):
    socket.socket.sendmsg = deny
socket.getaddrinfo = deny
profile = json.loads(sys.argv[1])
if "function" in profile:
    result = getattr(importlib.import_module(profile["module"]), profile["function"])()
    print(json.dumps({key: value.decode("utf-8") for key, value in result.items()}))
else:
    sys.argv = [profile["module"], *profile["argv"]]
    runpy.run_module(profile["module"], run_name="__main__")
"""
        environment = dict(
            os.environ,
            PYTHONPATH=str(stage),
            PYTHONDONTWRITEBYTECODE="1",
            PYTHONIOENCODING="utf-8",
            OPENBLAS_NUM_THREADS="1",
            OMP_NUM_THREADS="1",
        )
        for key in tuple(environment):
            if key.endswith("API_KEY") or key.endswith("ACCESS_TOKEN"):
                environment.pop(key)
        completed = subprocess.run(
            [sys.executable, "-B", "-c", driver, json.dumps(selected)],
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
        return json.loads(completed.stdout)
    finally:
        if stage.is_relative_to(scratch.resolve()) and stage.name.startswith("snapshot-"):
            shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--profile", required=True)
    args = parser.parse_args()
    repository = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    print(json.dumps(replay_bundle(repository, args.bundle, args.profile)))


if __name__ == "__main__":
    main()
