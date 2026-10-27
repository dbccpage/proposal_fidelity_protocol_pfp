"""Four-layer mutual verification harness for the Symbol Game release gate.

Each layer is verified independently and reports under its own identifier, so a
fault at layer *k* is attributable to layer *k* rather than to a collapsed
"the gate failed".  Layers report a three-valued outcome:

``SATISFIED``     the layer ran and every check held
``VIOLATED``      the layer ran and a check failed
``UNVERIFIABLE``  the layer could not run -- its subject is absent

``UNVERIFIABLE`` is never folded into either of the other two.  A layer with no
subject has produced no evidence, and reporting that as green is the failure
this harness exists to prevent.  ``is_release_ready`` therefore requires every
layer to be ``SATISFIED``.

Every finding carries the pair ``(checked, total)`` rather than a bare boolean,
so 1-of-23 and 23-of-23 stay distinguishable in the report.

AuthorityEffect: None.  Replaying a corpus is not certifying a release.
"""

from __future__ import annotations

import ast
import enum
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

LAYER_WIRE_PARITY = "LAYER_1_WIRE_PARITY"
LAYER_EPIC_MANIFEST = "LAYER_2_EPIC_MANIFEST"
LAYER_HOST_PARITY = "LAYER_3_HOST_PARITY"
LAYER_LEAN_CONCORDANCE = "LAYER_4_LEAN_CONCORDANCE"

#: Declared in the order the release dossier reports them.
ALL_LAYERS: tuple[str, ...] = (
    LAYER_WIRE_PARITY,
    LAYER_EPIC_MANIFEST,
    LAYER_HOST_PARITY,
    LAYER_LEAN_CONCORDANCE,
)

GOLDEN_CORPUS_PATH = "pfp/tests/golden_canonical_vectors.json"
PARITY_SCRIPT_PATH = (
    "operations/use_cases/packaging/sync_cross_host_skills.py"
)
LEAN_ROOT = "lean4"
LAKE_MANIFESTS = ("lakefile.lean", "lakefile.toml")

#: Keys every golden vector must carry.  A vector missing one is a corpus
#: defect, not a replay failure -- the two are reported differently on purpose.
VECTOR_KEYS = frozenset(
    {
        "canonical_bytes_hex",
        "canonical_json",
        "domain",
        "domain_digest_sha256",
        "name",
        "raw_input_json",
        "wire_representation",
    }
)


class ReleaseGateError(ValueError):
    """A refusal: the harness cannot produce a verdict from what it was given."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"RELEASE_GATE_ERROR[{code}]: {detail}")
        self.code = code
        self.detail = detail


class LayerOutcome(enum.Enum):
    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    UNVERIFIABLE = "UNVERIFIABLE"


@dataclass(frozen=True, slots=True)
class LayerFinding:
    """One layer's verdict, carrying the layer that produced it."""

    layer: str
    outcome: LayerOutcome
    checked: int
    total: int
    detail: str

    def __post_init__(self) -> None:
        if self.layer not in ALL_LAYERS:
            raise ReleaseGateError(
                "UNKNOWN_LAYER", f"{self.layer!r} is not a declared layer"
            )
        if self.total < 0 or self.checked < 0:
            raise ReleaseGateError(
                "NEGATIVE_COUNT", f"{self.layer}: ({self.checked}, {self.total})"
            )
        if self.checked > self.total:
            raise ReleaseGateError(
                "COUNT_EXCEEDS_TOTAL",
                f"{self.layer}: checked={self.checked} > total={self.total}",
            )

    def render(self) -> str:
        return (
            f"{self.outcome.value:13s} {self.layer}  "
            f"{self.checked}/{self.total}  {self.detail}"
        )


def first_difference(left: bytes, right: bytes) -> int | None:
    """Offset of the first differing byte, or of the truncation point.

    Returned so a replay failure can name *where* a recorded artifact drifted,
    not merely that it did.
    """
    for offset, (a, b) in enumerate(zip(left, right)):
        if a != b:
            return offset
    if len(left) != len(right):
        return min(len(left), len(right))
    return None


