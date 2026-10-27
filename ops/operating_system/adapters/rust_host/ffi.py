"""The single process seam between Python and the native `core_symbol_game` host.

AuthorityEffect: None. Nothing in this module certifies, promotes, admits, or
terminalizes anything. It moves exact bytes across a process boundary and
checks the native protocol's declared bindings. The prime protocol carries a
request commitment; the runtime protocol carries only an action echo, not a
cryptographic request identity.

Why a subprocess and not PyO3
-----------------------------
The native host's `main.rs` is already a JSON-over-stdin/stdout program with
prime modes (`--describe`, `--derive-carrier-manifest`, and bare stdin ->
evaluate) and a separate `invoke` runtime protocol. Every call crosses as a pair
of byte strings; this adapter returns the complete decoded outcome, not a
raw-stdout custody receipt. A process boundary also
keeps `SolveReceipt`, `ReplayedSolve`, `ControlState` and `StepPermit` inside
one Rust process, as that crate's documentation requires, and it needs no
Python packaging metadata in a repository that deliberately has none.

House rules this module exists to satisfy
-----------------------------------------
- `RULE_FFI_SEAM_ISOLATION_001` and the Parity Seam Isolation Invariant in
  `.agents/AGENTS.md`: FFI seams live in one dedicated module. Callers must not
  spawn the host themselves.
- `RULE_FFI_RESULT_PARITY_001`: every boundary crossing returns the kernel
  railway type. A process or integrity failure becomes `Err(Refusal(...))`,
  never a raised exception or a bare `None`; a valid native refusal remains
  `Ok` evidence. No non-zero exit, malformed byte stream, or timeout escapes
  this module as a traceback.
- OEOS ADR-0001: OEOS owns process and resource control. It does not own
  mathematics, evaluator decisions, terminal verdicts, or `ActionLicense`
  values, and this module authors none of them -- it returns what the host said,
  after checking the host said it about this request.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import tempfile
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Final

from operations.domain.rop.result import Err, Ok, Refusal, Result

__all__ = [
    "CANONICALIZATION_PROFILE",
    "DESCRIPTION_SCHEMA",
    "MAX_REQUEST_BYTES",
    "OUTCOME_SCHEMA",
    "REQUEST_SCHEMA",
    "RUNTIME_MAX_REQUEST_BYTES",
    "RUNTIME_OUTCOME_SCHEMA",
    "RUNTIME_REQUEST_SCHEMA",
    "HostLocation",
    "RustSandboxHost",
    "RustSymbolGameHost",
    "SymgamHost",
    "canonical_request_bytes",
    "locate_host_binary",
    "verify_exact_rational_witness",
    "verify_outcome",
]

DESCRIPTION_SCHEMA: Final[str] = "core.oesos.rust-prime-host-description.v1"
REQUEST_SCHEMA: Final[str] = "core.oesos.rust-prime-host-request.v1"
OUTCOME_SCHEMA: Final[str] = "core.oesos.rust-prime-host-outcome.v1"
RUNTIME_REQUEST_SCHEMA: Final[str] = "core.symbol-game.runtime-request.v1"
RUNTIME_OUTCOME_SCHEMA: Final[str] = "core.symbol-game.runtime-outcome.v1"

CANONICALIZATION_PROFILE: Final[str] = "core-sorted-json-no-float-v1"

MAX_REQUEST_BYTES: Final[int] = 1_048_576
# The campaign runtime intake ceiling is separate from the prime-host profile.
RUNTIME_MAX_REQUEST_BYTES: Final[int] = 65_536
# Signed projection material has its own complete-envelope bound, not a work budget.
ADVERSARY_BOUT_RUNTIME_MAX_REQUEST_BYTES: Final[int] = 1024 * 1024
# Matches invoke::MAX_DAG_RUNTIME_REQUEST_BYTES: payload ceiling plus envelope.
DAG_RUNTIME_MAX_REQUEST_BYTES: Final[int] = 256 * 1024 + 4096
# Raw byte arrays and nested artifact provenance need the native action's ceiling.
PROMPT_ARTIFACT_RUNTIME_MAX_REQUEST_BYTES: Final[int] = 12 * 1024 * 1024

HOST_BINARY_ENV: Final[str] = "CORE_SYMBOL_GAME_HOST"
CRATE_NAME: Final[str] = "core_symbol_game"
# The classifier/detector host. Same transport, same rules; a second binary
# rather than a second seam, so nothing outside this module spawns either.
SYMGAM_BINARY: Final[str] = "symgam"
SYMGAM_BINARY_ENV: Final[str] = "CORE_SYMGAM_HOST"
SYMGAM_DESCRIPTION_SCHEMA: Final[str] = "core.symgam.host-description.v1"
# Each override names one binary. A lookup for any other binary ignores it, so
# pointing CORE_SYMBOL_GAME_HOST at the main host cannot hand that binary to
# a symgam caller.
HOST_BINARY_ENVS: Final[Mapping[str, str]] = MappingProxyType(
    {CRATE_NAME: HOST_BINARY_ENV, SYMGAM_BINARY: SYMGAM_BINARY_ENV}
)
WORKSPACE_MARKER: Final[Path] = Path("engine") / "crates_rs" / "Cargo.toml"

DEFAULT_TIMEOUT_SECONDS: Final[float] = 300.0


def _refuse(code: str, message: str, locus: str = "", **details: Any) -> Err:
    """Build the one shape a failed crossing is allowed to take."""
    return Err(
        Refusal(
            code=code,
            message=message,
            locus=locus or "operating_system.adapters.rust_host.ffi",
            details=tuple((key, str(value)) for key, value in sorted(details.items())),
        )
    )


@dataclass(frozen=True)
class HostLocation:
    """Where the native host binary was found, and how."""

    binary: Path
    discovered_by: str


def repo_root(start: Path | None = None) -> Path | None:
    """Walk upward until the Rust workspace manifest is visible.

    Returns None rather than guessing, so a caller running from an unexpected
    working directory gets a typed refusal instead of a wrong path.
    """
    here = (start or Path(__file__).resolve()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / WORKSPACE_MARKER).is_file():
            return candidate
    return None


def locate_host_binary(
    explicit: Path | None = None,
    binary_name: str = CRATE_NAME,
) -> Result[HostLocation, Refusal]:
    """Resolve the native host binary.

    Order: explicit argument, then the environment variable that names this
    binary (`CORE_SYMBOL_GAME_HOST` for `core_symbol_game`,
    `CORE_SYMGAM_HOST` for `symgam`), then the workspace `target/` directory
    preferring `release` over `debug`. A missing binary is a refusal, not an
    exception -- the caller is expected to surface "the engine is not built"
    as a normal outcome.
    """
    if explicit is not None:
        path = Path(explicit)
        if path.is_file():
            return Ok(HostLocation(binary=path, discovered_by="explicit"))
        return _refuse(
            "HOST_BINARY_NOT_FOUND",
            "the explicitly supplied host binary path does not exist",
            path=path,
        )

    env_name = HOST_BINARY_ENVS.get(binary_name)
    from_env = os.environ.get(env_name) if env_name else None
    if from_env:
        path = Path(from_env)
        if path.is_file():
            return Ok(HostLocation(binary=path, discovered_by="environment"))
        return _refuse(
            "HOST_BINARY_NOT_FOUND",
            f"{env_name} is set but does not point at a file",
            path=path,
        )

    root = repo_root()
    if root is None:
        return _refuse(
            "HOST_BINARY_NOT_FOUND",
            "could not locate the Rust workspace root from this module",
            marker=WORKSPACE_MARKER,
        )

    roots = [root]
    git_file = root / ".git"
    if git_file.is_file():
        try:
            content = git_file.read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("gitdir:"):
                    gitdir = Path(line.split(":", 1)[1].strip()).resolve()
                    for parent in gitdir.parents:
                        if (parent / WORKSPACE_MARKER).is_file() and parent not in roots:
                            roots.append(parent)
                            break
        except OSError:
            pass

    for r in roots:
        target = r / "engine" / "crates_rs" / "target"
        suffixes = (".exe", "") if os.name == "nt" else ("", ".exe")
        for profile in ("release", "debug"):
            for suffix in suffixes:
                candidate = target / profile / f"{binary_name}{suffix}"
                if candidate.is_file():
                    return Ok(HostLocation(binary=candidate, discovered_by=f"target/{profile}"))

    return _refuse(
        "HOST_BINARY_NOT_FOUND",
        f"the native binary {binary_name!r} is not built; "
        "run `cargo build -j 1` for the crate that provides it",
        searched=target,
    )


def _reject_floats(value: Any, path: str = "$") -> str | None:
    """Return the path of the first float found, or None.

    The declared canonicalization profile is `core-sorted-json-no-float-v1`.
    Binary floating point has no exact canonical decimal form, so admitting one
    would silently break digest reproducibility between the two languages. A
    bool is deliberately not treated as a number here; `isinstance(True, int)`
    is true in Python and JSON keeps them distinct.
    """
    if isinstance(value, float):
        return path
    if isinstance(value, Mapping):
        for key, item in value.items():
            found = _reject_floats(item, f"{path}.{key}")
            if found is not None:
                return found
        return None
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            found = _reject_floats(item, f"{path}[{index}]")
            if found is not None:
                return found
    return None


def canonical_request_bytes(request: Mapping[str, Any]) -> Result[bytes, Refusal]:
    """Encode a request under the profile the host declares, or refuse.

    Uses exactly the encoding `compute_rust_host_outcome_root` uses on the
    return leg -- sorted keys, no whitespace, no NaN/Infinity -- so both
    directions of the boundary agree byte for byte.
    """
    if not isinstance(request, Mapping):
        return _refuse(
            "HOST_REQUEST_NOT_CANONICAL",
            "request must be a mapping",
            actual_type=type(request).__name__,
        )

    float_at = _reject_floats(request)
    if float_at is not None:
        return _refuse(
            "HOST_REQUEST_NOT_CANONICAL",
            f"canonicalization profile {CANONICALIZATION_PROFILE} forbids floating point values",
            locus=float_at,
        )

    try:
        encoded = json.dumps(
            request,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        return _refuse(
            "HOST_REQUEST_NOT_CANONICAL",
            "request is not JSON-encodable under the canonical profile",
            reason=exc,
        )

    if len(encoded) > MAX_REQUEST_BYTES:
        return _refuse(
            "HOST_REQUEST_TOO_LARGE",
            "request exceeds the host's declared maximum request size",
            size_bytes=len(encoded),
            max_bytes=MAX_REQUEST_BYTES,
        )

    return Ok(encoded)


def _require_string_keys(value: Any) -> None:
    """Reject coerced object keys and text that cannot cross UTF-8 JSON."""
    if isinstance(value, str):
        value.encode("utf-8")
    elif isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("runtime JSON object keys must be strings")
            key.encode("utf-8")
            _require_string_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_string_keys(item)


def _runtime_request_bytes(action: str, payload: Any) -> Result[bytes, Refusal]:
    """Encode finite JSON values for the runtime's action-owned validation.

    Transport admission of a finite float does not assert that any particular
    native action accepts that payload. This is not the prime host's no-float
    commitment profile. Nonfinite numbers, lossy object keys and values that
    cannot cross UTF-8 JSON are refused before spawning. The ceiling includes
    the complete three-field request envelope.
    """
    try:
        if not isinstance(action, str):
            raise TypeError("runtime action must be a string")
        _require_string_keys(payload)
        encoded = json.dumps(
            {
                "schema_version": RUNTIME_REQUEST_SCHEMA,
                "action": action,
                "payload": payload,
            },
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError, RecursionError) as exc:
        return _refuse(
            "HOST_RUNTIME_REQUEST_INVALID",
            "runtime request is not losslessly UTF-8 JSON-encodable",
            reason=exc,
        )
    limit = RUNTIME_MAX_REQUEST_BYTES
    if action == "architecture_dag_verify":
        limit = DAG_RUNTIME_MAX_REQUEST_BYTES
    elif action == "adversary_bout":
        limit = ADVERSARY_BOUT_RUNTIME_MAX_REQUEST_BYTES
    elif action in {"prompt_artifact", "validate_reply_residual"}:
        limit = PROMPT_ARTIFACT_RUNTIME_MAX_REQUEST_BYTES
    if len(encoded) > limit:
        return _refuse(
            "HOST_RUNTIME_REQUEST_TOO_LARGE",
            "runtime request exceeds the action's intake ceiling",
            size_bytes=len(encoded),
            max_bytes=limit,
        )
    return Ok(encoded)


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    decoded: dict[str, Any] = {}
    for key, value in pairs:
        if key in decoded:
            raise ValueError("native JSON contains a duplicate object key")
        decoded[key] = value
    return decoded


def _finite_json_float(token: str) -> float:
    value = float(token)
    if not math.isfinite(value):
        raise ValueError("native JSON contains a nonfinite number")
    return value


def _reject_json_constant(token: str) -> Any:
    raise ValueError(f"native JSON contains the non-JSON constant {token}")


def _verify_runtime_outcome(
    action: str, outcome: Mapping[str, Any]
) -> Result[Mapping[str, Any], Refusal]:
    """Validate the existing runtime envelope without inventing request custody."""
    fields = {
        "schema_version",
        "action",
        "success",
        "result",
        "error",
        "authority_effect",
    }
    if set(outcome) != fields:
        return _refuse(
            "HOST_RUNTIME_OUTCOME_INVALID",
            "runtime outcome must carry exactly the six declared fields",
            missing=sorted(fields - set(outcome)),
            extra=sorted(set(outcome) - fields),
        )
    if outcome["schema_version"] != RUNTIME_OUTCOME_SCHEMA:
        return _refuse(
            "HOST_RUNTIME_OUTCOME_SCHEMA_MISMATCH",
            "runtime outcome does not carry the expected schema version",
            expected=RUNTIME_OUTCOME_SCHEMA,
            actual=outcome["schema_version"],
        )
    if outcome["action"] != action:
        return _refuse(
            "HOST_RUNTIME_ACTION_MISMATCH",
            "runtime outcome action does not echo the request action",
            expected=action,
            actual=outcome["action"],
        )
    if outcome["authority_effect"] != "None":
        return _refuse(
            "HOST_AUTHORITY_CEILING_VIOLATED",
            "runtime outcome declares an authority effect other than None",
            actual=outcome["authority_effect"],
        )
    if type(outcome["success"]) is not bool:
        return _refuse("HOST_RUNTIME_OUTCOME_INVALID", "runtime success must be an exact boolean")
    if outcome["success"]:
        # Some(Value::Null) is a legitimate native success and serializes null.
        if outcome["error"] is not None:
            return _refuse(
                "HOST_RUNTIME_OUTCOME_INVALID",
                "successful runtime dispatch must not carry an error",
            )
    elif outcome["result"] is not None or not isinstance(outcome["error"], str):
        return _refuse(
            "HOST_RUNTIME_OUTCOME_INVALID",
            "failed runtime dispatch must carry a string error and a null result",
        )
    return Ok(outcome)


RUST_HOST_OUTCOME_SCHEMA = "core.oesos.rust-prime-host-outcome.v1"


def sorted_json_bytes(value: Any) -> bytes:
    """Sorted keys, no whitespace, no NaN: the host's commitment encoding."""
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def framed_sha256(domain: str, payload: bytes) -> str:
    """``u32_be(len(domain)) || domain || u64_be(len(payload)) || payload``.

    The framing behind every commitment the Rust host issues
    (``core_symbol_game_runtime::framed_sha256``), reproduced here so the seam
    can recompute a commitment rather than trust it.
    """
    encoded = domain.encode("utf-8")
    framed = len(encoded).to_bytes(4, "big") + encoded + len(payload).to_bytes(8, "big") + payload
    return hashlib.sha256(framed).hexdigest()


