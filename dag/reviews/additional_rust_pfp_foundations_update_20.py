import json
import pathlib

p = pathlib.Path(__file__).with_name('additional_rust_pfp_foundations_supplement.json')
d = json.loads(p.read_text(encoding='utf-8'))
v = {'id': 'RPF-V018', 'kind': 'exhaustive finite Unicode table data correspondence', 'details_file': 'additional_rust_pfp_foundations_unicode_validation.json', 'limits': 'All1112064 valid scalars; seven tables compared to admitted local CPython3.12 Unicode15 oracle. Separate from full source reading and not Rust or contextual string execution.'}
if not any(x['id'] == v['id'] for x in d['validation']):
    d['validation'].append(v)
c = {'id': 'RPF-C015', 'claim': 'Frozen Unicode tables agree with their admitted Python15 scalar oracle on the entire valid Unicode scalar carrier in this offline comparison.', 'evidence': [{'path': 'code/rust/core_types/src/python_alnum_v1.rs', 'lines': [1, 750]}, {'path': 'code/rust/core_types/src/python_case_v1.rs', 'lines': [1, 3562]}, {'path': 'code/rust/core_types/src/python_unicode_v1.rs', 'lines': [1, 2249]}, {'path': 'dag/reviews/additional_rust_pfp_foundations_unicode_validation.json'}], 'dependencies': ['Exact recorded source bytes', 'CPython3.12.12 Unicode15.0.0 scalar methods and exported internal case-ignorable predicate', 'Audited finite table parsing and exhaustive enumeration helper'], 'limitations': ['Data comparison is not a proof of the Unicode specification, semantic equivalence of identifiers or detector adequacy.', 'Surrogates are outside Rust char carrier; contextual final-sigma behavior and whole-string normalization are not covered.', 'Production structural certifiers check order/ranges only, not oracle correctness.']}
if not any(x['id'] == c['id'] for x in d['claims']):
    d['claims'].append(c)
p.write_text(json.dumps(d, indent=2) + '\n', encoding='utf-8')
