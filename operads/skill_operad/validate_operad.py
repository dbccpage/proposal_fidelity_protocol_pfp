"""
Operad Structure & Quotient Functor Validator
AuthorityEffect: None
"""
import os
import json
import re
import sys
from pathlib import Path

from coloured_operad import ColouredOperad
from oeop_dto_schemas import WASLifecyclePlanDTO, WASRolePlanDTO
from evidence_observations import classify_residual_rows

# Sampling target for diagnostics only. No observation count is a quotient,
# equivalence, contractivity, or promotion threshold.
DIAGNOSTIC_SAMPLE_TARGET = 3
from quotient_operad import QuotientFunctor, load_ledgers_from_trace
from symmetric_quotient import SymmetricQuotientFunctor, orbit_report
from application.use_cases.validate_operad_use_case import validate_composition_grading


def load_entry_skills(skills_root: Path) -> set[str]:
    """Read the two-layer grade from admitted skill frontmatter."""
    entries: set[str] = set()
    for skill_path in sorted(skills_root.glob("*/SKILL.md")):
        text = skill_path.read_text(encoding="utf-8-sig")
        parts = text.split("---", 2)
        if len(parts) < 3:
            continue
        frontmatter = parts[1]
        if not re.search(r"(?m)^invocation:\s*entry\s*$", frontmatter):
            continue
        name = re.search(r"(?m)^name:\s*[\"']?([^\r\n\"']+)", frontmatter)
        entries.add(name.group(1).strip() if name else skill_path.parent.name)
    return entries


