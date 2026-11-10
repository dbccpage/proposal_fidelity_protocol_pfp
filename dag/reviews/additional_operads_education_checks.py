"""Bounded checks on reviewed teaching contracts and their literal receipt snippet."""
import ast
from dataclasses import dataclass, FrozenInstanceError
import hashlib
import json
from pathlib import Path
import re
from typing import Mapping

import yaml

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_operads_education_remaining_scope.json').read_text())
pins = {r['path']: r['sha256'] for r in scope['files']}


def read(path):
    raw = (ROOT / path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == pins[path]
    return raw.decode('utf-8')


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key, value in node.value:
        key = loader.construct_object(key, deep=deep)
        assert key not in result
        result[key] = loader.construct_object(value, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
prefix = 'education/008_oeop/'
schema_path = prefix+'normal_forms/normal_form_contract_schema.yaml'
schema = yaml.load(read(schema_path), Loader=UniqueLoader)
schema_base = ROOT/'education/009_oeeis/normal_forms/normal_form_contract_schema.yaml'
assert (ROOT/schema_path).read_bytes() == schema_base.read_bytes()
assert pins[schema_path] == 'b7f991076733d9de27c6b5b772079929c0ed7566800a89f01740126cfcefa20a'
contracts = []
for path in sorted(p for p in pins if '/normal_forms/nf.' in p):
    data = yaml.load(read(path), Loader=UniqueLoader)
    missing = ['top.'+key for key in schema['required_top_level_sections'] if key not in data]
    invalid_enums = []
    for section, rules in schema['section_definitions'].items():
        for field in rules.get('required_fields', []):
            if field not in data.get(section, {}):
                missing.append(section+'.'+field)
        for field, rule in rules.get('field_types', {}).items():
            if isinstance(rule, dict) and 'enum' in rule and field in data.get(section, {}):
                value = data[section][field]
                if value not in rule['enum']:
                    invalid_enums.append({'field': section+'.'+field, 'actual': value, 'allowed': rule['enum']})
    assert set(data['terminal_routes']) == set(data['terminal_route_map'])
    assert set(data['terminal_route_map'].values()) <= set(schema['canonical_terminals']['enum'])
    contracts.append({'path': path, 'sha256': pins[path], 'identity': data['identity'],
                      'missing_required_fields': missing, 'invalid_declared_enums': invalid_enums,
                      'route_domains_and_targets_valid': True})
assert len(contracts) == 4

snippet_path = prefix+'multi_agent_swarm_orchestration_and_operad.md'
blocks = re.findall(r'```python\s*\n(.*?)\n```', read(snippet_path), re.S)
assert len(blocks) == 1
tree = ast.parse(blocks[0])
assert len(tree.body) == 1 and isinstance(tree.body[0], ast.ClassDef)
namespace = {'dataclass': dataclass, 'Mapping': Mapping}
exec(compile(tree, '<reviewed-teaching-receipt>', 'exec'), namespace)
Receipt = namespace['DeliberationReceipt']
verdicts = {}
receipt = Receipt('', '', (), (), verdicts, 'ACCEPT', (), '', '', authority_effect='EXECUTE')
assert receipt.participating_agents == () and receipt.receipt_sha256 == ''
verdicts['unreviewed-agent'] = 'ACCEPT'
assert receipt.verdicts == {'unreviewed-agent': 'ACCEPT'}
try:
    receipt.authority_effect = 'None'
except FrozenInstanceError:
    attribute_rebinding_blocked = True
else:
    raise AssertionError('frozen attribute positive control did not reject')

result = {
    'status': 'complete_offline_selected_controls',
    'schema_transfer': {'path': schema_path, 'sha256': pins[schema_path],
                        'fully_read_base': schema_base.relative_to(ROOT).as_posix(), 'exact_bytes': True},
    'contract_checks': contracts,
    'receipt_snippet_control': {'path': snippet_path, 'sha256': pins[snippet_path],
        'empty_participant_and_hash_accepted': True, 'explicit_authority_effect_accepted': receipt.authority_effect,
        'mapping_mutation_visible': dict(receipt.verdicts), 'frozen_attribute_rebinding_rejected': attribute_rebinding_blocked},
    'limits': ['Selected fields of a custom YAML meta-schema, not a complete domain/operad validator.',
               'Literal teaching dataclass only; no claim that a production receipt constructor has these gaps.',
               'No native or Lean execution, providers, source changes or private benchmark access.']
}
(REV/'additional_operads_education_checks.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'contracts': len(contracts), 'missing': [r['missing_required_fields'] for r in contracts],
                  'enum_violations': [{'path':r['path'],'errors':r['invalid_declared_enums']} for r in contracts if r['invalid_declared_enums']],
                  'receipt_control': result['receipt_snippet_control']}))
