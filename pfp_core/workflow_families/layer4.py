"""Layer 4 families: dialects, staged packets, crosswalks, witnesses, rewriting, custody, checkers, presets."""
from __future__ import annotations

from typing import Any

from .base import (
    HostedFamily,
    spec_from,
)
from .exact import (
    commitment,
    seal_chain,
    sha256_bytes,
)
from .registry import register

# ---------------------------------------------------------------- WF6

@register
class DialectSweep(HostedFamily):
    """WF6. Pose each seed item in k query-preserving dialects and grade every reply with one checker.

    Items are linear systems ``A x = b``. A dialect permutes and scales rows and renames variables.
    The host checks that each dialect keeps the rank-test status and the decoded solution before
    anything is dispatched, then grades each reply as WF7 does and reports acceptance per dialect,
    item by item. A dialect that changes the query or an incomplete sweep is refused.
    """
    spec = spec_from('WF6', 'Dialect sweep', 4, ['WF5'], 'Sweep', 'dialect_query_preservation_sweep',
                     'wf06_dialect_sweep')

    def fixtures(self):
        items = [{'id': 'i1', 'A': [[1, 2], [3, 4]], 'b': [5, 6]}, {'id': 'i2', 'A': [[1, 1], [2, 2]], 'b': [1, 3]}]
        plain = {'name': 'plain'}
        swapped = {'name': 'swapped', 'row_perm': [1, 0], 'col_perm': [1, 0], 'row_scale': [3, '-1/2']}
        st = 'Solve A x = b exactly or refuse with a code.'
        task = {'statement': st, 'items': items, 'dialects': [plain, swapped]}
        refuse = {'refusal': 'UNRESOLVED_INCONSISTENT'}
        good = [{'answer': [-4, '9/2']}, {'answer': ['9/2', -4]}, refuse, refuse]
        undecoded = [good[0], {'answer': [-4, '9/2']}, refuse, refuse]
        zero = {'name': 'zero_row', 'row_scale': [0, 1]}
        shifted = {'name': 'shifted', 'b_shift': [1, 0]}
        return {
            'all_dialects_accepted': ({'task': task, 'replies': good}, 'HOST_CERTIFIED'),
            'one_dialect_fails_item_by_item': ({'task': task, 'replies': undecoded}, 'HOST_CERTIFIED'),
            'dialect_zeroes_a_row': ({'task': {**task, 'dialects': [plain, zero]}, 'replies': good}, 'REFUSED'),
            'dialect_shifts_rhs': ({'task': {**task, 'dialects': [plain, shifted]}, 'replies': good}, 'REFUSED'),
            'incomplete_sweep': ({'task': task, 'replies': good[:3]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF8

def build_packets(seed: Any, stages: list[str], payloads: list[Any], carry: str) -> list[dict[str, Any]]:
    """Honest packets for ``payloads``, as a fixture: each carries the fenced text and links into the seal chain."""
    chain = seal_chain(seed, payloads)
    return [{'stage': s, 'carry': carry, 'payload': p, 'prev': chain[i], 'seal': chain[i + 1]}
            for i, (s, p) in enumerate(zip(stages, payloads, strict=True))]


@register
class StagedSealedPackets(HostedFamily):
    """WF8. Run a task as declared stages; seal each stage packet before the next stage reads it.

    The Rust host checks the packets: the fenced question byte for byte, the hash chain over the task
    seed, and each stage recomputed from the task. Instance: eliminate, solve, residual for ``A x = b``.
    """
    spec = spec_from('WF8', 'Staged sealed packets', 4, ['WF2', 'WF5'], None, 'stage_seal_chain_recompute',
                     'wf08_staged_sealed_packets')

    def fixtures(self):
        q = '<<Q>>Solve A x = b for x with A = [[2, 1], [1, 3]], b = [3, 5].<</Q>>'
        task = {'statement': q + ' Work in three sealed stages.', 'A': [[2, 1], [1, 3]], 'b': [3, 5]}
        names = ['eliminate', 'solve', 'residual']
        payloads = [[[1, 0, '4/5'], [0, 1, '7/5']], ['4/5', '7/5'], [0, 0]]
        honest = build_packets(task, names, payloads, q)
        edited = [honest[0], {**honest[1], 'payload': ['1', '1/3']}, honest[2]]
        broken = [honest[0], {**honest[1], 'prev': honest[0]['prev']}, honest[2]]
        no_fence = [honest[0], {**honest[1], 'carry': 'Solve A x = b.'}, honest[2]]
        wrong = build_packets(task, names, [payloads[0], ['1', '1/3'], [0, 0]], q)
        return {
            'three_sealed_stages': ({'task': task, 'replies': honest}, 'HOST_CERTIFIED'),
            'packet_edited_after_seal': ({'task': task, 'replies': edited}, 'REFUSED'),
            'chain_link_broken': ({'task': task, 'replies': broken}, 'REFUSED'),
            'fence_dropped_from_packet': ({'task': task, 'replies': no_fence}, 'REFUSED'),
            'sealed_but_wrong_stage': ({'task': task, 'replies': wrong}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF16

@register
class SubstrateCrosswalk(HostedFamily):
    """WF16. Map one finite task between two substrates and require the same host verdict in both.

    Source: an edge cochain ``c`` on an oriented graph (exact iff every fundamental cycle sum is 0).
    Target: a signed incidence matrix ``D`` and vector ``y`` (exact iff ``rank D = rank [D|y]``).
    A crosswalk maps vertices to columns and edges to signed rows; the host checks it is bijective,
    preserves every incidence relation and transports ``c`` to ``y``, and records where valid
    crosswalks differ (non-unique choices). A broken relation or a verdict mismatch is refused.
    """
    spec = spec_from('WF16', 'Substrate crosswalk', 4, ['WF5', 'WF10'], 'WF5', 'incidence_rank_crosswalk',
                     'wf16_substrate_crosswalk')

    def fixtures(self):
        task = {'statement': 'Map the graph cochain onto the incidence matrix: vertex -> column, edge -> [row, sign].',
                'edges': [['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'a']], 'c': [1, -1, 1, -1],
                'D': [[0, -1, 0, 1], [1, 0, -1, 0], [0, -1, 1, 0], [1, 0, 0, -1]], 'y': [-1, 1, -1, 1]}
        f1 = {'vertex_col': {'a': 2, 'b': 0, 'c': 3, 'd': 1}, 'edge_row': {'0': [1, 1], '1': [3, -1], '2': [0, -1],
                                                                          '3': [2, 1]}}
        f2 = {'vertex_col': {'a': 3, 'b': 1, 'c': 2, 'd': 0}, 'edge_row': {'0': [0, -1], '1': [2, 1], '2': [1, 1],
                                                                          '3': [3, -1]}}
        bad_sign = {**f1, 'edge_row': {**f1['edge_row'], '2': [0, 1]}}
        clash = {**f1, 'vertex_col': {**f1['vertex_col'], 'd': 2}}
        return {
            'one_crosswalk_preserves': ({'task': task, 'replies': [{'crosswalks': [f1]}]}, 'HOST_CERTIFIED'),
            'two_crosswalks_non_unique': ({'task': task, 'replies': [{'crosswalks': [f1, f2]}]}, 'HOST_CERTIFIED'),
            'orientation_sign_dropped': ({'task': task, 'replies': [{'crosswalks': [bad_sign]}]}, 'REFUSED'),
            'two_vertices_one_column': ({'task': task, 'replies': [{'crosswalks': [clash]}]}, 'REFUSED'),
            'target_data_not_transported': ({'task': {**task, 'y': [-1, 1, -1, 3]},
                                             'replies': [{'crosswalks': [f1]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF17

@register
class WitnessedDifferenceProgramme(HostedFamily):
    """WF17. Every claimed difference needs a separating formula; every equivalence needs a bisimulation.

    Instance: a finite labelled transition system (a.(b+c) versus a.b+a.c, and a.b versus a.b+a.b).
    A difference claim is accepted only if a Hennessy-Milner formula holds on one state and fails on
    the other; an equivalence only if the given relation contains the pair and is a bisimulation.
    Unwitnessed claims, non-separating formulas and false bisimulations are refused.
    """
    spec = spec_from('WF17', 'Witnessed-difference programme', 4, ['WF10', 'WF11'], 'WF10',
                     'hml_separator_bisimulation_check', 'wf17_witnessed_difference_programme')

    def fixtures(self):
        tr = [['p0', 'a', 'p1'], ['p1', 'b', 'p2'], ['p1', 'c', 'p3'],
              ['q0', 'a', 'q1'], ['q0', 'a', 'q2'], ['q1', 'b', 'q3'], ['q2', 'c', 'q4'],
              ['r0', 'a', 'r1'], ['r1', 'b', 'r2'],
              ['s0', 'a', 's1'], ['s0', 'a', 's2'], ['s1', 'b', 's3'], ['s2', 'b', 's4']]
        task = {'statement': 'Claim differences with a separating formula and equivalences with a bisimulation.',
                'transitions': tr}
        diff = {'kind': 'difference', 'left': 'p0', 'right': 'q0',
                'witness': ['dia', 'a', ['and', ['dia', 'b', 'tt'], ['dia', 'c', 'tt']]]}
        equiv = {'kind': 'equivalence', 'left': 'r0', 'right': 's0',
                 'certificate': [['r0', 's0'], ['r1', 's1'], ['r1', 's2'], ['r2', 's3'], ['r2', 's4']]}
        weak = {**diff, 'witness': ['dia', 'a', ['dia', 'b', 'tt']]}
        fake = {'kind': 'equivalence', 'left': 'p0', 'right': 'q0',
                'certificate': [['p0', 'q0'], ['p1', 'q1'], ['p1', 'q2'], ['p2', 'q3'], ['p3', 'q4']]}
        bare = {'kind': 'difference', 'left': 'p0', 'right': 'q0'}
        return {
            'difference_and_equivalence_witnessed': ({'task': task, 'replies': [{'claims': [diff, equiv]}]},
                                                     'HOST_CERTIFIED'),
            'unwitnessed_difference': ({'task': task, 'replies': [{'claims': [bare, equiv]}]}, 'REFUSED'),
            'formula_does_not_separate': ({'task': task, 'replies': [{'claims': [weak]}]}, 'REFUSED'),
            'trace_equivalent_is_not_bisimilar': ({'task': task, 'replies': [{'claims': [fake]}]}, 'REFUSED'),
            'claims_name_undeclared_states': ({'task': task, 'replies': [{'claims': [
                {**diff, 'right': 'no_such_state'},
                {'kind': 'equivalence', 'left': 'ghost1', 'right': 'ghost2', 'certificate': [['ghost1', 'ghost2']]},
            ]}]}, 'REFUSED'),
        }


# ---------------------------------------------------------------- WF21

@register
class StructuralPromptRewriting(HostedFamily):
    """WF21. Rewrite a prompt only outside its protected fences, then solve the rewritten prompt.

    The Rust host checks the rule applications (exact, disjoint, outside the question and output
    fences), that each fence survives once, that no answer-key literal leaks, and the answer exactly.
    """
    spec = spec_from('WF21', 'Structural prompt rewriting', 4, ['WF5'], 'WF5', 'fenced_rewrite_exact_judge',
                     'wf21_structural_prompt_rewriting')

    def fixtures(self):
        st = ('Please read the task.\n<<Q>>Compute det(M) for M = [[12, 5], [7, 263]].<</Q>>\n'
              '<<OUT>>Reply as {"answer": <int>}.<</OUT>>\nPlease be concise.')
        task = {'statement': st, 'matrix': [[12, 5], [7, 263]]}
        sealed = {'answer_key': 3121}
        tail = st.index('Please be concise.')
        clean = {'edits': [{'lhs': 'Please read the task.', 'rhs': 'Read the task below.', 'at': 0},
                           {'lhs': 'Please be concise.', 'rhs': 'Keep the reply short.', 'at': tail}]}
        inside = {'edits': [{'lhs': '263', 'rhs': '264', 'at': st.index('263')}]}
        leak = {'edits': [{'lhs': 'Please be concise.', 'rhs': 'Hint: it is 3121.', 'at': tail}]}
        overlap = {'edits': [{'lhs': 'Please', 'rhs': 'Kindly', 'at': 0},
                             {'lhs': 'Please read', 'rhs': 'Read', 'at': 0}]}
        dup = {'edits': [{'lhs': 'Please be concise.', 'rhs': st[st.index('<<Q>>'):st.index('<</Q>>') + 6],
                          'at': tail}]}
        ok = {'answer': 3121}

        def case(rewrite):
            return {'task': task, 'sealed': sealed, 'replies': [rewrite, ok]}
        return {
            'rewrite_outside_fences_solved': (case(clean), 'HOST_CERTIFIED'),
            'edit_inside_question_fence': (case(inside), 'REFUSED'),
            'rewrite_leaks_answer_key': (case(leak), 'REFUSED'),
            'overlapping_matches': (case(overlap), 'REFUSED'),
            'question_duplicated_outside_fence': (case(dup), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF23

def canonical_file(text: str) -> bytes:
    """File bytes as hashed by custody: UTF-8, LF line endings."""
    return text.replace('\r\n', '\n').encode('utf-8')


@register
class JudgePacketCustodyAudit(HostedFamily):
    """WF23. Audit a judge run: file hashes, answer-free participant bytes, sealed checker, stdout tags.

    The Rust host hashes every canonicalised file against the host-held manifest in ``sealed``, scans
    participant bytes and their trivial decodings for the sealed expected answer, checks the executed
    checker hash against the recorded hash of the sealed checker source, and checks every stdout line's
    keyed tag. A manifest in the reply is ignored.
    """
    spec = spec_from('WF23', 'Judge-packet custody audit', 4, ['WF11'], None, 'judge_packet_custody_audit',
                     'wf23_judge_packet_custody_audit')

    def fixtures(self):
        task = {'statement': 'Submit the participant packet and the judge run record.'}
        src = 'def check(answer):\r\n    return answer == det([[12, 5], [7, 263]])\r\n'
        key = 'stdout-key-wf23'
        sealed = {'expected_answer': 3121, 'checker_source': src,
                  'recorded_checker_sha256': sha256_bytes(canonical_file(src)), 'stdout_key': key}
        files = {'task.txt': 'Compute det(M) for M = [[12, 5], [7, 263]].', 'format.txt': 'Reply with one integer.'}
        line = 'ITEM det2 PASS'
        run = {'executed_checker_sha256': sealed['recorded_checker_sha256'],
               'stdout': [{'line': line, 'tag': commitment(key, line)}]}
        good = {'participant': files, 'run': run}

        def manifest(fs):
            return {n: sha256_bytes(canonical_file(t)) for n, t in fs.items()}

        def with_file(text):
            return {'participant': {**files, 'notes.txt': text}, 'run': run}
        forged = {**good, 'run': {**run, 'stdout': [*run['stdout'], {'line': 'ITEM det3 PASS', 'tag': '0' * 64}]}}
        stale = {**good, 'run': {**run, 'executed_checker_sha256': sha256_bytes(b'def check(answer): return True')}}
        edited = {**good, 'participant': {**files, 'format.txt': 'Reply with one integer or a guess.'}}
        self_hashed = {**edited, 'manifest': manifest(edited['participant'])}

        def case(sub):
            # the host recorded the manifest when the packet was built; the leaky notes were recorded honestly
            return {'task': task, 'sealed': {**sealed, 'manifest': manifest({**files, **{
                n: t for n, t in sub['participant'].items() if n == 'notes.txt'}})}, 'replies': [sub]}
        return {
            'clean_custody': (case(good), 'HOST_CERTIFIED'),
            'answer_in_participant_bytes': (case(with_file('Hint: the answer is 3121.')), 'REFUSED'),
            'answer_base64_encoded': (case(with_file('cache: MzEyMQ==')), 'REFUSED'),
            'forged_stdout_line': (case(forged), 'REFUSED'),
            'stale_checker_executed': (case(stale), 'REFUSED'),
            'file_edited_after_manifest': (case(edited), 'REFUSED'),
            'edited_file_with_self_computed_manifest': (case(self_hashed), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF29

@register
class CheckerSynthesisMutationKill(HostedFamily):
    """WF29. Score a proposed checker by its mutation kill rate, after it passes every valid case.

    The declared certificate is a vertex potential ``phi`` with ``delta phi = c`` on a fixed graph. The
    checker is a tree over declared predicates (never model code). The host runs it on the public
    valid panel and the sealed hostile mutants, and certifies only a sound checker (zero false
    rejections) whose kill rate meets the declared bar.
    """
    spec = spec_from('WF29', 'Checker synthesis scored by mutation kill rate', 4, ['WF11'], 'WF11',
                     'mutation_kill_rate_with_valid_panel', 'wf29_checker_synthesis_scored_by_mutation_kill_rate')

    def fixtures(self):
        phi = {'a': 0, 'b': 1, 'c': 3, 'd': 7}
        task = {'statement': 'Write a checker for "phi is a potential of c" from the declared predicates.',
                'edges': [['a', 'b'], ['b', 'c'], ['c', 'a'], ['c', 'd']], 'min_kill_rate': '4/5',
                'predicates': ['c_length_matches', 'coboundary_matches', 'cycle_sums_zero', 'phi_covers_vertices',
                               'phi_root_zero'],
                'valid': [{'c': [1, 2, -3, 4], 'phi': phi},
                          {'c': [1, 2, -3, 4], 'phi': {k: v + 5 for k, v in phi.items()}},
                          {'c': [0, -2, 2, -1], 'phi': {'a': 2, 'b': 2, 'c': 0, 'd': -1}}]}
        mutants = [{'c': [1, 2, -3, 4], 'phi': {**phi, 'b': 2}}, {'c': [1, 2, -2, 4], 'phi': phi},
                   {'c': [1, 2, -3, 4], 'phi': {'a': 0, 'b': 1, 'c': 3}}, {'c': [1, 2, -3, 4, 0], 'phi': phi},
                   {'c': [1, 2, -3, 4], 'phi': {'a': 0, 'b': 0, 'c': 0, 'd': 0}}]

        def case(checker):
            return {'task': task, 'sealed': {'mutants': mutants}, 'replies': [{'checker': checker}]}
        return {
            'sound_checker_kills_all': (case(['and', 'c_length_matches', 'phi_covers_vertices',
                                              'coboundary_matches']), 'HOST_CERTIFIED'),
            'root_gauge_falsely_rejects': (case(['and', 'phi_root_zero', 'coboundary_matches']), 'REFUSED'),
            'cycle_only_checker_too_weak': (case('cycle_sums_zero'), 'REFUSED'),
            'model_code_not_executed': (case('lambda case: True'), 'REFUSED'),
        }


# ---------------------------------------------------------------- WF44

@register
class ExactCertificatePresets(HostedFamily):
    """WF44. Check a certificate against a registered exact schema; type-check before evaluating.

    Presets: a coboundary potential (``delta phi = c``), an l1 primal-dual pair (residual
    ``r = w + B f``, circulation ``z`` with ``B^T z = 0`` and ``|z_e| <= cap_e``, and
    ``w . z = sum cap_e |r_e|``), and a solution in canonical rational form. A certificate with a
    float, a wrong shape or the wrong schema is refused before any equation is evaluated.
    """
    spec = spec_from('WF44', 'Exact certificate presets', 4, ['WF11', 'WF10'], 'WF11', 'exact_certificate_presets',
                     'wf44_exact_certificate_presets')

    def fixtures(self):
        square = [['a', 'b'], ['b', 'c'], ['c', 'd'], ['d', 'a'], ['a', 'c']]
        cob = {'schema': 'coboundary_potential', 'statement': 'Certify that c is exact with a potential.',
               'edges': [['a', 'b'], ['b', 'c'], ['c', 'a']], 'c': [1, 2, -3]}
        l1 = {'schema': 'l1_dual_circulation', 'statement': 'Certify the l1 distance of w to the coboundaries.',
              'edges': square, 'w': [2, 0, 0, 0, 1]}
        rat = {'schema': 'canonical_rational', 'statement': 'Solve A x = b in canonical rational form.',
               'A': [[2, 1], [1, 3]], 'b': [3, 5]}
        dual = {'f': {'a': 0, 'b': -1, 'c': -1, 'd': 0}, 'r': [1, 0, 1, 0, 0], 'z': [1, 1, 1, 1, 0]}

        def case(task, cert, schema=None):
            return {'task': task, 'replies': [{'schema': schema or task['schema'], 'certificate': cert}]}
        return {
            'coboundary_potential_valid': (case(cob, {'phi': {'a': 0, 'b': 1, 'c': 3}}), 'HOST_CERTIFIED'),
            'l1_dual_pair_optimal': (case(l1, dual), 'HOST_CERTIFIED'),
            'canonical_rational_solution': (case(rat, {'x': ['4/5', '7/5']}), 'HOST_CERTIFIED'),
            'non_canonical_rational': (case(rat, {'x': ['8/10', '7/5']}), 'REFUSED'),
            'dual_not_a_circulation': (case(l1, {**dual, 'z': [1, 0, 1, 0, 0]}), 'REFUSED'),
            'ill_typed_short_dual': (case(l1, {**dual, 'z': [1, 1, 1, 1]}), 'REFUSED'),
            'float_in_certificate': (case(l1, {**dual, 'f': {**dual['f'], 'b': -1.0}}), 'REFUSED'),
            'wrong_schema_named': (case(cob, {'phi': {'a': 0, 'b': 1, 'c': 3}}, 'canonical_rational'), 'REFUSED'),
        }