def compute_rust_host_outcome_root(outcome: Mapping[str, Any]) -> str:
    """Reproduce the Rust host's framed SHA-256 outcome commitment."""
    normalized = json.loads(json.dumps(dict(outcome)))
    if not isinstance(normalized, dict):
        raise TypeError("Rust host outcome must be a mapping")
    normalized.pop("outcome_root_sha256", None)
    return framed_sha256(RUST_HOST_OUTCOME_SCHEMA, sorted_json_bytes(normalized))


FUNCTIONAL_REQUEST_DOMAIN: Final[str] = "core.symbol-game.functional-evaluate-request.v1"
GENESIS_REQUEST_DOMAIN: Final[str] = "core.genesis.resolve-input.v1"
PROJECTION_REQUEST_DOMAIN: Final[str] = "core.symbol-game.projection-evaluate-request.v1"
CONTINUUM_REQUEST_DOMAIN: Final[str] = "core.symbol-game.continuum-evaluate-request.v1"
WDP_PACKET_REQUEST_DOMAIN: Final[str] = "core.wdp.source-packet-request.v1"
ADVERSARY_REQUEST_DOMAIN: Final[str] = "core.adversary.bout-input.v1"
NATIVE_PORT_REQUEST_DOMAIN: Final[str] = "core.native.port-input.v1"


