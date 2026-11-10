"""Offline checks of published teaching contracts; no runtime or provider execution."""
import hashlib
import json
from pathlib import Path
import re

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parents[2]
REV = ROOT / 'dag/reviews'
scope = json.loads((REV / 'additional_eis_pciv_education_remaining_scope.json').read_text())
pins = {r['path']: r['sha256'] for r in scope['files']}


class UniqueSafeLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    loader.flatten_mapping(node)
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError('duplicate YAML key: ' + str(key))
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueSafeLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def read(path):
    data = (ROOT / path).read_bytes()
    assert hashlib.sha256(data).hexdigest() == pins[path]
    return data.decode('utf-8')


def norm_paths(prefix):
    return sorted(p for p in pins if p.startswith(prefix + '/normal_forms/') and p.endswith('.yaml'))


contract_rows = []
schema_pins = []
for prefix in ('education/009_oeeis', 'education/010_oepciv'):
    schema_path = prefix + '/normal_forms/normal_form_contract_schema.yaml'
    schema = yaml.load(read(schema_path), Loader=UniqueSafeLoader)
    schema_pins.append({'path': schema_path, 'sha256': pins[schema_path]})
    for path in norm_paths(prefix):
        if path == schema_path:
            continue
        data = yaml.load(read(path), Loader=UniqueSafeLoader)
        missing = ['top.' + key for key in schema['required_top_level_sections'] if key not in data]
        for section, rules in schema['section_definitions'].items():
            for key in rules.get('required_fields', []):
                if section not in data or key not in data[section]:
                    missing.append(section + '.' + key)
        routes = data['terminal_routes']
        mapping = data['terminal_route_map']
        route_domain_match = set(routes) == set(mapping)
        canonical_targets = set(mapping.values()) <= set(schema['canonical_terminals']['enum'])
        contract_rows.append({'path': path, 'sha256': pins[path], 'identity': data['identity'],
                              'missing_required_fields': missing, 'route_domain_match': route_domain_match,
                              'all_route_targets_canonical': canonical_targets,
                              'limits': 'Selected structural requirements from the adjacent custom meta-schema; no domain predicate or verifier invoked.'})
assert len(contract_rows) == 10
assert sum(bool(r['missing_required_fields']) for r in contract_rows) == 6
assert all(r['route_domain_match'] and r['all_route_targets_canonical'] for r in contract_rows)


def embedded_schema(name):
    path = 'education/010_oepciv/normal_forms/' + name
    blocks = re.findall(r'```json\s*\n(.*?)\n```', read(path), flags=re.S)
    assert len(blocks) == 1
    data = json.loads(blocks[0])
    jsonschema.Draft202012Validator.check_schema(data)
    return path, data


stamp = '2026-11-10T00:00:00Z'
society = {'society_id': 'sha256:' + '0' * 64, 'domain_protocol': 'synthetic-control', 'family_ids': ['family-A'],
           'aggregate_fitness_vector': {'accuracy_rational': '1/1', 'cost_rational': '100/1', 'robustness_rational': '1/1'},
           'migration_policy': {'max_incoming_per_epoch': 100, 'taxonomic_admissibility': []}, 'created_utc': stamp}
mutation = {'receipt_id': 'sha256:' + '0' * 64, 'parent_genome_id': 'sha256:' + '1' * 64,
            'child_genome_id': 'sha256:' + '1' * 64, 'falsification_witness_sha256': '2' * 64,
            'cochain_residual': {'phi1': 'not a rational', 'gamma2': 'arbitrary', 'xi': 'arbitrary'},
            'antibody_id': 'synthetic', 'hop_distance': 3, 'attenuation_weight': '1/1', 'created_utc': stamp}
headstone = {'casualty_id': 'no-required-prefix', 'failure_mode': 'TEST_ASSERTION_FAILURE',
             'witness_summary': '', 'candidate_sha256': '3' * 64, 'interred_at_utc': stamp}
schema_controls = []
for name, sample, limits in [
    ('nf_01_prompt_society_and_civilization.md', society,
     'The schema has three named objective coordinates rather than four, and accepts a100-entry migration quota for one family. It does not certify global budget conservation or optimal routing.'),
    ('nf_02_lamarckian_pfp_adversary_loop.md', mutation,
     'The schema accepts arbitrary residual strings and weight1 at hop3 instead of1/8. Its shape check does not enforce the stated attenuation law, core preservation or authentic witness binding.'),
    ('nf_03_run_u_cemetery_and_antibody_gate.md', headstone,
     'The schema accepts an ID without the described headstone: prefix and an empty witness summary. This is a schema limitation, not a runtime gate bypass.')]:
    path, schema = embedded_schema(name)
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    errors = list(validator.iter_errors(sample))
    assert not errors, errors
    schema_controls.append({'path': path, 'sha256': pins[path], 'schema_valid_control': sample,
                            'validation_errors': [], 'conclusion': limits})

# Without homomorphism assumptions, agreement on generators does not extend.
carrier = tuple(range(4))
u = dict(zip(carrier, carrier))
r = {0: 0, 1: 1, 2: 3, 3: 3}
assert r[u[0]] == 0 and r[u[1]] == 1 and r[u[2]] != 2
# Even a full set-theoretic retraction need not preserve an admitted algebraic law.
u2 = {x: (x + 1) % 4 for x in carrier}
r2 = {x: (x - 1) % 4 for x in carrier}
assert all(r2[u2[x]] == x for x in carrier)
assert u2[(0 + 0) % 4] != (u2[0] + u2[0]) % 4

result = {'status': 'complete_bounded_document_contract_controls', 'source_schemas': schema_pins,
          'contract_checks': contract_rows, 'schema_controls': schema_controls,
          'retraction_controls': {'base_carrier': 'Z/4Z, additive generator1',
              'generator_check_counterexample': {'u': u, 'r': r, 'checks0and1': 'pass', 'at2': 'fails'},
              'relations_counterexample': {'u': u2, 'r': r2, 'roundtrip_all4': 'pass', 'addition_at_0_0': 'not_preserved'},
              'conclusion': 'A generator test needs homomorphism/extension assumptions; a set retraction alone does not preserve additional relations.'},
          'limits': ['Checks apply to published contract/schema language; no PCIV/EIS runtime failure is asserted from schema permissiveness alone.',
                     'No provider, historical execution, original source edit, native/Lean build, external reference or private benchmark access.']}
(REV / 'additional_eis_pciv_education_normal_form_checks.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'contracts_checked': len(contract_rows), 'missing_field_paths': [r['path'] for r in contract_rows if r['missing_required_fields']],
                  'schema_controls': len(schema_controls), 'exact_retraction_controls': 2}))
