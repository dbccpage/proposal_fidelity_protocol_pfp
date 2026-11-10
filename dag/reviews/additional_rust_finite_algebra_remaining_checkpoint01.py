"""Persist substantive reads; no original code execution."""
import sys
sys.dont_write_bytecode=True
import additional_rust_finite_algebra_remaining_audit as a

for crate,lines,note in [
 ('core_number_theory',76,'Dependencies delegate scalar laws/matrices to linear algebra, intervals to kernel and arithmetic to num crates. autotests=false, twelve explicit sibling integration targets; declarations do not establish collection or pass status.'),
 ('core_lie_theory',90,'Depends on number theory, category theory and linear algebra. autotests=false with seventeen explicit sibling integration targets. Description of exact group/Lie theory is an implementation claim requiring each owner; manifest does not prove it.'),
 ('core_fusion_categories',33,'Exact-symbol dependencies on number theory, linear algebra and num crates; autotests=false with three named integration targets. Multiplicity-free scope is explicit. No invocation or tests executed.'),
 ('core_holonomy',59,'Discrete gauge implementation depends on kernel/homology, linear-algebra Smith backend, rational/bigint, serde and hashing. autotests=false with eight explicit integration targets. Manifest pins semver requirements, not complete resolved execution environment.')]:
 a.record('code/rust/'+crate+'/Cargo.toml',1,lines,note)

n='code/rust/core_number_theory/src/lib.rs'
a.record(n,1,159,'Full module map and appended FareyEdge admission read. FareyEdge normalizes each rational then requires determinant plus or minus one with arbitrary precision; represents an unoriented adjacent pair in the Farey graph, without a fixed Farey-sequence denominator bound, ordering or saved endpoint binding. Zero denominator refused. Three tests exercise positive, negative and malformed denominator cases. Broad arithmetic/no-float and mutation-count prose remains subordinate to owners; appended six-killed comment is not a retained mutation execution receipt.')
l='code/rust/core_lie_theory/src/lib.rs'
a.record(l,1,171,'Full exact-Lie module map and So2Carrier admission read. Private four fields store input rational and reduced square determinant. Checked i128 arithmetic refuses overflow including MIN abs; determinant cross-products can conservatively refuse mathematically valid large inputs. Trace check is constant zero for the constructed skew template and not validation of an arbitrary supplied matrix. Only two inline tests. Module-level exact/no-tolerance and physical group-identification prose awaits owner assessment; no authority arises from labels.')
f='code/rust/core_fusion_categories/src/lib.rs'
a.record(f,1,84,'Full module declarations and FusionChannelWitness read. Private witness checks positive u64 dimensions/multiplicity and exactly one product identity dim_a*dim_b=multiplicity*dim_c with checked overflow. This is a single-channel dimension balance, not fusion-ring associativity, sum over all outputs, F/R coherence, or an anyon realization; existing deeper constructors are unchanged. Four inline cases include two valid identities and mismatched/zero controls. Mutation-accounting comment is declarative.')
h='code/rust/core_holonomy/src/lib.rs'
a.record(h,1,228,'Full exports, ClosedDisplacement and repeated capacity admission body/tests read directly. ClosedDisplacement requires a nonempty integer-step list and positive cyclic order, sums with checked i128, computes Euclidean residue and reconstructs its congruence, then insists residue zero. This is abelian cyclic displacement, not graph continuity or general matrix holonomy; source steps are not retained. Separate capacity record enforces only 1<=items<=capacity and has no holonomy payload. Historical governing-rule prose is data. Tests cover these declared scalar conditions, not overall module mathematics.')
notes=a.read('_notes.json')
notes['claims'].append({'id':'RFA-CL001','statement':'The four library-entry admissions enforce narrow arithmetic predicates: normalized Farey determinant magnitude one, an i128-bounded rational skew-block square, one positive fusion-channel product, and nonempty cyclic displacement zero. They do not by themselves certify the full domain modules or promote authority.','evidence':[a.ev(n,118,158),a.ev(l,86,169),a.ev(f,61,83),a.ev(h,52,97),a.ev(h,104,227)],'limits':'Source reasoning only; deeper module owners pending, sibling integration tests outside this scope, no Rust execution. Mutation-count comments do not supply reproducible mutation evidence.'})
a.write('_notes.json',notes)
a.report();a.validate('checkpoint01')
