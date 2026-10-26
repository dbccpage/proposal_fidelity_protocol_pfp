"""Governance Bundle Dispatch and Verification Use Case.

Implements the composition root dispatch contract specified in
`governance-symbol-game`:

                  governance-symbol-game
                           │
        ┌──────────────────┼────────────────────┐
        ▼                  ▼                    ▼
 governance-ddc      governance-coda    governance-clean-arch
     if DDC              if CODA            if Python code/
     tape used            surfaces used      architecture changed

The four historical role IDs remain stable. Versioned source bindings point to
their current canonical packages. PASS records source-byte custody only; no
governance checker or admission decision is implied.

AuthorityEffect: None.
"""

from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from omega_engine_operations.domain.rop.result import Err, Ok, Refusal, Result

CANONICAL_GOVERNANCE_SKILLS: tuple[str, ...] = (
    "governance-symbol-game",
    "governance-ddc",
    "governance-coda",
    "governance-clean-arch",
)
GOVERNANCE_SOURCE_BINDING_VERSION = "omega.woland.governance-source-binding.v1"
GOVERNANCE_SOURCE_SCOPE = "source_byte_custody_only"
GOVERNANCE_SOURCE_BINDINGS_V1: tuple[tuple[str, str], ...] = (
    ("governance-symbol-game", "governance-pfp"),
    ("governance-ddc", "governance-wdp"),
    ("governance-coda", "governance-wdp"),
    ("governance-clean-arch", "governance-clean-arch"),
)

_LOCUS = "omega_engine_woland.use_cases.governance_dispatch"


def find_repo_root(start: Path | None = None) -> Path:
    """Safely locate repository root by walking upwards to `.agents`."""
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ".agents").is_dir() and (parent / "omega_engine_operations").is_dir():
            return parent
    return current


def compute_skill_digest(repo_root: Path, skill_id: str) -> str:
    """Hash bytes within the specified source root; zero means unavailable.

    The bundle verifier refuses the zero sentinel. Never substitute another
    repository or the process working directory for an unavailable source.
    """
    skill_file = repo_root / "omega_engine_operads" / "skills" / skill_id / "SKILL.md"
    try:
        source_file = skill_file.resolve(strict=True)
        source_file.relative_to(repo_root.resolve(strict=True))
        return hashlib.sha256(source_file.read_bytes()).hexdigest()
    except (OSError, ValueError):
        return "0" * 64


