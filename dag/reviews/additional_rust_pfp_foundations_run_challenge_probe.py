"""Compile the unchanged challenge owner; never invoke its sandbox runner."""
import hashlib
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).parent
P = 'additional_rust_pfp_foundations'
deps = ROOT / 'code/rust/target/debug/deps'
prior = json.loads((HERE / (P + '_f2_validation.json')).read_text())
libs = {pathlib.Path(x['path']).name[3:].split('-')[0]: ROOT / x['path'] for x in prior['libraries']}
for name in ['sha2', 'core_sandbox']:
    libs[name] = max(deps.glob('lib' + name + '-*.rlib'), key=lambda p: p.stat().st_mtime)
owner = ROOT / 'code/rust/pfp/src/challenge.rs'
src = HERE / (P + '_challenge_probe.rs')
src.write_text('#[path=' + json.dumps(owner.as_posix()) + '] mod challenge;\n' + r'''
fn main() {
    use challenge::*;
    let commitment = JudgeCommitmentV1::new("synthetic", b"fixed manifest", "a", "bc");
    let freeze = FreezeRecordV1::new("synthetic", b"fixed deliverable", commitment.commitment_hash());
    let mut judge = JudgePacketV1 {
        challenge_id: "synthetic".into(), commitment_hash: "unrelated".into(),
        committed_at_utc: "after freeze".into(), operator: "changed".into(), version: "changed".into(),
        hidden_cases: vec![serde_json::json!({"input":7,"expected":11})],
        checker_a_id: "unbound-a".into(), checker_b_id: "unbound-b".into(), authority_effect:"anything".into()
    };
    assert!(verify_challenge_commit_reveal_prerequisites(&judge, &commitment, &freeze, b"fixed deliverable").is_ok());
    judge.hidden_cases[0]["expected"] = serde_json::json!(99);
    assert!(verify_challenge_commit_reveal_prerequisites(&judge, &commitment, &freeze, b"fixed deliverable").is_ok());
    println!("changed_judge_content_wrong_commitment_and_reversed_time_pass_prerequisites=true");
    let checker = ExactMatchChecker::new("same", "expected");
    let case = &judge.hidden_cases[0];
    assert_eq!(evaluate_dual_checkers(&checker, &checker, case, case), DisjointOutcome::Correct);
    println!("echo_of_complete_case_passes_same_checker_twice=true");
    let mut alias = commitment.clone(); alias.operator="ab".into(); alias.version="c".into();
    assert_ne!(alias, commitment); assert_eq!(alias.commitment_hash(), commitment.commitment_hash());
    println!("unframed_operator_version_alias=true");
    struct Panics;
    impl CaseChecker for Panics {
        fn checker_id(&self)->&str { "panic" }
        fn check(&self,_:&serde_json::Value,_:&serde_json::Value)->Result<bool,String>{ panic!("synthetic checker panic") }
    }
    assert!(std::panic::catch_unwind(|| evaluate_dual_checkers(&Panics, &checker, case, case)).is_err());
    println!("checker_panic_escapes_pause_classification=true");
}
''', encoding='utf-8')
exe = HERE / (P + '_challenge_probe.exe')
cmd = ['rustc', '--edition=2021', '-Awarnings', '-L', 'dependency=' + str(deps)]
for name, path in libs.items():
    cmd += ['--extern', name + '=' + str(path)]
cmd += [str(src), '-o', str(exe)]
c = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
run = {'command': cmd, 'compile_exit': c.returncode, 'compile_output': c.stdout + c.stderr}
if c.returncode == 0:
    r = subprocess.run([str(exe)], capture_output=True, text=True, timeout=15)
    run.update(exit_code=r.returncode, output=r.stdout + r.stderr)
receipt = {'source_files': [{'path': owner.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(owner.read_bytes()).hexdigest()}], 'libraries': [{'path': q.relative_to(ROOT).as_posix(), 'sha256': hashlib.sha256(q.read_bytes()).hexdigest()} for q in libs.values()], 'probe_sha256': hashlib.sha256(src.read_bytes()).hexdigest(), 'runs': [run], 'limits': 'Complete unchanged owner included with cached libraries. Only synthetic in-memory values; no sandbox, candidate process, provider, network, actual judge cases or private benchmark access. The echo observation models the exact full-case argument shown in source; it does not claim an end-to-end sandbox run.'}
(HERE / (P + '_challenge_validation.json')).write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({k:v for k,v in run.items() if k!='command'}, indent=2))
