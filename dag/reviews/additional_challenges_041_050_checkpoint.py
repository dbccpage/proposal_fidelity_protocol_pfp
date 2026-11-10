"""Substantive notes entered only after displayed full-body reads."""
from additional_challenges_041_050_audit import *

C041={
 'CHALLENGE.md':'Planned finite decidable core-Lean proof/refutation task; formal validity conditional on kernel/toolchain and axiom closure. Planned parsed command whitelist, independent lean4checker replay, 60s/default heartbeats, 4.34.0 pin and range-splitter exceed implementation. Model-budget capability and scientific claims explicitly bounded.',
 'participant_packet/TASK.md':'Participant theorem-body contract, strict aux commands and target equality, 4.34.1 pin. Correction accurately separates judge-file output and refuses UNKNOWN/OOS scoring; older inline compilation block remains historical. No JSON-schema engine or toolchain-version equality enforcement in owner.',
 'judge_packet/checkers/dual_evaluator.py':'Requires exact/independent Boolean agreement and same proof kind; separates abstention/refusal/infra from proof success. Both use same wrapper; dual is not an independent kernel implementation.',
 'judge_packet/checkers/exact_checker.py':'Checks matching IDs, nonempty proof, aux first token, two-stage compiler result and axiom whitelist. Missing IDs equal None; nonstring prelude is interpolated and rejected by Lean, while unhashable status crashes Python set membership. Aux first token is not parsed complete command list. Refusal witness content ignored but no refusal is a verified proof.',
 'judge_packet/checkers/independent_checker.py':'Clean elaboration then same verify_submission path and same axiom parser. No lean4checker or comparison to a separately reified clean expression; judge expected definition protects ordinary namespace shadowing. Does not independently enforce aux declaration whitelist.',
 'reference_solver/lean_compiler.py':'Raw regex ban scan including comments, PATH-selected Lean, timeout subprocess, separate Submission.olean/Judge.lean with copied target and axiom print. Shared wrapper has no OS sandbox, no version equality or binary hash, no parsed command-list whitelist. Native controls distinguish these limits from kernel proof validity.',
 'reference_solver/tactic_portfolio.py':'Seven fixed proof and three refutation scripts; retries infrastructure failures once, distinguishes repeated timeouts, then abstains. No range-split implementation despite header. Single-file solver check differs from two-stage judge; DDC closure is owner check only.',
 'reference_solver/solver.py':'Wraps fixed tactic portfolio with C,I,D,E,T or M traces. D/E scores are assigned from final status, not a measured per-tactic strict descent history. No provider call here.',
 'reference_solver/ddc_tracer.py':'Validates alphabet membership and stores supplied scores; no strict descent, zero gamma2, or mathematical correctness enforcement. Trace string alone does not prove kernel execution.',
 'reference_solver/symbol_game_experiment.py':'Exploratory prompt-method runner, full reply custody and separate outcomes; no actual attention/logit hooks. M5 omits prelude; CLI imports a matrix module absent from this frozen/current directory. Network-capable code was read only and never executed; external infrastructure remains a dependency.',
 'reference_solver/synthesize_matrix_report.py':'Aggregates retained scalar counts and known costs, corrected to avoid fixed findings. Tier naming uses model substrings, no parameter authentication; totals trust input records, no independent proof or billing validation.',
 'participant_packet/runner.py':'Calls reference solver and exact checker in-process, writes every answer even failures, then calls all answers verified in terminal message. Not U09 sandbox or independent replay; not run because it overwrites historical answers.',
 'participant_packet/generate_public_examples.py':'Defines 12 finite/arithmetic/table/refutation examples; generation runs solver+dual and accepts warranted refusal separately. Writes original example/answer paths, so not run. Claimed range split examples are ordinary small Nat statements.',
 'judge_packet/generate_cases.py':'Defines 40 base+16 controls+8 poison+48 mutants and raw-byte manifests. Base08 wrongly labels existence of x^2=3 mod11 REFUTATION: x=5 gives25 mod11=3. Labels are hard-coded, not computed by second checker as CHALLENGE promises. Poison and mutation coverage only bounded; generation not run.',
 'tests/conftest.py':'Import-path setup only, no math checks; searches provider directory but performs no provider calls.',
 'tests/test_c041_dual_checkers.py':'Positive small Fin proof and rejection of sorry/native_decide/illicit aux/wrong nonempty ID. Does not test absent IDs, pin equality, or multi-command aux blocks.',
 'tests/test_c041_participant_packet.py':'Checks 4.34.1 text, budget config, twelve examples and syntactically parsed answer fields; does not compile retained proofs or authenticate receipts.',
 'tests/test_c041_portfolio_infra_errors.py':'Stub-based regression tests for retry/timeout/infra distinctions; meaningful control-flow evidence, explicitly no Lean process and no theorem proof.',
 'tests/test_c041_refusals_and_lean_judge_hardening.py':'Native tests for printed axiom spoof, sorryAx, escape tokens, namespace target shadowing, refusal scoring and missing Lean. Uses any PATH toolchain and skip by executable presence, not version; covers known bypass classes only.',
 'tests/test_lean_compiler.py':'Small rfl/propext compilation, banned tokens and syntax diagnostics; does not cover parsed command enforcement or toolchain pin.',
 'tests/test_tactic_portfolio.py':'Three native portfolio controls: finite addition proof, false finite shift refutation, malformed prelude refusal. No completeness or large-case proof-search evidence.'}

def c041():
    record('c041',C041)
    n=read('_notes.json')
    n['family_assessments'].append({'family':'C041',
      'math':'Theorem bodies are checked against a judge-authored proposition and axiom closure restricted to propext/Quot.sound. This is conditional Lean validity. Refusals never count as proofs. The two routes share the same compiler/axiom parser; no independent lean4checker replay is implemented.',
      'data':'Data replay/disposition pending at this checkpoint.',
      'probe_artifact':'additional_challenges_041_050_c041_probes.json',
      'findings':[
        {'id':'AC41-F01','claim':'Both checker routes use arbitrary PATH Lean without enforcing the advertised pin; CHALLENGE says4.34.0, TASK4.34.1, current root/installed toolchain4.35.0. Native controls used only the installed4.35.0 and are explicitly scoped to it.'},
        {'id':'AC41-F02','claim':'Generator labels x^2=3 in Fin11 REFUTATION although5^2 mod11=3. Hard-coded expected labels are not independent checker ground truth.'},
        {'id':'AC41-F03','claim':'Auxiliary declaration scan checks only the first token of each string, permitting extra open commands after an allowed def; both missing IDs also compare equal and a correct proof is accepted without required case_id.'},
        {'id':'AC41-F04','claim':'An array-valued status crashes exact verification with TypeError rather than yielding a structured rejection. Finite/decidable domain and statement-length bounds remain trusted input premises.'}],
      'limits':['Native bounded controls used installed Lean4.35.0; no version installation or heavy build.','Neither raw regex scanning nor a subprocess timeout is a parsed command whitelist or an OS sandbox.','Full Lean proofs for every retained case are not claimed; source and data dispositions remain distinct.','Live experiment module is exploratory, with no logit/attention mechanisms or new provider evidence.']})
    write('_notes.json',n); report()
if __name__=='__main__': c041()