def resolve_governance_bundle(
    repo_root: Path | None = None,
    task_properties: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Resolve and generate the four-element governance_bundle receipt.

    Args:
        repo_root: Optional repository root path.
        task_properties: Optional mapping describing active task attributes:
            - ddc_tape_used: bool (or letter_tape present)
            - coda_surfaces_claimed: bool
            - python_code_changed: bool
            - objective: str
            - task_key: str

    Returns:
        A list of exactly 4 dictionary elements in canonical order.
    """
    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    props = task_properties or {}

    objective = str(props.get("objective", "")).lower()
    task_key = str(props.get("task_key", "")).lower()
    letter_tape = str(props.get("letter_tape", ""))

    # 1. governance-symbol-game: mandatory for every Woland / teamwork bout
    # 2. governance-ddc: if DDC tape used or letter_tape emitted
    if "ddc_tape_used" in props:
        ddc_tape_used = bool(props["ddc_tape_used"])
    else:
        ddc_tape_used = bool(letter_tape)
    # 3. governance-coda: if CODA surfaces claimed or referenced
    if "coda_surfaces_claimed" in props:
        coda_surfaces_claimed = bool(props["coda_surfaces_claimed"])
    else:
        coda_surfaces_claimed = any(
            tok in objective or tok in task_key
            for tok in ("coda", "foc", "mur", "cs_q", "gtla", "anomalon")
        )
    # 4. governance-clean-arch: if Python code modified or bounded context targeted
    if "python_code_changed" in props:
        python_code_changed = bool(props["python_code_changed"])
    else:
        python_code_changed = any(
            tok in objective or tok in task_key
            for tok in ("clean_arch", "bounded_context", "refactor", "code", "architecture")
        )
    bundle = []
    for (role, source), active in zip(
        GOVERNANCE_SOURCE_BINDINGS_V1,
        (True, ddc_tape_used, coda_surfaces_claimed, python_code_changed),
    ):
        digest = compute_skill_digest(root, source)
        bundle.append(
            {
                "skill_id": role,
                "source_skill_id": source,
                "source_path": f"omega_engine_operads/skills/{source}/SKILL.md",
                "source_binding_version": GOVERNANCE_SOURCE_BINDING_VERSION,
                "verification_scope": GOVERNANCE_SOURCE_SCOPE,
                "digest": digest,
                "result": ("PASS" if active else "N_A") if digest != "0" * 64 else "UNAVAILABLE",
            }
        )
    return bundle


def verify_governance_bundle(
    bundle: Any,
    expected_skills: tuple[str, ...] = CANONICAL_GOVERNANCE_SKILLS,
    *,
    repo_root: Path | None = None,
) -> Result[bool, Refusal]:
    """Verify role/source binding and current canonical source-byte custody.

    Invariants:
    1. Must be a list of exactly 4 elements.
    2. Elements must match expected skill IDs in exact canonical order.
    3. Each digest must match the declared canonical source under the source root.
    4. Each element result must be 'PASS' or 'N_A'.
    5. The root element 'governance-symbol-game' must be 'PASS'.

    PASS concerns byte custody only, not checker execution or admission. The
    default source root belongs to this installed workspace module, not CWD.
    """
    if expected_skills != CANONICAL_GOVERNANCE_SKILLS:
        return Err(
            Refusal(
                code="GOVERNANCE_BUNDLE_ROLE_SCHEMA_INVALID",
                message="the versioned binding requires the four canonical role IDs in order",
                locus=_LOCUS,
            )
        )
    if not isinstance(bundle, list):
        return Err(
            Refusal(
                code="GOVERNANCE_BUNDLE_MALFORMED",
                message="governance_bundle must be a list",
                locus=_LOCUS,
            )
        )
    if len(bundle) != len(expected_skills):
        return Err(
            Refusal(
                code="GOVERNANCE_BUNDLE_ARITY_MISMATCH",
                message=f"governance_bundle must have exactly {len(expected_skills)} elements, found {len(bundle)}",
                locus=_LOCUS,
            )
        )

    root = repo_root if repo_root is not None else Path(__file__).resolve().parents[2]
    sources = dict(GOVERNANCE_SOURCE_BINDINGS_V1)
    for idx, (elem, expected_id) in enumerate(zip(bundle, expected_skills)):
        if not isinstance(elem, dict):
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_ELEMENT_INVALID",
                    message=f"Element {idx} is not a dictionary",
                    locus=_LOCUS,
                )
            )
        skill_id = elem.get("skill_id")
        if skill_id != expected_id:
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_SKILL_ID_MISMATCH",
                    message=f"Element {idx} expected {expected_id}, found {skill_id}",
                    locus=_LOCUS,
                )
            )
        digest = elem.get("digest")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or digest == "0" * 64
            or not all(c in "0123456789abcdefABCDEF" for c in digest)
        ):
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_DIGEST_INVALID",
                    message=f"Element {idx} ({skill_id}) has invalid sha256 digest: {digest}",
                    locus=_LOCUS,
                )
            )
        source = sources.get(expected_id)
        if source is None or (
            elem.get("source_skill_id") != source
            or elem.get("source_path") != f"omega_engine_operads/skills/{source}/SKILL.md"
            or elem.get("source_binding_version") != GOVERNANCE_SOURCE_BINDING_VERSION
            or elem.get("verification_scope") != GOVERNANCE_SOURCE_SCOPE
        ):
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_SOURCE_BINDING_INVALID",
                    message=f"Element {idx} ({skill_id}) has an invalid versioned source binding",
                    locus=_LOCUS,
                )
            )
        expected_digest = compute_skill_digest(root, source)
        if expected_digest == "0" * 64 or digest.lower() != expected_digest:
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_SOURCE_CUSTODY_INVALID",
                    message=f"Element {idx} ({skill_id}) does not bind current source bytes",
                    locus=_LOCUS,
                )
            )
        result = elem.get("result")
        if result not in ("PASS", "N_A"):
            return Err(
                Refusal(
                    code="GOVERNANCE_BUNDLE_RESULT_INVALID",
                    message=f"Element {idx} ({skill_id}) has invalid result: {result} (must be PASS or N_A)",
                    locus=_LOCUS,
                )
            )
        if idx == 0 and result != "PASS":
            return Err(
                Refusal(
                    code="GOVERNANCE_ROOT_NOT_PASSED",
                    message=f"Composition root {expected_id} must have result PASS, found {result}",
                    locus=_LOCUS,
                )
            )

    return Ok(True)
