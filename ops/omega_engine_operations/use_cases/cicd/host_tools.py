"""Absolute git and cargo paths for gates whose parent removed PATH."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path

_MIN_BUILD_FREE_BYTES = 5 * 1024**3
_BUILD_POLL_SECONDS = 0.5
_WINDOWS_PROCESS_CONTROL = os.name == "nt"


def _outside_repository(path: Path, repository: Path) -> bool:
    try:
        path.resolve().relative_to(repository.resolve())
    except ValueError:
        return True
    return False


def _accept(candidate: Path, repository: Path) -> Path | None:
    if not candidate.is_file():
        return None
    absolute = Path(os.path.abspath(candidate))
    if not _outside_repository(absolute, repository):
        return None
    return absolute


def resolve_from_env(name: str, repository: Path) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return _accept(Path(value), repository)


def resolve_git_executable(repository: Path) -> Path | None:
    trusted = resolve_from_env("OMEGA_TRUSTED_GIT", repository)
    if trusted is not None:
        return trusted
    for key, parts in (
        ("ProgramFiles", ("Git", "cmd", "git.exe")),
        ("ProgramFiles(x86)", ("Git", "cmd", "git.exe")),
        ("LOCALAPPDATA", ("Programs", "Git", "cmd", "git.exe")),
    ):
        root = os.environ.get(key)
        if not root:
            continue
        found = _accept(Path(root).joinpath(*parts), repository)
        if found is not None:
            return found
    local = os.environ.get("LOCALAPPDATA")
    if local:
        matches = sorted(Path(local).glob("grok/git/*/cmd/git.exe"))
        if matches:
            found = _accept(matches[-1], repository)
            if found is not None:
                return found
    return None


def resolve_cargo_executable(repository: Path) -> Path | None:
    trusted = resolve_from_env("OMEGA_TRUSTED_CARGO", repository)
    if trusted is not None:
        return trusted
    roots: list[Path] = []
    cargo_home = os.environ.get("CARGO_HOME")
    if cargo_home:
        roots.append(Path(cargo_home))
    profile = os.environ.get("USERPROFILE")
    if profile:
        roots.append(Path(profile) / ".cargo")
    home = f"{os.environ.get('HOMEDRIVE', '')}{os.environ.get('HOMEPATH', '')}"
    if home:
        roots.append(Path(home) / ".cargo")
    names = ("cargo.exe", "cargo") if os.name == "nt" else ("cargo",)
    seen: set[Path] = set()
    for root in roots:
        if root in seen:
            continue
        seen.add(root)
        for name in names:
            found = _accept(root / "bin" / name, repository)
            if found is not None:
                return found
    return None


def shared_cargo_target_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA") or os.environ.get("TEMP") or os.getcwd()
    return Path(local) / "omega-review-cargo-target"


def _toolchain_environment(cargo: Path, target: Path) -> dict[str, str]:
    environment = dict(os.environ)
    parts = [str(cargo.parent)]
    system_root = os.environ.get("SYSTEMROOT") or os.environ.get("SystemRoot")
    if system_root:
        parts.append(str(Path(system_root) / "System32"))
        parts.append(system_root)
    environment["PATH"] = os.pathsep.join(parts)
    if os.name == "nt":
        environment["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
    environment["CARGO_TARGET_DIR"] = str(target)
    environment["CARGO_INCREMENTAL"] = "0"
    environment["CARGO_PROFILE_DEV_DEBUG"] = "0"
    return environment


def _build_disk_available(target: Path) -> bool:
    try:
        free_bytes = shutil.disk_usage(target).free
    except OSError as error:
        print(f"BUILD_DISK_BUDGET_REFUSED: {error}", file=sys.stderr)
        return False
    if free_bytes < _MIN_BUILD_FREE_BYTES:
        print(
            f"BUILD_DISK_BUDGET_REFUSED: {free_bytes} bytes free at {target}; "
            f"require at least {_MIN_BUILD_FREE_BYTES} throughout Cargo build",
            file=sys.stderr,
        )
        return False
    return True


def _stop_owned_build(process: subprocess.Popen) -> None:
    """Attempt Windows tree cleanup; request POSIX abort; reap the owned leader."""
    try:
        if _WINDOWS_PROCESS_CONTROL:
            system_root = os.environ.get("SYSTEMROOT") or os.environ["SystemRoot"]
            stopped = subprocess.run(
                [
                    str(Path(system_root) / "System32" / "taskkill.exe"),
                    "/PID",
                    str(process.pid),
                    "/T",
                    "/F",
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=10,
                check=False,
            )
            if stopped.returncode != 0:
                print(
                    "BUILD_CLEANUP_REFUSED: owned build tree termination unconfirmed",
                    file=sys.stderr,
                )
        else:
            print(
                "BUILD_CLEANUP_REFUSED: POSIX descendants unverified; "
                "requesting owned Cargo abort without signaling the inherited group",
                file=sys.stderr,
            )
            if process.poll() is None:
                process.send_signal(signal.SIGINT)
                process.wait(timeout=2)
    except (OSError, subprocess.SubprocessError, KeyError) as error:
        print(f"BUILD_CLEANUP_REFUSED: {error}", file=sys.stderr)
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=10)


def ensure_symbol_game_host(repository: Path) -> Path | None:
    """Build omega_symbol_game into a shared target and return the binary.

    A fresh review worktree has no target directory. Dependency artifacts stay
    in LOCALAPPDATA so the next pull request does not recompile the registry.
    """

    cargo = resolve_cargo_executable(repository)
    if cargo is None:
        return None
    target = shared_cargo_target_dir()
    manifest = repository / "omega_engine" / "crates_rs" / "Cargo.toml"
    if not manifest.is_file():
        return None
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        print(f"BUILD_DISK_BUDGET_REFUSED: {error}", file=sys.stderr)
        return None
    if not _build_disk_available(target):
        return None
    process = None
    completed = False
    try:
        process = subprocess.Popen(
            [
                str(cargo),
                "build",
                "-j",
                "1",
                "--manifest-path",
                str(manifest),
                "-p",
                "omega_symbol_game",
                "--bin",
                "omega_symbol_game",
            ],
            cwd=repository,
            env=_toolchain_environment(cargo, target),
            stdin=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if _WINDOWS_PROCESS_CONTROL else 0,
            start_new_session=False,
        )
        while True:
            try:
                returncode = process.wait(timeout=_BUILD_POLL_SECONDS)
                completed = True
                break
            except subprocess.TimeoutExpired:
                if not _build_disk_available(target):
                    return None
    finally:
        if process is not None and not completed:
            _stop_owned_build(process)
    disk_available = _build_disk_available(target)
    if returncode != 0 or not disk_available:
        return None
    name = "omega_symbol_game.exe" if os.name == "nt" else "omega_symbol_game"
    binary = target / "debug" / name
    if not binary.is_file():
        return None
    return binary
