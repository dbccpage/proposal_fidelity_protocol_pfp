"""Compile the Git-tracked agent/skill estate into deterministic projections.

Only direct, Git-tracked canonical entrypoints are eligible. On-disk cache
directories and untracked packages never enter the catalog by discovery.
Generated projections carry declarations and digests with AuthorityEffect
``none``; executor reachability, health, and authorization are later facets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, NoReturn

import yaml

from operads.canon import COLOUR_MEANINGS
from operads.domain.capability_catalog_v1 import (
    BOUND_EXECUTOR_V1,
    OPERAD_COLOURS_V1,
    AgentCapabilityV1,
    CapabilityCatalogRefusal,
    CapabilityCatalogV1,
    ExecutorBindingV1,
    ResourceRefV1,
    SkillCapabilityV1,
    compute_agent_license_digest,
    decode_capability_catalog,
    encode_capability_catalog,
    seal_capability_catalog,
)

HOST_NAMES = (".agents", ".claude", ".codex", ".grok")
CATALOG_FILENAME = "capability_catalog.v1.json"
SIGNATURE_FILENAME = "operad_signature.json"
SLICES_FILENAME = "agent_capability_slices.json"
INVENTORY_PATH = Path("operads/skill_operad/yaml/op_inventory.yaml")
SCRIPT_EXECUTORS_PATH = Path("operads/skill_operad/yaml/script_executors.yaml")

COLOUR_DESCRIPTIONS = COLOUR_MEANINGS

if frozenset(COLOUR_DESCRIPTIONS) != OPERAD_COLOURS_V1:
    raise RuntimeError("colour descriptions do not cover the admitted vocabulary exactly")


class CatalogCompileRefusal(ValueError):
    def __init__(self, code: str, locus: str, detail: str) -> None:
        super().__init__(f"{code}:{locus}:{detail}")
        self.code = code
        self.locus = locus
        self.detail = detail


def _refuse(code: str, locus: str, detail: str) -> NoReturn:
    raise CatalogCompileRefusal(code, locus, detail)


class _DuplicateRefusingLoader(yaml.SafeLoader):
    pass


def _construct_mapping(
    loader: _DuplicateRefusingLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[Any, Any]:
    loader.flatten_mapping(node)
    result: dict[Any, Any] = {}
    for key, value in loader.construct_pairs(node, deep=deep):  # type: ignore[no-untyped-call]
        if type(key) is not str or key in result:
            _refuse("FRONTMATTER_KEY_REFUSED", "frontmatter", "keys must be unique strings")
        result[key] = value
    return result


_DuplicateRefusingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping
)


@dataclass(frozen=True, slots=True)
class TrackedEstateInventoryV1:
    paths: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.paths or self.paths != tuple(sorted(set(self.paths))):
            _refuse(
                "TRACKED_INVENTORY_REFUSED",
                "inventory",
                "paths must be non-empty, sorted, and unique",
            )
        for path in self.paths:
            if (
                type(path) is not str
                or "\\" in path
                or path.startswith("/")
                or any(part in {"", ".", ".."} for part in path.split("/"))
            ):
                _refuse("TRACKED_PATH_REFUSED", "inventory", repr(path))


def git_tracked_estate_inventory(repo_root: Path) -> TrackedEstateInventoryV1:
    """Return tracked resource paths; entrypoint discovery stays in canonical roots.

    Digested guidance may reference tracked rules, patterns or historical sources.
    """

    environment = os.environ.copy()
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-files",
            "-z",
        ],
        check=False,
        capture_output=True,
        env=environment,
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", errors="replace").strip()
        _refuse("GIT_INVENTORY_UNAVAILABLE", str(repo_root), detail or "git ls-files failed")
    try:
        paths = tuple(
            sorted(
                item.decode("utf-8", errors="strict")
                for item in completed.stdout.split(b"\0")
                if item
            )
        )
    except UnicodeError as error:
        raise CatalogCompileRefusal(
            "GIT_PATH_ENCODING_REFUSED", str(repo_root), str(error)
        ) from error
    return TrackedEstateInventoryV1(paths=paths)


def _frontmatter(raw: bytes, locus: str) -> tuple[dict[str, Any], str]:
    if raw.startswith(b"\xef\xbb\xbf"):
        _refuse("SOURCE_BOM_REFUSED", locus, "UTF-8 BOM is forbidden")
    try:
        text = raw.decode("utf-8", errors="strict").replace("\r\n", "\n").replace("\r", "\n")
    except UnicodeError as error:
        raise CatalogCompileRefusal("SOURCE_UTF8_REFUSED", locus, str(error)) from error
    if not text.startswith("---\n"):
        _refuse("FRONTMATTER_MISSING", locus, "opening delimiter is missing")
    end = text.find("\n---", 4)
    if end < 0:
        _refuse("FRONTMATTER_MISSING", locus, "closing delimiter is missing")
    after = end + 4
    if after < len(text) and text[after] != "\n":
        _refuse("FRONTMATTER_DELIMITER_REFUSED", locus, "closing delimiter has trailing content")
    try:
        value = yaml.load(text[4:end], Loader=_DuplicateRefusingLoader)
    except CatalogCompileRefusal:
        raise
    except yaml.YAMLError as error:
        raise CatalogCompileRefusal("FRONTMATTER_YAML_REFUSED", locus, str(error)) from error
    if type(value) is not dict:
        _refuse("FRONTMATTER_OBJECT_REFUSED", locus, "frontmatter must be an object")
    return value, text[after:]


def _required_text(meta: dict[str, Any], key: str, locus: str) -> str:
    value = meta.get(key)
    if type(value) is not str or not value.strip():
        _refuse("FIELD_TEXT_REFUSED", locus, f"{key} must be a non-empty string")
    return value


def _string_list(
    meta: dict[str, Any],
    key: str,
    locus: str,
    *,
    required: bool,
    sort_values: bool = True,
) -> tuple[str, ...]:
    if key not in meta:
        if required:
            _refuse("FIELD_MISSING", locus, key)
        return ()
    raw = meta[key]
    if type(raw) is not list or any(type(item) is not str or not item for item in raw):
        _refuse("FIELD_LIST_REFUSED", locus, f"{key} must be a list of non-empty strings")
    values = tuple(raw)
    if len(set(values)) != len(values):
        _refuse("FIELD_DUPLICATE_REFUSED", locus, key)
    return tuple(sorted(values)) if sort_values else values


def _canonical_source_digest(raw: bytes, locus: str) -> str:
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeError as error:
        raise CatalogCompileRefusal("SOURCE_UTF8_REFUSED", locus, str(error)) from error
    canonical = text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _read_tracked(repo_root: Path, relative: str) -> bytes:
    candidate = (repo_root / Path(*relative.split("/"))).resolve()
    root = repo_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        _refuse("PATH_ESCAPE_REFUSED", relative, "path escaped repository")
    if not candidate.is_file():
        _refuse("TRACKED_FILE_MISSING", relative, "Git-tracked source is absent")
    if candidate.is_symlink():
        _refuse("SYMLINK_REFUSED", relative, "catalog sources must be regular files")
    return candidate.read_bytes()


def _neutral_path(path: str) -> str:
    for prefix in ("operads/", ".agents/"):
        if path.startswith(prefix):
            return path[len(prefix) :]
    _refuse("CANONICAL_HOST_REFUSED", path, "source is outside the capability source roots")


def _generated_skill(
    repo_root: Path, path: str, raw: bytes, skill_id: str,
    package_paths: tuple[str, ...], tracked_paths: tuple[str, ...],
) -> SkillCapabilityV1:
    from .typed_contract_compiler import compile_typed_contracts, read_typed_package_resource

    bundle = compile_typed_contracts(repo_root)
    expected = dict(bundle.packages).get(skill_id)
    if expected is None or raw != expected:
        _refuse("TYPED_PROJECTION_DRIFT", path, "recompile current canonical contract bytes")
    skill = next(item for item in bundle.catalog.skills if item.skill_id == skill_id)
    for resource in skill.package_resources:
        if resource.path not in tracked_paths:
            if not resource.path.startswith("_ic/nara/historical/oewas007/research/"):
                _refuse("TYPED_SOURCE_UNTRACKED", path, "canonical sources must be in the Git inventory")
            read_typed_package_resource(repo_root, skill_id, resource)
    resources = list(skill.package_resources)
    for resource_path in package_paths:
        resource_raw = _read_tracked(repo_root, resource_path)
        resources.append(ResourceRefV1(
            path=_neutral_path(resource_path),
            sha256=hashlib.sha256(resource_raw).hexdigest(),
            byte_length=len(resource_raw),
        ))
    return replace(skill, package_resources=tuple(sorted(resources, key=lambda item: item.path)))


def _skill_from_source(
    *, repo_root: Path, path: str, package_paths: tuple[str, ...],
    tracked_paths: tuple[str, ...] = (),
) -> SkillCapabilityV1:
    raw = _read_tracked(repo_root, path)
    meta, _body = _frontmatter(raw, path)
    skill_id = path.split("/")[2]
    name = _required_text(meta, "name", path)
    if name != skill_id:
        _refuse("SKILL_NAME_PATH_REFUSED", path, f"name={name!r}")
    description = _required_text(meta, "description", path)
    metadata = meta.get("metadata")
    if type(metadata) is dict and metadata.get("core-generated") == "oewas.typed-capability.v1":
        return _generated_skill(repo_root, path, raw, skill_id, package_paths, tracked_paths)
    source_colours = _string_list(
        meta,
        "operad_source_colours",
        path,
        required=True,
        sort_values=False,
    )
    target_colour = _required_text(meta, "operad_target_colour", path)
    arity = meta.get("operad_arity")
    if type(arity) is not int or arity != len(source_colours):
        _refuse("SKILL_ARITY_REFUSED", path, f"arity={arity!r} source_count={len(source_colours)}")
    residual = _required_text(meta, "operad_residual", path)
    if any(colour not in OPERAD_COLOURS_V1 for colour in (*source_colours, target_colour)):
        _refuse("SKILL_COLOUR_REFUSED", path, "operation names an unknown colour")
    invocation_explicit = "invocation" in meta
    invocation = meta.get("invocation", "discipline")
    if type(invocation) is not str or not invocation:
        _refuse("INVOCATION_REFUSED", path, "invocation must be a non-empty string")
    families = _string_list(meta, "families", path, required=False)
    if not families:
        families = (skill_id.split("-", 1)[0] if "-" in skill_id else "default",)
    dependencies = _string_list(meta, "skill_dependencies", path, required=False)
    triggers = _string_list(meta, "triggers", path, required=False)
    equivariant = meta.get("operad_equivariant")
    if equivariant is not None and type(equivariant) is not bool:
        _refuse("EQUIVARIANCE_REFUSED", path, "operad_equivariant must be bool")
    agent_scope = _string_list(meta, "agent_scope", path, required=False)
    if "executor" in meta or "host_executor_id" in meta:
        _refuse("EXECUTOR_DECLARATION_REFUSED", path, "v1 source declarations must remain unbound")
    resources: list[ResourceRefV1] = []
    for resource_path in package_paths:
        resource_raw = _read_tracked(repo_root, resource_path)
        resources.append(
            ResourceRefV1(
                path=_neutral_path(resource_path),
                sha256=hashlib.sha256(resource_raw).hexdigest(),
                byte_length=len(resource_raw),
            )
        )
    return SkillCapabilityV1(
        skill_id=skill_id,
        name=name,
        description=description,
        source_path=_neutral_path(path),
        source_digest=_canonical_source_digest(raw, path),
        source_colours=source_colours,
        target_colour=target_colour,
        arity=arity,
        residual_effect=residual,
        invocation=invocation,
        invocation_explicit=invocation_explicit,
        families=families,
        declared_dependencies=dependencies,
        declared_triggers=triggers,
        package_resources=tuple(resources),
        executor=ExecutorBindingV1(),
        equivariant=equivariant,
        agent_scope=agent_scope,
    )


def _agent_from_source(*, repo_root: Path, path: str) -> AgentCapabilityV1:
    raw = _read_tracked(repo_root, path)
    meta, _body = _frontmatter(raw, path)
    agent_id = Path(path).stem
    name = _required_text(meta, "name", path)
    if name != agent_id:
        _refuse("AGENT_NAME_PATH_REFUSED", path, f"name={name!r}")
    if "skills" in meta:
        _refuse("LEGACY_LICENSE_KEY_REFUSED", path, "use licensed_skills only")
    licensed_skills = _string_list(meta, "licensed_skills", path, required=True)
    licensed_colours = _string_list(meta, "licensed_colours", path, required=True)
    tools = _string_list(meta, "tools", path, required=True)
    standalone = meta.get("standalone")
    if type(standalone) is not bool:
        _refuse("STANDALONE_REFUSED", path, "standalone must be bool")
    if meta.get("authority_effect") != "none":
        _refuse("AUTHORITY_REFUSED", path, "authority_effect must be none")
    return AgentCapabilityV1(
        agent_id=agent_id,
        name=name,
        description=_required_text(meta, "description", path),
        model=_required_text(meta, "model", path),
        source_path=_neutral_path(path),
        source_digest=_canonical_source_digest(raw, path),
        license_digest=compute_agent_license_digest(
            agent_id=agent_id,
            licensed_skill_ids=licensed_skills,
            licensed_colour_ids=licensed_colours,
            tools=tools,
            standalone=standalone,
        ),
        licensed_skill_ids=licensed_skills,
        licensed_colour_ids=licensed_colours,
        tools=tools,
        standalone=standalone,
    )


def executor_bindings(repo_root: Path) -> dict[str, ExecutorBindingV1]:
    """BOUND bindings for every op-inventory skill whose ops all have host executors.

    The digest covers each op's host target and the bytes of the file that defines it,
    so editing an executor changes the catalogue. A skill with any op lacking a
    registered executor, or a target whose file or symbol is gone, stays UNBOUND.
    """
    inventory_path = repo_root / INVENTORY_PATH
    if not inventory_path.is_file():
        return {}
    from operads.skill_operad.resolver.executors import executable_coverage
    from operads.skill_operad.skill_compiler.op_inventory import load_inventory

    inventory = load_inventory(inventory_path)
    covered = executable_coverage(inventory)
    bindings: dict[str, ExecutorBindingV1] = {}
    for skill in inventory.skills:
        if not covered.get(skill.skill_id):
            continue
        targets = [
            (op.op_id, op.binding if type(op.binding) is str else getattr(op.binding, "target", None))
            for op in (*skill.ops, *skill.anti_ops)
        ]
        rows = []
        for op_id, target in sorted(targets, key=lambda row: row[0]):
            if type(target) is not str or "::" not in target:
                break
            file_part, _, symbol = target.partition("::")
            source = repo_root / Path(*file_part.split("/"))
            if not source.is_file() or f"def {symbol}(" not in source.read_text(encoding="utf-8"):
                break
            rows.append([op_id, target, hashlib.sha256(source.read_bytes()).hexdigest()])
        else:
            payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True).encode("ascii")
            bindings[skill.skill_id] = ExecutorBindingV1(
                state=BOUND_EXECUTOR_V1,
                host_executor_id=f"op_inventory:{skill.skill_id}",
                implementation_digest=hashlib.sha256(payload).hexdigest(),
            )
    return bindings


def script_bindings(repo_root: Path) -> dict[str, ExecutorBindingV1]:
    """BOUND bindings for the skill scripts listed in ``script_executors.yaml``.

    A listed script must sit in its own skill package and have a ``__main__`` guard;
    ``test_script_executors.py`` checks that each one starts.
    """
    path = repo_root / SCRIPT_EXECUTORS_PATH
    if not path.is_file():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(data) is not dict or data.get("schema_version") != "core.oewas.script_executors.v1":
        _refuse("SCRIPT_EXECUTORS_REFUSED", SCRIPT_EXECUTORS_PATH.as_posix(), "unknown schema")
    bindings: dict[str, ExecutorBindingV1] = {}
    for row in data.get("skills") or []:
        skill_id, script = row.get("skill_id"), row.get("script")
        locus = f"{SCRIPT_EXECUTORS_PATH.as_posix()}:{skill_id}"
        if type(skill_id) is not str or type(script) is not str or skill_id in bindings:
            _refuse("SCRIPT_EXECUTOR_REFUSED", locus, "skill_id and script must be unique strings")
        if not script.startswith(f"operads/skills/{skill_id}/scripts/"):
            _refuse("SCRIPT_EXECUTOR_REFUSED", locus, "script must be in the skill's own package")
        raw = _read_tracked(repo_root, script)
        if b'__name__ == "__main__"' not in raw:
            _refuse("SCRIPT_EXECUTOR_REFUSED", locus, "script has no __main__ guard")
        payload = json.dumps(
            [[skill_id, script, hashlib.sha256(raw).hexdigest()]], separators=(",", ":")
        ).encode("ascii")
        bindings[skill_id] = ExecutorBindingV1(
            state=BOUND_EXECUTOR_V1,
            host_executor_id=f"script:{script}",
            implementation_digest=hashlib.sha256(payload).hexdigest(),
        )
    return bindings


def _bind_executors(
    repo_root: Path, skills: tuple[SkillCapabilityV1, ...]
) -> tuple[SkillCapabilityV1, ...]:
    host = executor_bindings(repo_root)
    scripts = script_bindings(repo_root)
    for skill_id in sorted(set(host) & set(scripts)):
        _refuse("EXECUTOR_DOUBLE_BINDING", skill_id, "bound by the op inventory and a script")
    bindings = {**host, **scripts}
    known = {skill.skill_id for skill in skills}
    for skill_id in sorted(set(bindings) - known):
        _refuse("EXECUTOR_SKILL_UNKNOWN", INVENTORY_PATH.as_posix(), skill_id)
    return tuple(
        replace(skill, executor=bindings[skill.skill_id]) if skill.skill_id in bindings else skill
        for skill in skills
    )


def compile_capability_catalog(
    repo_root: Path,
    *,
    tracked_paths: tuple[str, ...] | None = None,
) -> CapabilityCatalogV1:
    inventory = (
        git_tracked_estate_inventory(repo_root)
        if tracked_paths is None
        else TrackedEstateInventoryV1(paths=tracked_paths)
    )
    # Explicit inventories still support retained host-format fixtures. Live
    # discovery always selects OEOP and cannot fall back to generated host bytes.
    prefix = "operads/" if tracked_paths is None or any(
        path.startswith("operads/skills/") for path in inventory.paths
    ) else ".agents/"
    agent_paths = tuple(
        path
        for path in inventory.paths
        if path.startswith(prefix + "agents/")
        and len(path.split("/")) == 3
        and path.endswith(".md")
        and not Path(path).name.startswith(("_", "."))
    )
    skill_paths = tuple(
        path
        for path in inventory.paths
        if path.startswith(prefix + "skills/")
        and len(path.split("/")) == 4
        and path.endswith("/SKILL.md")
        and not path.split("/")[2].startswith(("_", "."))
    )
    if not skill_paths:
        _refuse(
            "ENTRYPOINT_INVENTORY_REFUSED",
            "inventory",
            "tracked skills are required",
        )
    package_names = {path.split("/")[2] for path in skill_paths}
    tracked_package_names = {
        path.split("/")[2]
        for path in inventory.paths
        if path.startswith(prefix + "skills/")
        and len(path.split("/")) >= 4
        and not path.split("/")[2].startswith(("_", "."))
    }
    missing_entrypoints = sorted(tracked_package_names - package_names)
    if missing_entrypoints:
        _refuse("TRACKED_ENTRYPOINT_MISSING", "inventory", repr(missing_entrypoints))
    skills = tuple(sorted((
        _skill_from_source(
            repo_root=repo_root,
            path=path,
            package_paths=tuple(
                item
                for item in inventory.paths
                if item.startswith(f"{prefix}skills/{path.split('/')[2]}/")
            ),
            tracked_paths=inventory.paths,
        )
        for path in skill_paths
    ), key=lambda item: item.skill_id))
    skills = _bind_executors(repo_root, skills)
    agents = tuple(sorted(
        (_agent_from_source(repo_root=repo_root, path=path) for path in agent_paths),
        key=lambda item: item.agent_id,
    ))
    try:
        return seal_capability_catalog(skills=skills, agents=agents)
    except CapabilityCatalogRefusal as error:
        raise CatalogCompileRefusal(error.code, error.locus, error.detail) from error


def render_operad_signature(catalog: CapabilityCatalogV1) -> bytes:
    identities = [
        {
            "skill_id": f"id_{colour.lower()}",
            "name": f"Identity {colour} Pass-Through",
            "arity": 1,
            "source_colours": [colour],
            "target_colour": colour,
            "equivariant": True,
            "agent_scope": ["all"],
            "residual_effect": "residual_unknown",
        }
        for colour in sorted(OPERAD_COLOURS_V1)
    ]
    operations: list[dict[str, object]] = []
    for skill in catalog.skills:
        operation: dict[str, object] = {
            "skill_id": skill.skill_id,
            "name": skill.name,
            "arity": skill.arity,
            "source_colours": list(skill.source_colours),
            "target_colour": skill.target_colour,
            "residual_effect": skill.residual_effect,
            "description": skill.description,
        }
        if skill.equivariant is not None:
            operation["equivariant"] = skill.equivariant
        if skill.agent_scope:
            operation["agent_scope"] = list(skill.agent_scope)
        operations.append(operation)
    payload = {
        "colours": COLOUR_DESCRIPTIONS,
        "identities": identities,
        "operations": operations,
    }
    return (json.dumps(payload, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def render_agent_slices(catalog: CapabilityCatalogV1) -> bytes:
    payload = {
        "agents": {
            agent.agent_id: {
                "sub_operad": list(agent.licensed_colour_ids),
                "licensed_skills": list(agent.licensed_skill_ids),
            }
            for agent in catalog.agents
        }
    }
    return (json.dumps(payload, indent=2, ensure_ascii=True) + "\n").encode("ascii")


def projection_bytes(catalog: CapabilityCatalogV1) -> dict[str, bytes]:
    return {
        CATALOG_FILENAME: encode_capability_catalog(catalog),
        SIGNATURE_FILENAME: render_operad_signature(catalog),
        SLICES_FILENAME: render_agent_slices(catalog),
    }


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_host_projections(repo_root: Path, catalog: CapabilityCatalogV1) -> None:
    projections = projection_bytes(catalog)
    written = False
    for host in HOST_NAMES:
        operad_root = repo_root / host / "operad"
        if operad_root.is_dir():
            for filename, payload in projections.items():
                _atomic_write(operad_root / filename, payload)
            written = True
    target_skill_operads = repo_root / ".agents" / "skill_operads"
    if target_skill_operads.is_dir():
        for filename, payload in projections.items():
            _atomic_write(target_skill_operads / filename, payload)
        written = True
    ops_operad = repo_root / "operads" / "skill_operad" / "json"
    if ops_operad.is_dir():
        for filename, payload in projections.items():
            _atomic_write(ops_operad / filename, payload)
        written = True
    if not written:
        _refuse("HOST_OPERAD_MISSING", "operad", "no operad projection directory found")


def verify_host_projections(repo_root: Path, catalog: CapabilityCatalogV1) -> None:
    expected = projection_bytes(catalog)
    verified = False
    for host in HOST_NAMES:
        operad_root = repo_root / host / "operad"
        if operad_root.is_dir():
            for filename, payload in expected.items():
                path = operad_root / filename
                if not path.is_file() or path.read_bytes() != payload:
                    _refuse(
                        "HOST_PROJECTION_DRIFT",
                        f"{host}/operad/{filename}",
                        "bytes differ from compiled projection",
                    )
            verified = True
    target_skill_operads = repo_root / ".agents" / "skill_operads"
    if target_skill_operads.is_dir():
        for filename, payload in expected.items():
            path = target_skill_operads / filename
            if not path.is_file() or path.read_bytes() != payload:
                _refuse(
                    "HOST_PROJECTION_DRIFT",
                    f".agents/skill_operads/{filename}",
                    "bytes differ from compiled projection",
                )
        verified = True
    ops_operad = repo_root / "operads" / "skill_operad" / "json"
    if ops_operad.is_dir():
        for filename, payload in expected.items():
            path = ops_operad / filename
            if not path.is_file() or path.read_bytes() != payload:
                _refuse(
                    "HOST_PROJECTION_DRIFT",
                    f"{ops_operad.relative_to(repo_root).as_posix()}/{filename}",
                    "bytes differ from compiled projection",
                )
        verified = True
    if not verified:
        _refuse("HOST_OPERAD_MISSING", "operad", "no operad projection directory found")
    decode_capability_catalog(expected[CATALOG_FILENAME])


def _main(argv: tuple[str, ...] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compile the tracked OEWAS capability catalog")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        catalog = compile_capability_catalog(args.repo_root.resolve())
        if args.write:
            write_host_projections(args.repo_root.resolve(), catalog)
        verify_host_projections(args.repo_root.resolve(), catalog)
    except (CatalogCompileRefusal, CapabilityCatalogRefusal) as error:
        print(str(error), file=sys.stderr)
        return 1
    print(f"skills={len(catalog.skills)}")
    print(f"agents={len(catalog.agents)}")
    print(f"catalog_digest={catalog.catalog_digest}")
    print("authority_effect=none")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "CATALOG_FILENAME",
    "HOST_NAMES",
    "SIGNATURE_FILENAME",
    "SLICES_FILENAME",
    "CatalogCompileRefusal",
    "TrackedEstateInventoryV1",
    "compile_capability_catalog",
    "git_tracked_estate_inventory",
    "projection_bytes",
    "render_agent_slices",
    "render_operad_signature",
    "verify_host_projections",
    "write_host_projections",
]
