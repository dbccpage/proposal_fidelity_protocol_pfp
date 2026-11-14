"""Transport to the Rust operad host ``pfp_operad``.

This module moves a request to the host and its outcome back. It decides nothing:
every verdict in the outcome was computed by the host. AuthorityEffect: None.

The host is found, in order, at ``PFP_OPERAD_BIN``, on ``PATH``, or in a source
checkout's ``code/rust/target`` build directory.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path

from pfp.domain.pfp_ingress import strict_json

ENVIRONMENT = "PFP_OPERAD_BIN"
NAME = "pfp_operad"
TIMEOUT_SECONDS = 60
BUILD_HINT = (
    "OPERAD_HOST_NOT_FOUND: set PFP_OPERAD_BIN to the pfp_operad binary, put it on PATH, "
    "or build it with `cargo build --release -p pfp_operads` in code/rust"
)


class OperadHostError(RuntimeError):
    """The host could not be reached or refused the request; no verdict exists."""


def _checkout_builds():
    executable = NAME + (".exe" if os.name == "nt" else "")
    for parent in Path(__file__).resolve().parents:
        for profile in ("release", "debug"):
            yield parent / "code" / "rust" / "target" / profile / executable


def binary() -> Path:
    """The host binary this process will run."""
    named = os.environ.get(ENVIRONMENT) or shutil.which(NAME)
    if named:
        return Path(named)
    for candidate in _checkout_builds():
        if candidate.is_file():
            return candidate
    raise OperadHostError(BUILD_HINT)


def call(command: tuple[str, ...], request: dict | None = None) -> dict:
    """Run one host command and return its outcome: ``PASS``, ``FAIL`` or ``REFUSED``."""
    arguments = [str(binary()), *command]
    with tempfile.TemporaryDirectory(prefix="pfp-operad-") as scratch:
        if request is not None:
            path = Path(scratch) / "request.json"
            path.write_text(json.dumps(request, ensure_ascii=False, allow_nan=False), encoding="utf-8")
            arguments.append(str(path))
        try:
            # The arguments are the host binary and a request file written just above.
            done = subprocess.run(  # noqa: S603
                arguments, capture_output=True, timeout=TIMEOUT_SECONDS, check=False
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise OperadHostError(f"OPERAD_HOST_DID_NOT_RUN: {exc}") from exc
    try:
        outcome = strict_json(done.stdout.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        detail = done.stderr.decode("utf-8", errors="replace").strip()
        raise OperadHostError(f"OPERAD_HOST_NO_OUTCOME: {detail}") from exc
    return outcome


def result(outcome: dict) -> dict:
    """The host's result for a request it could read; a refusal has no result."""
    if outcome.get("status") == "REFUSED":
        refusal = outcome["refusal"]
        raise OperadHostError(f"OPERAD_HOST_REFUSED: {refusal['code']}: {refusal['message']}")
    return outcome["result"]


@lru_cache(maxsize=1)
def identity() -> dict:
    """Name, version and canon of the host, as the host states them."""
    return result(call(("version",)))


def ask(command: str, **request) -> dict:
    """Send one request to a host command and return the host's result."""
    return result(call((command,), request))


def judge(checker: str, case: object, answer: object) -> tuple[bool, str]:
    """The host's verdict on a task result: it recomputes the answer itself."""
    verdict = ask("judge", checker=checker, case=case, answer=answer)
    return verdict["accepted"], verdict["reason"]


def envelope(*, catalogue: list, required: list, sources: dict, checker: str, answer: dict) -> dict:
    """The host's reading of a full-slot reply: structure errors and canon typing."""
    return ask(
        "envelope",
        catalogue=catalogue,
        required=required,
        sources=sources,
        checker=checker,
        answer=answer,
    )


def mining(*, catalogue: list, sources: dict, checker: str, answer: dict) -> dict:
    """The host's screen of a mining reply: digits, candidates and guidance."""
    return ask("mining", catalogue=catalogue, sources=sources, checker=checker, answer=answer)


def typing(checker: str, candidates: list) -> list:
    """The host's canon typing of a candidate list, one row per candidate."""
    return ask("typing", checker=checker, candidates=candidates)["candidates"]


def grounding(*, checker: str, values: list, slot_report: dict, candidates: list) -> dict:
    """The host's recheck of a solver reply's grounded slots against the public input."""
    return ask("grounding", checker=checker, values=values, slot_report=slot_report, candidates=candidates)


def reuse(mined: list, emitted: list) -> list:
    """The ids of the emitted candidates whose signature a mined candidate also has."""
    return ask("reuse", mined=mined, emitted=emitted)["reused"]


def outcome(command: str, request: dict) -> dict:
    """Send one request and return the host's whole outcome, for a caller that reports a refusal."""
    return call((command,), request)


def ledger(action: str, path: Path | str, record: dict | None = None) -> dict:
    """Run ``verify``, ``admitted`` or ``append`` on a failure ledger file and return the outcome.

    Only the host writes the file: an ``append`` it passes adds one line, a refused one adds none.
    """
    return call(("ledger", action, str(path)), record)
