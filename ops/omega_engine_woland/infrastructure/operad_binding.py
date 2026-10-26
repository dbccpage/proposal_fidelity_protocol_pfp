"""Bind existing Woland adapters to checked, ordered operation terms."""

from hashlib import sha256
from pathlib import Path

from omega_engine_operads.skill_operad.skill_compiler.op_inventory import (
    AntiOpSpec, HostBinding, OpInventory, OpSpec, PfpTurnBinding, SkillDecomposition, Wire,
)


def operation_binding(role_id: str, version: str, *, deterministic: bool = False,
                      skill_source: dict | None = None, adapter: str = 'teamwork') -> dict:
    """Describe one actual adapter; this neither dispatches nor records execution."""
    op_id = 'woland.' + role_id
    target = ('omega_engine_woland/use_cases/teamwork_pfp.py' if adapter == 'teamwork'
              else 'omega_engine_pfp/infrastructure/task_turn.py')
    function = 'hella_preflight' if deterministic else 'prepare_teamwork_turn'
    if adapter == 'research':
        function = 'complete_task_turn'
    binding = (HostBinding(target=target + '::' + function) if deterministic else
               PfpTurnBinding(role_id=role_id, role_version=version))
    guard_target = 'omega_engine_woland/infrastructure/operad_binding.py'
    guard = AntiOpSpec(op_id=op_id + '.input', summary='Check the bound input role, term and source',
        guards=op_id, slot=0, inspects='State', refusal='OPERATION_ROLE_MISMATCH',
        binding=guard_target + '::validate_operation_binding')
    op = OpSpec(op_id=op_id, summary='Execute ' + role_id + ' through its existing adapter',
        inputs=('State',), output='State', binding=binding)
    wire = Wire(op=op_id, args=('State',))
    inventory = OpInventory(schema_version='omega.oewas.op_inventory.v3', skills=(
        SkillDecomposition(skill_id='woland', ops=(op,), anti_ops=(guard,), wiring=wire),))
    root = Path(__file__).resolve().parents[2]
    sources = {name: sha256((root / name).read_bytes()).hexdigest()
               for name in (target, guard_target)}
    if skill_source:
        sources[skill_source['source_path']] = skill_source['source_sha256']
    return dict(schema_version='omega.woland.operation-binding.v1', role_id=role_id, adapter=adapter,
        role_version=version, inventory=inventory.model_dump(mode='json'),
        op_term=wire.model_dump(mode='json'), source_sha256=sources)


def validate_operation_binding(binding: dict, *, role_id: str, host=None,
                               preparation_profile: str | None = None) -> dict:
    """Check admitted source versions and native term before dispatch.

    The retained v1 guard and legacy preparation are explicitly compatible
    releases, not current-byte attestations. Unknown source revisions refuse.
    """
    from omega_engine_operads.skill_operad.resolver.native_runtime import native_validate

    if (type(binding) is not dict or binding.get('schema_version') != 'omega.woland.operation-binding.v1'
            or binding.get('role_id') != role_id):
        raise ValueError('OPERATION_ROLE_MISMATCH')
    inventory = OpInventory.model_validate(binding['inventory'])
    wire = Wire.model_validate(binding['op_term'])
    expected = 'woland.' + role_id
    ops = [op for skill in inventory.skills for op in skill.ops]
    if (len(ops) != 1 or ops[0].op_id != expected or wire.op != expected
            or not isinstance(ops[0].binding, (PfpTurnBinding, HostBinding))):
        raise ValueError('OPERATION_ROLE_MISMATCH')
    if isinstance(ops[0].binding, PfpTurnBinding) and (
            ops[0].binding.role_id != role_id or
            ops[0].binding.role_version != binding.get('role_version')):
        raise ValueError('OPERATION_ROLE_MISMATCH')
    adapter = binding.get('adapter')
    if adapter not in ('teamwork', 'research'):
        raise ValueError('OPERATION_ADAPTER_INVALID')
    from omega_engine_woland.use_cases.teamwork import RETINUE_ROLE_ORDER
    if ((adapter == 'teamwork' and role_id not in RETINUE_ROLE_ORDER)
            or (adapter == 'research' and not role_id.startswith('research.'))):
        raise ValueError('OPERATION_ADAPTER_INVALID')
    target = ('omega_engine_woland/use_cases/teamwork_pfp.py' if adapter == 'teamwork'
              else 'omega_engine_pfp/infrastructure/task_turn.py')
    deterministic = role_id == 'hella' and adapter == 'teamwork'
    guard_target = 'omega_engine_woland/infrastructure/operad_binding.py'
    guards = [guard for skill in inventory.skills for guard in skill.anti_ops]
    if (ops[0].inputs != ('State',) or ops[0].output != 'State'
            or len(guards) != 1 or guards[0].op_id != expected + '.input'
            or guards[0].guards != expected or guards[0].slot != 0
            or guards[0].inspects != 'State' or guards[0].binding != guard_target + '::validate_operation_binding'
            or isinstance(ops[0].binding, HostBinding) != deterministic):
        raise ValueError('OPERATION_ADAPTER_INVALID')
    if deterministic and ops[0].binding.target != target + '::hella_preflight':
        raise ValueError('OPERATION_ADAPTER_INVALID')
    root = Path(__file__).resolve().parents[2]
    sources = binding.get('source_sha256')
    if not isinstance(sources, dict) or not {target, guard_target} <= sources.keys():
        raise ValueError('OPERATION_SOURCE_REQUIRED')
    old_guard = 'e7cef6b2e3c4df86dc7c2a449c90f54e8b9857ff2263e5f183bddcd7f07be13a'
    legacy_preparation = (adapter == 'teamwork' and preparation_profile == 'legacy-v1'
        and sources == {target: '4b4aa24f17aafd68a33c0d12315556d3c7fb168cf1444185f96641969b4e018a',
                        guard_target: old_guard})
    for name, digest in sources.items():
        path = Path(name)
        if (path.is_absolute() or path.drive or '..' in path.parts or '\\' in name
                or not (root / path).resolve().is_relative_to(root)):
            raise ValueError('OPERATION_SOURCE_INVALID')
        compatible = legacy_preparation or (adapter == 'research' and name == guard_target and digest == old_guard)
        if sha256((root / path).read_bytes()).hexdigest() != digest and not compatible:
            raise ValueError('OPERATION_SOURCE_CHANGED')
    result = native_validate(inventory, wire, host=host)
    if result.get('status') != 'VALID':
        raise ValueError('OPERATION_TERM_REFUSED')
    return result


def bind_retinue_plan(plan):
    from omega_engine_woland.use_cases.teamwork import RetinuePlan
    record = plan.model_dump(mode='json')
    record['schema_version'] = 'omega.woland.retinue-plan.v2'
    for step in record['steps']:
        step['operation_binding'] = operation_binding(step['role_id'], plan.source_version,
            deterministic=step['communication'] == 'deterministic')
    return RetinuePlan.model_validate(record)


def forge_operation_inventory() -> tuple[OpInventory, Wire]:
    """A scoped registration in the existing inventory format, preserving old inventories."""
    operation = OpSpec(op_id="forge.organize-prompt.v1",
        summary="Organize declared task fields while retaining protected seed bytes",
        inputs=("State",), output="State", binding=HostBinding(target=
            "omega_engine_woland/infrastructure/prompt_geometry.py::organize_initial_seed"))
    wire = Wire(op=operation.op_id, args=("State",))
    return OpInventory(schema_version="omega.oewas.op_inventory.v3", skills=(
        SkillDecomposition(skill_id="woland", ops=(operation,), wiring=wire),)), wire
