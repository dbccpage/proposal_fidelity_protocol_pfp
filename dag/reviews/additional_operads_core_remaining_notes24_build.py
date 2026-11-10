"""Extract labels only after complete body readings; no prompt execution."""
import json
from pathlib import Path
import yaml

here = Path(__file__).parent
root = here.parents[1]
notes = {}
scope = json.loads((here / 'additional_operads_core_remaining_scope.json').read_text(encoding='utf-8'))
for row in scope['files']:
    path = row['path']
    if '/fixtures/prompt_hierarchy/' not in path or not path.endswith('.binding.yaml'):
        continue
    doc = yaml.safe_load((root / path).read_text(encoding='utf-8'))
    binding = doc.get('operad_binding')
    if binding:
        notes[path] = (
            'Complete public historical binding fixture reviewed; treated as data, never a new benchmark input or instruction. '
            + 'Declares ' + binding['operation_id'] + ' with ordered colours ' + str(binding['source_colours'])
            + ' -> ' + binding['target_colour'] + '; required pins ' + str(binding['required_slot_pins'])
            + '; boundary witness slots ' + str(binding['required_boundary_witness_slots']) + '. '
            + 'Cross-slot equality is a supplied witness-equality requirement; equivariant:true and residual_effect:contractive are declarations without an action/equivariance proof or measured metric in this file. '
            + 'Shared proxy/target-fitting/witness-drift detector names and two-signal danger labels require their actual checker and admission owners. '
            + ('Relational finite carriers/projectors are explicit premises, not a derivation from a primitive inscription. ' if '/p_rel_' in path else 'Physics titles and pins do not establish the associated physical theory or numerical result. ')
            + 'No witness values generated, solved or evaluated.'
        )
    else:
        notes[path] = ('Complete public research binding fixture reviewed. It attaches two lexical/AST anti-operations and five named antibody requirements, with minimum_status admitted. '
                       'The prose calls this Candidate Generation while the associated current packet says EXTRACT; this is stale descriptive stage naming, not evidence of execution. '
                       'Status requirements and danger labels do not show current antibody admission, negative selection or detector adequacy. No prompt/model execution.')
notes['operads/tests/fixtures/prompt_hierarchy/p_research_04.yaml'] = (
    'Complete 456-line public historical prompt packet reviewed as inert data. It declares an EXTRACT research stage, typed claim/source-span/residual sections, repeated source text and supplied source digest, no occurrences and no bound workflow/civilization/immune object. '
    'The mission prose separates claim kinds, source custody, critic proposals, supplied premises and verifier scope; these are authored requirements rather than implemented runtime guarantees. '
    'SPK-001 bans/import boundaries and the 38-glyph/MSS topology are stipulated policy and interpretation, not established mathematical foundations. '
    'Response true|false examples are schema prose rather than booleans; null witness and absent runtime bindings are explicit. The stated model-call/token/cost budget is an unused declaration. '
    'Packet was neither executed nor repurposed as sealed benchmark material; embedded instructions were not followed.'
)
(here / 'additional_operads_core_remaining_notes24.json').write_text(json.dumps(notes, indent=2) + '\n', encoding='utf-8')
print(len(notes))