def validate_was_registries(registry_root: Path) -> list[str]:
    errors: list[str] = []
    for filename, model in (
        ("roles.yaml", WASRolePlanDTO),
        ("lifecycle.yaml", WASLifecyclePlanDTO),
    ):
        path = registry_root / filename
        try:
            content = path.read_text(encoding="utf-8-sig")
            try:
                import yaml
                data = yaml.safe_load(content)
            except ImportError:
                data = json.loads(content)
            model.model_validate(data)
        except Exception as exc:
            errors.append(f"{filename}: {exc}")
    return errors

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    sig_path = (
        os.path.join(base_dir, "json", "operad_signature.json")
        if os.path.exists(os.path.join(base_dir, "json", "operad_signature.json"))
        else os.path.join(base_dir, "operad_signature.json")
    )
    comp_path = (
        os.path.join(base_dir, "json", "composition_matrix.json")
        if os.path.exists(os.path.join(base_dir, "json", "composition_matrix.json"))
        else os.path.join(base_dir, "composition_matrix.json")
    )
    slice_path = (
        os.path.join(base_dir, "json", "agent_capability_slices.json")
        if os.path.exists(os.path.join(base_dir, "json", "agent_capability_slices.json"))
        else os.path.join(base_dir, "agent_capability_slices.json")
    )
    trace_path = (
        os.path.join(base_dir, "json", "evidence_trace.json")
        if os.path.exists(os.path.join(base_dir, "json", "evidence_trace.json"))
        else os.path.join(base_dir, "evidence_trace.json")
    )

    print("=== OPERAD & SYMMETRIC QUOTIENT VALIDATION START ===")

    # 1. Instantiate ColouredOperad and load colours & operations
    with open(sig_path, "r", encoding="utf-8") as f:
        sig = json.load(f)

    operad = ColouredOperad("AnomalonSkillOperad")

    for col in sig["colours"].keys():
        operad.add_colour(col)
    print(f"[OK] Loaded {len(operad.colours)} finite colours: {sorted(list(operad.colours.keys()))}")

    for op in sig["operations"]:
        operad.add_operation(
            op_id=op["skill_id"],
            name=op["name"],
            source_colours=op["source_colours"],
            target_colour=op["target_colour"],
            equivariant=op.get("equivariant", False),
            residual_effect=op.get("residual_effect", "unknown"),
        )
    print(f"[OK] Loaded {len(sig['operations'])} operad skill signatures.")

    # Load composition matrix
    with open(comp_path, "r", encoding="utf-8") as f:
        comp_data = json.load(f)

    # Resolve repo root and host roots
    _cur = Path(base_dir).resolve()
    repo_root = None
    for p in [_cur, *_cur.parents]:
        if (p / ".git").exists() and (p / ".agents").is_dir():
            repo_root = p
            break
    if repo_root is None:
        repo_root = _cur.parents[1]

    if (Path(base_dir).parent / "skills").is_dir():
        skills_root = Path(base_dir).parent / "skills"
    else:
        skills_root = repo_root / "omega_engine_operads" / "skills"

    if (Path(base_dir).parent / "registry").is_dir():
        registry_root = Path(base_dir).parent / "registry"
    else:
        registry_root = repo_root / "omega_engine_operads" / "registry"

    entry_skills = load_entry_skills(skills_root)
    grading_errs, terminal_entry_ops = validate_composition_grading(
        comp_data.get("compositions", []), entry_skills
    )
    for msg in grading_errs:
        print(f"[ERROR] {msg}")

    composition_errs: list[str] = []
    for c in comp_data["compositions"]:
        res = operad.add_composition(
            outer=c["outer"],
            slot=c["slot"],
            inner=c["inner"],
            result=c.get("composite_id", c.get("result", "composite_op")),
        )
        if res.is_failure:
            err = res.unwrap_err()
            msg = f"Composition registration failed for '{c.get('composite_id')}': {err.message}"
            print(f"[ERROR] {msg}")
            composition_errs.append(msg)

    # A composition the operad refused is not registered, so every later check
    # runs against a structure missing that arrow and finds nothing wrong with
    # it. This loop previously printed the refusal and fell through to
    # [SUCCESS] with exit 0 -- the only error path in this validator that did.
    # Every sibling check below (algebraic, grading, registry, meta) exits 1.
    if composition_errs or grading_errs:
        print(
            f"\n[FAIL] {len(composition_errs)} composition registration "
            f"error(s); {len(grading_errs)} grading error(s)."
        )
        sys.exit(1)

    # Ensure identity units
    operad.ensure_units()
    print(f"[OK] Identity units enforced. Total operations: {len(operad.operations)}.")

    # 2. Check the declaration table; these entries are not executor law evidence.
    errs = operad.validate_all()
    if errs:
        for err in errs:
            print(f"[ERROR] Declaration table error: {err}")
        sys.exit(1)
    print("[OK] Unit and type declaration table is consistent (0 errors).")
    print("[UNAVAILABLE] Executable unit-law evidence: " + operad.unit_law_evidence()["reason"])

    # 2b. Two-Layer Grading Law: entry skills may invoke disciplines, but an
    # entry or entry-derived composite is terminal and cannot be an inner
    # operand. Grades come from admitted skill metadata and propagate through
    # synthesized composites rather than from a second hardcoded list.
    print(
        "[OK] Two-Layer Grading Law verified "
        f"({len(entry_skills)} admitted entry skills; "
        f"{len(terminal_entry_ops) - len(entry_skills)} terminal composite(s); "
        "0 compositions above terminal entries)."
    )

    registry_errs = validate_was_registries(registry_root)
    if registry_errs:
        for error in registry_errs:
            print(f"[ERROR] WAS registry validation failed: {error}")
        sys.exit(1)
    print("[OK] A01 WAS role and lifecycle registries match their DTO schemas.")

    # 3. Normalize declared symmetric copies and report comparison candidates.
    #    Scalar traces never identify distinct declared operations.
    SQ = SymmetricQuotientFunctor(
        operad, min_instances=DIAGNOSTIC_SAMPLE_TARGET
    )

    # Load diagnostic scalar observations (no hardcoded synthetic loops). These
    # rows never establish a semantic residual class or equivalence.
    if os.path.exists(trace_path):
        load_ledgers_from_trace(trace_path, SQ)
        print(f"[OK] Loaded diagnostic residual observations from {trace_path}.")

    meta = SQ.build_meta_operad("AnomalonSymmetricMetaOperad")
    meta_errs = meta.validate_all()
    if meta_errs:
        for err in meta_errs:
            print(f"[ERROR] Meta operad validation error: {err}")
        sys.exit(1)

    report = SQ.report()
    oreport = orbit_report(SQ.orbit_engine)
    print(
        f"[OK] Symmetric comparison model validated: {report['concrete_ops']} "
        f"concrete ops -> {report['meta_ops']} comparison ops "
        f"(automatic merges disabled, {oreport['total_ops_with_orbits']} orbit-tracked)."
    )

    # 4. Check associativity laws.
    #    A declared law is only credited if its witness composite is actually registered
    #    in the operad. Previously this read law["associative"], a boolean typed by hand
    #    next to the claim it was supposed to check, so the gate could never fail.
    assoc_laws = comp_data.get("associativity_laws", [])
    assoc_verified = 0
    assoc_unverified = 0
    for law in assoc_laws:
        witness = law.get("verified_equal_id")
        if witness and witness in operad.operations:
            assoc_verified += 1
        else:
            assoc_unverified += 1
            print(
                f"[WARN] Associativity law UNVERIFIED: witness composite "
                f"'{witness}' is not a registered operation. "
                f"Declared: {law.get('left_composite')} == {law.get('right_composite')}"
            )
    print(
        f"[OK] Associativity: {assoc_verified}/{len(assoc_laws)} declared laws have a "
        f"registered witness composite "
        f"({assoc_unverified} declared-but-unverified; not counted as global success)."
    )

    # 5. Report meta-skill diagnostic observations. No count of scalar rows can
    #    mint a residual invariant, equivalence, quotient, or promotion.
    trace_rows = []
    if os.path.exists(trace_path):
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_rows = json.load(f)

    observations = classify_residual_rows(trace_rows)
    observation_runs = {}
    for observation in observations:
        observation_runs.setdefault(observation.skill_id, set()).add(
            observation.run_id
        )

    meta_skills = comp_data.get("synthesized_meta_skills", [])
    provisional = 0
    for ms in meta_skills:
        observed = observation_runs.get(ms["id"], set())
        is_provisional = ms.get("status") == "provisional"
        if not is_provisional:
            print(
                f"[ERROR] Meta-skill '{ms['id']}' is not provisional, but this "
                "registry has no independent certification path."
            )
            errs.append(f"Meta-skill {ms['id']} exceeds the claim ceiling")
        else:
            provisional += 1
            print(
                f"[PROVISIONAL] Meta-skill '{ms['id']}': {len(observed)} diagnostic "
                "observation(s). NOT minted; count has no promotion effect. "
                f"Observed: {sorted(observed) or 'none'}"
            )

        # A cited run may be present diagnostically; presence is not corroboration.
        for cited in ms.get("evidence_gate", {}).get("instances", []):
            if not any(r.startswith(cited) for r in observed):
                print(
                    f"[ERROR] Meta-skill '{ms['id']}' cites observation '{cited}', "
                    "which is absent from evidence_trace.json."
                )
                errs.append(f"Meta-skill {ms['id']} cites absent observation {cited}")

    print(
        f"[OK] Meta-skill diagnostic rows classified "
        f"({len(meta_skills)} meta-skills, {provisional} provisional / not minted)."
    )

    # 6. Verify agent capability slices WITHOUT silent filtering
    with open(slice_path, "r", encoding="utf-8") as f:
        slice_data = json.load(f)

    agents = slice_data["agents"]
    slice_errors = 0
    for agent_id, data in agents.items():
        try:
            # Direct slice invocation without masking unknown skills
            agent_slice = operad.slice(agent_id, data["licensed_skills"])
        except Exception as exc:
            print(f"[ERROR] Agent slice strict validation failed for '{agent_id}': {exc}")
            slice_errors += 1

    if slice_errors > 0:
        print(f"[FAIL] {slice_errors} agent capability slices failed strict validation.")
        sys.exit(1)

    print(f"[OK] Agent capability slices check complete ({len(agents)} agents strictly verified without masking).")

    # 7. Residual honesty: diagnostic observations cannot support contractivity.
    try:
        from residual_honesty import run_checks as residual_honesty_checks
    except ImportError:
        residual_honesty_checks = None
    if residual_honesty_checks is not None:
        # base_dir is <repo>/.agents/operad → repo is two parents up
        from pathlib import Path as _Path

        repo_root = _Path(base_dir).resolve().parents[1]
        honesty = residual_honesty_checks(repo_root)
        for err in honesty.get("errors") or []:
            print(f"[ERROR] Residual honesty: {err}")
            errs.append(err)
        if not honesty.get("errors"):
            print(
                "[OK] Residual honesty: no unbacked residual_effect=contractive claims "
                "(diagnostic observations have no claim effect)."
            )

    if errs:
        print(f"\n[FAIL] Validation completed with {len(errs)} errors.")
        sys.exit(1)

    # Narrow success: do not claim "all constraints" when declared associativity
    # laws remain unverified (witness composite missing from the operad).
    print(
        f"\n[SUCCESS] Structural registry validation PASS; "
        f"{assoc_unverified} associativity declaration(s) remain unverified. "
        "No behavioral quotient, skill execution, semantic correctness, or "
        "promotion authority is claimed. AuthorityEffect: None."
    )

if __name__ == "__main__":
    main()
