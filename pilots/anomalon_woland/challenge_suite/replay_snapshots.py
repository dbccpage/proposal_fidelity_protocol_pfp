"""Offline replay in a clean, detached, disposable checkout.

The supplied checkout is temporarily overlaid with each run's recorded sources,
then restored using explicit paths. No provider dispatch is performed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from hashlib import sha256
from pathlib import Path

from omega_engine_pfp.infrastructure.adapters.pfp_frozen_replay import inside


def git(checkout, *args):
    return subprocess.check_output(["git", "-C", str(checkout), *args], text=True).strip()


def replay(checkout: Path, evidence: Path, output: Path, run_names=()):
    checkout, evidence = checkout.resolve(), evidence.resolve()
    if (
        checkout == Path.cwd().resolve()
        or git(checkout, "rev-parse", "--abbrev-ref", "HEAD") != "HEAD"
    ):
        raise ValueError("USE_A_DISPOSABLE_DETACHED_CHECKOUT")
    if Path(git(checkout, "rev-parse", "--show-toplevel")).resolve() != checkout:
        raise ValueError("CHECKOUT_ROOT_MISMATCH")
    if git(checkout, "status", "--porcelain"):
        raise ValueError("CHECKOUT_MUST_BE_CLEAN")
    if output.exists():
        raise ValueError("REPLAY_RECEIPT_ALREADY_EXISTS")
    rows = []
    env = dict(
        os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(checkout), PYTHONIOENCODING="utf-8"
    )
    for key in tuple(env):
        if key.endswith("API_KEY") or key.endswith("ACCESS_TOKEN"):
            env.pop(key)
    head = git(checkout, "rev-parse", "HEAD")
    for config_path in sorted((evidence / "live").glob("*/config.json")):
        run = config_path.parent
        if run_names and run.name not in run_names:
            continue
        if not (run / "summary.json").exists() or not list(run.glob("stage_*/receipt.json")):
            continue
        config = json.loads(config_path.read_bytes())
        paths = sorted(config["sources"])
        for name in paths:
            target = inside(checkout, name)
            raw = inside(run / "source_snapshot", name).read_bytes()
            if sha256(raw).hexdigest() != config["sources"][name]:
                raise ValueError("SNAPSHOT_DIGEST_MISMATCH")
        tracked = set(git(checkout, "ls-files", "--", *paths).splitlines())
        for name in set(paths) - tracked:
            if inside(checkout, name).exists():
                raise ValueError("UNTRACKED_SNAPSHOT_TARGET_EXISTS")
        live_sources = [
            name
            for name in paths
            if name.endswith(("/challenge_campaign/live.py", "/challenge_suite/live.py"))
            or name == "omega_engine_pfp/infrastructure/challenge_live.py"
        ]
        if len(live_sources) != 1:
            raise ValueError("CAPTURED_LIVE_ENTRYPOINT_REQUIRED")
        module = live_sources[0][:-3].replace("/", ".")
        driver = """import importlib, json, socket, sys
from pathlib import Path
def deny(*args, **kwargs):
    raise RuntimeError("OFFLINE_REPLAY_NETWORK_FORBIDDEN")
socket.create_connection = socket.getaddrinfo = deny
socket.socket.connect = socket.socket.connect_ex = socket.socket.sendto = deny
if hasattr(socket.socket, "sendmsg"):
    socket.socket.sendmsg = deny
count = importlib.import_module(sys.argv[1]).replay_live(Path(sys.argv[2]))
print(json.dumps({"replayed_stages": count}))
"""
        command = [
            sys.executable,
            "-B",
            "-c",
            driver,
            module,
            str(run),
        ]
        try:
            for name in paths:
                target = inside(checkout, name)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(inside(run / "source_snapshot", name).read_bytes())
            process = subprocess.run(
                command,
                cwd=checkout,
                env=env,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            row = dict(
                run=run.name,
                command=command,
                exit_code=process.returncode,
                status="PASS" if process.returncode == 0 else "FAIL",
                config_sha256=sha256(config_path.read_bytes()).hexdigest(),
                stdout=process.stdout,
                stderr=process.stderr,
            )
            rows.append(row)
            print(json.dumps(dict(run=run.name, status=row["status"])), flush=True)
        finally:
            if tracked:
                subprocess.run(
                    ["git", "-C", str(checkout), "restore", "--worktree", "--", *sorted(tracked)],
                    check=True,
                )
            for name in set(paths) - tracked:
                target = inside(checkout, name)
                target.unlink(missing_ok=True)
                parent = target.parent
                while parent != checkout and parent.is_relative_to(checkout):
                    try:
                        parent.rmdir()
                    except OSError:
                        break
                    parent = parent.parent
        if git(checkout, "status", "--porcelain"):
            raise ValueError("DISPOSABLE_CHECKOUT_NOT_RESTORED")
        if row["status"] == "FAIL":
            print(row["stderr"], flush=True)
            break
    result = dict(
        schema="pfp.frozen-replay.v1",
        authority_effect="None",
        head=head,
        python=sys.version,
        provider_calls=0,
        runs=rows,
        status="PASS" if rows and all(r["status"] == "PASS" for r in rows) else "FAIL",
        scope="Saved provider replies with historical source overlays; excludes transport failures and the exploratory NO_LLM sweep",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkout", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--run", action="append", default=[], help="Replay only these saved run names"
    )
    args = parser.parse_args()
    result = replay(args.checkout, args.evidence, args.output, args.run)
    raise SystemExit(0 if result["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
