"""Compile typed capabilities and digested guidance into OEWAS catalogs and IDE text.

The executable bindings are host-owned below, never imports named by a source.
No declaration or generated file grants detector activation or execution authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
from dataclasses import replace
from pathlib import Path

from pydantic import TypeAdapter

from operations.domain.rop.result import Err

from ..application.anti_skill.anti_skill_v2 import (
    anti_skill_v2_implementation_digest,
    evaluate_antiskill_fixture_bank,
    parse_antiskill_fixture_bank_v1,
)
from ..contracts.typed_capabilities_v1 import (
    ROOT,
    SCHEMA,
    AntibodyWireV1,
    AntiSkillWireV1,
    DigestedGuidanceWireV1,
    PortWireV1,
    RepositoryResourceWireV1,
    ResourceWireV1,
    SkillWireV1,
    canonical_bytes,
    contract_json_schema,
    digest_bytes,
    parse_typed_capability,
)
from ..domain.anti_skills.anti_skill_v2 import AntiSkillHitV1, AntiSkillSpecV2, AntiSkillSubjectV1
from ..domain.capability_catalog_v1 import ResourceRefV1, SkillCapabilityV1, seal_capability_catalog
from ..domain.entities.operation_v3 import OperationV3, PortSpecV3
from ..domain.entities.skill_document_v3 import SkillDocumentV3
from ..domain.entities.typed_contract_package import CompiledTypedPackageV1
from ..domain.prompt_hierarchy.models import AntibodyBinding, PromptTreeNode, PromptUri
from ..domain.value_objects.byte_span import SourceByteSpan
from ..domain.value_objects.content_digest import ContentDigest
from ..domain.value_objects.identifier import (
    ColourId,
    DocumentId,
    OperandId,
    OperationId,
    SchemaRef,
    SkillId,
)
from ..domain.value_objects.lifecycle_facets import (
    AdmissionFacet,
    DeclarationFacet,
    ExecutorBindingFacet,
    SchemaBindingFacet,
    SkillLifecycleV3,
    ValidationFacet,
)
from ..domain.value_objects.operands import InstructionOperand

CONTRACT_FILES = ("adversary_claim_audit.json", "adversary_scope_falsifier.json")
GENERATED_IDS = ("adversary-claim-audit", "adversary-scope-falsifier")


class TypedContractCompileRefusal(ValueError):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code


def _read(root: Path, relative: str) -> bytes:
    path = root / relative
    for component in (path, *path.parents):
        if component == root.parent:
            break
        try:
            info = component.lstat()
        except OSError as exc:
            raise TypedContractCompileRefusal("SOURCE_UNAVAILABLE", relative) from exc
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise TypedContractCompileRefusal("SOURCE_LINK_REFUSED", relative)
    if not path.resolve().is_relative_to(root) or not path.is_file():
        raise TypedContractCompileRefusal("SOURCE_PATH_REFUSED", relative)
    if path.stat().st_size > 131072:
        raise TypedContractCompileRefusal("SOURCE_SIZE_REFUSED", relative)
    return path.read_bytes()


def _resource(root: Path, resource: RepositoryResourceWireV1) -> bytes:
    raw = _read(root, resource.path)
    if hashlib.sha256(raw).hexdigest() != resource.sha256 or len(raw) != resource.byte_length:
        raise TypedContractCompileRefusal("RESOURCE_BINDING_REFUSED", resource.path)
    return raw


def _lesson_source(root: Path, wire: DigestedGuidanceWireV1) -> bytes:
    """Only retired lesson evidence may resolve its exact retained Git blob."""
    from .autopoiesis.git_learning import git_blob, safe_path
    import subprocess

    source = wire.lesson.source
    try:
        path = safe_path(root, source.path)
    except ValueError as error:
        raise TypedContractCompileRefusal("SOURCE_PATH_REFUSED", source.path) from error
    if path.exists():
        return _resource(root, source)
    if not source.path.startswith("_ic/nara/historical/oewas007/research/") or re.fullmatch(
        r"[0-9a-f]{40}", wire.lesson.source_revision
    ) is None:
        raise TypedContractCompileRefusal("SOURCE_UNAVAILABLE", source.path)
    try:
        raw = git_blob(root, wire.lesson.source_revision + ":" + source.path)
    except (OSError, subprocess.CalledProcessError) as error:
        raise TypedContractCompileRefusal("HISTORICAL_SOURCE_UNAVAILABLE", source.path) from error
    if len(raw) > 131072 or len(raw) != source.byte_length or hashlib.sha256(raw).hexdigest() != source.sha256:
        raise TypedContractCompileRefusal("RESOURCE_BINDING_REFUSED", source.path)
    return raw


def read_typed_package_resource(root: Path, skill_id: str, resource: ResourceRefV1) -> bytes:
    """Read a package resource, retaining the canonical lesson's historical pin."""
    if resource.path.startswith("_ic/nara/historical/oewas007/research/"):
        wire = parse_typed_capability(_read(root, ROOT + "/lessons/" + skill_id + ".json"))
        if not isinstance(wire, DigestedGuidanceWireV1) or wire.lesson.source.to_domain() != resource:
            raise TypedContractCompileRefusal("RESOURCE_BINDING_REFUSED", resource.path)
        return _lesson_source(root, wire)
    raw = _read(root, resource.path)
    if len(raw) != resource.byte_length or hashlib.sha256(raw).hexdigest() != resource.sha256:
        raise TypedContractCompileRefusal("RESOURCE_BINDING_REFUSED", resource.path)
    return raw