def functional_input_digest(payload: Mapping[str, Any]) -> str:
    """The digest a ``functional_evaluate`` receipt must carry for ``payload``."""
    return framed_sha256(FUNCTIONAL_REQUEST_DOMAIN, sorted_json_bytes(payload))


def projection_input_digest(payload: Mapping[str, Any]) -> str:
    """The commitment carried by a declared finite projection receipt."""
    return framed_sha256(PROJECTION_REQUEST_DOMAIN, sorted_json_bytes(payload))


# Runtime actions whose answer names the request it answers, mapped to the part
# of the payload that answer is bound to. Every other action echoes only its
# name, which binds nothing.
_INPUT_BOUND_ACTIONS: Final[Mapping[str, str | None]] = MappingProxyType(
    {
        "functional_evaluate": None,
        "functional_verify": "request",
        "wdp_packet_evaluate": None,
        "wdp_packet_verify": "request",
        "genesis_resolve": None,
        "projection_evaluate": None,
        "projection_verify": "request",
        "continuum_evaluate": None,
        "adversary_bout": None,
        "immune_allostery": None,
        "immune_clonal": None,
        "immune_admission": None,
        "immune_activation": None,
        "prompt_civilization": None,
        "prompt_rank": None,
        "prompt_metabolism": None,
        "prompt_metabolism_file": None,
        "learning_signals": None,
        "learning_signals_file": None,
        "skill_garden_cull": None,
        "skill_garden_cull_file": None,
        "adversary_support": None,
        "adversary_support_file": None,
        "workflow_substitute": None,
        "workflow_validate": None,
        "workflow_graph": None,
        "provider_budget": None,
        "anthropic_messages": None,
        "anthropic_messages_file": None,
        "workflow_operation_v3": None,
    }
)


