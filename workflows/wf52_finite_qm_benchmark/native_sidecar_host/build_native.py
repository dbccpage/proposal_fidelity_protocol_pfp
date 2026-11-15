"""Build only this isolated, offline native experiment and retain exact custody.

AuthorityEffect: None.
Contract: urn:pfp-wf52:build-native:v1
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OWNER = ROOT / "code/rust/pfp_runtime/src/rational.rs"
OWNER_SHA = "9d78981a19c942a70d4d4262f1df9538024754b2b87c0e0288a46d377cd3916c"
PREFIX = b"// Verbatim production owner lines 291..353; see source_binding.json.\nimpl RationalMatrix {\n"
SUFFIX = b"}\n"
ALLOW_ENV = {
    "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
    "TMPDIR", "HOME", "USERPROFILE", "HOMEDRIVE", "HOMEPATH",
    "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432",
    "CARGO_HOME", "RUSTUP_HOME",
}
MSVC_LINKER = Path(
    "C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Tools/MSVC/14.44.35207/bin/Hostx64/x64/link.exe"
)
WIN_SDK = Path("C:/Program Files (x86)/Windows Kits/10/Lib/10.0.26100.0")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _exe_suffix(platform: str | None = None) -> str:
    target = sys.platform if platform is None else platform
    return ".exe" if target == "win32" else ""


def _platform_link_flags(platform: str | None = None) -> list[str]:
    target = sys.platform if platform is None else platform
    if target == "win32":
        return ["-C", "link-arg=/Brepro", "-C", "link-arg=/DEBUG:NONE"]
    if target.startswith("linux"):
        return ["-C", "link-arg=-Wl,--build-id=none", "-C", "strip=debuginfo"]
    return ["-C", "strip=debuginfo"]


def deterministic_cargo_env(folder: Path, sysroot: str, platform: str | None = None) -> tuple[dict[str, str], Path]:
    """Build sanitized, reproducible Cargo/MSVC environment for ``folder``."""
    env = {k: v for k, v in os.environ.items() if k.upper() in ALLOW_ENV}
    env.update(
        CARGO_NET_OFFLINE="true",
        CARGO_TARGET_DIR=str(folder / "target"),
        CARGO_BUILD_JOBS="1",
        CARGO_INCREMENTAL="0",
    )
    if MSVC_LINKER.is_file():
        env["PATH"] = str(MSVC_LINKER.parent) + os.pathsep + env.get("PATH", "")
        env["LIB"] = os.pathsep.join(
            str(p) for p in [MSVC_LINKER.parents[3] / "lib/x64", WIN_SDK / "ucrt/x64", WIN_SDK / "um/x64"]
        )
    folder_resolved = folder.resolve()
    cargo_home = Path(os.environ.get("CARGO_HOME") or (Path.home() / ".cargo")).resolve()
    remaps = [
        f"--remap-path-prefix={folder_resolved / 'target'}=/pfp_target",
        f"--remap-path-prefix={folder_resolved}=/pfp_sidecar",
        f"--remap-path-prefix={cargo_home}=/cargo_home",
        f"--remap-path-prefix={Path(sysroot.strip()).resolve()}=/rust_sysroot",
        *_platform_link_flags(platform),
    ]
    env["CARGO_ENCODED_RUSTFLAGS"] = "\x1f".join(remaps)
    return env, MSVC_LINKER


def _sync_source_binding() -> tuple[dict, Path]:
    owner = OWNER.read_bytes()
    if hashlib.sha256(owner).hexdigest() != OWNER_SHA:
        raise RuntimeError("SOURCE_OWNER_CHANGED")
    fragment = b"".join(owner.splitlines(keepends=True)[290:353])
    generated = HERE / "src/production_charpoly.rs"
    expected_generated = PREFIX + fragment + SUFFIX
    if not generated.is_file() or generated.read_bytes() != expected_generated:
        generated.write_bytes(expected_generated)
    binding = {
        "owner": OWNER.relative_to(ROOT).as_posix(),
        "owner_sha256": OWNER_SHA,
        "lines": [291, 353],
        "transfer": "verbatim bytes, including original line endings",
        "fragment_sha256": hashlib.sha256(fragment).hexdigest(),
        "generated_path": "src/production_charpoly.rs",
        "generated_sha256": sha(generated),
        "prefix_bytes": len(PREFIX),
        "fragment_bytes": len(fragment),
        "scope": "Only these four arithmetic methods are reused; carrier and admission are new wrapper code.",
    }
    binding_path = HERE / "source_binding.json"
    existing = json.loads(binding_path.read_text(encoding="utf-8")) if binding_path.is_file() else None
    if existing != binding:
        binding_path.write_text(json.dumps(binding, indent=2) + "\n", encoding="utf-8", newline="\n")
    return binding, generated


def main():
    binding, generated = _sync_source_binding()
    cargo = shutil.which("cargo")
    rustc = shutil.which("rustc")
    if not cargo or not rustc:
        raise RuntimeError("NATIVE_TOOLCHAIN_UNAVAILABLE")
    base_env = {k: v for k, v in os.environ.items() if k.upper() in ALLOW_ENV}
    commands = []

    def run(args, env, timeout=120):
        result = subprocess.run(
            args, cwd=HERE, env=env, capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=timeout,
        )
        commands.append({"args": args, "returncode": result.returncode,
                         "stdout": result.stdout, "stderr": result.stderr})
        return result

    receipt = {
        "schema": "pfp.native-sidecar.build.v1",
        "status": "INFRASTRUCTURE_REFUSAL",
        "commands": commands,
        "source_binding": binding,
        "provider_calls": 0,
        "scope": "Standalone exact arithmetic extraction only; not the full PFP host.",
    }
    try:
        sysroot = run([rustc, "--print", "sysroot"], base_env)
        if sysroot.returncode:
            raise RuntimeError("TOOLCHAIN_QUERY_FAILED")
        env, linker = deterministic_cargo_env(HERE, sysroot.stdout)
        if linker.is_file():
            receipt["linker"] = {"path": str(linker), "sha256": sha(linker), "library_paths": env["LIB"]}
        for args in ([rustc, "--version", "--verbose"], [cargo, "--version", "--verbose"]):
            if run(args, env).returncode:
                raise RuntimeError("TOOLCHAIN_QUERY_FAILED")
        toolroot = Path(sysroot.stdout.strip()) / "bin"
        suffix = _exe_suffix()
        receipt["toolchain"] = {
            name: {"path": str(toolroot / name), "sha256": sha(toolroot / name)}
            for name in (f"rustc{suffix}", f"cargo{suffix}")
        }
        receipt["launcher_hashes"] = {cargo: sha(cargo), rustc: sha(rustc)}
        lock_path = HERE / "Cargo.lock"
        if lock_path.exists():
            receipt["lock_policy"] = "preserved_existing"
        else:
            receipt["lock_policy"] = "generated_only_when_absent"
            if run([cargo, "generate-lockfile", "--offline"], env).returncode:
                raise RuntimeError("OFFLINE_DEPENDENCY_LOCK_FAILED")
        receipt["lock_sha256_before_build"] = sha(lock_path)
        if run([cargo, "build", "--offline", "--locked", "--jobs", "1"], env, timeout=180).returncode:
            raise RuntimeError("ISOLATED_NATIVE_BUILD_FAILED")
        receipt["lock_sha256_after_build"] = sha(lock_path)
        if receipt["lock_sha256_after_build"] != receipt["lock_sha256_before_build"]:
            raise RuntimeError("DEPENDENCY_LOCK_CHANGED")
        binary = HERE / f"target/debug/pfp-native-sidecar-host{suffix}"
        receipt.update(
            status="BUILT",
            binary={"path": binary.relative_to(ROOT).as_posix(), "sha256": sha(binary), "bytes": binary.stat().st_size},
        )
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        receipt["reason"] = str(exc)
    receipt["files"] = {
        p.relative_to(HERE).as_posix(): sha(p)
        for p in [HERE / "Cargo.toml", HERE / "Cargo.lock", HERE / "src/main.rs", generated,
                  HERE / "source_binding.json", Path(__file__)]
        if p.exists()
    }
    output = HERE / "build_receipt.json"
    if output.exists() and "--archive-attempt" in sys.argv:
        attempt = len(list(HERE.glob("build_attempt_*.json"))) + 1
        (HERE / f"build_attempt_{attempt:03d}.json").write_bytes(output.read_bytes())
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": receipt["status"], "reason": receipt.get("reason"),
                      "receipt_sha256": sha(output), "binary": receipt.get("binary")}))
    return 0 if receipt["status"] == "BUILT" else 2

if __name__ == "__main__":
    sys.exit(main())