def _instruction(root: Path, resource: ResourceWireV1) -> str:
    raw = _resource(root, resource)
    try:
        body = raw.decode("utf-8")
    except UnicodeError as exc:
        raise TypedContractCompileRefusal(
            "INSTRUCTION_REFUSED", "UTF-8 instruction required"
        ) from exc
    if not body.strip() or len(raw) > 2048 or "\r" in body or body.startswith("\ufeff"):
        raise TypedContractCompileRefusal(
            "INSTRUCTION_REFUSED", "bounded BOM-free LF instruction required"
        )
    return body


def _port(
    wire: PortWireV1, schemas: dict[str, dict], validator_digest: ContentDigest
) -> PortSpecV3:
    return PortSpecV3(
        name=wire.name,
        colour_id=ColourId(wire.colour),
        schema_ref=SchemaRef(f"schema:oewas:{wire.wire_type}:v1"),
        schema_digest=ContentDigest.sha256(
            hashlib.sha256(canonical_bytes(schemas[wire.wire_type])).hexdigest()
        ),
        validator_ref=f"oewas:{wire.wire_type}:v1",
        validator_digest=validator_digest,
    )


def _render(wire, body: str, binding_text: str, source_path: str, contracts_digest: str) -> bytes:
    # Only standard Agent Skills fields; domain metadata is a string-key/value map.
    metadata = {
        "core-contract": source_path,
        "core-contracts-digest": contracts_digest,
        "core-generated": SCHEMA,
        "core-kind": wire.kind,
        "core-source-colours": json.dumps([port.colour for port in wire.inputs]),
        "core-target-colour": wire.output.colour,
        "core-arity": str(len(wire.inputs)),
        "core-residual": "unknown",
    }
    frontmatter = (
        "---\nname: "
        + wire.skill_id
        + "\ndescription: "
        + json.dumps(wire.description)
        + "\nmetadata:\n"
    )
    frontmatter += "".join(
        f"  {key}: {json.dumps(value)}\n" for key, value in sorted(metadata.items())
    )
    signature = ", ".join(f"{port.name}: {port.colour}" for port in wire.inputs)
    if isinstance(wire, DigestedGuidanceWireV1):
        return (
            frontmatter + "---\n\n# " + wire.skill_id + "\n\n"
            "Generated guidance; edit the canonical typed contract and instruction resource.\n\n"
            + body.rstrip()
            + "\n\n"
            + _lesson_markdown(wire)
            + f"\n\nOrdered signature: `({signature}) -> {wire.output.name}: {wire.output.colour}`."
            + f"\n\nContracts: `{contracts_digest}`.\n\n"
            "Source admission: `Unadmitted`. AuthorityEffect: None.\n"
            "This on-demand instruction package does not install an ambient rule, "
            "execute a detector or activate an antibody.\n"
        ).encode("utf-8")
    text = (
        frontmatter + "---\n\n# " + wire.skill_id + "\n\n"
        "Generated from the OEOP typed catalog. "
        "Edit the canonical contract and instruction resource.\n\n"
        + body.rstrip()
        + f"\n\nOrdered signature: `({signature}) -> {wire.output.name}: {wire.output.colour}`."
        + "\n\n## Evidence and execution boundary\n\n"
        + binding_text
        + "\n\nSource admission: `Unadmitted`. AuthorityEffect: None.\n"
        "The finite detector reports findings. It does not activate a production guard.\n\n"
        "From the repository root, run the offline audit with:\n\n```text\n"
        "python -m operads.infrastructure.typed_contract_compiler "
        "--repo-root . --audit-subject <subject.json>\n```\n"
    )
    return text.encode("utf-8")