def _verify_input_binding(
    action: str, payload: Any, outcome: Mapping[str, Any]
) -> Result[Mapping[str, Any], Refusal]:
    """Refuse an input-bound answer whose digest is not this request's digest.

    A native refusal (``success: false``) carries no result and so no digest;
    it is returned unchanged, as every native verdict is.
    """
    if action not in _INPUT_BOUND_ACTIONS or not outcome["success"]:
        return Ok(outcome)
    key = _INPUT_BOUND_ACTIONS[action]
    subject = payload.get(key) if key is not None and isinstance(payload, Mapping) else payload
    result = outcome["result"]
    claimed = result.get("input_digest") if isinstance(result, Mapping) else None
    digest = (
        projection_input_digest if action.startswith("projection_") else functional_input_digest
    )
    expected = (
        framed_sha256(NATIVE_PORT_REQUEST_DOMAIN, sorted_json_bytes(subject))
        if action
        in {
            "immune_allostery",
            "immune_clonal",
            "immune_admission",
            "immune_activation",
            "prompt_civilization",
            "prompt_rank",
            "prompt_metabolism",
            "prompt_metabolism_file",
            "learning_signals",
            "learning_signals_file",
            "skill_garden_cull",
            "skill_garden_cull_file",
            "adversary_support",
            "adversary_support_file",
            "workflow_substitute",
            "workflow_validate",
            "workflow_graph",
            "provider_budget",
            "anthropic_messages",
            "anthropic_messages_file",
            "workflow_operation_v3",
        }
        and isinstance(subject, Mapping)
        else framed_sha256(ADVERSARY_REQUEST_DOMAIN, sorted_json_bytes(subject))
        if action == "adversary_bout" and isinstance(subject, Mapping)
        else framed_sha256(GENESIS_REQUEST_DOMAIN, sorted_json_bytes(subject))
        if action == "genesis_resolve" and isinstance(subject, Mapping)
        else framed_sha256(CONTINUUM_REQUEST_DOMAIN, sorted_json_bytes(subject))
        if action == "continuum_evaluate" and isinstance(subject, Mapping)
        else framed_sha256(WDP_PACKET_REQUEST_DOMAIN, sorted_json_bytes(subject))
        if action in {"wdp_packet_evaluate", "wdp_packet_verify"} and isinstance(subject, Mapping)
        else digest(subject)
        if isinstance(subject, Mapping)
        else None
    )
    if not isinstance(subject, Mapping) or claimed != expected:
        return _refuse(
            "HOST_INPUT_BINDING_MISMATCH",
            "the runtime answer is not bound to the request that was sent",
            action=action,
            claimed=claimed,
        )
    return Ok(outcome)