def load_golden_corpus(path: Path) -> list[dict[str, Any]]:
    """Read the golden vector corpus, refusing a corpus that cannot be replayed."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ReleaseGateError("CORPUS_MISSING", f"{path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ReleaseGateError("CORPUS_UNREADABLE", f"{path}: {error}") from error
    if not isinstance(raw, dict):
        raise ReleaseGateError(
            "CORPUS_SHAPE", f"{path}: top level is {type(raw).__name__}"
        )
    vectors = raw.get("vectors")
    if not isinstance(vectors, list):
        raise ReleaseGateError("CORPUS_SHAPE", f"{path}: 'vectors' is not a list")
    if not vectors:
        raise ReleaseGateError(
            "CORPUS_EMPTY", f"{path}: no vectors; refusing to report 0 of 0 as parity"
        )
    declared = raw.get("vector_count")
    # The corpus states its own size.  If the file and its declaration disagree,
    # a vector was dropped without the count being updated -- replaying the
    # survivors and reporting them all green is exactly the silent truncation
    # this check exists to refuse.
    if declared != len(vectors):
        raise ReleaseGateError(
            "CORPUS_COUNT_MISMATCH",
            f"{path}: vector_count={declared!r}, vectors={len(vectors)}",
        )
    for index, vector in enumerate(vectors):
        if not isinstance(vector, dict):
            raise ReleaseGateError(
                "CORPUS_SHAPE", f"{path}: vector {index} is not an object"
            )
        missing = VECTOR_KEYS - set(vector)
        if missing:
            raise ReleaseGateError(
                "CORPUS_VECTOR_KEYS", f"{path}: vector {index} lacks {sorted(missing)}"
            )
    return vectors


def replay_vector(vector: dict[str, Any]) -> list[str]:
    """Replay one recorded vector through the Python encoder.

    Returns the list of problems; empty means the Python encoder reproduced the
    recorded Rust artifact exactly.  Each problem names the vector and, for the
    byte comparison, the offset at which the two disagree.
    """
    from pfp.domain.shared_kernel.canonical import (
        canonical_bytes,
        canonical_json,
        canonical_wire,
        domain_digest,
    )

    name = vector["name"]
    try:
        value = json.loads(vector["raw_input_json"])
    except json.JSONDecodeError as error:
        return [f"{name}: raw_input_json is not JSON: {error}"]

    problems: list[str] = []
    try:
        observed_wire = canonical_wire(value)
        observed_json = canonical_json(value)
        observed_bytes = canonical_bytes(value)
        observed_digest = domain_digest(vector["domain"], value)
    except Exception as error:  # noqa: BLE001 - any encoder failure is a replay failure
        return [f"{name}: encoder raised {type(error).__name__}: {error}"]

    if observed_wire != vector["wire_representation"]:
        problems.append(f"{name}: wire representation differs")
    if observed_json != vector["canonical_json"]:
        problems.append(f"{name}: canonical json differs")
    recorded_bytes = bytes.fromhex(vector["canonical_bytes_hex"])
    if observed_bytes != recorded_bytes:
        offset = first_difference(observed_bytes, recorded_bytes)
        problems.append(f"{name}: canonical bytes differ at offset {offset}")
    if observed_digest != vector["domain_digest_sha256"]:
        problems.append(
            f"{name}: domain digest differs "
            f"(observed={observed_digest}, recorded={vector['domain_digest_sha256']})"
        )
    return problems


def verify_wire_parity(
    repo_root: Path, corpus_path: Path | None = None
) -> LayerFinding:
    """Layer 1 -- every recorded vector replays byte-identically in Python.

    The corpus is written by the Rust runtime and, until this layer existed, was
    read back only by Rust.  A golden file checked solely by the implementation
    that produced it is a self-comparison; this is the second witness.
    """
    path = corpus_path or (repo_root / GOLDEN_CORPUS_PATH)
    vectors = load_golden_corpus(path)
    problems: list[str] = []
    replayed = 0
    for vector in vectors:
        found = replay_vector(vector)
        if found:
            problems.extend(found)
        else:
            replayed += 1
    if problems:
        return LayerFinding(
            layer=LAYER_WIRE_PARITY,
            outcome=LayerOutcome.VIOLATED,
            checked=replayed,
            total=len(vectors),
            detail="; ".join(problems),
        )
    return LayerFinding(
        layer=LAYER_WIRE_PARITY,
        outcome=LayerOutcome.SATISFIED,
        checked=replayed,
        total=len(vectors),
        detail=f"all {replayed} recorded vectors replay byte-identically in Python",
    )


def verify_epic_manifest(repo_root: Path) -> LayerFinding:
    """Layer 2 -- the epic manifest audit passes against the real repository."""
    from product_planning_office.domain.manifest_models import (
        EXPECTED_EPIC_COUNT,
        EpicManifestError,
    )
    from product_planning_office.use_cases.epic_manifest_audit import (
        audit_epic_manifest,
    )

    try:
        report = audit_epic_manifest(repo_root)
    except EpicManifestError as error:
        return LayerFinding(
            layer=LAYER_EPIC_MANIFEST,
            outcome=LayerOutcome.VIOLATED,
            checked=0,
            total=EXPECTED_EPIC_COUNT,
            detail=str(error),
        )
    return LayerFinding(
        layer=LAYER_EPIC_MANIFEST,
        outcome=LayerOutcome.SATISFIED,
        checked=report.epic_count,
        total=EXPECTED_EPIC_COUNT,
        detail=f"content_set_sha256={report.content_set_sha256}",
    )


def _run_parity_script(repo_root: Path) -> tuple[int, str]:
    script = repo_root / PARITY_SCRIPT_PATH
    if not script.is_file():
        raise ReleaseGateError("PARITY_SCRIPT_MISSING", str(script))
    completed = subprocess.run(
        [sys.executable, str(script), "--check"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, (completed.stdout or "") + (completed.stderr or "")


def verify_host_parity(
    repo_root: Path, runner: Callable[[Path], tuple[int, str]] | None = None
) -> LayerFinding:
    """Layer 3 -- the four skill hosts are byte-identical.

    Runs inside this harness rather than as a separate manual step, which is
    what the epic asks for: a gate nobody remembers to run is not a gate.
    """
    run = runner or _run_parity_script
    code, output = run(repo_root)
    failures = [line for line in output.splitlines() if line.startswith("FAIL")]
    checked = sum(1 for line in output.splitlines() if line.startswith(("OK", "FAIL")))
    if code != 0 or failures:
        return LayerFinding(
            layer=LAYER_HOST_PARITY,
            outcome=LayerOutcome.VIOLATED,
            checked=checked - len(failures),
            total=checked,
            detail=(
                f"exit={code}; "
                + ("; ".join(failures) if failures else "no FAIL line reported")
            ),
        )
    return LayerFinding(
        layer=LAYER_HOST_PARITY,
        outcome=LayerOutcome.SATISFIED,
        checked=checked,
        total=checked,
        detail=f"{checked} skill packages identical across four hosts",
    )


def verify_lean_concordance(repo_root: Path) -> LayerFinding:
    """Layer 4 -- Lean theorem concordance.

    ``lean4/`` is a pointer to the CODA estate and holds no Lake project, so
    there is nothing here to elaborate against.  That is reported as
    ``UNVERIFIABLE``: the layer has no subject in this repository.  Reporting it
    as ``SATISFIED`` would let an absent proof obligation read as a discharged
    one.
    """
    lean_root = repo_root / LEAN_ROOT
    if not lean_root.is_dir():
        return LayerFinding(
            layer=LAYER_LEAN_CONCORDANCE,
            outcome=LayerOutcome.UNVERIFIABLE,
            checked=0,
            total=0,
            detail=f"{LEAN_ROOT}/ is absent; no Lean source is present to verify",
        )
    manifests = [name for name in LAKE_MANIFESTS if (lean_root / name).is_file()]
    if not manifests:
        return LayerFinding(
            layer=LAYER_LEAN_CONCORDANCE,
            outcome=LayerOutcome.UNVERIFIABLE,
            checked=0,
            total=0,
            detail=(
                f"{LEAN_ROOT}/ is a pointer to CODA and declares no Lake manifest "
                f"({', '.join(LAKE_MANIFESTS)}); concordance cannot be elaborated here"
            ),
        )
    return LayerFinding(
        layer=LAYER_LEAN_CONCORDANCE,
        outcome=LayerOutcome.UNVERIFIABLE,
        checked=0,
        total=len(manifests),
        detail=(
            f"a Lake manifest appeared ({', '.join(manifests)}); this layer must be "
            "implemented rather than left as a pointer check"
        ),
    )


def run_all_layers(repo_root: Path) -> tuple[LayerFinding, ...]:
    """Run every layer independently and return one finding per layer.

    Each layer is run whatever the previous layer reported: a harness that
    short-circuits cannot attribute a second, simultaneous fault.
    """
    findings = (
        verify_wire_parity(repo_root),
        verify_epic_manifest(repo_root),
        verify_host_parity(repo_root),
        verify_lean_concordance(repo_root),
    )
    reported = [finding.layer for finding in findings]
    if reported != list(ALL_LAYERS):
        raise ReleaseGateError(
            "LAYER_SET",
            f"expected one finding per declared layer, observed {reported!r}",
        )
    return findings


def is_release_ready(findings: Sequence[LayerFinding]) -> bool:
    """True only when every declared layer is ``SATISFIED``.

    An ``UNVERIFIABLE`` layer blocks release exactly as a ``VIOLATED`` one does.
    The two are reported distinctly because they call for different work, not
    because one of them is a pass.
    """
    covered = {finding.layer for finding in findings}
    if covered != set(ALL_LAYERS):
        raise ReleaseGateError("LAYER_SET", f"findings cover {sorted(covered)}")
    return all(finding.outcome is LayerOutcome.SATISFIED for finding in findings)


def outcome_census(findings: Iterable[LayerFinding]) -> dict[str, int]:
    """Count findings by outcome -- the *kind* of the result, not only a total."""
    census = {outcome.value: 0 for outcome in LayerOutcome}
    for finding in findings:
        census[finding.outcome.value] += 1
    return census


def test_names_in(path: Path) -> frozenset[str]:
    """Every test function name defined in a Python test module, over the AST.

    Over the AST rather than a text search: a docstring or comment naming a test
    would satisfy a grep without a test existing.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as error:
        raise ReleaseGateError("TEST_MODULE_UNREADABLE", f"{path}: {error}") from error
    return frozenset(
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def unbacked_claims(dossier: dict[str, str], repo_root: Path) -> list[str]:
    """Claims whose named discharging test does not exist.

    ``dossier`` maps a claim id to ``"<module path>::<test name>"``.  A claim
    with no discharge is reported, never dropped: an omitted claim reads as an
    absent obligation rather than an open one.
    """
    if not dossier:
        raise ReleaseGateError(
            "DOSSIER_EMPTY", "refusing to report 0 of 0 claims as discharged"
        )
    problems: list[str] = []
    cache: dict[Path, frozenset[str]] = {}
    for claim, discharge in sorted(dossier.items()):
        if "::" not in discharge:
            problems.append(f"{claim}: discharge {discharge!r} does not name a test")
            continue
        module, _, test_name = discharge.partition("::")
        path = repo_root / module
        if not path.is_file():
            problems.append(f"{claim}: test module {module} does not exist")
            continue
        if path not in cache:
            cache[path] = test_names_in(path)
        if test_name not in cache[path]:
            problems.append(f"{claim}: {module} defines no {test_name}")
    return problems


def format_report(findings: Sequence[LayerFinding]) -> str:
    """Render findings already computed.

    Takes the findings rather than a repository root so the CLI and any other
    caller share one rendering site and one set of layer runs.  Rendering twice
    from two call sites is how a report and its exit code come to disagree.
    """
    census = outcome_census(findings)
    lines = ["Symbol Game four-layer release gate", ""]
    lines.extend(finding.render() for finding in findings)
    lines.append("")
    lines.append(
        "  ".join(f"{name}={count}" for name, count in sorted(census.items()))
        + f"   release_ready={is_release_ready(findings)}"
    )
    lines.append("AuthorityEffect: None")
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    # Windows consoles default to cp1252 and the golden corpus carries CJK and
    # other non-cp1252 vectors, so a mismatch detail would crash the reporter
    # rather than report.  Configure the stream explicitly.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")
    argv = list(sys.argv[1:] if argv is None else argv)
    repo_root = Path(argv[0]) if argv else Path(__file__).resolve().parents[2]
    try:
        findings = run_all_layers(repo_root)
    except ReleaseGateError as error:
        print(str(error))
        return 2
    print(format_report(findings))
    return 0 if is_release_ready(findings) else 1


if __name__ == "__main__":
    raise SystemExit(main())