def _lesson_markdown(wire: DigestedGuidanceWireV1) -> str:
    lesson = wire.lesson
    fence = "`" * max(
        3, 1 + max((len(run) for run in re.findall(r"`+", lesson.evidence_excerpt)), default=0)
    )
    lines = [
        "## Digested lesson",
        "",
        f"Source: `{lesson.source.path}` @ `{lesson.source_revision}` "
        f"(sha256:{lesson.source.sha256}).",
        "",
        "Source excerpt (evidence to inspect):",
        "",
        fence + "text",
        lesson.evidence_excerpt,
        fence,
    ]
    for field in (
        "failed_claim",
        "counterexample",
        "cause",
        "correction",
        "verification",
        "applicability",
        "exceptions",
    ):
        lines.extend(("", f"**{field.replace('_', ' ').title()}:** {getattr(lesson, field)}"))
    fields = {
        "rule": ("trigger", "predicate", "response"),
        "helpful_pattern": ("conditions", "construction", "example"),
        "anti_pattern": ("failure", "witness", "repair"),
        "antibody": (
            "antibody_id",
            "prompt_uri",
            "signal1_epitope",
            "signal2_required_danger",
            "harmful_example",
            "benign_example",
        ),
    }
    lines.extend(("", "## Guidance contract"))
    for field in fields[wire.kind]:
        lines.extend(("", f"**{field.replace('_', ' ').title()}:** {getattr(wire, field)}"))
    if isinstance(wire, AntibodyWireV1):
        lines.extend(
            (
                "",
                f"Prompt resource: `{wire.prompt.path}` (sha256:{wire.prompt.sha256}).",
                "",
                "Use the bound prompt when reviewing this failure class. Candidate only; "
                "the existing OEEIS admission and two-signal gate decide activation.",
            )
        )
    return "\n".join(lines)


def _guidance_sources(root: Path, existing_ids: tuple[str, ...]):
    rows, wires, nodes = [], [], []
    paths = sorted((root / ROOT / "lessons").glob("*.json"))
    if len(paths) > 64:
        raise TypedContractCompileRefusal("CONTRACT_COUNT_REFUSED", "at most 64 digested entries")
    seen = set(existing_ids)
    for file in paths:
        path = file.relative_to(root).as_posix()
        raw = _read(root, path)
        try:
            wire = parse_typed_capability(raw)
            if not isinstance(wire, DigestedGuidanceWireV1):
                raise ValueError("lessons directory accepts only digested guidance")
        except (TypeError, ValueError, UnicodeError) as exc:
            raise TypedContractCompileRefusal("CONTRACT_SCHEMA_REFUSED", str(exc)) from exc
        if wire.skill_id in seen or file.stem != wire.skill_id:
            raise TypedContractCompileRefusal("CONTRACT_ID_REFUSED", path)
        seen.add(wire.skill_id)
        _require_listable_description(wire)
        expected_output = "code_text" if wire.kind == "helpful_pattern" else "anti_skill_hits"
        if (
            tuple(p.wire_type for p in wire.inputs) != ("code_text",)
            or wire.output.wire_type != expected_output
        ):
            raise TypedContractCompileRefusal("COMPOSITION_BOUNDARY_REFUSED", path)
        source = _lesson_source(root, wire)
        if wire.lesson.evidence_excerpt not in source.decode("utf-8-sig"):
            raise TypedContractCompileRefusal("LESSON_SOURCE_REFUSED", path)
        if isinstance(wire, AntibodyWireV1):
            prompt = _resource(root, wire.prompt)
            if not prompt.decode("utf-8-sig").strip():
                raise TypedContractCompileRefusal("ANTIBODY_PROMPT_REFUSED", path)
            epitope = wire.signal1_epitope.lower()
            if (
                not epitope.strip()
                or epitope not in wire.harmful_example.lower()
                or epitope in wire.benign_example.lower()
            ):
                raise TypedContractCompileRefusal("ANTIBODY_CONTROLS_REFUSED", path)
            nodes.append(
                PromptTreeNode(
                    uri=PromptUri.parse(wire.prompt_uri),
                    title=wire.skill_id,
                    source_file=wire.prompt.path,
                    antibodies=(
                        AntibodyBinding(
                            wire.antibody_id, wire.signal1_epitope, wire.signal2_required_danger
                        ),
                    ),
                )
            )
        rows.append((path, raw))
        wires.append(wire)
    # Dependencies are declarations, but dangling/cyclic declarations cannot compose.
    edges = {wire.skill_id: wire.dependencies for wire in wires}

    def visit(key, ancestors):
        if key in ancestors:
            raise TypedContractCompileRefusal("DEPENDENCY_REFUSED", "cyclic digested guidance")
        for dependency in edges.get(key, ()):
            if dependency not in seen:
                raise TypedContractCompileRefusal("DEPENDENCY_REFUSED", dependency)
            visit(dependency, ancestors | {key})

    for key in edges:
        visit(key, set())
    return tuple(rows), tuple(wires), tuple(nodes)