def _compute_outcome_root(outcome: Mapping[str, Any]) -> Result[str, Refusal]:
    """Recompute the host's framed commitment over the outcome."""
    try:
        return Ok(compute_rust_host_outcome_root(outcome))
    except (TypeError, ValueError) as exc:
        return _refuse(
            "HOST_OUTCOME_ROOT_UNVERIFIABLE",
            "the outcome could not be re-encoded for commitment recomputation",
            reason=exc,
        )


def verify_outcome(
    request: Mapping[str, Any],
    outcome: Mapping[str, Any],
) -> Result[Mapping[str, Any], Refusal]:
    """Check that this outcome is bound to this request, and is self-consistent.

    Independently recomputes the host's `outcome_root_sha256` rather than
    trusting the field, then checks the request-identity echo. An outcome that
    parses but belongs to a different request is the failure mode this exists
    to catch.
    """
    if outcome.get("schema_version") != OUTCOME_SCHEMA:
        return _refuse(
            "HOST_OUTCOME_SCHEMA_MISMATCH",
            "outcome does not carry the expected schema version",
            expected=OUTCOME_SCHEMA,
            actual=outcome.get("schema_version"),
        )

    claimed_root = outcome.get("outcome_root_sha256")
    recomputed = _compute_outcome_root(outcome)
    if isinstance(recomputed, Err):
        return recomputed
    if claimed_root != recomputed.value:
        return _refuse(
            "HOST_OUTCOME_ROOT_MISMATCH",
            "recomputed outcome commitment does not match the value the host emitted",
            claimed=claimed_root,
            recomputed=recomputed.value,
        )

    refused_at_intake = outcome.get("execution_status") == "REFUSED"

    for field in ("request_id_sha256", "challenge_hex"):
        expected = request.get(field)
        actual = outcome.get(field)
        if actual is None:
            # The host nulls the identity fields when it refuses before parsing
            # them -- a malformed request has no id to echo. That is a real
            # outcome and must reach the caller with the host's own refusal
            # codes intact, so it is not treated as a binding failure. Outside
            # a refusal there is no legitimate reason for a null id.
            if refused_at_intake:
                continue
            return _refuse(
                "HOST_OUTCOME_BINDING_MISMATCH",
                f"outcome omits {field} without refusing",
                field=field,
                execution_status=outcome.get("execution_status"),
            )
        if expected is not None and expected != actual:
            return _refuse(
                "HOST_OUTCOME_BINDING_MISMATCH",
                f"outcome {field} does not echo the request",
                field=field,
                expected=expected,
                actual=actual,
            )

    expected_registry = request.get("expected_host_registry_hash_sha256")
    actual_registry = outcome.get("host_registry_hash_sha256")
    if expected_registry is not None and expected_registry != actual_registry:
        return _refuse(
            "HOST_OUTCOME_BINDING_MISMATCH",
            "outcome came from a host whose registry hash is not the one the request pinned",
            expected=expected_registry,
            actual=actual_registry,
        )

    if outcome.get("authority_effect") != "None":
        return _refuse(
            "HOST_AUTHORITY_CEILING_VIOLATED",
            "outcome declares an authority effect other than None",
            actual=outcome.get("authority_effect"),
        )

    return Ok(outcome)


