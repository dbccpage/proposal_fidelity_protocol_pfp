# Current-task guard review

Read the current task and the learned guard. Identify exact source/target carriers and the protected answer before reuse. In the supplied nine-pair example, compare u != 1 learned for d=1 with task-matched u != d: a valid d=2 pair (1,1) maps to (2,0), so the fixed guard rejects it. Retain the benign d=1 control and exclude out-of-image (1,0). For other tasks, require their own checked counterexample or sound transport; metadata drift alone is not semantic failure. This candidate prompt supplies neither independent checker evidence nor OEEIS admission.

For a regulation request, name the detector, independent witness and original
task. Return UNKNOWN for unavailable verification. The harmful control is a
checked valid d=2 answer rejected by the fixed d=1 guard; the benign control is
the task-matched guard retaining valid answers while rejecting invalid ones.
Use the existing Treg suspension/repair action only for the learned detector.
Preserve mandatory budget, provenance, authorization and original-task checks;
stopping a branch retains evidence and never changes an answer into PASS.