def _require_listable_description(wire) -> None:
    """Refuse a description the model listing gate would reject after projection."""
    from operads.skill_operad.skill_compiler.skill_listing import (
        DESCRIPTION_CAP_BYTES,
    )

    size = len(wire.description.encode("utf-8"))
    if "\n" in wire.description or size > DESCRIPTION_CAP_BYTES:
        raise TypedContractCompileRefusal(
            "DESCRIPTION_REFUSED",
            f"{wire.skill_id}: description is {size} B, cap {DESCRIPTION_CAP_BYTES} B",
        )


def _source_pair(root: Path):
    source_rows = tuple(
        (ROOT + "/" + name, _read(root, ROOT + "/" + name)) for name in CONTRACT_FILES
    )
    try:
        wires = tuple(parse_typed_capability(raw) for _, raw in source_rows)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise TypedContractCompileRefusal("CONTRACT_SCHEMA_REFUSED", str(exc)) from exc
    skill, anti = wires
    if type(skill) is not SkillWireV1 or type(anti) is not AntiSkillWireV1:
        raise TypedContractCompileRefusal(
            "CONTRACT_KINDS_REFUSED", "one skill and one anti-skill required"
        )
    if (skill.skill_id, anti.skill_id) != GENERATED_IDS or skill.guard != anti.skill_id:
        raise TypedContractCompileRefusal("CONTRACT_ID_REFUSED", "registered pair required")
    if skill.dependencies != (anti.skill_id,) or anti.dependencies:
        raise TypedContractCompileRefusal(
            "DEPENDENCY_REFUSED", "one acyclic guard dependency required"
        )
    for wire in wires:
        _require_listable_description(wire)
    if (
        tuple(p.wire_type for p in skill.inputs),
        skill.output.wire_type,
        tuple(p.wire_type for p in anti.inputs),
        anti.output.wire_type,
    ) != (
        ("anti_skill_hits", "anti_skill_subject"),
        "typed_audit_receipt",
        ("anti_skill_subject",),
        "anti_skill_hits",
    ):
        raise TypedContractCompileRefusal(
            "COMPOSITION_BOUNDARY_REFUSED", "registered ordered interfaces required"
        )
    return source_rows, wires