class RustSymbolGameHost:
    """Bounded, refusal-typed access to the native host process."""

    #: Which binary in the workspace target directory this host drives.
    BINARY_NAME: str = CRATE_NAME

    def __init__(
        self,
        binary: Path | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        process_environ: Mapping[str, str] | None = None,
        *,
        process_observer: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> None:
        if process_observer is not None and not callable(process_observer):
            raise TypeError("process_observer must be callable")
        self._explicit = binary
        self._timeout_seconds = timeout_seconds
        self._process_environ = process_environ
        self._process_observer = process_observer

    def _run(
        self,
        args: Sequence[str],
        stdin_bytes: bytes | None,
    ) -> Result[Mapping[str, Any], Refusal]:
        located = locate_host_binary(self._explicit, self.BINARY_NAME)
        if isinstance(located, Err):
            return located
        binary = located.value.binary

        started = time.monotonic_ns()
        try:
            completed = subprocess.run(
                [str(binary), *args],
                input=stdin_bytes if stdin_bytes is not None else b"",
                capture_output=True,
                timeout=self._timeout_seconds,
                check=False,
                env=self._process_environ,
            )
        except subprocess.TimeoutExpired:
            return _refuse(
                "HOST_TIMEOUT",
                "the native host did not terminate within the allotted time",
                timeout_seconds=self._timeout_seconds,
                binary=binary,
            )
        except OSError as exc:
            return _refuse(
                "HOST_SPAWN_FAILED",
                "the native host process could not be started",
                reason=exc,
                binary=binary,
            )

        if self._process_observer is not None:
            # A per-instance host-owned observer receives the actual capture
            # before parsing, including failed exits and invalid JSON. It does
            # not authenticate an OS/kernel observation or bound stream size.
            capture = MappingProxyType({
                "args": (str(binary), *args),
                "stdin_bytes": stdin_bytes if stdin_bytes is not None else b"",
                "stdout_bytes": completed.stdout,
                "stderr_bytes": completed.stderr,
                "exit_code": completed.returncode,
                "elapsed_seconds": (time.monotonic_ns() - started) / 1_000_000_000,
            })
            try:
                self._process_observer(capture)
            except Exception as exc:
                return _refuse("HOST_OBSERVATION_FAILED", "native capture could not be retained", reason=exc)

        if completed.returncode != 0:
            return _refuse(
                "HOST_NONZERO_EXIT",
                "the native host exited non-zero",
                exit_code=completed.returncode,
                stderr=completed.stderr.decode("utf-8", errors="replace")[:2048],
            )

        try:
            decoded = json.loads(
                completed.stdout.decode("utf-8"),
                object_pairs_hook=_unique_json_object,
                parse_float=_finite_json_float,
                parse_constant=_reject_json_constant,
            )
            _require_string_keys(decoded)
        except (UnicodeDecodeError, ValueError, RecursionError) as exc:
            return _refuse(
                "HOST_OUTPUT_NOT_JSON",
                "the native host wrote something that is not JSON to stdout",
                reason=exc,
                stdout_prefix=completed.stdout[:256],
            )

        if not isinstance(decoded, dict):
            return _refuse(
                "HOST_OUTPUT_NOT_OBJECT",
                "the native host returned a JSON value that is not an object",
                actual_type=type(decoded).__name__,
            )

        return Ok(decoded)

    def invoke_runtime_with_file(
        self, action: str, payload: Any, *, file_action: str
    ) -> Result[Mapping[str, Any], Refusal]:
        """Move large artifacts through a digest-bound file owned by this process seam.

        The file action must verify the declared digest and size before decoding.
        Small inputs continue through the ordinary runtime envelope.
        """
        try:
            _require_string_keys(payload)
            raw = json.dumps(
                payload, allow_nan=False, ensure_ascii=False, separators=(",", ":")
            ).encode("utf-8")
            if len(raw) <= 60_000:
                return self.invoke_runtime(action, payload)
            if len(raw) > 64 * 1024 * 1024:
                return _refuse("RUNTIME_REQUEST_TOO_LARGE", "bound artifact exceeds 64 MiB")
            with tempfile.TemporaryDirectory(prefix="core-runtime-") as directory:
                request_file = Path(directory) / "request.json"
                request_file.write_bytes(raw)
                return self.invoke_runtime(
                    file_action,
                    {
                        "request_file": str(request_file),
                        "size": len(raw),
                        "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                    },
                )
        except (OSError, TypeError, ValueError, RecursionError) as exc:
            return _refuse("RUNTIME_ARTIFACT_UNAVAILABLE", str(exc))

    def invoke_runtime(self, action: str, payload: Any) -> Result[Mapping[str, Any], Refusal]:
        """Return the complete runtime outcome, never only its result payload.

        ``Ok`` means transport and envelope checks passed. Native ``success``
        reports dispatch, not semantic acceptance; even ``success: false`` is
        retained as ``Ok`` with the native error. Callers must retain this
        record before inspecting either success or the inner semantic result.

        Most runtime actions carry no request digest, so their action echo is
        not a request binding. Input-bound actions (``functional_evaluate``,
        ``functional_verify``) answer with an ``input_digest`` that is recomputed
        here and refused as ``HOST_INPUT_BINDING_MISMATCH`` when it differs. The
        request is size-limited; stdout is still captured in memory, not
        protected by a bounded streaming reader.
        """
        encoded = _runtime_request_bytes(action, payload)
        if isinstance(encoded, Err):
            return encoded
        produced = self._run(["invoke"], stdin_bytes=encoded.value)
        if isinstance(produced, Err):
            return produced
        verified = _verify_runtime_outcome(action, produced.value)
        if isinstance(verified, Err):
            return verified
        return _verify_input_binding(action, payload, verified.value)

    def describe(self) -> Result[Mapping[str, Any], Refusal]:
        """Ask the host to identify itself.

        The returned record carries the registry hash and source revision a
        caller must pin into a request, so this is normally the first call.
        """
        result = self._run(["--describe"], stdin_bytes=None)
        if isinstance(result, Err):
            return result

        description = result.value
        if description.get("schema_version") != DESCRIPTION_SCHEMA:
            return _refuse(
                "HOST_DESCRIPTION_SCHEMA_MISMATCH",
                "host description does not carry the expected schema version",
                expected=DESCRIPTION_SCHEMA,
                actual=description.get("schema_version"),
            )
        if description.get("authority_effect") != "None":
            return _refuse(
                "HOST_AUTHORITY_CEILING_VIOLATED",
                "host description declares an authority effect other than None",
                actual=description.get("authority_effect"),
            )
        return Ok(description)

    def derive_carrier_manifest(
        self,
        request: Mapping[str, Any],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Summarise a request's carrier without evaluating it."""
        encoded = canonical_request_bytes(request)
        if isinstance(encoded, Err):
            return encoded
        return self._run(["--derive-carrier-manifest"], stdin_bytes=encoded.value)

    def evaluate(self, request: Mapping[str, Any]) -> Result[Mapping[str, Any], Refusal]:
        """Evaluate one request and return a verified outcome.

        The outcome is checked against this request before it is returned, so a
        caller receiving `Ok` has an outcome whose commitment was independently
        recomputed here and whose identity fields echo what was sent.

        `Ok` does NOT mean the host accepted anything. A host outcome carrying
        `execution_status: "REFUSED"` is still returned as `Ok`, because it is a
        verified evidence record and the refusal is the host's verdict to make.
        OEOS may not author an evaluator decision or terminal verdict
        (ADR-0001), so this seam must not relabel a host refusal as its own.
        `Err` is reserved for the transport and integrity failures this module
        genuinely owns: a missing binary, a timeout, a non-zero exit, output
        that is not a JSON object, a commitment that does not recompute, or an
        outcome bound to a different request.

        Callers must branch on `execution_status` and retain the whole record;
        the Zero Data-Loss Invariant in `.agents/AGENTS.md` forbids discarding
        it.
        """
        encoded = canonical_request_bytes(request)
        if isinstance(encoded, Err):
            return encoded

        produced = self._run([], stdin_bytes=encoded.value)
        if isinstance(produced, Err):
            return produced

        return verify_outcome(request, produced.value)


class SymgamHost(RustSymbolGameHost):
    """The classifier and detector host.

    Same process seam, same refusal discipline, different binary. Two operations
    that prune a search *without a model call*:

    - :meth:`classify_board` decides which repair moves can possibly help. A
      ``LOCAL_CURVATURE`` verdict means every gauge move provably preserves the
      syndrome, so rewording is wasted effort and the branch dies for free.
    - :meth:`detect` decides whether a candidate is worth replaying at all.

    Both return ``Ok`` for any well-formed answer, including a refusal, for the
    same reason :meth:`RustSymbolGameHost.evaluate` does: the verdict belongs to
    the host, and OEOS may not author one. ``Err`` means the seam could not
    vouch for the bytes.
    """

    BINARY_NAME = SYMGAM_BINARY

    def request(
        self, mode: str, raw_bytes: bytes | None = None
    ) -> Result[Mapping[str, Any], Refusal]:
        """Forward a bounded symgam request without rewriting its custody bytes.

        Keep all detector context fields and the raw-byte digest intact. This
        is the public presentation seam; callers do not select another binary
        or access the private process runner when symgam is unavailable.
        """
        if mode == "--describe" and raw_bytes is None:
            return self.describe()
        if mode not in ("classify-board", "detect"):
            return _refuse("HOST_MODE_UNSUPPORTED", "unsupported symgam operation", mode=mode)
        if not isinstance(raw_bytes, bytes):
            return _refuse("HOST_REQUEST_NOT_BYTES", "symgam request must be bytes")
        if len(raw_bytes) > MAX_REQUEST_BYTES:
            return _refuse(
                "HOST_REQUEST_TOO_LARGE",
                "symgam request exceeds its byte limit",
                limit=MAX_REQUEST_BYTES,
            )
        return self._run([mode], stdin_bytes=raw_bytes)

    def describe(self) -> Result[Mapping[str, Any], Refusal]:
        result = self._run(["--describe"], stdin_bytes=None)
        if isinstance(result, Err):
            return result
        description = result.value
        if description.get("schema_version") != SYMGAM_DESCRIPTION_SCHEMA:
            return _refuse(
                "HOST_DESCRIPTION_SCHEMA_MISMATCH",
                "symgam description does not carry the expected schema version",
                expected=SYMGAM_DESCRIPTION_SCHEMA,
                actual=description.get("schema_version"),
            )
        return Ok(description)

    def classify_board(
        self,
        d0: Sequence[Sequence[int]],
        d1: Sequence[Sequence[int]],
        a: Sequence[int],
    ) -> Result[Mapping[str, Any], Refusal]:
        """Classify one declared finite gauge board.

        The chain law is checked first: a nonzero ``D1*D0`` is ``BOARD_INVALID``
        and outranks everything, because a graded diagram is not a cochain
        complex and interpreting its syndrome would be a category error.
        """
        request = {
            "d0": [list(row) for row in d0],
            "d1": [list(row) for row in d1],
            "a": list(a),
        }
        encoded = canonical_request_bytes(request)
        if isinstance(encoded, Err):
            return encoded
        return self._run(["classify-board"], stdin_bytes=encoded.value)

    def detect(
        self,
        candidate: Mapping[str, Any],
        *,
        prompt: str | None = None,
        unexplored_branches: int = 0,
        seen_digests: Sequence[str] | None = None,
        semantic_replay_passed: bool = False,
    ) -> Result[Mapping[str, Any], Refusal]:
        """Run the anti-skill pharmacy over one candidate packet."""
        request = {
            "candidate": dict(candidate),
            "context": {
                "prompt": prompt,
                "unexplored_branches": unexplored_branches,
                "seen_digests": list(seen_digests or []),
                "semantic_replay_passed": semantic_replay_passed,
            },
        }
        encoded = canonical_request_bytes(request)
        if isinstance(encoded, Err):
            return encoded
        return self._run(["detect"], stdin_bytes=encoded.value)


class RustSandboxHost(RustSymbolGameHost):
    """Transport SandboxConfig to the native resource-control owner.

    This uses the same process seam as the Symbol Game host. Native sandbox
    refusals remain evidence; unavailable binaries never run the command in Python.
    """

    BINARY_NAME = "core-sandbox-run"

    def execute(self, config: Mapping[str, Any], *, observe_resources: bool = False) -> Result[Mapping[str, Any], Refusal]:
        try:
            encoded = json.dumps(dict(config), allow_nan=False).encode("utf-8")
        except (TypeError, ValueError, UnicodeError) as exc:
            return _refuse(
                "SANDBOX_CONFIG_INVALID", "sandbox configuration is not JSON", reason=exc
            )
        if len(encoded) > MAX_REQUEST_BYTES:
            return _refuse(
                "SANDBOX_CONFIG_TOO_LARGE", "sandbox configuration exceeds ingress limit"
            )
        return self._run(["--observe-resources"] if observe_resources else [], encoded)


def verify_exact_rational_witness(
    boundary_cochains: Mapping[str, Any],
    carrier_hash: str,
) -> tuple[bool, str, dict[str, Any]]:
    """Contract reference for Rust FFI rational witness verification.

    Bridges PROJECT.md line 124 interface contract to the Clean Architecture domain port.
    Unpacks Result[WitnessVerificationResult, Refusal] to (is_valid, residual_digest, details).
    AuthorityEffect: None.
    """
    from operations.domain.ports.witness_port import (
        ExactRational,
        FloatForbiddenError,
        WitnessVerificationRequest,
    )
    from operations.infrastructure.rust_host.witness_adapter import (
        RustWitnessAdapter,
    )

    if not isinstance(boundary_cochains, Mapping):
        return (
            False,
            "",
            {
                "error": f"boundary_cochains must be a mapping, got {type(boundary_cochains).__name__}"
            },
        )

    parsed: dict[str, ExactRational] = {}
    for edge, val in boundary_cochains.items():
        if isinstance(val, float):
            return (
                False,
                "",
                {"error": f"Float forbidden for {edge}: {val}", "refusal_code": "FLOAT_FORBIDDEN"},
            )
        if not isinstance(val, (str, int, ExactRational)):
            return (False, "", {"error": f"Invalid coefficient type for {edge}: {type(val)}"})
        try:
            if isinstance(val, ExactRational):
                parsed[edge] = val
            elif isinstance(val, int):
                parsed[edge] = ExactRational(val, 1)
            else:
                parsed[edge] = ExactRational.from_str(val)
        except FloatForbiddenError as exc:
            return (False, "", {"error": str(exc), "refusal_code": "FLOAT_FORBIDDEN"})
        except (ValueError, ZeroDivisionError) as exc:
            return (False, "", {"error": f"Invalid rational representation for {edge}: {exc}"})

    try:
        req = WitnessVerificationRequest(
            boundary_cochains=parsed,
            carrier_hash=carrier_hash,
            authority_effect="None",
        )
    except (TypeError, ValueError) as exc:
        return (False, "", {"error": str(exc)})

    adapter = RustWitnessAdapter()
    result = adapter.verify_witness(req)
    if result.is_ok:
        val = result.unwrap()
        return (val.is_valid, val.residual_digest, dict(val.details))
    refusal = result.unwrap_err()
    return (False, "", {"error": refusal.message, "refusal_code": refusal.code})