def compile_typed_contracts(repo_root: Path) -> CompiledTypedPackageV1:
    """Read pinned resources, replay controls and return a non-authorizing package."""
    from ..application.typed_contract_audit import TypedContractAuditReceiptV1

    root = repo_root.absolute()
    source_rows, wires = _source_pair(root)
    skill, anti = wires
    learned_rows, learned_wires, prompt_attachments = _guidance_sources(root, GENERATED_IDS)
    source_rows += learned_rows
    wires += learned_wires
    bodies = tuple(_instruction(root, wire.instruction) for wire in wires)
    bodies = tuple(
        body
        + (
            "\n## Attached review prompt\n\n" + _resource(root, wire.prompt).decode("utf-8-sig")
            if isinstance(wire, AntibodyWireV1)
            else ""
        )
        for wire, body in zip(wires, bodies)
    )
    bank_result = parse_antiskill_fixture_bank_v1(_resource(root, anti.fixtures))
    if isinstance(bank_result, Err):
        raise TypedContractCompileRefusal("FIXTURE_BANK_REFUSED", bank_result.error.message)
    bank = bank_result.value
    implementation_digest = anti_skill_v2_implementation_digest()
    spec = AntiSkillSpecV2(
        spec_id=anti.skill_id,
        predicate=anti.predicate.to_domain(),
        failure_code="CLAIM_SCOPE_EXCEEDS_EVIDENCE",
        disposition=anti.enforcement,
        protected_fields=("claim_scope",),
        evidence_refs=(anti.fixtures.path,),
        counterexamples=tuple(case.case_id for case in bank.cases if case.expected_hit),
        implementation_digest=implementation_digest,
    )
    evaluation = evaluate_antiskill_fixture_bank((spec,), bank)
    if isinstance(evaluation, Err) or evaluation.value[0].outcome != "COMPUTED_PASS":
        raise TypedContractCompileRefusal(
            "FALSIFIER_CONTROLS_REFUSED", "positive/negative controls must replay"
        )
    audit_path = Path(sys.modules[TypedContractAuditReceiptV1.__module__].__file__)
    validator_digest = ContentDigest.sha256(
        hashlib.sha256(audit_path.read_bytes() + implementation_digest.encode("ascii")).hexdigest()
    )
    schemas = {
        "anti_skill_subject": TypeAdapter(AntiSkillSubjectV1).json_schema(),
        "anti_skill_hits": TypeAdapter(tuple[AntiSkillHitV1, ...]).json_schema(),
        "typed_audit_receipt": TypeAdapter(TypedContractAuditReceiptV1).json_schema(),
        "code_text": TypeAdapter(str).json_schema(),
    }
    schema_digest = ContentDigest.sha256(hashlib.sha256(canonical_bytes(schemas)).hexdigest())
    guidance_validator_digest = ContentDigest.sha256(
        hashlib.sha256(
            Path(__file__).read_bytes()
            + Path(sys.modules[SkillWireV1.__module__].__file__).read_bytes()
        ).hexdigest()
    )
    contracts_digest = digest_bytes(
        canonical_bytes(
            {
                "schema_version": SCHEMA,
                "sources": [[path, digest_bytes(raw)] for path, raw in source_rows],
                "implementation_digest": implementation_digest,
                "validator_digest": str(validator_digest),
                "schemas_digest": str(schema_digest),
                "evaluation_receipt_id": evaluation.value[0].receipt_id,
                "compiler_digest": digest_bytes(Path(__file__).read_bytes()),
                "wire_digest": digest_bytes(
                    Path(sys.modules[SkillWireV1.__module__].__file__).read_bytes()
                ),
            }
        )
    )
    bindings = (
        f"Contracts: `{contracts_digest}`\n\nSpec: `{spec.spec_digest}`\n\n"
        f"Fixtures: `{bank.bank_id}`\n\nEvaluation: `{evaluation.value[0].receipt_id}`\n\n"
        f"Implementation: `{implementation_digest}`"
    )
    life = SkillLifecycleV3(
        declaration=DeclarationFacet.DECLARED,
        schema_binding=SchemaBindingFacet.BOUND,
        executor_binding=ExecutorBindingFacet.BOUND,
        validation=ValidationFacet.VALIDATED,
        admission=AdmissionFacet.UNADMITTED,
        schema_digest=schema_digest,
        executor_digest=validator_digest,
    )
    operations, documents, packages, skills = [], [], [], []
    for (path, raw), wire, body in zip(source_rows, wires, bodies):
        op_id, operand_id = OperationId(wire.skill_id), OperandId(wire.skill_id + ".instruction")
        guidance = isinstance(wire, DigestedGuidanceWireV1)
        port_validator = guidance_validator_digest if guidance else validator_digest
        operation_life = replace(life, executor_digest=port_validator) if guidance else life
        op = OperationV3(
            operation_id=op_id,
            inputs=tuple(_port(p, schemas, port_validator) for p in wire.inputs),
            output=_port(wire.output, schemas, port_validator),
            operand_refs=(operand_id,),
            lifecycle=operation_life,
            residual_status="unknown",
            effects=wire.effects,
            description=wire.description,
        )
        operations.append(op)
        # This span identifies the declaration's pinned instruction reference.
        # The external body has its own ResourceRefV1 byte hash in the catalog.
        reference_bytes = canonical_bytes(wire.instruction.model_dump(mode="json")).rstrip(b"\n")
        start = raw.index(b'"instruction":') + len(b'"instruction":')
        span = SourceByteSpan(
            start, start + len(reference_bytes), 1, start, 1, start + len(reference_bytes)
        )
        operand = InstructionOperand(
            operand_id,
            "instruction",
            body.rstrip()
            + "\n\n"
            + (
                _lesson_markdown(wire) + f"\n\nContracts: `{contracts_digest}`"
                if guidance
                else bindings
            ),
            span,
        )
        raw_digest = ContentDigest.sha256(hashlib.sha256(raw).hexdigest())
        documents.append(
            SkillDocumentV3(
                document_id=DocumentId(wire.skill_id),
                skill_id=SkillId(wire.skill_id),
                source_relative_path=path,
                raw_digest=raw_digest,
                semantic_digest=raw_digest,
                operands=(operand,),
                operations=(op,),
            )
        )
        markdown = _render(wire, body, bindings, path, contracts_digest)
        packages.append((wire.skill_id, markdown))
        resources = [
            ResourceRefV1(path, hashlib.sha256(raw).hexdigest(), len(raw)),
            wire.instruction.to_domain(),
        ]
        if type(wire) is AntiSkillWireV1:
            resources.append(wire.fixtures.to_domain())
        if isinstance(wire, DigestedGuidanceWireV1):
            resources.append(wire.lesson.source.to_domain())
        if isinstance(wire, AntibodyWireV1):
            resources.append(wire.prompt.to_domain())
        resources = list({resource.path: resource for resource in resources}.values())
        skills.append(
            SkillCapabilityV1(
                skill_id=wire.skill_id,
                name=wire.skill_id,
                description=wire.description,
                source_path=f"skills/{wire.skill_id}/SKILL.md",
                source_digest=hashlib.sha256(markdown).hexdigest(),
                source_colours=tuple(p.colour for p in wire.inputs),
                target_colour=wire.output.colour,
                arity=len(wire.inputs),
                residual_effect="unknown",
                invocation="discipline",
                invocation_explicit=False,
                families=("adversary",),
                declared_dependencies=wire.dependencies,
                declared_triggers=("PRE_SEAL",)
                if not isinstance(wire, DigestedGuidanceWireV1)
                else ((wire.trigger,) if wire.kind == "rule" else ()),
                package_resources=tuple(sorted(resources, key=lambda item: item.path)),
            )
        )
    return CompiledTypedPackageV1(
        contracts_digest,
        seal_capability_catalog(
            skills=tuple(sorted(skills, key=lambda item: item.skill_id)), agents=()
        ),
        tuple(operations),
        tuple(documents[: len(CONTRACT_FILES)]),
        spec,
        bank,
        tuple(packages),
        prompt_attachments,
        tuple(documents[len(CONTRACT_FILES) :]),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--audit-subject", type=Path)
    mode.add_argument("--show-schema", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.repo_root.absolute()
        if args.show_schema:
            sys.stdout.buffer.write(canonical_bytes(contract_json_schema()))
        elif args.audit_subject:
            from ..application.typed_contract_audit import audit_typed_contracts
            from ..domain.anti_skills.json_wire import loads_strict_json

            subject = AntiSkillSubjectV1.from_dict(
                loads_strict_json(args.audit_subject.read_text(encoding="utf-8"))
            )
            result = audit_typed_contracts(
                subject, compile_current=lambda: compile_typed_contracts(root)
            )
            if isinstance(result, Err):
                print(result.error.code, file=sys.stderr)
                return 1
            sys.stdout.buffer.write(canonical_bytes(result.value.to_dict()))
        else:
            from operations.use_cases.packaging.project_typed_contracts import (
                project_typed_packages,
            )

            bundle = compile_typed_contracts(root)
            paths = project_typed_packages(root, bundle.packages, check=args.check)
            print(
                f"TYPED_PACKAGES_OK packages={len(bundle.packages)} files={len(paths)} "
                f"contracts={bundle.contracts_digest}"
            )
    except (ValueError, TypeError, OSError) as exc:
        print(f"TYPED_CONTRACT_REFUSED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
